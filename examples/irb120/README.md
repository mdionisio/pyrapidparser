# ABB IRB 120: drawing with a pen

`demo.mod` moves an ABB IRB 120 (`!robot: irb120_3_58`, the ROS-Industrial model with
masses and inertias) that draws on a table with a pen:

1. joint movements (`MoveAbsJ`): home, a pose with all the axes moved, home;
2. a 150 mm square with stop points (`MoveL ... fine`);
3. a smaller square with fly-by corners (`z20`): the robot rounds the corners without
   stopping;
4. a circle of radius 50 mm made of two `MoveC`;
5. the pen tilted by 30 degrees with `RelTool`, then `CRobT` reads the position;
6. back home.

The pen is a `tooldata` (120 mm along z of the flange, 0.3 kg), the table a `wobjdata` 200
mm above the base: the points of the drawing are in the frame of the table.

## Run

From the project folder (the dependencies of the motion: `pip install .[view]`, and the
submodule `third_party/abb`).

Simulated time, with one line for each movement:

```sh
PYRAPID_MOTION_LOG=1 python rapid2py.py -e demo.main -i examples/irb120/demo.mod -d out -f demo.py -r
```

```
   0.43 s  MoveAbsJ fine      axes [0.0, 0.0, 0.0, 0.0, 30.0, 0.0] deg  max torque [0.0, 5.8, 5.8, 0.0, 0.1, 0.0] Nm
   1.37 s  MoveAbsJ fine      axes [-60.0, 20.0, -20.0, 90.0, 60.0, 180.0] deg  max torque [1.9, 12.4, 6.1, 0.1, 0.1, 0.0] Nm
...
tilted pen at [75,75,50]
```

The time is the end of each movement, the torques are the largest of the axes during the
movement (the model has the inertial data). Without the viewer the time is simulated: the
program runs in a fraction of a second.

In the browser, in real time:

```sh
PYRAPID_VIEWER=meshcat python rapid2py.py -e demo.main -i examples/irb120/demo.mod -d out -f demo.py -r
```

MeshCat prints the address to open (`http://127.0.0.1:7000/static/`); the path of the
pen is drawn in orange. At the end the program waits for Ctrl+C (`PYRAPID_VIEWER_HOLD=0`
to exit at once).

`PYRAPID_VIEWER=meshcat` runs the robot in real time by itself; `PYRAPID_REALTIME=1` is
for the real time without the viewer.
