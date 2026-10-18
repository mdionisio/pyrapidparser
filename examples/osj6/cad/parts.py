"""Parts of osj6, the robot with oblique swivel joints, as a modular kit (CadQuery).

Every end of every piece is the same interface (a face): a plate with a bore for the
cables and two circles of 8 holes. The pieces:

    piece45   a short tube with a flat face and a 45 degree face (all equal)
    spacer    a tube with two flat faces, to make the arm longer
    base      the foot and a flat face on top
    flange    the tool flange
    ring      the joint: a slewing ring printed in 3 parts (inner ring with the internal
              gear, outer ring in two halves) with balls

A joint is face + ring + face: the outer ring is screwed to the face of one piece (the
piece with the motor), the inner ring to the face of the other piece. The inner ring
stands out by RING_STEP on one side, the outer ring on the other: two equal faces touch
one ring each. Two faces screwed together without a ring are a rigid joint, turned by a
multiple of 45 degrees (the holes): a module of the arm is piece45 + (spacers) + piece45.

The internal gear has module 1 like the LEGO Technic gears: the LEGO gear with 12 teeth
on a motor 24 mm (3 holes) from the axis of the joint meshes with it (ratio 5:1). The
motor is held by a bracket screwed inside the face: lego_bracket for the LEGO Medium
Angular Motor (Technic pins), nema14_bracket for a NEMA 14 stepper with the printed
pinion.

Units: mm. The frame of a face: z out of the piece, the surface of the face at z = 0.
The frame of a joint: z along the axis, 0 in the middle of the ring; the face of the
piece with the motor is at z = -JOINT, the other at z = +JOINT.

    hatch run cad:python examples/osj6/cad/parts.py

writes the parts in step/ and stl/ next to this file, and the robot assembled at the
zero position (assembly.step).
"""

import math
import os
import sys
from typing import Optional

import numpy as np
import cadquery as cq
from OCP.gp import gp_Trsf

HERE = os.path.dirname(os.path.abspath(__file__))

# tube and pieces
D = 100.0  # outer diameter of the tube
WALL = 3.0
ANGLE = math.radians(45)  # the 45 degree face: its normal from the tube axis
PIECE45 = 70.0  # piece45: flat face to the center of the 45 degree face
SPACER = 60.0  # spacer: length (make more of them with other lengths)
BASE = 70.0  # base: floor to the face

# the arm: how many spacers between the pieces (the model of the simulation,
# models/osj6.urdf, is built from the same parts: build_model.py)
SHOULDER_SPACERS = 0  # between the joint of axis 1 and the shoulder piece45
MODULE_SPACERS = (0, 0, 0)  # between the two piece45 of each module (axes 2-3, 3-4, 4-5)
WRIST_SPACERS = 1  # between the wrist piece45 and the joint of axis 6 (room for its motor)
TOOL = 12.0  # tool flange: the tool face above the face of the flange
FOOT = 75.0  # radius of the foot of the base

# face (the interface of all the pieces)
FACE = 6.0  # thickness of the plate
FLANGE = 53.0  # radius of the collar of the face (over the tube)
BORE = 31.5  # cables, the pinion and the motor axle pass through it
INNER_HOLES = 34.5  # 8 holes: the inner ring, the motor bracket, rigid joints (M3)
OUTER_HOLES = 48.5  # 8 holes (turned by 22.5 degrees): the outer ring
INSERT = 4.2  # hole of the M3 heat-set inserts (also a loose hole for M3)
CLEARANCE = 3.4  # loose hole M3
HEAD = 6.2  # counterbore of the M3 screw heads

# slewing ring
JOINT = 7.0  # joint center to the face
RING_STEP = 1.0  # the inner ring stands out of the outer ring on one side, and back
BALL = 6.0  # ball diameter: 6 mm airsoft BB or steel ball
BALL_CLEARANCE = 0.15  # added to the ball in the grooves (printing tolerance)
GROOVE = "gothic"  # "gothic" (4 contact points), "v" (90 degree V), "round" (2 points)
CONFORMITY = 0.53  # radius of the arcs of the groove / ball ("gothic", "round")
BALLS_RADIUS = 41.0  # radius of the ball centers
RING_GAP = 0.5  # radial gap between the inner and the outer ring
RING_OUT = 53.0  # outer radius of the outer ring

# gears (module 1, pressure angle 20 degrees, like the LEGO Technic gears)
MODULE = 1.0
RING_TEETH = 60  # internal gear of the inner ring
PINION_TEETH = 12  # LEGO gear 12 teeth, or the printed pinion
BACKLASH = 0.2  # thinner teeth (printing tolerance and LEGO profile)
PINION_OFFSET = MODULE * (RING_TEETH - PINION_TEETH) / 2  # 24 mm: 3 LEGO holes

# LEGO Medium Angular Motor (LDraw 54696p02, CustomParts-51515 Mindstorms): axle at the
# origin along -y (the output), body 24 mm wide (x), from y -14.2 to +12, from z -11.6
# to +52 (+ the cable plug to 59.6); the output hub to y -20; pin holes on the sides
# (x = +-12) at y = +-8 and z = -8, +8, +56
LEGO_WIDTH = 24.0
LEGO_FRONT, LEGO_BACK = -14.2, 12.0
LEGO_HUB, LEGO_HUB_RADIUS = -20.0, 11.6
LEGO_START, LEGO_END, LEGO_PLUG = -11.6, 52.0, 59.6
LEGO_PIN_Y = (-8.0, 8.0)
LEGO_PIN_Z = (-8.0, 8.0, 56.0)
# the motor in the face frame: the axle at PINION_OFFSET in the direction LEGO_AXLE, the
# body toward LEGO_BODY. The motor is 71 mm long in a tube of 94: these directions fit in
# the pieces with a flat face and with a 45 degree face (the tube goes to -y going into
# the piece from a 45 degree face)
LEGO_AXLE = math.radians(215)
LEGO_BODY = math.radians(0)
TECHNIC_HOLE = 4.85  # Technic pin hole
TECHNIC_COUNTERBORE = 6.2  # the collar of the pin, 0.8 mm deep
STUD = 8.0

# NEMA 14 stepper
NEMA = 35.2
NEMA_HOLES = 26.0
NEMA_PILOT = 22.0
NEMA_LENGTH = 34.0
NEMA_SHAFT = 5.0
NEMA_AXLE = math.radians(235)  # direction of the shaft (the sides of the motor radial)

# hatch: a window in the wall with a cover screwed on 4 bosses
HATCH_WIDTH = 50.0
HATCH_MARGIN = 8.0

R = D / 2


# frames (4 x 4 matrices, mm)


def rot_x(a: float) -> np.ndarray:
    c, s = math.cos(a), math.sin(a)
    t = np.eye(4)
    t[1:3, 1:3] = [[c, -s], [s, c]]
    return t


def rot_y(a: float) -> np.ndarray:
    c, s = math.cos(a), math.sin(a)
    t = np.eye(4)
    t[0, 0], t[0, 2], t[2, 0], t[2, 2] = c, s, -s, c
    return t


def rot_z(a: float) -> np.ndarray:
    c, s = math.cos(a), math.sin(a)
    t = np.eye(4)
    t[0:2, 0:2] = [[c, -s], [s, c]]
    return t


def move(x: float = 0.0, y: float = 0.0, z: float = 0.0) -> np.ndarray:
    t = np.eye(4)
    t[:3, 3] = (x, y, z)
    return t


def place(shape: cq.Shape, t: np.ndarray) -> cq.Shape:
    trsf = gp_Trsf()
    trsf.SetValues(*[float(v) for v in t[:3, :].flatten()])
    return shape.moved(cq.Location(trsf))


# solids


def cylinder(radius: float, z0: float, z1: float, inner: float = 0.0) -> cq.Shape:
    solid = cq.Solid.makeCylinder(radius, z1 - z0, cq.Vector(0, 0, z0))
    if inner > 0:
        solid = solid.cut(cq.Solid.makeCylinder(inner, z1 - z0 + 2, cq.Vector(0, 0, z0 - 1)))
    return solid


def box(x0: float, x1: float, y0: float, y1: float, z0: float, z1: float) -> cq.Shape:
    return cq.Solid.makeBox(x1 - x0, y1 - y0, z1 - z0, cq.Vector(x0, y0, z0))


def half_space(t: np.ndarray) -> cq.Shape:
    """the side z < 0 of the frame t"""
    return place(box(-500, 500, -500, 500, -500, 0), t)


def revolve(points: list[tuple[float, float]]) -> cq.Shape:
    """a solid of revolution around z of the profile (r, z)"""
    return cq.Workplane("XZ").polyline(points).close().revolve(360, (0, 0, 0), (0, 1, 0)).val()


def holes(radius: float, count: int, start: float, diameter: float, z0: float, z1: float):
    shape: Optional[cq.Shape] = None
    for k in range(count):
        a = start + 2 * math.pi * k / count
        hole = cylinder(diameter / 2, z0, z1).moved(
            cq.Location(cq.Vector(radius * math.cos(a), radius * math.sin(a), 0))
        )
        shape = hole if shape is None else shape.fuse(hole)
    assert shape is not None
    return shape


def radial(radius: float, r0: float, r1: float, angle: float, z: float) -> cq.Shape:
    """a cylinder along the radius from r0 to r1, at the angle and the height z"""
    solid = cylinder(radius, r0, r1)
    return place(solid, rot_z(angle) @ move(z=z) @ rot_y(math.pi / 2))


def involute(teeth: int, thickness: float, addendum: float, dedendum: float) -> list:
    """outline of an external involute gear (module MODULE, 20 degrees); thickness is
    the tooth at the pitch circle, addendum and dedendum in modules"""
    m, alpha = MODULE, math.radians(20)
    rp = m * teeth / 2
    rb = rp * math.cos(alpha)
    ra = rp + m * addendum
    rf = rp - m * dedendum

    def inv(a: float) -> float:
        return math.tan(a) - a

    half = thickness / 2 / rp

    def half_angle(r: float) -> float:
        r = max(r, rb)
        return half + inv(alpha) - inv(math.acos(min(1.0, rb / r)))

    radii = [rf + (ra - rf) * i / 10 for i in range(11)]
    points = []
    for i in range(teeth):
        center = 2 * math.pi * i / teeth
        flank = [(r, center - half_angle(r)) for r in radii]
        flank += [(r, center + half_angle(r)) for r in reversed(radii)]
        start = center + half_angle(rf)
        end = 2 * math.pi * (i + 1) / teeth - half_angle(rf)
        flank += [(rf, start + (end - start) * k / 4) for k in range(1, 4)]
        points += [(r * math.cos(a), r * math.sin(a)) for r, a in flank]
    return points


def extrude(points: list, z0: float, z1: float) -> cq.Shape:
    return cq.Workplane("XY").workplane(offset=z0).polyline(points).close().extrude(z1 - z0).val()


# the face


def face_plate() -> cq.Shape:
    """the plate of a face (collar, bore, holes), in the face frame"""
    plate = cylinder(FLANGE, -FACE, 0, BORE)
    plate = plate.cut(holes(INNER_HOLES, 8, 0, INSERT, -FACE - 1, 1))
    return plate.cut(holes(OUTER_HOLES, 8, math.pi / 8, INSERT, -FACE - 1, 1))


def face_holes() -> cq.Shape:
    """what the face cuts from the tube: the bore and the holes"""
    shape = cylinder(BORE, -FACE - 0.01, 0.01)
    shape = shape.fuse(holes(INNER_HOLES, 8, 0, INSERT, -FACE - 1, 1))
    return shape.fuse(holes(OUTER_HOLES, 8, math.pi / 8, INSERT, -FACE - 1, 1))


# pieces: a tube along z between faces (frames in the piece frame)


class Piece:
    def __init__(
        self,
        name: str,
        faces: list[np.ndarray],
        length: float,
        hatch: Optional[tuple],
        plates: Optional[list[bool]] = None,
    ):
        self.name = name
        self.faces = faces
        self.plates = plates or [True] * len(faces)
        self.length = length
        self.hatch = hatch  # (angle, z0, z1) of the window, or None

    def inside(self, radius: float) -> cq.Shape:
        """the tube of the radius between the faces"""
        tube = cylinder(radius, -300, self.length + 300)
        for face in self.faces:
            tube = tube.intersect(half_space(face))
        return tube

    def hatch_parts(self) -> tuple[cq.Shape, cq.Shape, cq.Shape]:
        """window, bosses with the holes of the inserts, cover"""
        angle, z0, z1 = self.hatch
        half = HATCH_WIDTH / 2
        window = place(box(R - WALL - 1, R + 1, -half, half, z0, z1), rot_z(angle))
        bosses, inserts, screws = None, None, None
        for dz in (z0 - HATCH_MARGIN / 2, z1 + HATCH_MARGIN / 2):
            for side in (-1, 1):
                a = angle + side * (half + HATCH_MARGIN / 2) / R
                boss = radial(4.5, R - WALL - 5, R - WALL + 0.5, a, dz)
                hole = radial(INSERT / 2, R - WALL - 5.1, R + 3, a, dz)
                screw = radial(CLEARANCE / 2, R - 1, R + 4, a, dz)
                bosses = boss if bosses is None else bosses.fuse(boss)
                inserts = hole if inserts is None else inserts.fuse(hole)
                screws = screw if screws is None else screws.fuse(screw)
        margin = HATCH_MARGIN
        outline = place(
            box(0, R + 5, -half - margin, half + margin, z0 - margin, z1 + margin), rot_z(angle)
        )
        cover = cylinder(R + 2.0, z0 - margin, z1 + margin, R + 0.1).intersect(outline).cut(screws)
        return window, bosses.cut(inserts), cover

    def solid(self) -> cq.Shape:
        shell = self.inside(R).cut(cylinder(R - WALL, -300, self.length + 300))
        if self.hatch is not None:
            window, bosses, _ = self.hatch_parts()
            shell = shell.cut(window).fuse(bosses.intersect(self.inside(R)))
        for face, plated in zip(self.faces, self.plates):
            if not plated:
                continue
            # the plate closes the whole section of the tube (an ellipse on the 45 degree
            # faces) and has the collar of the interface
            section = self.inside(R).intersect(place(box(-200, 200, -200, 200, -FACE, 0), face))
            plate = section.fuse(place(cylinder(FLANGE, -FACE, 0), face))
            shell = shell.fuse(plate.cut(place(face_holes(), face)))
        if self.hatch is not None:
            angle, z0, z1 = self.hatch
            for dz in (z0 - HATCH_MARGIN / 2, z1 + HATCH_MARGIN / 2):
                for side in (-1, 1):
                    a = angle + side * (HATCH_WIDTH / 2 + HATCH_MARGIN / 2) / R
                    shell = shell.cut(radial(INSERT / 2, R - WALL - 5.1, R + 3, a, dz))
        return shell

    def cover(self) -> cq.Shape:
        return self.hatch_parts()[2]


def piece45() -> Piece:
    flat = rot_x(math.pi)
    oblique = move(z=PIECE45) @ rot_x(ANGLE)
    # the long side of the tube is y > 0
    z1 = PIECE45 + R - FACE - 34
    return Piece("piece45", [flat, oblique], PIECE45, (math.pi / 2, FACE + 12, z1))


def spacer(length: float = SPACER) -> Piece:
    z0, z1 = FACE + 12, length - FACE - 18
    hatch = (math.pi / 2, z0, z1) if z1 - z0 >= 15 else None
    return Piece("spacer", [rot_x(math.pi), move(z=length)], length, hatch)


def base() -> cq.Shape:
    """the base: tube from the floor to the face, foot with 4 holes M5, cable exit"""
    top = move(z=BASE)
    floor = rot_x(math.pi)
    piece = Piece("base", [floor, top], BASE, (math.pi / 2, 14, BASE - FACE - 18), [False, True])
    solid = piece.solid()
    foot = cylinder(FOOT, 0, 6, R - WALL)
    for k in range(4):
        a = math.pi / 4 + k * math.pi / 2
        foot = foot.cut(
            cylinder(2.75, -1, 7).moved(
                cq.Location(cq.Vector(63 * math.cos(a), 63 * math.sin(a), 0))
            )
        )
    solid = solid.fuse(foot)
    return solid.cut(radial(10, R - WALL - 1, R + 1, -math.pi / 2, 25))


def tool_flange() -> cq.Shape:
    """the tool flange: on the inner ring of the last joint (face frame: z out of the
    flange, toward the joint); the tool face TOOL above, 4 M3 on 31.5 mm"""
    disk = cylinder(INNER_HOLES + 5.5, -TOOL, 0, 10)
    disk = disk.cut(holes(INNER_HOLES, 8, 0, CLEARANCE, -TOOL - 1, 1))
    disk = disk.cut(holes(INNER_HOLES, 8, 0, HEAD, -TOOL - 1, -FACE))
    return disk.cut(holes(15.75, 4, 0, 2.5, -TOOL - 1, -6))


# the slewing ring, in the joint frame


def groove_tool(inner: bool) -> cq.Shape:
    """what the groove removes from the inner (or the outer) ring"""
    d = BALL + BALL_CLEARANCE
    sign = 1 if inner else -1  # the race faces outwards on the inner ring
    if GROOVE == "v":
        apex = d / math.sqrt(2)
        tip = BALLS_RADIUS - sign * (apex - 0.5)  # small flat at the bottom
        far = BALLS_RADIUS + sign * 3
        h = abs(far - tip) + 0.5
        return revolve([(tip, -0.5), (far, -h), (far, h), (tip, 0.5)])
    if GROOVE == "round":
        return cq.Solid.makeTorus(BALLS_RADIUS, CONFORMITY * d, cq.Vector(0, 0, 0))
    # gothic arch: two arcs, contact at 45 degrees
    radius = CONFORMITY * d
    e = radius - d / 2
    c = e * math.cos(math.pi / 4)
    shape = None
    for side in (-1, 1):
        arc = cq.Solid.makeTorus(BALLS_RADIUS + sign * c, radius, cq.Vector(0, 0, side * c))
        shape = arc if shape is None else shape.fuse(arc)
    return shape


def inner_ring() -> cq.Shape:
    """inner ring with the internal gear: screwed to the face at +JOINT (inserts)"""
    rp = MODULE * RING_TEETH / 2
    top, bottom = JOINT, -JOINT + RING_STEP
    body = cylinder(BALLS_RADIUS - RING_GAP / 2, bottom, top, rp - MODULE)
    # the spaces of the teeth: an external gear with the tooth as thick as the space
    cutter = involute(RING_TEETH, math.pi * MODULE / 2 + BACKLASH, 1.25, 1.0)
    body = body.cut(extrude(cutter, bottom - 1, top + 1))
    body = body.cut(groove_tool(True))
    return body.cut(holes(INNER_HOLES, 8, 0, INSERT, top - 6, top + 1))


def outer_ring() -> tuple[cq.Shape, cq.Shape]:
    """the outer ring in two halves: the lower one on the face at -JOINT, the upper one
    with the counterbored screws (M3 through both halves into the face inserts)"""
    top, bottom = JOINT - RING_STEP, -JOINT
    body = cylinder(RING_OUT, bottom, top, BALLS_RADIUS + RING_GAP / 2).cut(groove_tool(False))
    body = body.cut(holes(OUTER_HOLES, 8, math.pi / 8, CLEARANCE, bottom - 1, top + 1))
    body = body.cut(holes(OUTER_HOLES, 8, math.pi / 8, HEAD, top - 3, top + 1))
    lower = body.intersect(box(-100, 100, -100, 100, bottom - 1, 0))
    upper = body.intersect(box(-100, 100, -100, 100, 0, top + 1))
    return lower, upper


def balls() -> cq.Shape:
    """the balls (not printed): as many as fit with a small gap"""
    count = int(2 * math.pi * BALLS_RADIUS / (BALL + 0.3))
    shape = None
    for k in range(count):
        a = 2 * math.pi * k / count
        ball = cq.Solid.makeSphere(BALL / 2).moved(
            cq.Location(cq.Vector(BALLS_RADIUS * math.cos(a), BALLS_RADIUS * math.sin(a), 0))
        )
        shape = ball if shape is None else shape.fuse(ball)
    return shape


def ball_count() -> int:
    return int(2 * math.pi * BALLS_RADIUS / (BALL + 0.3))


# motors, in the face frame of the piece with the motor (z out of the piece); the motor
# axle at PINION_OFFSET in the direction angle


def lego_frame(axle: float = LEGO_AXLE, body: float = LEGO_BODY) -> np.ndarray:
    """the frame of the LEGO motor (LDraw axes in mm): the output (-y) toward the joint,
    the body (+z) in the direction body; the hub just under the face plate"""
    hub = -FACE - 0.5
    c, s = math.cos(body), math.sin(body)
    t = np.eye(4)
    t[:3, :3] = np.column_stack([(s, -c, 0), (0, 0, -1), (c, s, 0)])
    t[:3, 3] = (PINION_OFFSET * math.cos(axle), PINION_OFFSET * math.sin(axle), hub + LEGO_HUB)
    return t


def lego_motor() -> cq.Shape:
    """the LEGO Medium Angular Motor (simplified, not printed), in its own frame"""
    w = LEGO_WIDTH / 2
    body = box(-w, w, LEGO_FRONT, LEGO_BACK, LEGO_START, LEGO_END)
    plug = box(-w / 2, w / 2, LEGO_FRONT + 2, LEGO_BACK - 2, LEGO_END, LEGO_PLUG)
    hub = place(
        cylinder(LEGO_HUB_RADIUS, 0, LEGO_FRONT - LEGO_HUB),
        rot_x(math.pi / 2) @ move(z=-LEGO_FRONT),
    )
    return body.fuse(plug).fuse(hub)


def lego_gear() -> cq.Shape:
    """LEGO gear 12 teeth (not printed, its root circle), in the face frame of the piece
    with the motor: on the axle, in the middle of the internal gear"""
    rp = MODULE * PINION_TEETH / 2
    middle = JOINT + RING_STEP / 2
    a = LEGO_AXLE
    gear = cylinder(rp - 1.25 * MODULE, middle - 3.6, middle + 3.6, 2.4)
    return gear.moved(
        cq.Location(cq.Vector(PINION_OFFSET * math.cos(a), PINION_OFFSET * math.sin(a), 0))
    )


def bracket_room() -> cq.Shape:
    """where a bracket fits, in the face frame: inside the tube of a flat face and of a
    45 degree face (the same bracket goes in every piece)"""
    radius = R - WALL - 0.5
    flat = cylinder(radius, -200, -FACE)
    p45 = piece45()
    oblique = p45.faces[1]
    tilted = place(cylinder(radius, -300, 300), np.linalg.inv(oblique))
    return flat.intersect(tilted)


def bracket_plate(angle: float, clear: float) -> cq.Shape:
    """the plate under the face: screwed to the inner holes, free around the axle"""
    plate = cylinder(R - WALL - 0.5, -FACE - 4, -FACE, BORE - 0.5)
    axle = rot_z(angle) @ move(PINION_OFFSET)
    plate = plate.cut(place(cylinder(clear, -FACE - 5, -FACE + 1), axle))
    for k in range(8):
        a = 2 * math.pi * k / 8
        p = np.array([INNER_HOLES * math.cos(a), INNER_HOLES * math.sin(a)])
        if np.linalg.norm(p - axle[:2, 3]) < clear + INSERT:
            continue
        hole = cylinder(CLEARANCE / 2, -FACE - 5, -FACE + 1).moved(
            cq.Location(cq.Vector(p[0], p[1], 0))
        )
        head = cylinder(HEAD / 2, -FACE - 5, -FACE - 2).moved(cq.Location(cq.Vector(p[0], p[1], 0)))
        plate = plate.cut(hole).cut(head)
    return plate


def technic_hole(length: float) -> cq.Shape:
    """a Technic pin hole along z from 0 to length, with the counterbores"""
    hole = cylinder(TECHNIC_HOLE / 2, -0.1, length + 0.1)
    hole = hole.fuse(cylinder(TECHNIC_COUNTERBORE / 2, -0.1, 0.8))
    return hole.fuse(cylinder(TECHNIC_COUNTERBORE / 2, length - 0.8, length + 0.1))


def lego_bracket() -> cq.Shape:
    """bracket of the LEGO motor: two walls one stud thick on the sides of the motor,
    near the output, with the Technic holes (4 pins into the side holes of the motor)"""
    motor = lego_frame()
    w = LEGO_WIDTH / 2
    plate = bracket_plate(LEGO_AXLE, LEGO_HUB_RADIUS + 1.0)
    walls = None
    # motor y of the plate (face z = -FACE - 2), and under the back of the motor
    top = motor[2, 3] + FACE + 2
    low = LEGO_BACK + 2
    for side in (-1, 1):
        x0, x1 = (w, w + STUD) if side > 0 else (-w - STUD, -w)
        wall = place(box(x0, x1, top, low, LEGO_START - 9, LEGO_PIN_Z[1] + 6), motor)
        walls = wall if walls is None else walls.fuse(wall)
    bracket = plate.fuse(walls).intersect(bracket_room())
    for y in LEGO_PIN_Y:
        for z in LEGO_PIN_Z[:2]:
            hole = place(technic_hole(STUD), move(w, y, z) @ rot_y(math.pi / 2))
            bracket = bracket.cut(place(hole, motor))
            hole = place(technic_hole(STUD), move(-w - STUD, y, z) @ rot_y(math.pi / 2))
            bracket = bracket.cut(place(hole, motor))
    # room for the motor
    return bracket.cut(place(lego_motor(), motor))


def nema_motor() -> cq.Shape:
    """NEMA 14 stepper (not printed), in the face frame: the front on the plate"""
    h = NEMA / 2
    body = box(-h, h, -h, h, -FACE - 4 - NEMA_LENGTH, -FACE - 4)
    shaft = cylinder(NEMA_SHAFT / 2, -FACE - 4, 13)
    return body.fuse(shaft)


def nema14_bracket(angle: float = NEMA_AXLE) -> cq.Shape:
    """plate for a NEMA 14 stepper: the shaft at PINION_OFFSET"""
    axle = rot_z(angle) @ move(PINION_OFFSET)
    plate = bracket_plate(angle, NEMA_PILOT / 2 + 0.3)
    h = NEMA / 2
    square = place(box(-h, h, -h, h, -FACE - 4, -FACE), axle).cut(
        place(cylinder(NEMA_PILOT / 2 + 0.3, -FACE - 5, -FACE + 1), axle)
    )
    plate = plate.fuse(square).intersect(bracket_room())
    for x in (-1, 1):
        for y in (-1, 1):
            hole = cylinder(CLEARANCE / 2, -FACE - 5, -FACE + 1).moved(
                cq.Location(cq.Vector(x * NEMA_HOLES / 2, y * NEMA_HOLES / 2, 0))
            )
            plate = plate.cut(place(hole, axle))
    return plate


def pinion() -> cq.Shape:
    """printed pinion for the stepper (D shaft), 7 mm wide"""
    teeth = involute(PINION_TEETH, math.pi * MODULE / 2 - BACKLASH, 1.0, 1.25)
    gear = extrude(teeth, 0, 7)
    shaft = cylinder(NEMA_SHAFT / 2 + 0.1, -1, 8).cut(box(NEMA_SHAFT / 2 - 0.5, 5, -5, 5, -2, 9))
    return gear.cut(shaft)


# the robot at the zero position


def joint_frames(face_p: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """the joint and the face of the other piece, from the face of the piece with the
    motor (both in the world)"""
    joint = face_p @ move(z=JOINT)
    face_q = joint @ move(z=JOINT) @ rot_x(math.pi)
    return joint, face_q


def mate(face: np.ndarray, turn: float = 0.0) -> np.ndarray:
    """the face that touches face (rigid joint), turned by turn"""
    return face @ rot_x(math.pi) @ rot_z(turn)


def pose(piece_face: np.ndarray, world_face: np.ndarray) -> np.ndarray:
    """the piece frame that puts its face piece_face on world_face"""
    return world_face @ np.linalg.inv(piece_face)


class Part:
    """a part of the robot at the zero position"""

    def __init__(self, name: str, shape: cq.Shape, frame: np.ndarray, color: str, link: int):
        self.name = name
        self.shape = shape  # in its own frame
        self.frame = frame  # in the world (the base)
        self.color = color  # print, ring, bracket, motor
        self.link = link  # 0 = base_link, 1 ... 6 = moved by the axis


class Robot:
    def __init__(self) -> None:
        self.parts: list[Part] = []
        self.joints: list[np.ndarray] = []  # joint frames in the world (z = the axis)
        self.tool = np.eye(4)  # tool0 in the world
        self.spacers = 0


def robot() -> Robot:
    """the robot at the zero position: base, shoulder, 3 modules, wrist, tool flange; the
    spacers of SHOULDER_SPACERS, MODULE_SPACERS, WRIST_SPACERS"""
    p45, sp = piece45(), spacer()
    lower_ring, upper_ring = outer_ring()
    shapes = {
        "base": base(),
        "piece45": p45.solid(),
        "piece45_cover": p45.cover(),
        "spacer": sp.solid(),
        "spacer_cover": sp.cover(),
        "inner_ring": inner_ring(),
        "outer_ring_lower": lower_ring,
        "outer_ring_upper": upper_ring,
        "flange": tool_flange(),
        "lego_motor": lego_motor(),
        "lego_bracket": lego_bracket(),
        "lego_gear": lego_gear(),
    }
    result = Robot()
    link = 0

    def add(name: str, frame: np.ndarray, color: str, on: int) -> None:
        result.parts.append(Part(name, shapes[name], frame, color, on))

    def piece(name: str, frame: np.ndarray) -> None:
        add(name, frame, "print", link)
        if name + "_cover" in shapes:
            add(name + "_cover", frame, "print", link)

    def joint(face_p: np.ndarray) -> np.ndarray:
        """the ring and the motor at the face of the piece with the motor; returns the
        face of the next piece"""
        nonlocal link
        j, face_q = joint_frames(face_p)
        add("outer_ring_lower", j, "print", link)
        add("outer_ring_upper", j, "print", link)
        add("lego_motor", face_p @ lego_frame(), "motor", link)
        add("lego_bracket", face_p, "bracket", link)
        add("lego_gear", face_p, "ring", link)
        add("inner_ring", j, "ring", link + 1)
        result.joints.append(j)
        link += 1
        return face_q

    def spacers(face: np.ndarray, count: int) -> np.ndarray:
        """count spacers on the face (outward) of a piece: returns the last face"""
        for _ in range(count):
            frame = pose(sp.faces[0], mate(face))
            piece("spacer", frame)
            result.spacers += 1
            face = frame @ sp.faces[1]
        return face

    piece("base", np.eye(4))
    face = joint(move(z=BASE))  # axis 1
    # shoulder: spacers and a piece45 with the flat face toward axis 1
    if SHOULDER_SPACERS:
        face = mate(spacers(mate(face), SHOULDER_SPACERS))
    frame = pose(p45.faces[0], face)
    piece("piece45", frame)
    face = joint(frame @ p45.faces[1])  # axis 2
    for count in MODULE_SPACERS:
        # a module: piece45 on the joint, spacers, piece45 turned by 180 degrees
        lower = pose(p45.faces[1], face)
        piece("piece45", lower)
        flat = spacers(lower @ p45.faces[0], count)
        upper = pose(p45.faces[0], mate(flat, math.pi))
        piece("piece45", upper)
        face = joint(upper @ p45.faces[1])  # axes 3, 4, 5
    # wrist: piece45 and spacers for the motor of axis 6
    lower = pose(p45.faces[1], face)
    piece("piece45", lower)
    face = joint(spacers(lower @ p45.faces[0], WRIST_SPACERS))  # axis 6
    add("flange", face, "print", link)
    # tool0: on the tool face, z out of the robot, x as the base at the zero position
    tool = face @ move(z=-TOOL) @ rot_x(math.pi)
    result.tool = tool @ rot_z(-math.atan2(tool[1, 0], tool[0, 0]))
    return result


def export(shape: cq.Shape, name: str) -> None:
    os.makedirs(os.path.join(HERE, "step"), exist_ok=True)
    os.makedirs(os.path.join(HERE, "stl"), exist_ok=True)
    cq.exporters.export(shape, os.path.join(HERE, "step", name + ".step"))
    cq.exporters.export(
        shape, os.path.join(HERE, "stl", name + ".stl"), tolerance=0.05, angularTolerance=0.1
    )


def main() -> int:
    p45, sp = piece45(), spacer()
    lower, upper = outer_ring()
    spacers = SHOULDER_SPACERS + sum(MODULE_SPACERS) + WRIST_SPACERS
    printed = {
        "piece45": (p45.solid(), 8),
        "piece45_cover": (p45.cover(), 8),
        "spacer": (sp.solid(), spacers),
        "spacer_cover": (sp.cover(), spacers),
        "base": (base(), 1),
        "flange": (tool_flange(), 1),
        "inner_ring": (inner_ring(), 6),
        "outer_ring_lower": (lower, 6),
        "outer_ring_upper": (upper, 6),
        "lego_bracket": (lego_bracket(), 6),
        "nema14_bracket": (nema14_bracket(), 6),
        "pinion": (pinion(), 6),
    }
    for name, (shape, count) in printed.items():
        export(shape, name)
        print(
            "%-18s x%d  %6.1f cm3  %5.0f g PLA"
            % (name, count, shape.Volume() / 1000, shape.Volume() * 1.24e-3)
        )
    print(
        "balls: %d per ring, %d in all (%s groove, ball %.1f mm)"
        % (ball_count(), 6 * ball_count(), GROOVE, BALL)
    )

    assembly = cq.Assembly(name="osj6")
    colors = {
        "print": cq.Color(0.95, 0.55, 0.1),
        "ring": cq.Color(0.2, 0.45, 0.85),
        "motor": cq.Color(0.2, 0.2, 0.2),
        "bracket": cq.Color(0.6, 0.6, 0.6),
    }
    for k, part in enumerate(robot().parts):
        assembly.add(
            place(part.shape, part.frame), name="%s_%d" % (part.name, k), color=colors[part.color]
        )
    assembly.export(os.path.join(HERE, "step", "assembly.step"))
    print("step/assembly.step: the robot at the zero position")
    return 0


if __name__ == "__main__":
    sys.exit(main())
