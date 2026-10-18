"""Simulation of the palletizer cell: the reality around the robot.

Loaded by the robot controller (run/pyrapid_motion.py) with

    PYRAPID_SIMULATION=examples/pallettizer/cell.py

The RAPID program does not know this file: it moves the robot and uses the I/O
signals of EIO.cfg, as on the robot. The cell answers to the signals:

- doOrder<n> (pulse) with goOrderCount<n>: the pick line n delivers that number of
  products, one at a time on the pick point; diProduct<n> is 1 while a product is
  on the pick point;
- doGripper: the gripper closes (1) and takes the product under it, or opens (0)
  and leaves it where it is; diGripperClosed follows after GRIPPER_TIME;
- doPalletIn<n> (pulse): an empty pallet comes on the station n, then diPallet<n>
  is 1; doPalletOut<n> (pulse): the pallet leaves with its products.

With the viewer (PYRAPID_VIEWER=meshcat) the cell is drawn with the robot: the
floor (floor.png next to this file, or a grid), the conveyors, the stations, the
pallets, the products and the gripper. The gripper is grey when open, green when
it holds a product, yellow when it closed on nothing.

The positions must match the points taught in environment.mod, as on a real cell.
"""

import math
import os
import struct
import sys
import zlib
from dataclasses import dataclass
from typing import Any, Optional

import numpy as np
import pinocchio as pin

# the gripper: 450 x 450 x 250 mm under the flange, the TCP at its bottom face
GRIPPER_SIZE = (0.45, 0.45, 0.25)
# a product is taken when the top of the product is this close to the TCP (m)
GRIP_TOLERANCE = 0.02
# time to close or open the gripper (s)
GRIPPER_TIME = 0.2
# time for the conveyor to bring the next product on the pick point (s)
CONVEYOR_TIME = 1.0
# time for a pallet to come on the station or to leave it (s)
PALLET_TIME = 2.0

# pick lines: product on the end of the conveyor (center of the bottom, m), direction
# of the conveyor (degrees), size of the products (m), color
PICK_LINES = {
    1: {
        "point": (-0.5814, 1.5975, 0.7),
        "angle": 110.0,
        "size": (0.4, 0.4, 0.25),
        "color": 0xFF7F0E,
    },
    2: {
        "point": (-0.5814, -1.5975, 0.7),
        "angle": -110.0,
        "size": (0.4, 0.3, 0.15),
        "color": 0x17BECF,
    },
}
CONVEYOR_SIZE = (2.0, 0.6, 0.7)
CONVEYOR_CENTER = 2.5  # distance of the center of the conveyor from the robot (m)

# pallet stations: corner of the pallet (m) and angle of its x axis (degrees)
STATIONS = {
    1: {"origin": (1.3049, 0.3117, 0.0), "angle": 40.0},
    2: {"origin": (0.5336, -1.2310, 0.0), "angle": -40.0},
}
PALLET_SIZE = (0.8, 1.2, 0.15)

FLOOR_SIZE = 6.0


def rotation_z(degrees: float) -> Any:
    return pin.utils.rotate("z", math.radians(degrees))


def placement(rotation: Any, position: Any) -> Any:
    return pin.SE3(np.asarray(rotation, dtype=float), np.asarray(position, dtype=float))


@dataclass
class Box:
    name: str
    size: tuple[float, float, float]
    color: int
    # center of the bottom face: in the world, or on the flange when attached
    placement: Any
    attached: bool = False


def grid_png(pixels: int = 512) -> bytes:
    """a grey floor with a line every 0.5 m, as PNG"""
    step = pixels / (FLOOR_SIZE / 0.5)
    rows = []
    for y in range(pixels):
        row = bytearray(b"\0")
        for x in range(pixels):
            line = (x % step) < 1.5 or (y % step) < 1.5
            row += bytes((150, 150, 150) if line else (205, 205, 200))
        rows.append(bytes(row))

    def chunk(kind: bytes, data: bytes) -> bytes:
        crc = zlib.crc32(kind + data) & 0xFFFFFFFF
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", crc)

    header = struct.pack(">IIBBBBB", pixels, pixels, 8, 2, 0, 0, 0)
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", header)
        + chunk(b"IDAT", zlib.compress(b"".join(rows)))
        + chunk(b"IEND", b"")
    )


class Cell:
    def __init__(self, world: Any) -> None:
        self.world = world
        self.boxes: dict[str, Box] = {}
        self.ordered = {n: 0 for n in PICK_LINES}
        self.feeding = {n: False for n in PICK_LINES}
        self.at_pick: dict[int, Optional[str]] = {n: None for n in PICK_LINES}
        self.on_pallet: dict[int, list[str]] = {n: [] for n in STATIONS}
        self.pallet: dict[int, Optional[str]] = {n: None for n in STATIONS}
        self.shipped = {n: [0, 0] for n in STATIONS}  # pallets, products
        self.held: Optional[str] = None
        self.products = 0
        self.gripper = Box("gripper", GRIPPER_SIZE, 0x9A9A9A, pin.SE3.Identity(), True)
        self.draw_environment()

    # ------------------------------------------------------------- drawing

    def viewer(self) -> Any:
        return self.world.viewer()

    def draw(self, box: Box) -> None:
        viewer = self.viewer()
        if viewer is None:
            return
        import meshcat.geometry as g

        viewer["cell/" + box.name].set_object(
            g.Box(list(box.size)), g.MeshLambertMaterial(color=box.color)
        )
        self.move(box)

    def move(self, box: Box) -> None:
        viewer = self.viewer()
        if viewer is None:
            return
        world = self.world.flange() * box.placement if box.attached else box.placement
        center = world * placement(np.eye(3), (0, 0, box.size[2] / 2))
        viewer["cell/" + box.name].set_transform(center.homogeneous)

    def add(self, box: Box) -> None:
        self.boxes[box.name] = box
        self.draw(box)

    def remove(self, name: str) -> None:
        del self.boxes[name]
        viewer = self.viewer()
        if viewer is not None:
            viewer["cell/" + name].delete()

    def draw_environment(self) -> None:
        viewer = self.viewer()
        if viewer is None:
            return
        import meshcat.geometry as g

        image = os.path.join(os.path.dirname(os.path.abspath(__file__)), "floor.png")
        png = g.PngImage.from_file(image) if os.path.exists(image) else g.PngImage(grid_png())
        viewer["cell/floor"].set_object(
            g.Box([FLOOR_SIZE, FLOOR_SIZE, 0.002]),
            g.MeshLambertMaterial(map=g.ImageTexture(image=png), color=0xFFFFFF),
        )
        viewer["cell/floor"].set_transform(placement(np.eye(3), (0, 0, -0.002)).homogeneous)
        # a view of the whole cell
        self.world.camera((3.4, 2.4, 2.4), 1.0)
        for n, line in PICK_LINES.items():
            angle = float(line["angle"])  # type: ignore[arg-type]
            direction = rotation_z(angle)
            center = direction @ np.array([CONVEYOR_CENTER, 0, 0])
            self.draw(Box("conveyor%d" % n, CONVEYOR_SIZE, 0x505050, placement(direction, center)))
        for n in STATIONS:
            marker = self.station(n) * placement(np.eye(3), (0.4, 0.6, 0))
            self.draw(Box("station%d" % n, (0.9, 1.3, 0.01), 0xFFD92F, marker))
        self.draw(self.gripper)

    def set_gripper_color(self, color: int) -> None:
        self.gripper.color = color
        self.draw(self.gripper)

    # ------------------------------------------------------------- the cell

    @staticmethod
    def station(n: int) -> Any:
        station = STATIONS[n]
        return placement(rotation_z(float(station["angle"])), station["origin"])  # type: ignore[arg-type]

    def tcp(self) -> Any:
        return self.world.flange() * placement(np.eye(3), (0, 0, GRIPPER_SIZE[2]))

    def feed(self, n: int) -> None:
        """the conveyor brings the next ordered product"""
        if self.at_pick[n] is None and self.ordered[n] > 0 and not self.feeding[n]:
            self.feeding[n] = True
            self.world.after(CONVEYOR_TIME, lambda: self.arrive(n))

    def arrive(self, n: int) -> None:
        line = PICK_LINES[n]
        self.products += 1
        name = "product%d" % (self.products,)
        where = placement(rotation_z(float(line["angle"])), line["point"])  # type: ignore[arg-type]
        self.add(Box(name, line["size"], int(line["color"]), where))  # type: ignore[arg-type]
        self.at_pick[n] = name
        self.ordered[n] -= 1
        self.feeding[n] = False
        self.world.set_signal("diProduct%d" % n, 1)

    def close(self) -> None:
        tcp = self.tcp().translation
        for box in self.boxes.values():
            if box.attached or not box.name.startswith("product"):
                continue
            top = (box.placement * placement(np.eye(3), (0, 0, box.size[2]))).translation
            if np.linalg.norm(top - tcp) < GRIP_TOLERANCE:
                box.placement = self.world.flange().inverse() * box.placement
                box.attached = True
                self.held = box.name
                for n, name in self.at_pick.items():
                    if name == box.name:
                        self.at_pick[n] = None
                        self.world.set_signal("diProduct%d" % n, 0)
                        self.feed(n)
                for names in self.on_pallet.values():
                    if box.name in names:
                        names.remove(box.name)
                break
        if self.held is None:
            print("cell: the gripper closed on nothing", file=sys.stderr)
        self.set_gripper_color(0x2CA02C if self.held else 0xFFD92F)
        self.world.set_signal("diGripperClosed", 1)

    def open(self) -> None:
        if self.held is not None:
            box = self.boxes[self.held]
            box.placement = self.world.flange() * box.placement
            box.attached = False
            self.move(box)
            for n in STATIONS:
                local = self.station(n).inverse() * box.placement
                x, y = local.translation[:2]
                if 0 <= x <= PALLET_SIZE[0] and 0 <= y <= PALLET_SIZE[1]:
                    self.on_pallet[n].append(box.name)
            self.held = None
        self.set_gripper_color(0x9A9A9A)
        self.world.set_signal("diGripperClosed", 0)

    def pallet_in(self, n: int) -> None:
        name = "pallet%d" % n
        where = self.station(n) * placement(np.eye(3), (PALLET_SIZE[0] / 2, PALLET_SIZE[1] / 2, 0))
        self.add(Box(name, PALLET_SIZE, 0xC8A165, where))
        self.pallet[n] = name
        self.world.set_signal("diPallet%d" % n, 1)

    def pallet_out(self, n: int) -> None:
        if self.pallet[n] is not None:
            self.remove("pallet%d" % n)
            self.pallet[n] = None
            self.shipped[n][0] += 1
        self.shipped[n][1] += len(self.on_pallet[n])
        for name in self.on_pallet[n]:
            self.remove(name)
        self.on_pallet[n] = []
        self.world.set_signal("diPallet%d" % n, 0)

    # ------------------------------------------------------------- actions

    def signal(self, world: Any, name: str, value: Any) -> None:
        if name == "doGripper":
            self.world.after(GRIPPER_TIME, self.close if value else self.open)
        elif name.startswith("doOrder") and value == 1:
            n = int(name[len("doOrder") :])
            self.ordered[n] += int(world.signal("goOrderCount%d" % n))
            self.feed(n)
        elif name.startswith("doPalletIn") and value == 1:
            n = int(name[len("doPalletIn") :])
            self.world.after(PALLET_TIME, lambda: self.pallet_in(n))
        elif name.startswith("doPalletOut") and value == 1:
            n = int(name[len("doPalletOut") :])
            self.world.after(PALLET_TIME, lambda: self.pallet_out(n))

    def frame(self, world: Any) -> None:
        """the gripper and the product it holds follow the robot"""
        self.move(self.gripper)
        if self.held is not None:
            self.move(self.boxes[self.held])

    def finish(self, world: Any) -> None:
        for n, (pallets, products) in self.shipped.items():
            print("cell: station %d shipped %d pallets, %d products" % (n, pallets, products))
        sys.stdout.flush()


def setup(world: Any) -> None:
    cell = Cell(world)
    world.on_signal(cell.signal)
    world.on_frame(cell.frame)
    world.on_finish(cell.finish)
