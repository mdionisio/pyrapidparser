"""Build the stylized meshes of the IRB 460-110/2.4 (stylized/*.stl, in the repository)
from the meshes of the ABB CAD model (cad/*.stl, built by build_cad.py).

The stylized parts are low polygon shapes with the outline and the size of the real
parts, for the view when the CAD model is not available: each part is cut in cells
(slices along its longest dimension, and along the second one) and every cell is
replaced by its convex hull, with the vertices snapped to a grid. They are written in
the frame of their link (mm), so the URDF uses them without offsets.

Needs numpy and scipy:

    python models/irb460_110_240/build_cad.py
    python models/irb460_110_240/build_stylized.py
"""

import os
import struct
import sys

import numpy as np
from scipy.spatial import ConvexHull

HERE = os.path.dirname(os.path.abspath(__file__))
CAD = os.path.join(HERE, "cad")
OUTPUT = os.path.join(HERE, "stylized")

# part -> (origin of its link at the zero position in the base frame (mm), cells along
# the longest and the second dimension)
PARTS = {
    "foot": ((0, 0, 0), (5, 4)),
    "swing": ((0, 0, 0), (8, 5)),
    "lower_arm": ((260, 0, 742.5), (6, 2)),
    "upper_arm": ((260, 0, 1687.5), (8, 2)),
    "tilt": ((1285, 0, 1687.5), (3, 3)),
    "disk": ((1505, 0, 1436), (1, 1)),
    "link_plate": ((260, 0, 1687.5), (3, 2)),
    "upper_link": ((489.8, 0, 1880.3), (4, 1)),
    "p_arm": ((260, 0, 742.5), (3, 2)),
    "p_link": ((-140, 0, 742.5), (4, 1)),
    "lower_link": ((-4.9, 0, 883.3), (4, 1)),
}
# grid of the vertices (mm)
GRID = 12.0


def read_stl(path: str) -> np.ndarray:
    with open(path, "rb") as f:
        data = f.read()
    count = struct.unpack("<I", data[80:84])[0]
    record = np.dtype([("normal", "<3f4"), ("vertices", "<9f4"), ("attribute", "<u2")])
    triangles = np.frombuffer(data[84 : 84 + count * 50], dtype=record)
    return triangles["vertices"].reshape(-1, 3).astype(float)


def write_stl(path: str, triangles: list[np.ndarray]) -> None:
    with open(path, "wb") as f:
        f.write(b"stylized ABB IRB 460 part, pyrapidparser".ljust(80, b" "))
        f.write(struct.pack("<I", len(triangles)))
        for a, b, c in triangles:
            normal = np.cross(b - a, c - a)
            length = np.linalg.norm(normal)
            normal = normal / length if length > 0 else normal
            f.write(struct.pack("<12fH", *normal, *a, *b, *c, 0))


def hull_triangles(points: np.ndarray) -> list[np.ndarray]:
    points = np.unique(np.round(points / GRID) * GRID, axis=0)
    if len(points) < 4:
        return []
    hull = ConvexHull(points)
    center = points[hull.vertices].mean(axis=0)
    triangles = []
    for simplex in hull.simplices:
        a, b, c = points[simplex]
        # outward normal
        if np.dot(np.cross(b - a, c - a), a - center) < 0:
            b, c = c, b
        triangles.append(np.array([a, b, c]))
    return triangles


def bands(values: np.ndarray, count: int) -> list[np.ndarray]:
    """masks of count bands of values, a little overlapping"""
    low, high = values.min(), values.max()
    step = (high - low) / count
    return [
        (values >= low + (k - 0.1) * step) & (values <= low + (k + 1.1) * step)
        for k in range(count)
    ]


def stylize(points: np.ndarray, cells: tuple[int, int]) -> list[np.ndarray]:
    """convex hulls of the cells along the longest and the second dimension"""
    order = np.argsort(points.max(axis=0) - points.min(axis=0))[::-1]
    triangles: list[np.ndarray] = []
    for first in bands(points[:, order[0]], cells[0]):
        for second in bands(points[:, order[1]], cells[1]):
            triangles += hull_triangles(points[first & second])
    return triangles


def main() -> int:
    if not os.path.isdir(CAD):
        print("no CAD meshes: run build_cad.py first", file=sys.stderr)
        return 1
    os.makedirs(OUTPUT, exist_ok=True)
    for name, (origin, cells) in PARTS.items():
        points = read_stl(os.path.join(CAD, name + ".stl")) - np.array(origin, dtype=float)
        triangles = stylize(points, cells)
        path = os.path.join(OUTPUT, name + ".stl")
        write_stl(path, triangles)
        print("%-11s %5d triangles  %s" % (name, len(triangles), os.path.relpath(path)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
