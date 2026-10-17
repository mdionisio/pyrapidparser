# TODO

References: ABB manuals in `doc/abb/official/` (not in the repository):
kernel = 3HAC050946-001, overview = 3HAC050947-001,
instructions = 3HAC050917-001.

## rapid2py / runtime

- [ ] **Recovery points with long jump** `ERROR (56, ERR_DIVZERO)` (kernel 7.2): rapid2py
  translates the handler but ignores the list of error numbers, so the long jump is not
  implemented.
- [ ] **CONNECT / interrupts / TRAP** (kernel 4.13, 8): rapid2py raises
  "Connect not yet supported".
- [ ] **BACKWARD and UNDO handlers** (kernel 6, 7.2): check the semantics of the generated
  code, no test runs them.
- [ ] **`pi` and `dnum`**: the validator knows them (they are predefined in RAPID), the
  runtime `run/pyrapid.py` does not: a program that uses `pi` passes the validation and
  then fails at run time.
- [ ] **DIV and MOD with negative operands**: rapid2py uses `//` and `%`, which in Python
  round towards minus infinity. Check the RAPID result in the instructions manual and fix
  it if different.
- [ ] **Late binding** `% expr % args;` (kernel 4.6): check the generated code and the
  resolution of `"module:procedure"`.
- [ ] **Missing installed instructions** in `default/standard.sys` (MoveJ, MoveC, ...):
  today rapidvalidate and rapid2py reject them as undefined procedures.

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
