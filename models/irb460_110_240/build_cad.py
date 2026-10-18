"""Download the ABB CAD model of the IRB 460-110/2.4 and convert it to meshes for the
viewer.

The CAD model (STEP, one file for each part, the robot at the zero position) is
published by ABB in the ABB Library (document 9AKK107992A7905, "CAD Model, STEP, IRB
460, ALL, 110-240, IRC5, rev01, joint"). It is ABB copyright, so the files are not in
the repository: this script downloads them and writes the STL meshes in the folder
cad/ next to it (ignored by git). Then robotmodel.py uses them in place of the boxes of
irb460_110_240.urdf (see "cad_meshes" in irb460_110_240.json).

The conversion needs gmsh (OpenCASCADE), not a dependency of the project:

    pip install gmsh
    python models/irb460_110_240/build_cad.py
"""

import io
import os
import sys
import tempfile
import urllib.request
import zipfile

URL = (
    "https://search.abb.com/library/Download.aspx?DocumentID=9AKK107992A7905"
    "&LanguageCode=en&DocumentPartId=&Action=Launch"
)
HERE = os.path.dirname(os.path.abspath(__file__))
OUTPUT = os.path.join(HERE, "cad")

# STEP file (without "IRB 460_110-240_IRC5_" and "_REV1.STEP") -> mesh
PARTS = {
    "FOOT": "foot",
    "SWING": "swing",
    "LOWER ARM": "lower_arm",
    "UPPER ARM": "upper_arm",
    "TILT": "tilt",
    "DISK": "disk",
    "LINK PLATE": "link_plate",
    "UPPER LINK": "upper_link",
    "P LINK": "p_link",
    "P ARM": "p_arm",
    "LOWER LINK": "lower_link",
}


def download(url: str) -> bytes:
    print("download %s" % (url,))
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(request, timeout=300) as response:
        data: bytes = response.read()
    return data


def convert(step: str, stl: str, parts: int = 40) -> None:
    """STEP -> binary STL, a coarse surface mesh (the largest size / parts)"""
    import gmsh

    gmsh.clear()
    gmsh.model.occ.importShapes(step)
    gmsh.model.occ.synchronize()
    xmin, ymin, zmin, xmax, ymax, zmax = gmsh.model.getBoundingBox(-1, -1)
    size = max(xmax - xmin, ymax - ymin, zmax - zmin) / parts
    gmsh.option.setNumber("Mesh.MeshSizeMax", size)
    gmsh.option.setNumber("Mesh.MeshSizeMin", size / 10)
    gmsh.option.setNumber("Mesh.Algorithm", 6)
    gmsh.option.setNumber("Mesh.Binary", 1)
    gmsh.model.mesh.generate(2)
    gmsh.write(stl)


def main() -> int:
    try:
        import gmsh
    except ImportError:
        print("the conversion needs gmsh: pip install gmsh", file=sys.stderr)
        return 1
    archive = zipfile.ZipFile(io.BytesIO(download(URL)))
    os.makedirs(OUTPUT, exist_ok=True)
    gmsh.initialize()
    gmsh.option.setNumber("General.Terminal", 0)
    with tempfile.TemporaryDirectory() as folder:
        archive.extractall(folder)
        for root, _, files in os.walk(folder):
            for name in sorted(files):
                part = name.replace("IRB 460_110-240_IRC5_", "").replace("_REV1.STEP", "")
                if part not in PARTS:
                    continue
                stl = os.path.join(OUTPUT, PARTS[part] + ".stl")
                convert(os.path.join(root, name), stl)
                print("%-12s -> %s" % (part, os.path.relpath(stl, os.getcwd())))
    gmsh.finalize()
    return 0


if __name__ == "__main__":
    sys.exit(main())
