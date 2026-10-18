"""Show the parts of osj6 in the OCP CAD Viewer.

The viewer is the extension "OCP CAD Viewer" of VS Code, or the same viewer in the
browser (http://127.0.0.1:3939/viewer):

    hatch run cad:viewer

Then, in another terminal:

    hatch run cad:python examples/osj6/cad/show.py                 the robot
    hatch run cad:python examples/osj6/cad/show.py joint           a joint, cut in half
    hatch run cad:python examples/osj6/cad/show.py piece45 inner_ring    some parts
    hatch run cad:python examples/osj6/cad/show.py file.step       a STEP file
"""

import os
import sys

import numpy as np
import cadquery as cq
from ocp_vscode import set_port, show

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import parts as P  # noqa: E402

COLORS = {"print": "orange", "ring": "royalblue", "bracket": "gray", "motor": "#333333"}


def single(name: str) -> cq.Shape:
    """a part of parts.py by name"""
    p45, sp = P.piece45(), P.spacer()
    lower, upper = P.outer_ring()
    makers = {
        "piece45": p45.solid,
        "piece45_cover": p45.cover,
        "spacer": sp.solid,
        "spacer_cover": sp.cover,
        "base": P.base,
        "flange": P.tool_flange,
        "inner_ring": P.inner_ring,
        "outer_ring_lower": lambda: lower,
        "outer_ring_upper": lambda: upper,
        "lego_bracket": P.lego_bracket,
        "nema14_bracket": P.nema14_bracket,
        "pinion": P.pinion,
        "lego_motor": P.lego_motor,
        "balls": P.balls,
    }
    if name not in makers:
        raise SystemExit("unknown part %s: %s" % (name, ", ".join(makers)))
    return makers[name]()


def joint() -> tuple[list, list, list]:
    """a joint between two spacers, cut by the plane x = 0"""
    sp = P.spacer()
    j, face_q = P.joint_frames(np.eye(4))
    items = [
        (P.place(sp.solid(), np.linalg.inv(sp.faces[1])), "print", "lower spacer"),
        (P.place(sp.solid(), face_q @ np.linalg.inv(sp.faces[0])), "print", "upper spacer"),
        (P.place(P.inner_ring(), j), "ring", "inner ring"),
        (P.place(P.outer_ring()[0], j), "print", "outer ring lower"),
        (P.place(P.outer_ring()[1], j), "print", "outer ring upper"),
        (P.place(P.balls(), j), "bracket", "balls"),
        (P.place(P.lego_motor(), P.lego_frame()), "motor", "LEGO motor"),
        (P.lego_bracket(), "bracket", "bracket"),
        (P.lego_gear(), "ring", "LEGO gear"),
    ]
    half = P.box(-200, 0, -200, 200, -100, 100)
    shapes = [shape.intersect(half) for shape, _, _ in items]
    return shapes, [COLORS[c] for _, c, _ in items], [n for _, _, n in items]


def main() -> int:
    set_port(3939)
    args = sys.argv[1:]
    if not args:
        robot = P.robot()
        shapes = [P.place(p.shape, p.frame) for p in robot.parts]
        colors = [COLORS[p.color] for p in robot.parts]
        names = ["%s_%d" % (p.name, k) for k, p in enumerate(robot.parts)]
    elif args == ["joint"]:
        shapes, colors, names = joint()
    else:
        shapes, colors, names = [], [], []
        for k, name in enumerate(args):
            if name.lower().endswith((".step", ".stp")):
                shape = cq.importers.importStep(name).val()
            else:
                shape = single(name)
            # side by side
            shapes.append(shape.moved(cq.Location(cq.Vector(150 * k, 0, 0))))
            colors.append("orange")
            names.append(os.path.basename(name))
    show(*shapes, names=names, colors=colors)
    return 0


if __name__ == "__main__":
    sys.exit(main())
