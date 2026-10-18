"""Draw the stylized parts of the IRB 460-110/2.4 (stylized/*.stl, in the repository).

The parts are drawn from scratch with CadQuery: boxes, cylinders and extruded profiles
that give the outline and the space taken by each link of the robot. The only data are
the lengths of the kinematic model (the pivots of irb460_110_240.urdf) and a few
dimensions of the parts that a picture of the robot shows; nothing is copied from the
CAD model of ABB. Each part is written in the frame of its link (mm), so the URDF uses it
without offsets.

Needs CadQuery, not a dependency of the project:

    pip install cadquery
    python models/irb460_110_240/build_parts.py
"""

import os
import sys
from typing import Any, Callable

import cadquery as cq

HERE = os.path.dirname(os.path.abspath(__file__))
OUTPUT = os.path.join(HERE, "stylized")


def box(x: tuple[float, float], y: tuple[float, float], z: tuple[float, float], fillet: float = 0) -> Any:
    """a box with the given extents, with rounded edges"""
    solid = (
        cq.Workplane("XY")
        .box(x[1] - x[0], y[1] - y[0], z[1] - z[0], centered=False)
        .translate((x[0], y[0], z[0]))
    )
    return solid.edges().fillet(fillet) if fillet else solid


def cylinder(axis: str, center: tuple[float, float, float], radius: float, length: float) -> Any:
    """a cylinder along x, y or z, centered at center"""
    normal = {"x": (1, 0, 0), "y": (0, 1, 0), "z": (0, 0, 1)}[axis]
    plane = cq.Plane(origin=center, xDir=(0, 0, 1) if axis != "z" else (1, 0, 0), normal=normal)
    return cq.Workplane(plane).circle(radius).extrude(length / 2, both=True)


def profile(points: list[tuple[float, float]], y: tuple[float, float]) -> Any:
    """a polygon in the plane xz, extruded between the two values of y"""
    plane = cq.Plane(origin=(0, y[0], 0), xDir=(1, 0, 0), normal=(0, 1, 0))
    # the normal (0, 1, 0) makes the local y the axis -z: the points are mirrored
    shape = cq.Workplane(plane).polyline([(px, -pz) for px, pz in points]).close()
    return shape.extrude(y[1] - y[0])


def foot() -> Any:
    """the fixed base: a plate with the housing of the axis 1"""
    plate = box((-624, 384), (-360, 360), (0, 72), 12)
    housing = box((-420, 300), (-300, 300), (72, 288), 40)
    return plate.union(housing)


def swing() -> Any:
    """the turning column of the axis 1, with the shoulder at (260, 0, 742.5)"""
    column = box((-252, 420), (-300, 300), (216, 972), 45)
    # the shoulder: the pivot of the lower arm and of the parallelograms
    shoulder = cylinder("y", (260, 0, 742.5), 190, 560)
    motor = cylinder("y", (260, 0, 742.5), 110, 760)
    # the lever of the axis 2 on the back
    back = box((-252, 100), (-588, -300), (300, 700), 30)
    return column.union(shoulder).union(motor).union(back)


def lower_arm() -> Any:
    """the lower arm, from the pivot of the axis 2 to the elbow, 945 mm along z"""
    tube = box((-110, 110), (-110, 110), (0, 945), 40)
    root = cylinder("y", (0, 0, 0), 144, 288)
    elbow = cylinder("y", (0, 0, 945), 144, 288)
    return tube.union(root).union(elbow)


def upper_arm() -> Any:
    """the upper arm, 1025 mm along x from the elbow, with the lever at the back"""
    side = [(-468, -60), (-300, -84), (1080, -60), (1080, 90), (0, 204), (-300, 120), (-468, 60)]
    arm = profile(side, (-84, 84))
    head = cylinder("y", (1025, 0, 0), 90, 168)
    return arm.union(head)


def tilt() -> Any:
    """the wrist housing at the end of the upper arm: it stays horizontal"""
    housing = box((-60, 324), (-132, 132), (-216, 240), 30)
    pivot = cylinder("y", (0, 0, 0), 90, 360)
    return housing.union(pivot)


def disk() -> Any:
    """the flange of the axis 6"""
    return cylinder("z", (0, 0, 18), 84, 36)


def link_plate() -> Any:
    """the plate that the lower link and the upper link hold, beside the lower arm"""
    side = [(-312, -60), (276, -60), (276, 240), (0, 240), (-312, 60)]
    return profile(side, (-288, -144))


def upper_link() -> Any:
    """the rod parallel to the upper arm, from the plate to the wrist housing"""
    return cylinder("x", (510, -168, 0), 32, 1116).union(cylinder("y", (0, -168, 0), 48, 96))


def p_arm() -> Any:
    """the lever of the motor of the axis 3 on the shoulder"""
    side = [(-444, -144), (-300, -144), (144, 0), (144, 216), (-300, 216), (-444, 100)]
    return profile(side, (-156, 36))


def p_link() -> Any:
    """the rod parallel to the lower arm, from the lever to the upper arm"""
    return cylinder("z", (0, -36, 504), 36, 1008).union(cylinder("y", (0, -36, 0), 60, 144))


def lower_link() -> Any:
    """the rod parallel to the lower arm, from the swing to the plate"""
    return cylinder("z", (-3, -264, 474), 30, 1044).union(cylinder("y", (0, -264, 0), 48, 48))


PARTS: dict[str, Callable[[], Any]] = {
    "foot": foot,
    "swing": swing,
    "lower_arm": lower_arm,
    "upper_arm": upper_arm,
    "tilt": tilt,
    "disk": disk,
    "link_plate": link_plate,
    "upper_link": upper_link,
    "p_arm": p_arm,
    "p_link": p_link,
    "lower_link": lower_link,
}


def main() -> int:
    os.makedirs(OUTPUT, exist_ok=True)
    for name, make in PARTS.items():
        path = os.path.join(OUTPUT, name + ".stl")
        cq.exporters.export(make(), path, tolerance=1.0, angularTolerance=0.3)
        print("%-11s -> %s" % (name, os.path.relpath(path)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
