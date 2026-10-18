# osj6: the parts as a modular kit

`parts.py` builds the parts of osj6 with [CadQuery](https://cadquery.readthedocs.io):
STEP files (solids, to open and change in FreeCAD, Fusion, ...) in `step/` and STL files
for the slicer in `stl/`, plus the robot assembled at the zero position
(`step/assembly.step`). The parts are parametric: the constants at the top of the script.

```sh
hatch run cad:python examples/osj6/cad/parts.py        # the parts: step/, stl/
hatch run cad:python examples/osj6/cad/build_model.py  # the model: models/osj6.urdf
```

The hatch environment `cad` (CadQuery, numpy, the OCP CAD Viewer) is separate from the
dependencies of the project. `step/` and `stl/` are not in the repository: run the script.

### View

- **in the browser**: `hatch run cad:viewer` starts the OCP CAD Viewer
  (http://127.0.0.1:3939/viewer); in another terminal `show.py` sends the parts to it:

  ```sh
  hatch run cad:python examples/osj6/cad/show.py                  # the robot
  hatch run cad:python examples/osj6/cad/show.py joint            # a joint cut in half
  hatch run cad:python examples/osj6/cad/show.py piece45 spacer   # some parts
  hatch run cad:python examples/osj6/cad/show.py examples/osj6/cad/step/base.step
  ```

- **in VS Code**: the extension "OCP CAD Viewer" (bernhard-42.ocp-cad-viewer) shows the
  same in a panel of the editor, with the same `show.py`;
- **FreeCAD** (better installed in Windows): File > Open of the STEP files, from
  `\\wsl.localhost\<distribution>\home\...\examples\osj6\cad\step`; the STL files
  open in the slicer the same way.

![the robot at the zero position](images/robot.png)

## The kit

Every end of every piece is the same **face**, so the pieces combine in any way:

| Part                  | What it is                                                     | For the robot |
| --------------------- | -------------------------------------------------------------- | ------------- |
| `piece45`             | short tube, a flat face and a 45 degree face, all equal        | 8             |
| `spacer`              | tube with two flat faces, to make the arm longer               | 1 (wrist)     |
| `base`, `flange`      | the foot, the tool flange                                      | 1 + 1         |
| `inner_ring`          | inner ring of the joint, with the internal gear                | 6             |
| `outer_ring_lower`, `outer_ring_upper` | outer ring of the joint, in two halves        | 6 + 6         |
| `lego_bracket`        | holds a LEGO Medium Angular Motor with 4 Technic pins          | 6             |
| `nema14_bracket`, `pinion` | the same for a NEMA 14 stepper, with the printed pinion   | (6)           |
| `piece45_cover`, `spacer_cover` | the covers of the hatches                            | 8 + 1         |

![the parts](images/parts.png)

- **Joint** = face + ring + face. The outer ring is screwed to the face of the piece
  with the motor, the inner ring to the face of the other piece. The inner ring stands
  out by 1 mm on one side and the outer ring on the other, as in the industrial slewing
  rings: two equal faces touch one ring each.
- **Rigid joint** = two faces screwed together (M3 screws and nuts in the inner holes),
  turned by a multiple of 45 degrees. A module of the arm is piece45 + (spacers) +
  piece45 turned by 180 degrees: the joint axes alternate as in the robot of the model.
  Other turns give other arms (the 8 holes allow steps of 45 degrees).
- **Length**: spacers between the two piece45 of a module make the arm longer. The robot
  of `assembly.step` and of the model: base, shoulder (piece45), 3 modules (2 piece45
  each, no spacer), wrist (piece45 + 1 spacer for the motor of axis 6), tool flange; 770
  mm high when straight, 150 mm between the oblique joints. `SHOULDER_SPACERS`,
  `MODULE_SPACERS` and `WRIST_SPACERS` in `parts.py` set the spacers of each arm (table
  in [../README.md](../README.md)).

### The face

| Feature                          | Size                                             |
| -------------------------------- | ------------------------------------------------ |
| tube                             | 100 mm, wall 3 mm                                |
| plate                            | 6 mm, collar of 106 mm                           |
| bore (cables, pinion, axle)      | 63 mm                                            |
| inner holes: 8 on 69 mm          | inner ring, motor bracket, rigid joints          |
| outer holes: 8 on 97 mm, turned by 22.5 degrees | outer ring                        |
| holes                            | 4.2 mm: M3 heat-set inserts, or loose for M3     |

## The slewing ring

![a joint, cut through the axis](images/joint.png)

The balls (6 mm) run between the inner and the outer ring on a circle of 82 mm: 40 balls
in each ring. The outer ring is in two halves: the balls go in on the lower half, the
upper half closes them. The screws of the outer ring pass through both halves into the
face; a thin shim (or sanding) between the halves sets the play.

The internal gear has 60 teeth, module 1, pressure angle 20 degrees, like the LEGO Technic
gears (8 and 24 teeth are 16 mm apart, two holes). With a 12 teeth gear the ratio is 5:1
and the axle of the motor is 24 mm from the axis of the joint: three LEGO holes.
`PINION_TEETH` changes the gear (the axle moves accordingly), `BACKLASH` makes the teeth
thinner.

### Steel balls or airsoft BBs

The ball changes the groove (`GROOVE`, `BALL`, `BALL_CLEARANCE`, `CONFORMITY`):

- **steel balls** are hard and precise: the shape of the groove decides the play and the
  stiffness. `GROOVE = "gothic"` (two arcs, contact at 45 degrees on 4 points) takes the
  tilting moments of an arm joint, with `CONFORMITY` 0.52 - 0.54 (radius of the arcs /
  ball) and a small clearance (0.1 mm);
- **airsoft BBs** (plastic, 0.2 g, very round) are light and cheap, but they deform under
  load: the contact on a precise arc does not matter, `GROOVE = "v"` (90 degree V,
  4 points at 45 degrees, flat flanks that print well) with more clearance (0.2 mm) is
  enough.

`GROOVE = "round"` is the deep groove of the ball bearings (2 contact points), weaker
against the tilting moments.

## The motors

The brackets are screwed inside the face of the piece with the motor (inner holes, with
inserts). The motor is 24 mm from the axis, its body in a direction that fits both in
the pieces with a flat face and in the pieces with a 45 degree face (the tube is
inclined there): `LEGO_AXLE`, `LEGO_BODY`, `NEMA_AXLE`. The assembly at the zero
position has no interferences (checked by intersecting every pair of parts); after a
change of the parameters, check it again in FreeCAD or with the intersections.

- **LEGO Medium Angular Motor** (`lego_bracket`): the dimensions and the pin holes come
  from the LDraw model 54696p02 in `doc/lego/`. Two walls one stud thick on the sides of
  the motor take 4 Technic pins in the side holes near the output. The gear goes on an
  axle in the output hub, in the middle of the internal gear (a half bush as spacer).
- **NEMA 14 stepper** (`nema14_bracket`): 26 mm holes, 22 mm pilot; the printed pinion
  (12 teeth, module 1) on the 5 mm shaft with a flat.

## Material for the robot of `assembly.step`

| Part                                 | Quantity                    |
| ------------------------------------ | --------------------------- |
| balls 6 mm                           | 240 (40 per joint)          |
| M3 heat-set inserts                  | about 170                   |
| M3 x 10 (inner rings)                | 48                          |
| M3 x 16 (outer rings)                | 48                          |
| M3 x 16 + nuts (rigid joints)        | 32                          |
| M3 x 8 (brackets), M3 x 6 (covers)   | about 40, 36                |
| M5 (foot)                            | 4                           |

The printed parts are about 2.4 kg as solid PLA, the robot of the model 2.7 kg with
motors, balls and screws: the LEGO motors (stall 18 Ncm, x5 = 0.9 Nm) can move the joints
near the tool, not the shoulder of the whole arm (3.7 Nm, see [../README.md](../README.md)).
For the first steps with LEGO: a shorter arm (3 - 4 axes), light prints.

## The model of the simulation

`build_model.py` makes `models/osj6.urdf` from `parts.robot()`, the same robot of
`assembly.step`: the joint frames, the meshes of each link (`models/osj6/parts/`, one file
for each color) and the masses (printed parts at 80% of their volume, LEGO motors 54 g,
steel balls, 30 g of screws for each joint). Run it after every change of the parts or of
the spacers.

## To do

- the hall sensors for the zero of the axes (a magnet in the inner ring);
- not printed yet: the clearances (`BALL_CLEARANCE`, `BACKLASH`, the holes) need a test
  print of a ring.
