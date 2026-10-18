# osj6: a 3D printed robot with oblique swivel joints

`osj6` is a 6 axis robot to build with a 3D printer: a tube of 100 mm cut at 45 degrees,
where each piece turns on the cut face of the previous one. All the cables pass inside the
tube. The parts are a modular kit, in [cad/](cad/README.md); the model of the simulation
(`models/osj6.urdf`) is generated from the same parts. `demo.mod` shows how the joints
fold the tube, then the robot draws on a table with a pen.

![osj6 in some positions](poses.png)

## Oblique swivel joints

In the usual robot arms (the ABB IRB, for example) each axis is at 90 degrees from the
previous one. In an *oblique swivel joint* the axis of the joint is inclined on the tube:
the tube is cut at 45 degrees and the joint turns on the cut plane. The mechanism was
proposed by Shigeo Hirose (Tokyo Institute of Technology) in 1981. Examples:

- Akiyuki, *LEGO Oblique swivel joint mechanisms*: modules and a 4 axis arm made of LEGO
  bricks (YouTube `fSMC4tfOqHM`);
- James Bruton, the "tentacle" arm of 2.5 m with oblique joints at 30/60 degrees;
- Arm-Z (Polish Academy of Sciences): a chain of equal modules with one twist each.

What the geometry gives:

- **a joint at 180 degrees bends the tube by 90 degrees**: the tube axis is at 45 degrees
  from the joint axis, so turning the joint moves the next piece on a cone of 90 degrees;
- **all the pieces are equal**: the two cuts of a module are mirrored (a trapezoid seen
  from the side), so the module has the same joint at both ends and the next module is
  the same part turned by 180 degrees;
- **the straight tube is a singular position**: with all the axes at 0 the joint axes
  are in one plane and the robot can move the flange in 3 directions only. The home
  position is bent (`[0, -90, -45, 45, 90, 0]`);
- **no closed form inverse kinematics**: there is no spherical wrist, the positions are
  found numerically (`run/robotmodel.py` tries random starting positions when the current
  position and the home position do not converge). A straight line of the TCP can need
  large movements of the axes: in the demo the 100 mm square moves axis 2 by 50 degrees;
- the `confdata` of the ABB arms (cf1, cf4, cf6, cfx) does not describe the solutions of
  this robot: the demo turns off the configuration supervision (`ConfL \Off`).

With the flange pointing down the robot reaches the points from 200 to 400 mm in front of
the base with the flange 100 mm above the floor, from 150 to 300 mm with the flange at 200
mm. The straight arm is 770 mm high.

## The robot

The robot of the model and of `cad/step/assembly.step` is made of the parts of the kit
(the numbers of spacers are in `cad/parts.py`: `SHOULDER_SPACERS`, `MODULE_SPACERS`,
`WRIST_SPACERS`):

| Link | Parts                                                      | Motor   |
| ---- | ---------------------------------------------------------- | ------- |
| base | base                                                       | axis 1  |
| 1    | shoulder: piece45 (no spacer)                              | axis 2  |
| 2    | module: piece45 + piece45 turned by 180 degrees (no spacer)| axis 3  |
| 3    | module: piece45 + piece45 (no spacer)                      | axis 4  |
| 4    | module: piece45 + piece45 (no spacer)                      | axis 5  |
| 5    | wrist: piece45 + 1 spacer of 60 mm (room for the motor)    | axis 6  |
| 6    | tool flange (tool0 on its face, 12 mm above the joint face)| -       |

Each joint is a printed slewing ring with 40 balls and an internal gear driven by a LEGO
Medium Angular Motor (12 teeth gear, ratio 5:1); the motor is in the link before the
joint. 150 mm between the oblique joints, 8 piece45 and 1 spacer in all.

After a change of the parts or of the spacers, generate the model again:

```sh
hatch run cad:python examples/osj6/cad/build_model.py
```

It writes `models/osj6.urdf` (the joint frames of the assembly, the masses and inertias
of the parts) and the meshes of the links in `models/osj6/parts/`. The masses are the
printed parts (PLA, 80% of the volume), the LEGO motors, the balls (steel) and the
screws: 2.7 kg in all.

### Motors

The log of the demo shows the torques of the axes (`PYRAPID_MOTION_LOG=1`). The largest
torques due to the weight, over the whole working range:

| Axis              | 1   | 2   | 3   | 4   | 5    | 6 |
| ----------------- | --- | --- | --- | --- | ---- | - |
| joint (Nm)        | 0   | 3.7 | 2.9 | 1.3 | 0.33 | 0 |
| motor, /5 (Nm)    | 0   | 0.73| 0.57| 0.26| 0.07 | 0 |

The LEGO Medium Angular Motor stalls at 0.18 Nm (0.9 Nm on the joint): it moves the
axes 5 and 6, not the axes 2 - 4 of the whole arm. With LEGO the first tests need a
shorter arm (fewer modules); the whole arm needs steppers with a gearbox on the axes 2
and 3 (see [cad/](cad/README.md)). The velocity of the axes in the model (90 degrees/s)
is below the 160 degrees/s of a LEGO motor at 135 rpm (its best efficiency) with the ratio
5.

## Run

From the project folder (the dependencies of the motion: `pip install .[view]`).

```sh
PYRAPID_MOTION_LOG=1 python rapid2py.py -e demo.main -i examples/osj6/demo.mod -d out -f demo.py -r
```

```
1. joints: the tube straight up, all the axes at 0 (singular position)
   1.79 s  MoveAbsJ fine      axes [0.0, 0.0, 0.0, 0.0, 0.0, 0.0] deg  max torque [0.1, 3.4, 0.7, 0.1, 0.4, 0.0] Nm
2. joints: axis 2 at 180 degrees, the tube bends by 90 degrees
   4.58 s  MoveAbsJ fine      axes [0.0, 180.0, 0.0, 0.0, 0.0, 0.0] deg  max torque [0.4, 3.2, 1.9, 0.9, 0.2, 0.0] Nm
...
7. linear: the edges of the 100 mm square, stop at each corner
...
10. circular: the circle inscribed in the square, two half circles
...
```

A message (`TPWrite`) before each step says the movement: the joints fold the tube
(1 - 5), the pen goes down on the table (6), draws the edges of a 100 mm square with stop
points (7) and with fly-by corners (8), then the circle inscribed in the square with two
`MoveC` (9 - 11).

In the browser, in real time, with the printed parts:

```sh
PYRAPID_VIEWER=meshcat python rapid2py.py -e demo.main -i examples/osj6/demo.mod -d out -f demo.py -r
```
