# Palletizer

An ABB IRB 460-110/2.4 (4 axes, `!robot: irb460_110_240`) fills two pallets at the same
time, each with its own product and schema:

| Place line | Pick line | Product           | Schema                                       |
| ---------- | --------- | ----------------- | -------------------------------------------- |
| 1 (+40°)   | 1 (+110°) | 400 x 400 x 250   | 2 layers of 6: 12 boxes                      |
| 2 (-40°)   | 2 (-110°) | 400 x 300 x 150   | a layer of 8, a layer of 6 turned by 90°: 14 |

The program orders an empty pallet and the products of the schema; the conveyors bring
the products one at a time on the pick points; the robot takes a product (closing the
gripper), places it on the pallet of its line, and serves the two lines in turn. A full
pallet leaves the station with its products. The demo ends when each line has filled
`nPalletsToDo` pallets (`environment.mod`, 0 = never ends).

## Files

| File              |                                                                      |
| ----------------- | -------------------------------------------------------------------- |
| `maintask.mod`    | the program: it runs the commands of the schemas                     |
| `schema.mod`      | the schemas: product, pallet, pick line, commands of the two queues |
| `environment.mod` | the data of the cell taught on the robot: pick points, pallet work objects, gripper, home, and the I/O of the equipment |
| `settings.mod`, `gloadschema.mod`, `types.mod` | data of the program                     |
| `EIO.cfg`         | the I/O signals of the cell (I/O configuration of the controller)    |
| `cell.py`         | the simulation of the cell, not part of the program                  |

The RAPID program is the program of the robot: it talks with the cell only through the
movements and the I/O signals. `cell.py` is the reality around it: the conveyors, the
pallets, the products, the gripper (it takes the product under the TCP when `doGripper`
closes).

Commands of a schema (`schema.mod`):

```
OrderProd [ <number of products>, <disposition> ]
StopQueue <queue>, StartQueue <queue>
TakeProduct [ x, y, z, rot ]            offset from the pick point
PlaceProduct [ type, x, acc_x, y, acc_y, z, acc_z, rot, (second product) ]
OrderPallet, TakePallet, PlacePallet, ExitPallet, TakeSheet, PlaceSheet
```

`PlaceProduct`: `x`, `y` center of the product in the pallet frame, `z` its bottom from the
top of the pallet, `rot` degrees around z; the robot comes from the point displaced by
`acc_x`, `acc_y`, `acc_z`.

## Run

From the project folder (the dependencies of the motion: `pip install .[view]`).

```sh
E=examples/pallettizer
MODULES="-i $E/settings.mod -i $E/gloadschema.mod -i $E/schema.mod -i $E/types.mod -i $E/environment.mod -i $E/maintask.mod"
```

Simulated time: the whole run (about 125 s of the robot) takes a few seconds:

```sh
PYRAPID_SIMULATION=$E/cell.py python rapid2py.py --eio $E/EIO.cfg $MODULES -e MAIN -d out -f pallettizer.py -r
```

```
...
LINE 2 DONE: 1 PALLETS
END AUTOMATIC TASK
cell: station 1 shipped 1 pallets, 12 products
cell: station 2 shipped 1 pallets, 14 products
```

`PYRAPID_MOTION_LOG=1` adds a line for each movement.

In the browser, in real time:

```sh
PYRAPID_SIMULATION=$E/cell.py PYRAPID_VIEWER=meshcat python rapid2py.py --eio $E/EIO.cfg $MODULES -e MAIN -d out -f pallettizer.py -r
```

Open the address that MeshCat prints (`http://127.0.0.1:7000/static/`): the products appear
on the conveyors, travel with the gripper and leave with the pallet. The gripper is grey
when open, green when it holds a product, yellow when it closed on nothing. A file
`floor.png` in this folder replaces the grid of the floor (6 x 6 m, centered on the robot).

`PYRAPID_VIEWER=meshcat` runs the robot in real time by itself; `PYRAPID_REALTIME=1` is
for the real time without the viewer.

## The robot with the ABB CAD model

The robot model is `models/irb460_110_240.urdf`: the lengths come from the ABB CAD
model, the geometry is made of boxes. ABB publishes the CAD model of the IRB 460-110/2.4
in the ABB Library (document 9AKK107992A7905, "CAD Model, STEP, IRB 460, ALL, 110-240,
IRC5, rev01, joint"): it is ABB copyright, so it is not in the repository. The script
`models/irb460_110_240/build_cad.py` downloads it and converts it to meshes for the
viewer; from then on the viewer shows the real robot, with the two parallelograms of the
arm moving.

### Build the meshes

The conversion uses [gmsh](https://gmsh.info) (OpenCASCADE reads the STEP files); it is
not a dependency of the project, it is needed only once:

```sh
pip install gmsh
python models/irb460_110_240/build_cad.py
```

```
download https://search.abb.com/library/Download.aspx?DocumentID=9AKK107992A7905&...
DISK         -> models/irb460_110_240/cad/disk.stl
FOOT         -> models/irb460_110_240/cad/foot.stl
...
UPPER LINK   -> models/irb460_110_240/cad/upper_link.stl
```

The script downloads the archive (about 5 MB of STEP files, one for each part, the robot
at the zero position), meshes each part and writes 11 STL files (about 6 MB) in
`models/irb460_110_240/cad/`, a folder ignored by git. It takes about 20 seconds.

| Option        | Effect                                                                   |
| ------------- | ------------------------------------------------------------------------ |
| `--zip FILE`  | use an archive already downloaded (no network, or the ABB address changed) |
| `--detail N`  | size of the triangles: the size of each part / N (default 40); higher is finer and the files are larger |

Without the network, download the archive from the [ABB Library](https://library.abb.com)
(search "CAD Model STEP IRB 460 joint") and give it with `--zip`. The script ends with an
error if a part is missing in the archive.

### Check

```sh
python robotmodel.py irb460_110_240
```

prints `view:       CAD meshes 11 of 11` when the meshes are there (`0 of 11 (boxes)`
otherwise). The meshes are used only by the viewer: the kinematics and the simulation are
the same with and without them. Delete the folder `models/irb460_110_240/cad/` to go back
to the boxes, run the script again to rebuild the meshes.

### How the meshes are placed

`models/irb460_110_240.json` lists the mesh of each link (`cad_meshes`). The parts of the
CAD model are in the base frame of the robot at the zero position, in mm: `robotmodel.py`
scales them to m and places each one in its link with the inverse of the placement of the
link at the zero position. The links of the parallel linkage (`p_arm`, `p_link`,
`lower_link`, `link_plate`, `upper_link`) are joints of the URDF coupled to the axes, so
the rods move with the arm.

### Limits of the model

- The combined limits of the axes 2 and 3 of the parallel linkage are not modeled, only
  the range of each axis: the model reaches 2446 mm (axis 2 at +85, axis 3 at 0) where the
  ABB data sheet says 2403 mm, so a point a little out of the real working range can be
  reachable in the simulation. The top of the working range (1786 mm) is the one of the
  data sheet.
- There is no inertial data: the joint torques are not computed.
