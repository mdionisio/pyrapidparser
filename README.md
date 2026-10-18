# pyrapidparser

Parser, syntax tree tools and Python translator for **ABB RAPID**, the programming
language of ABB robot controllers.

The project contains:

| Tool                    | What it does                                                          |
| ----------------------- | --------------------------------------------------------------------- |
| `rapid_parser.py`       | lexer and parser (PLY) that build the syntax tree (`rapid_ast`)       |
| `rapidvalidate.py`      | static semantic checks after parsing (names, types, arguments, ...)   |
| `rapid2rapid.py`        | writes the tree back as RAPID (formatting and round-trip check)       |
| `rapid2py.py`           | translates RAPID modules into an executable Python program            |
| `run/pyrapid.py`        | runtime used by the generated code (symbols, types, scopes, errors)   |
| `run/robotmodel.py`     | robot models (URDF) with kinematics and dynamics of Pinocchio         |
| `run/pyrapid_motion.py` | simulated motion instructions, real time view with MeshCat            |
| `eio.py`                | I/O signals of the controller configuration (EIO.cfg)                 |

The reference for syntax and semantics is the ABB *Technical reference manual - RAPID
kernel* (3HAC050946-001), together with the *RAPID Overview* (3HAC050947-001) and
*Instructions, Functions and Data types* (3HAC050917-001).

## Requirements

- Python 3.9 or later
- [ply](https://pypi.org/project/ply/) 3.11
- [hatch](https://hatch.pypa.io/) for development (optional)
- for the motion instructions: [Pinocchio](https://github.com/stack-of-tasks/pinocchio)
  (`pin`), numpy, xacro, and [MeshCat](https://github.com/meshcat-dev/meshcat-python) for
  the view in the browser

```sh
pip install ply
pip install pin numpy xacro meshcat     # or: pip install .[view]
```

The ABB robot models are in a git submodule:

```sh
git clone --recurse-submodules https://github.com/mdionisio/pyrapidparser.git
# or, in a clone made without it:
git submodule update --init
```

The module `rapid_ast.py` is generated from `_rapid_ast.cfg` and is not in the repository.
Generate it before the first use (with hatch the `test` and `typecheck` scripts and the
package build do it for you):

```sh
python _ast_gen.py
```

## Usage

The examples use this module, `hello.mod`:

```
MODULE hello
    VAR num total := 0;
    PROC main()
        FOR i FROM 1 TO 10 DO
            total := total + i;
        ENDFOR
        TPWrite "total = " \Num:=total;
    ENDPROC
ENDMODULE
```

### Validation

```sh
python rapidvalidate.py hello.mod
```

The command checks all the modules of the task together with the standard modules in
`default/*.sys`. It prints the diagnostics as `file:line: severity: message [code]` and
exits with 1 when it finds errors. For example:

```
bad.mod:4: error: cannot assign to the constant k [assign-constant]
bad.mod:5: error: undefined procedure foo [undefined-routine]
```

The checks include:

- duplicate names and scope rules;
- unknown types and aliases;
- array dimensions and indexes;
- constant and literal expressions;
- value classes and type compatibility in assignments and operators;
- aggregates;
- procedure and function calls: number, name, order and mode of the arguments, optional
  and mutually exclusive arguments, `\switch`;
- assignments to constants and read-only data;
- labels and `GOTO`, including jumps into a statement list;
- `RETURN`, error handlers and `RAISE`;
- length of identifiers and strings.

| Option             | Effect                                              |
| ------------------ | --------------------------------------------------- |
| `-s`               | do not load the standard modules                    |
| `--check-standard` | also report the diagnostics of the standard modules |
| `--eio FILE`       | I/O configuration: the signals of the task          |

From Python:

```python
import rapidvalidate

for d in rapidvalidate.validate_files(["hello.mod"]):
    print(d.file, d.line, d.severity, d.code, d.message)
```

### Translation to Python

```sh
python rapid2py.py -i hello.mod -d out -f hello.py -e hello.main -r
```

`rapid2py` validates the program before translating it and generates nothing if there are
errors. With `-r` it runs the program at once. The generated program imports `pyrapid`
(folder `run/`) and the project modules, so to run it by hand `PYTHONPATH` is needed:

```sh
cd out
PYTHONPATH=../run:.. python hello.py
```

| Option             | Effect                                                            |
| ------------------ | ----------------------------------------------------------------- |
| `-i FILE`          | module to translate (repeat it for more modules of the same task) |
| `-d DIR`           | output folder (created if missing)                                |
| `-f FILE`          | output file (default `rapid_program.py`)                          |
| `-e [MODULE.]PROC` | procedure called as entry point                                   |
| `-r`               | run the program after the translation, exit with its exit code    |
| `-s`               | do not include the standard symbols of `default/*.sys`            |
| `--eio FILE`       | I/O configuration of the controller (see I/O signals)             |
| `--no-validate`    | skip the checks of `rapidvalidate`                                |

Comment lines starting with `!python:` are copied as they are into the generated code.
This is how `default/standard.sys` implements the system instructions in Python
(`TPWrite`, `ExitCycle`, ...):

```
PROC ExitCycle()
    !python:import sys
    !python:print("Exit for ExitCycle")
    !python:sys.exit(0)
ENDPROC
```

How the constructs without a direct Python equivalent are translated:

- **GOTO**: every statement list that contains labels becomes a dispatch loop, and `GOTO`
  raises `pyrapid.Goto`.
- **FOR**: the loop variable exists only while the loop runs and hides any variable with
  the same name.
- **Error handlers**: `RETRY`, `TRYNEXT`, `RAISE` and `RETURN` are implemented.

### Rewriting as RAPID

```sh
python rapid2rapid.py -i hello.mod -d out -f hello.mod
```

The command reads the module and writes it back with a uniform formatting. Parentheses are
added only where they are needed to keep the same expression tree. The tests check that
rewriting the result a second time gives the same text.

## Robot motion

The motion instructions move a simulated robot. The comment `!robot: <model>` in a module
of the task selects the robot model:

```
MODULE demo
    !robot: irb120_3_58
    PERS tooldata tpen := [TRUE, [[0, 0, 120], [1, 0, 0, 0]], [0.3, [0, 0, 60], [1, 0, 0, 0], 0, 0, 0]];
    CONST robtarget pa := [[400, -100, 300], [0, 0, 1, 0], [-1, 0, -1, 0], [9E9, 9E9, 9E9, 9E9, 9E9, 9E9]];

    PROC main()
        MoveAbsJ [[0, 0, 0, 0, 30, 0], [9E9, 9E9, 9E9, 9E9, 9E9, 9E9]], v1000, fine, tool0;
        MoveJ Offs(pa, 0, 0, 50), v1000, fine, tpen;
        MoveL pa, v100, fine, tpen;
    ENDPROC
ENDMODULE
```

`rapidvalidate` checks that the model exists, that the comment is outside the routines and
that all the modules of the task name the same robot.

### Robot models

`python run/robotmodel.py` lists the models, `python run/robotmodel.py <model>` shows the data of
one:

- the 28 ABB models of [ROS-Industrial](https://github.com/ros-industrial/abb) (submodule
  `third_party/abb`): IRB 120, 1200, 1600, 2400, 2600, 4400, 4600, 52, 5400, 6600, 6640,
  6650S, 6700, 7600 and CRB 15000, named after their xacro file (`irb120_3_58`,
  `irb4600_60_205`, ...);
- `irb460_110_240` in `models/`: the 4 axis palletizer ABB IRB 460-110/2.4, with the
  parallel linkage. There is no URDF of this robot: the lengths come from the ABB CAD
  model, the view uses stylized parts (low polygon shapes with the outline and the size
  of the real ones). `python models/irb460_110_240/build_cad.py` (needs `pip install
  gmsh`) downloads the CAD model from the ABB Library and converts it to meshes in
  `models/irb460_110_240/cad/` (not in the repository: ABB copyright); then the viewer
  shows the real robot.

- `osj6` in `models/`: a 6 axis robot to build with a 3D printer, with oblique swivel
  joints (a tube cut at 45 degrees). `models/osj6/build.py` (needs `pip install
  manifold3d`) generates the printable parts and the model, with the masses of the parts.
  See [examples/osj6](examples/osj6/README.md).

The models contain the geometry, the limits and the maximum speed of the axes (from the ABB
data sheets). The other data is often missing, and the loading prints a warning for each
default value used instead:

| Data                       | Available                                 | Default when missing                |
| -------------------------- | ----------------------------------------- | ----------------------------------- |
| axis acceleration          | never                                     | full speed in 0.5 s                 |
| masses and inertias        | IRB 120, IRB 120T, IRB 1200-5/90          | no dynamics: torques not computed   |
| motor torque limits        | never (ABB does not publish them)         | torques not checked                 |

```
warning: irb4600_60_205: no acceleration limits, using velocity / 0.5 s (full speed in 0.5 s)
warning: irb4600_60_205: no motor torque limits (effort), the torques are not checked
warning: irb4600_60_205: no inertial data, the joint torques are not computed
```

`models/<model>.json` adds or overrides data of a model: accelerations, torque limits,
limits of the axes, coupled joints, meshes of a CAD model (see the comment at the top of
`run/robotmodel.py` and `models/irb460_110_240.json`).

### Motion instructions

| Instruction or function            | Notes                                                    |
| ---------------------------------- | -------------------------------------------------------- |
| `MoveAbsJ`                         | to a `jointtarget`                                       |
| `MoveJ`                            | to a `robtarget`, with its `confdata` (`ConfJ \On`)      |
| `MoveL`, `MoveC`                   | straight line and circle of the TCP                      |
| `ConfJ`, `ConfL`                   | configuration supervision on or off                      |
| `WaitTime`, `WaitRob`              | `\InPos`: wait for the robot to stop                     |
| `CJointT`, `CRobT`                 | current position                                         |
| `CalcJointT`, `CalcRobT`           | inverse and forward kinematics                           |
| `Offs`, `RelTool`                  | displaced points                                         |

The supported arguments are `\Conc`, `\V`, `\T`, `\Z` and `\WObj`; `tooldata` (TCP and load) and
`wobjdata` (user and object frame) work as on the robot, `tool0`, `wobj0` and `load0` are
predefined.

### Program and robot

As on the robot controller, the program and the robot run at the same time (RAPID
overview 2.3, *Synchronization with logical instructions*). A movement instruction plans
the movement (reach, configuration, speed) and passes it to the robot; then the program
waits:

| Zone of the instruction | The program continues                                        |
| ----------------------- | ------------------------------------------------------------ |
| `fine` (stop point)     | when the robot stands still on the point                     |
| `z10`, ... (fly-by)     | 0.1 s before the robot enters the zone (planning time)       |
| with `\Conc`            | at once; at most 5 movements with `\Conc` in succession       |

If the next movement instruction arrives before the robot enters the zone, the robot
does not stop: it starts the next movement inside the zone (corner path) and leaves the
zone on the path that starts from the programmed point. The zone is `pzone_tcp` of the
`zonedata` (or `\Z`), reduced to half the distance to the neighbor points. If the next
movement arrives late, for example after a `WaitTime`, the fly-by point becomes a stop
point and a warning says so (`corner path failure`, as on the robot).

The logical instructions do not stop the robot: during `WaitTime` the robot continues its
movements, `CRobT` and `CJointT` read the position of that moment. `WaitTime \InPos` and
`WaitRob \InPos` wait for the robot to stop. At the end of the program the robot completes
the movements.

The time is simulated: the robot moves only while the program waits, the logical
instructions take no time. The execution is fast and gives always the same result. With
the viewer, or `PYRAPID_REALTIME=1`, the robot moves in real time while the program runs.

How the movements are computed:

- **Speed**: the speed of the instruction (`speeddata`: TCP and reorientation speed, or
  the time `\T`) is reduced when an axis would exceed its velocity or acceleration. The
  profile is trapezoidal; the joint movements move all the axes together.
- **Kinematics**: the inverse kinematics is in closed form for the 6 axis arms with a
  spherical wrist (most ABB models), numeric for the others (from the current position,
  the home position and, when they do not converge, 30 random positions). `confdata` (cf1, cf4, cf6,
  cfx) follows the RAPID instructions manual: `MoveJ` reaches the programmed configuration,
  `MoveL` and `MoveC` stop the program if the end point has another configuration (as
  `ConfL \On` on the robot).
- **Errors**: a point out of reach, a path through a singularity or a configuration error
  stop the program with `MotionError`.
- **Dynamics**: with the inertial data the joint torques are computed along the path,
  including the load of the tool.
- **Corner paths** superpose the end of a movement and the start of the next one in the
  space of the axes: the path in the zone is close to the parabola of the robot, not
  equal to it; only the TCP zone is used (not the reorientation zone).

### I/O signals

On the robot the I/O signals are defined in the I/O configuration of the controller, not
in the program: the program uses them by name. `--eio` (rapidvalidate and rapid2py) reads
the signals from the section `EIO_SIGNAL` of an ABB configuration file:

```
EIO:CFG_1.0:6:1::
EIO_SIGNAL:
      -Name "doGripper" -SignalType "DO" -Device "d652" -DeviceMap "0"
      -Name "diGripperClosed" -SignalType "DI" -Device "d652" -DeviceMap "0"
```

The signals have the types `signaldi`, `signaldo`, `signalgi`, `signalgo`, `signalai`,
`signalao`; they are semi-value objects (kernel manual 2.16): in an expression they are
their value (`IF diReady = 1 THEN`), they cannot be assigned. The instructions are
`SetDO`, `Set`, `Reset`, `PulseDO`, `SetGO`, `SetAO`, `WaitDI`, `WaitDO`, `WaitGI`,
`WaitUntil` (`\MaxTime`, `\TimeFlag`, `ERR_WAIT_MAXTIME`), and the functions `DInput`,
`DOutput`, `GInput`, `GOutput`, `AInput`, `AOutput`, `TestDI`. The values are in
`pyrapid.IO`; with a robot the waits follow the time of the robot.

### Simulation of the cell

The RAPID program talks with the equipment around the robot only through the movements and
the I/O signals, as on the robot. The equipment is simulated by a Python file, given with
`PYRAPID_SIMULATION=file.py`, that is not part of the program. The file has a function
`setup(world)`; `world` gives:

| `world.`                          |                                                          |
| --------------------------------- | -------------------------------------------------------- |
| `robot`, `time`, `axes()`, `flange()` | the robot model, the time, the axes, the flange (pin.SE3) |
| `viewer()`                        | the MeshCat viewer (`meshcat.Visualizer`) or None        |
| `signal(name)`, `set_signal(name, value)` | read the outputs, set the inputs of the program  |
| `on_signal(action)`               | `action(world, name, value)` when a signal changes       |
| `on_step(action)`, `on_frame(action)` | `action(world)` at every sample of the robot, at every frame of the viewer |
| `on_finish(action)`               | `action(world)` at the end of the program                |
| `after(delay, action)`            | `action()` after `delay` seconds of the robot time       |

See `examples/pallettizer/cell.py`.

### Log and view

| Environment variable      | Effect                                                      |
| ------------------------- | ----------------------------------------------------------- |
| `PYRAPID_MOTION_LOG=1`    | one line at the end of each movement: time, zone, axes, torques |
| `PYRAPID_REALTIME=1`      | the robot moves in real time                                |
| `PYRAPID_VIEWER=meshcat`  | the robot in the browser, in real time, with the TCP path   |
| `PYRAPID_VIEWER_HOLD=0`   | do not wait for Ctrl+C at the end of the program            |
| `PYRAPID_SIMULATION=file` | the simulation of the cell                                  |

With the viewer, MeshCat prints the address to open (`http://127.0.0.1:7000/static/`) and
the program runs at the speed of the robot: `PYRAPID_VIEWER=meshcat` implies the real time,
`PYRAPID_REALTIME=1` is for the real time without the viewer.

### Examples

Each example has a README with what it does and how to run it:

- [examples/irb120](examples/irb120/README.md): an ABB IRB 120 draws on a table with a pen:
  joint, linear and circular movements, stop and fly-by points, a work object and a tool;
- [examples/pallettizer](examples/pallettizer/README.md): an ABB IRB 460 fills two pallets
  at the same time with different products and schemas; the cell (conveyors, pallets,
  products, gripper) is simulated by `cell.py` and talks with the program through the I/O
  signals; with the ABB CAD model the viewer shows the real robot;
- [examples/osj6](examples/osj6/README.md): osj6, a 3D printed robot with oblique swivel
  joints, folds its tube and draws on a table; the README describes the robot, its parts
  and its motors.

```sh
PYRAPID_MOTION_LOG=1 python rapid2py.py -e demo.main -i examples/irb120/demo.mod -d out -f demo.py -r
PYRAPID_VIEWER=meshcat python rapid2py.py -e demo.main -i examples/irb120/demo.mod -d out -f demo.py -r
```

## Supported language

- **Case**: the language is not case sensitive, as the manual says (Overview 1.1.1).
  `PROC`, `proc` and `Proc` are the same keyword, `Total` and `total` the same name.
- **Strings**: only the escapes of the manual (kernel 2.7): `\hh` (hexadecimal character
  code), `\\` and `""`. A string with any other escape is a lexer error.
- **Expressions**: priority and associativity as in the manual (kernel 3.1). Operators of
  the same priority are evaluated from left to right, and `NOT` applies to the first
  logical term.

The missing features are listed in [todo.md](todo.md). Among them:

- interrupts and `CONNECT`;
- long jumps in error handlers;
- semantics of `BACKWARD` and `UNDO`;
- external axes, the reorientation zones and the other motion instructions;
- installed data types such as `signaldi`.

## Layout

```
rapid_lexer.py        RAPID lexer (PLY)
rapid_parser.py       grammar and AST construction
_rapid_ast.cfg        definition of the AST nodes
_ast_gen.py           generates rapid_ast.py from _rapid_ast.cfg
ast_gen.py            generator used by _ast_gen.py
plyparser.py          common parser support (coordinates, errors)
browse_rapid_ast.py   base visitor and evaluation of constant expressions
rapidvalidate.py      semantic validation
rapid2rapid.py        AST -> RAPID
rapid2py.py           AST -> Python
run/pyrapid.py        runtime of the generated code
run/pyrapid_motion.py motion instructions, viewer, simulation of the cell
run/robotmodel.py     robot models, kinematics, dynamics
eio.py                I/O configuration (EIO.cfg)
models/               robot models of this project (IRB 460, osj6) and data overrides
third_party/abb/      ABB robot models of ROS-Industrial (git submodule)
default/standard.sys  declarations and implementations of the standard types and routines
test/                 RAPID test modules
test/exec/            programs translated and run, with the expected output (.out)
examples/irb120/      IRB 120 drawing with a pen
examples/pallettizer/ palletizer for the IRB 460 with the simulation of the cell
doc/abb/official/     ABB manuals (not in the repository, see below)
```

## Development

```sh
hatch run test          # all the tests, including mypy --strict and ruff format --check
hatch run cov           # tests with coverage
hatch run typecheck     # mypy --strict only
hatch run format        # reformat the code with ruff
hatch run gen-ast       # regenerate rapid_ast.py
```

The tests:

| Test                       | What it checks                                                     |
| -------------------------- | ------------------------------------------------------------------ |
| `test_rapid.py`            | parsing of the modules in `test/` and visit of the tree            |
| `test_roundtrip.py`        | the second rewrite with rapid2rapid is identical to the first      |
| `test_expressions.py`      | operator priority and associativity                                |
| `test_strings.py`          | string literals and escapes                                        |
| `test_case_insensitive.py` | keywords and names regardless of case                              |
| `test_rapidvalidate.py`    | one case for each diagnostic, and the invalid files in `test/`     |
| `test_robotmodel.py`       | models, inverse kinematics of every model, confdata, torques       |
| `test_motion.py`           | motion instructions: limits, paths, configurations, viewer         |
| `test_rapid2py.py`         | the generated Python compiles, the `test/exec/` programs and the examples run right |
| `test_quality.py`          | mypy strict and ruff formatting                                    |

The project code is typed and must pass `mypy --strict`. The generated files are excluded
(`rapid_ast.py` and the PLY tables `lextab.py` and `yacctab.py`). The formatting is the one
of `ruff format`, with lines of at most 100 characters.

Code comments and documentation are in English.

### ABB manuals

The official manuals are ABB copyright and are not distributed with the project. Download
them from the [ABB Library](https://library.e.abb.com/) and put them in
`doc/abb/official/`, which is excluded by `.gitignore`.
