# TODO

References: ABB manuals in `doc/abb/official/` (not in the repository):
kernel = 3HAC050946-001, overview = 3HAC050947-001,
instructions = 3HAC050917-001.

## rapid2py / runtime

- [ ] **Recovery points with long jump** `ERROR (56, ERR_DIVZERO)` (kernel 7.2): rapid2py
  translates the handler but ignores the list of error numbers, so the long jump is not
  implemented.
- [ ] **Interrupts**: `ISignalAI`, `ISignalAO`, `IError`, `IPers`, `IVarValue`,
  `GetTrapData`, `ReadErrData`; the priorities of the traps (`SYNC`, `ISleep` of the
  ones that run) and the interrupts during the execution of the error handlers.
- [ ] **BACKWARD and UNDO handlers** (kernel 6, 7.2): check the semantics of the generated
  code, no test runs them.
- [ ] **DIV and MOD with negative operands**: rapid2py uses `//` and `%`, which in Python
  round towards minus infinity. Check the RAPID result in the instructions manual and fix
  it if different.
- [ ] **Late binding** `% expr % args;` (kernel 4.6): check the generated code and the
  resolution of `"module:procedure"`.
- [ ] **Missing installed instructions** in `default/standard.sys`: the motion
  instructions other than MoveAbsJ, MoveJ, MoveL, MoveC (MoveExtJ, the Sync and DO
  variants, SearchL, TriggL, ...), the serial channels (`com1:`), `ReadAnyBin`,
  `WriteAnyBin`, `FSSize`, `TryInit`, `ErrWrite`/`GetSysInfo` have no test.
- [ ] **Sockets**: `SocketSend` and `SocketReceive` support only `\Str`; `\RawData`,
  `\Data` and `\NoOfBytes` are missing, and a message longer than 1024 bytes is cut.
- [ ] **Movements that stop on a condition and the path control**: `SearchC`, `SearchL` on a
  persistent variable (`PersBool`) and `\Sup` (more than one hit is not counted
  after the movement stops), `TriggRampAO`, `TriggCheckIO`, `MoveExtJ`, `EOffsSet`/`EOffsOn`,
  `DefDFrame`/`DefFrame`, `PathResol`, `MoveJSync`/`MoveLSync`, `PathAccLim`, `SpeedLimAxis`, `CirPathMode`.
- [ ] **Math and general functions**: `StrFormat`, `StrDigCmp`/`StrDigCalc`, `ValidIO`, `RobName`, `OpMode`, `RunMode`;
  the bit functions work on bytes (0 to 255) only; `STR_UPPER` and `STR_LOWER` have only
  the ASCII letters; the argument errors (`ASin(2)`) raise a Python exception, not
  `ERR_ARGVALERR`.
- [ ] **Stop and wait**: `Stop`, `Break`, `SystemStopAction` end the program (there is
  no operator to restart it); `TPReadNum` and `TPReadFK` read the standard input and the
  other `UI*` instructions (`UIMsgBox`, ...) are missing; `WaitUntil` on routines called
  by name.
- [ ] **Raw bytes** (`PackRawBytes`, `UnPackRawBytes`, ...): implemented, no test.

## Motion (run/pyrapid_motion.py, run/robotmodel.py)

- [ ] **Corner paths**: computed in the space of the axes (superposition of the two
  movements), not as the parabola of the TCP; the reorientation zone (`pzone_ori`,
  `zone_ori`) is not used; during the corner path the axes may briefly exceed their
  velocity limit.
- [ ] **Servo lag**: the program continues PREFETCH_TIME (0.1 s) before the zone; the
  robot adds a delay of 0 - 1 s depending on the speed (RAPID overview 2.3).
- [ ] **External axes** (`extax`, `v_leax`, `v_reax`) are ignored.
- [ ] **ConfL supervision**: the RAPID manual (confdata) checks that the axes 1, 4, 6 do
  not move more than 180 degrees and that cfx does not change; today only the
  configuration of the end point is compared.
- [ ] **Stationary tool** and **work object held by the robot** (`robhold`) are not
  supported.
- [ ] **cfx of the 6 axis models with numeric inverse kinematics** (CRB 15000, IRB 5400,
  IRB 6640): cfx is always 0.
- [ ] **Acceleration and torque limits**: no model has them; add `models/<model>.json`
  when the data is available (ABB does not publish it).
- [ ] **IRB 460**: the lengths come from the ABB CAD model, but there is no inertial data
  (it could be estimated from the volumes of the CAD parts) and the combined limits of
  the axes 2 and 3 are not modeled (the reach of the model is 2446 mm, the data sheet
  says 2403 mm).
- [ ] **Palletizer example**: `PlaceProduct` of two products at once (type 2),
  `TakeSheet`/`PlaceSheet` and the pallet magazine (`TakePallet`/`PlacePallet`) only
  write a message; the positions of `cell.py` repeat the points of `environment.mod`.
- [ ] **I/O**: interrupts on signals (`ISignalDI`), the cross connections
  and the device mapping of EIO.cfg are not supported.
- [ ] **osj6**: the parts are a first design, not printed yet. The hatches have no
  fixing, the gear is only keyed on the spigot (no axial screw), there is no reference
  for the zero of the axes (the N20 encoders are incremental), the motor torques are not
  in the model (`effort`). The confdata of the ABB arms does not describe its solutions:
  a configuration of its own (e.g. the signs of the oblique joints) would let MoveJ
  choose the solution.
- [ ] **SingArea**: `SingArea \Wrist` (the orientation is joint interpolated to pass a
  wrist singularity) and `\LockAxis4` are missing. ABB with `\Off` (the default) passes
  near a singularity sweeping the axes at a lower TCP speed; here the program stops
  (`the path crosses a singularity`, `test/exec/motion_singular.mod`).
- [ ] **Interruption**: a motion error stops the program with a Python exception; ABB
  raises recoverable errors for some of them (ERR_ROBLIMIT with `\ErrorNumber`).

## Parser / lexer

- [ ] **Comments inside RECORD** (kernel 2.10, 2.14): they are allowed at the end of a line
  and on the last line, but the parser rejects any comment inside a RECORD.
- [ ] **Octal literals** `0o17` (kernel 2.5): the token `INT_CONST_OCT` is declared but
  there is no lexer rule.
- [ ] **Range of numeric literals** (kernel 2.5, IEEE 754): not checked.
- [ ] **Code inherited from pycparser** in the lexer (character constants,
  `t_UNMATCHED_QUOTE`, `t_BAD_CHAR_CONST`): it does not exist in RAPID, it can be removed.

## rapidvalidate

- [ ] **Entry routine without parameters** (kernel 9.1, "Entry routines cannot have
  parameters"): the procedure passed to `rapid2py -e` could be checked.
- [ ] **Late binding** (kernel 5.4): the procedures called by the same statement must have
  compatible parameters. Today only the name is checked to be a string.
- [ ] **Installed and semi-value types** (kernel 2.16): signaldi, signaldo, etc. are not in
  the catalog, so the expressions that use them are not checked (the catalog from the
  instructions manual 3HAC050917 is needed).
- [ ] **TEST with repeated CASE values** (kernel 4.18, "only the first is recognized"):
  it could be a warning.
- [ ] **Use of an optional parameter that is not present** (kernel 5.2): it is a run time
  error, statically only the use outside `IF Present(...)` could be reported (warning).
- [ ] **Placeholders** (`<SMT>`, `<EXP>`, ...): syntactically valid, but rapid2py cannot
  translate them. Consider a warning.
