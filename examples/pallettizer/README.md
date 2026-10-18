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

Without the CAD model the robot is drawn with boxes. ABB publishes the CAD model of the
IRB 460 (ABB Library, document 9AKK107992A7905); it is ABB copyright and not in the
repository. To download it and convert it to meshes (in `models/irb460_110_240/cad/`):

```sh
pip install gmsh
python models/irb460_110_240/build_cad.py
```

From then on the viewer shows the real robot, with the parallel linkage moving.
