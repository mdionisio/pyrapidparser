# osj6: a 3D printed robot with oblique swivel joints

`osj6` is a 6 axis robot to build with a 3D printer: a tube of 80 mm cut at 45 degrees,
where each piece turns on the cut face of the previous one. All the cables pass inside the
tube. `demo.mod` shows how the joints fold the tube, then the robot draws on a table
with a pen.

![osj6 in some positions](poses.png)

## Oblique swivel joints

In the usual robot arms (the ABB IRB, for example) each axis is at 90 degrees from the
previous one. In an *oblique swivel joint* the axis of the joint is inclined on the tube:
the tube is cut at 45 degrees and the joint turns on the cut plane. The mechanism was
proposed by Shigeo Hirose (Tokyo Institute of Technology) in 1981. Examples:

- Akiyuki, *LEGO Oblique swivel joint mechanisms*: modules and a 4 axis arm made of LEGO
  bricks (YouTube `fSMC4tfOqHM`); osj6 has about the same size;
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
  large movements of the axes: in the demo the 100 mm square moves axis 2 by 80 degrees;
- the `confdata` of the ABB arms (cf1, cf4, cf6, cfx) does not describe the solutions of
  this robot: the demo turns off the configuration supervision (`ConfL \Off`).

With the flange pointing down the robot reaches the points from 150 to 300 mm in front of
the base, with the flange 100 - 200 mm above the floor. The straight arm is 600 mm high,
530 mm above the joint of axis 1.

## The parts

```
base       flat top: the motor of axis 1, a foot with 4 holes M5
shoulder   flat bottom (axis 1), 45 degree top: the motor of axis 2
module x3  45 degree cuts at both ends: the motors of axes 3, 4, 5
wrist      45 degree bottom, flat top: the motor of axis 6
flange     tool flange ISO 9409-1-31.5-4-M3, 10 mm above the joint
```

![the printed parts](parts.png)

Every joint is the same. The upper piece has a hollow spigot that turns in a thin section
ball bearing 61808 (40 x 52 x 7 mm) held by the lower piece; a printed gear (48 teeth,
module 1, keyed on the spigot) is driven by the pinion (10 teeth, ratio 4.8) of an N20
gear motor in the lower piece. The bearing is held by a printed cap with 4 screws M2.5,
the inner ring between the collar of the spigot and the hub of the gear. The bore of the
spigots (34 mm) is the way of the cables. A hatch on the long side of each piece gives
access to the gear, the motor and the cables.

![a joint, cut through the axis](joint.png)

The geometry is parametric: `models/osj6/build.py` writes the parts (STL, mm) in
`models/osj6/parts/` and the model `models/osj6.urdf` (kinematics, the parts for the view,
masses and inertias from the volumes of the parts). To change the diameter, the length
of the modules, the gears or the motors, edit the constants at the top of the script and
run it (`pip install manifold3d`):

```sh
python models/osj6/build.py
```

The STL files are in the orientation of printing: the face of the bearing housing on the
bed. The 45 degree walls print without supports; the spigot of the module and of the
wrist needs a few supports.

### Material

| Part                                    | Quantity |
| --------------------------------------- | -------- |
| printed parts (PLA)                     | about 1 kg |
| ball bearing 61808 (40 x 52 x 7 mm)     | 6        |
| N20 gear motor with encoder, 6 V        | 6        |
| screws M2.5 x 6 (bearing caps)          | 24       |
| screws M5 (foot)                        | 4        |

`motor.stl` and `bearing.stl` are only for the view.

### Motors

The model has the masses of the parts (PLA as solid material, motors and bearings), so
the log of the demo shows the torques of the axes (`PYRAPID_MOTION_LOG=1`). The largest
torques due to the weight, over the whole working range:

| Axis              | 1   | 2   | 3   | 4   | 5    | 6 |
| ----------------- | --- | --- | --- | --- | ---- | - |
| joint (Nm)        | 0   | 1.1 | 0.8 | 0.3 | 0.06 | 0 |
| pinion, /4.8 (Nm) | 0   | 0.23| 0.17| 0.07| 0.01 | 0 |

The axes 2 and 3 need the strongest motors: an N20 with a 1000:1 gearbox is at its limit
there. Light parts (fewer walls and infill in the plates) or a larger gear help. The
velocity of the axes in the model (40 degrees/s) is an N20 1000:1 at about 30 rpm with
the ratio 4.8.

### First steps with LEGO

The kinematics can be tried with LEGO before printing, as in the video of Akiyuki: a set
like LEGO Robot Inventor (4 motors) builds the base and the first 3 oblique joints. The
model of this project gives the positions of the axes for each point of the program
(`PYRAPID_MOTION_LOG=1`).

## Run

From the project folder (the dependencies of the motion: `pip install .[view]`).

```sh
PYRAPID_MOTION_LOG=1 python rapid2py.py -e demo.main -i examples/osj6/demo.mod -d out -f demo.py -r
```

```
   2.60 s  MoveAbsJ fine      axes [0.0, 0.0, 0.0, 0.0, 0.0, 0.0] deg  max torque [0.0, 1.0, 0.2, 0.0, 0.1, 0.0] Nm
   7.45 s  MoveAbsJ fine      axes [0.0, 180.0, 0.0, 0.0, 0.0, 0.0] deg  max torque [0.1, 1.0, 0.5, 0.2, 0.0, 0.0] Nm
...
pen at [20,50,30]
```

In the browser, in real time, with the printed parts:

```sh
PYRAPID_VIEWER=meshcat python rapid2py.py -e demo.main -i examples/osj6/demo.mod -d out -f demo.py -r
```
