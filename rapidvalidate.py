#!/usr/bin/env python3
# -----------------------------------------------------------------
# rapidvalidate.py
#
# Static semantic checks of RAPID modules, run after the parsing.
#
# The parser only checks the syntax: a program can be syntactically
# correct and still be rejected by the robot controller when it is
# loaded ("semantic errors, violation of semantic rules, typically
# type errors"). This module reports those errors.
#
# The rules come from "Technical reference manual - RAPID kernel"
# (ABB, 3HAC050946-001, RobotWare 6); every check quotes the section
# of the manual it implements.
# -----------------------------------------------------------------
import glob
import os
import re
import sys
from dataclasses import dataclass, field
from typing import Any, Iterator, Optional, Sequence, Union

import rapid_ast
import rapid_parser
import run.pyrapid as pyrapid
from plyparser import ParseError

ERROR = "error"
WARNING = "warning"


@dataclass
class Diagnostic:
    file: str
    line: int
    severity: str
    code: str
    message: str

    def __str__(self) -> str:
        return "%s:%d: %s: %s [%s]" % (self.file, self.line, self.severity, self.message, self.code)


# 2.3 Identifiers: "The maximum length of an identifier is 32 characters."
MAX_IDENTIFIER_LENGTH = 32

# "!robot: <model>": the robot model of the task (robotmodel.py), not in the manual
ROBOT_DIRECTIVE = "robot:"

# 9.2 Module declarations: attributes in table order
MODULE_ATTRIBUTES = ("SYSMODULE", "NOVIEW", "NOSTEPIN", "VIEWONLY", "READONLY")

# 2.16 Data type value classes: installed types known to be non-value types
NON_VALUE_TYPES = frozenset(("iodev", "socketdev", "clock", "rawbytes"))

# 2.15 The alias data types: "The built-in alias types are errnum and intnum - both are
# alias for num." (dionum, byte and socketstatus are alias for num too)
BUILTIN_ALIASES = {
    "errnum": "num",
    "intnum": "num",
    "dionum": "num",
    "byte": "num",
    "socketstatus": "num",
}

# 12 Built-in data objects, errors that belong to the kernel (missing in run.pyrapid)
KERNEL_ERRORS = (
    "ERR_ALRDYCNT ERR_ARGDUPCND ERR_ARGNOTPER ERR_ARGNOTVAR ERR_CALLPROC ERR_CNTNOTVAR "
    "ERR_DIVZERO ERR_EXECPHR ERR_FNCNORET ERR_ILLDIM ERR_ILLQUAT ERR_ILLRAISE ERR_INOISSAFE "
    "ERR_INOMAX ERR_MAXINTVAL ERR_NOTARR ERR_NOTEQDIM ERR_NOTINTVAL ERR_NOTPRES ERR_OUTOFBND "
    "ERR_REFUNKDAT ERR_REFUNKFUN ERR_REFUNKPRC ERR_REFUNKTRP ERR_STRTOOLNG ERR_UNKINO "
    "LONG_JMP_ALL_ERR"
).split()

# 4.9 The Raise statement: "error number ... in the range from 1 to 90"
MIN_ERROR_NUMBER = 1
MAX_ERROR_NUMBER = 90

# 2.13 The type string: "A string may consist of 0 to 80 characters"
MAX_STRING_LENGTH = 80

# 2.22 Variable declarations: "an array (of degree 1, 2, or 3)"
MAX_ARRAY_DEGREE = 3

RELATIONAL_OPERATORS = ("<", "<=", ">", ">=")
EQUALITY_OPERATORS = ("=", "<>")
LOGICAL_OPERATORS = ("AND", "OR", "XOR")
NUMERIC_TYPES = ("num", "dnum")


# ----------------------------------------------------------------- symbol table


@dataclass(eq=False)
class ModuleInfo:
    name: str
    node: Any
    file: str
    objects: dict[str, "Entry"] = field(default_factory=dict)


@dataclass(eq=False)
class TypeInfo:
    name: str
    # "atomic", "record", "alias", "installed" (opaque) or "anytype"
    kind: str
    module: Optional[ModuleInfo] = None
    local: bool = False
    node: Any = None
    # record components, resolved after the collection of the declarations
    components: list[tuple[str, Optional["DataType"]]] = field(default_factory=list)
    # alias: the aliased type
    alias_of: Optional["TypeInfo"] = None


@dataclass(frozen=True)
class DataType:
    info: TypeInfo
    # array dimensions, None when not known (conformant parameter "{*}" or not constant)
    dims: tuple[Optional[int], ...] = ()

    @property
    def base(self) -> TypeInfo:
        return base_type(self.info)

    @property
    def element(self) -> "DataType":
        return DataType(self.info, self.dims[1:])

    def __str__(self) -> str:
        if not self.dims:
            return self.info.name
        return "%s{%s}" % (
            self.info.name,
            ",".join("*" if d is None else str(d) for d in self.dims),
        )


@dataclass(eq=False)
class DataObject:
    name: str
    # "VAR", "PERS", "CONST", "PARAM" (routine parameter) or "LOOP" (FOR loop variable)
    kind: str
    type: Optional[DataType] = None
    module: Optional[ModuleInfo] = None
    routine: Optional["RoutineInfo"] = None
    local: bool = False
    task: bool = False
    # declaration (VarDeclarationAST, PersDeclarationAST, ConstDeclarationAST, parameter)
    node: Any = None
    # parameters: access mode IN, VAR, PERS, INOUT or REF
    mode: str = "IN"
    optional: bool = False
    switch: bool = False
    group: Optional[int] = None
    # FOR loop variables, ERRNO, INTNO
    readonly: bool = False
    predefined: bool = False


@dataclass(eq=False)
class RoutineInfo:
    name: str
    # "PROC", "FUNC" or "TRAP"
    kind: str
    module: Optional[ModuleInfo] = None
    local: bool = False
    node: Any = None
    params: list[DataObject] = field(default_factory=list)
    return_type: Optional[DataType] = None
    # kernel routines with special rules (Present, Dim)
    special: Optional[str] = None


Entry = Union[TypeInfo, DataObject, RoutineInfo]


def base_type(info: TypeInfo) -> TypeInfo:
    seen = 0
    while info.kind == "alias" and info.alias_of is not None and seen < 16:
        info = info.alias_of
        seen += 1
    return info


def describe(entry: Entry) -> str:
    if isinstance(entry, TypeInfo):
        return "data type"
    if isinstance(entry, RoutineInfo):
        return {"PROC": "procedure", "FUNC": "function", "TRAP": "trap"}[entry.kind]
    return {
        "VAR": "variable",
        "PERS": "persistent",
        "CONST": "constant",
        "PARAM": "parameter",
        "LOOP": "loop variable",
    }[entry.kind]


@dataclass
class RoutineContext:
    module: ModuleInfo
    routine: Optional[RoutineInfo] = None
    # innermost last: routine data objects, then the FOR loop variables
    scopes: list[dict[str, Entry]] = field(default_factory=list)
    # label name -> (label node, statement list path)
    labels: dict[str, tuple[Any, tuple[int, ...]]] = field(default_factory=dict)
    # "body", "backward", "error" or "undo"
    handler: str = "body"
    has_return_value: bool = False


# ----------------------------------------------------------------- helpers


def node_position(node: Any) -> tuple[Optional[str], Optional[int]]:
    """file and line of a node: the first coordinate found in the subtree"""
    if node is None:
        return None, None
    coord = getattr(node, "coord", None)
    if coord is not None and getattr(coord, "line", None) is not None:
        return coord.file, coord.line
    if isinstance(node, rapid_ast.Node):
        for _, child in node.children():
            f, line = node_position(child)
            if line is not None:
                return f, line
    elif isinstance(node, (list, tuple)):
        for child in node:
            f, line = node_position(child)
            if line is not None:
                return f, line
    return None, None


def statements(statement_list: Optional[Sequence[Any]]) -> Iterator[Any]:
    """the statements of a statement list (comments and <SMT> placeholders are skipped,
    the compact IF has the statement without StatementAST)"""
    for item in statement_list or []:
        if isinstance(item, rapid_ast.StatementAST):
            item = item.statement
        if item is None or isinstance(item, rapid_ast.CommentAST):
            continue
        yield item


def robot_comments(node: Any, in_routine: bool = False) -> Iterator[tuple[Any, bool]]:
    """the !robot: comments of a module, and whether they are inside a routine"""
    if isinstance(node, rapid_ast.CommentAST):
        if node.comment.strip().lower().startswith(ROBOT_DIRECTIVE):
            yield node, in_routine
    elif isinstance(node, (list, tuple)):
        for child in node:
            yield from robot_comments(child, in_routine)
    elif isinstance(node, rapid_ast.Node):
        inside = in_routine or isinstance(node, rapid_ast.RoutineDeclarationATS)
        for _, child in node.children():
            yield from robot_comments(child, inside)


def unwrap(node: Any) -> Any:
    while isinstance(node, (rapid_ast.ExpressionAST, rapid_ast.ConstExpressionAST)):
        node = node.expr if isinstance(node, rapid_ast.ExpressionAST) else node.expression
    return node


def string_length(raw: str) -> int:
    """characters of a string literal as written between the quotes: a character code
    \\hh, a doubled back slash or double quote are one character (2.7)"""
    return len(re.sub(r'\\[0-9A-Fa-f]{2}|\\\\|""', "x", raw))


def identifier_name(node: Any) -> Optional[str]:
    if isinstance(node, rapid_ast.IdentifierAST):
        name: Optional[str] = node.name
        return name
    return None


# ----------------------------------------------------------------- built-in objects


class Builtins:
    """predefined types, data objects and routines (2.19, 11, 12, 13), taken from the
    runtime run.pyrapid and from the kernel manual"""

    def __init__(self) -> None:
        self.objects: dict[str, Entry] = {}
        symbols = pyrapid.Symbols()
        class_names: dict[type, str] = {}
        datatypes: list[tuple[str, type]] = []
        for name, sym in symbols.global_symbol.items():
            if sym.type == pyrapid.Symbol.SYM_TYPE_DATATYPE:
                datatypes.append((name, sym.data))
                # the runtime class rapid_<name> is the canonical type of the class
                if sym.data.__name__.lower() == "rapid_" + name.lower():
                    class_names[sym.data] = name
        for name, cls in datatypes:
            class_names.setdefault(cls, name)

        for atomic in ("num", "dnum", "bool", "string"):
            self.objects[atomic] = TypeInfo(atomic, "atomic")
        for name, cls in datatypes:
            key = name.lower()
            if key in self.objects:
                continue
            if key == "anytype":
                self.objects[key] = TypeInfo(name, "anytype")
            elif key in BUILTIN_ALIASES:
                self.objects[key] = TypeInfo(name, "alias")
            elif isinstance(cls, type) and issubclass(cls, pyrapid.rapid_struct):
                self.objects[key] = TypeInfo(name, "record")
            else:
                self.objects[key] = TypeInfo(name, "installed")
        for key, target in BUILTIN_ALIASES.items():
            info = self.objects.get(key)
            if isinstance(info, TypeInfo):
                aliased = self.objects[target]
                assert isinstance(aliased, TypeInfo)
                info.alias_of = aliased
        for name, cls in datatypes:
            info = self.objects[name.lower()]
            assert isinstance(info, TypeInfo)
            if info.kind == "record":
                instance = cls()
                for cname, ctype in zip(instance.names, instance.types):
                    cinfo = self.objects.get(class_names.get(ctype, "").lower())
                    info.components.append(
                        (cname, DataType(cinfo) if isinstance(cinfo, TypeInfo) else None)
                    )

        for name, sym in symbols.global_symbol.items():
            if sym.type in (pyrapid.Symbol.SYM_TYPE_CONST_VAR, pyrapid.Symbol.SYM_TYPE_VAR):
                vartype = getattr(sym, "vartype", None)
                vname = class_names.get(vartype, "") if isinstance(vartype, type) else ""
                tinfo = self.objects.get(vname.lower())
                kind = "CONST" if sym.type == pyrapid.Symbol.SYM_TYPE_CONST_VAR else "VAR"
                self.objects[name.lower()] = DataObject(
                    name,
                    kind,
                    DataType(tinfo) if isinstance(tinfo, TypeInfo) else None,
                    predefined=True,
                )
        errnum = self.type("errnum")
        intnum = self.type("intnum")
        for name in KERNEL_ERRORS:
            self.objects.setdefault(
                name.lower(), DataObject(name, "CONST", errnum, predefined=True)
            )
        num_type = self.type("num")
        self.objects.setdefault("pi", DataObject("pi", "CONST", num_type, predefined=True))
        # "The predefined (readonly) variable ERRNO", "variable INTNO" (7.1, 8)
        self.objects["errno"] = DataObject("ERRNO", "VAR", errnum, readonly=True, predefined=True)
        self.objects["intno"] = DataObject("INTNO", "VAR", intnum, readonly=True, predefined=True)

        # 11 Built-in routines
        anytype = self.type("anytype")
        num = self.type("num")
        boolean = self.type("bool")
        self.objects["present"] = RoutineInfo(
            "Present",
            "FUNC",
            params=[DataObject("OptPar", "PARAM", anytype, mode="REF")],
            return_type=boolean,
            special="Present",
        )
        self.objects["dim"] = RoutineInfo(
            "Dim",
            "FUNC",
            params=[
                DataObject("ArrPar", "PARAM", anytype, mode="REF"),
                DataObject("DimNo", "PARAM", num),
            ],
            return_type=num,
            special="Dim",
        )
        for name in ("IsPers", "IsVar"):
            self.objects[name.lower()] = RoutineInfo(
                name,
                "FUNC",
                params=[DataObject("DatObj", "PARAM", anytype, mode="INOUT")],
                return_type=boolean,
            )
        self.objects["isleep"] = RoutineInfo(
            "ISleep", "PROC", params=[DataObject("Ino", "PARAM", intnum, mode="VAR")]
        )
        # installed instruction translated by rapid2py
        self.objects["waituntil"] = RoutineInfo(
            "WaitUntil",
            "PROC",
            params=[
                DataObject("InPos", "PARAM", None, mode="IN", optional=True, switch=True),
                DataObject("Cond", "PARAM", boolean),
                DataObject("MaxTime", "PARAM", num, optional=True),
                DataObject("TimeFlag", "PARAM", boolean, mode="VAR", optional=True),
                DataObject("PollRate", "PARAM", num, optional=True),
            ],
        )

    def type(self, name: str) -> Optional[DataType]:
        info = self.objects.get(name)
        return DataType(info) if isinstance(info, TypeInfo) else None


# ----------------------------------------------------------------- validator


class Validator:
    def __init__(self) -> None:
        self.builtins = Builtins()
        self.diagnostics: list[Diagnostic] = []
        self.modules: dict[str, ModuleInfo] = {}
        self.global_objects: dict[str, Entry] = {}
        self.routines: list[RoutineInfo] = []
        self.types: list[TypeInfo] = []
        self.data: list[DataObject] = []
        self.current_file = ""
        self.evaluating: set[int] = set()

    # ------------------------------------------------------------- reporting

    def report(self, node: Any, code: str, message: str, severity: str = ERROR) -> None:
        file, line = node_position(node)
        self.diagnostics.append(
            Diagnostic(file or self.current_file, line or 0, severity, code, message)
        )

    def where(self, entry: Entry) -> str:
        file, line = node_position(entry.node)
        if line is None:
            return "predefined"
        return "%s:%d" % (file, line)

    def check_identifier(self, name: Optional[str], node: Any) -> None:
        if name is None:
            return
        # 2.3 Identifiers
        if len(name) > MAX_IDENTIFIER_LENGTH:
            self.report(
                node,
                "identifier-too-long",
                "identifier '%s' is longer than %d characters" % (name, MAX_IDENTIFIER_LENGTH),
            )

    # ------------------------------------------------------------- entry point

    def validate(self, modules: Sequence[Any]) -> list[Diagnostic]:
        module_nodes = [m for m in modules if isinstance(m, rapid_ast.ModuleAST)]
        infos = [self.collect_module(m) for m in module_nodes]
        self.check_module_names()
        self.check_robot_directives(module_nodes)
        for t in self.types:
            self.resolve_type_definition(t)
        for d in self.data:
            assert d.module is not None
            self.resolve_data_type(d, RoutineContext(d.module))
        for r in self.routines:
            self.resolve_routine_signature(r)
        for d in self.data:
            assert d.module is not None
            self.check_data_declaration(d, RoutineContext(d.module))
        for r in self.routines:
            self.check_routine(r)
        del infos
        return sorted(self.diagnostics, key=lambda d: (d.file, d.line))

    # ------------------------------------------------------------- collection

    def register(self, module: ModuleInfo, name: Optional[str], entry: Entry, node: Any) -> None:
        if name is None:
            return
        self.check_identifier(name, node)
        key = name.lower()
        # 2.12, 2.20, 5.3: "Two module objects declared in the same module may not have the
        # same name."
        previous = module.objects.get(key)
        if previous is not None:
            self.report(
                node,
                "duplicate-name",
                "'%s' is already declared in module %s as %s (%s)"
                % (name, module.name, describe(previous), self.where(previous)),
            )
            return
        module.objects[key] = entry
        if entry.local:
            return
        # "Two global objects declared in two different modules in the task buffer may not
        # have the same name."
        previous = self.global_objects.get(key)
        if previous is not None:
            assert previous.module is not None
            self.report(
                node,
                "duplicate-global",
                "global '%s' is already declared in module %s as %s (%s)"
                % (name, previous.module.name, describe(previous), self.where(previous)),
            )
            return
        self.global_objects[key] = entry

    def collect_module(self, node: Any) -> ModuleInfo:
        name = identifier_name(node.module_name) or "<ID>"
        file, _ = node_position(node)
        self.current_file = file or self.current_file
        module = ModuleInfo(name, node, file or "")
        self.check_identifier(identifier_name(node.module_name), node.module_name)
        key = name.lower()
        # 9.2 "Two different modules may not share the same name."
        if key in self.modules and identifier_name(node.module_name) is not None:
            self.report(
                node.module_name,
                "duplicate-module",
                "module %s is already declared (%s)" % (name, self.modules[key].file),
            )
        else:
            self.modules[key] = module
        self.check_module_attributes(node)

        for item in node.type_definitions:
            if not isinstance(item, rapid_ast.TypeDefAST) or item.definition is None:
                continue
            definition = item.definition
            local = item.type == "LOCAL"
            if isinstance(definition, rapid_ast.RecordDefAST):
                tname = identifier_name(definition.record_name)
                info = TypeInfo(tname or "<ID>", "record", module, local, definition)
            else:
                tname = identifier_name(definition.alias_name)
                info = TypeInfo(tname or "<ID>", "alias", module, local, definition)
            self.types.append(info)
            self.register(module, tname, info, definition)

        for item in node.data_definitions:
            obj = self.data_object(item, module, None)
            if obj is not None:
                self.data.append(obj)
                self.register(module, obj.name, obj, obj.node)

        for item in node.routine_definitions:
            if not isinstance(item, rapid_ast.RoutineDeclarationATS) or item.definition is None:
                continue
            definition = item.definition
            if isinstance(definition, rapid_ast.ProcedureDeclarationAST):
                rname, kind = identifier_name(definition.procedure_name), "PROC"
            elif isinstance(definition, rapid_ast.FunctionDeclarationAST):
                rname, kind = identifier_name(definition.function_name), "FUNC"
            else:
                rname, kind = identifier_name(definition.procedure_name), "TRAP"
            routine = RoutineInfo(rname or "<ID>", kind, module, item.type == "LOCAL", definition)
            self.routines.append(routine)
            self.register(module, rname, routine, definition)
        return module

    def data_object(
        self, item: Any, module: ModuleInfo, routine: Optional[RoutineInfo]
    ) -> Optional[DataObject]:
        if not isinstance(item, rapid_ast.DataDefATS) or item.definition is None:
            return None
        decl = item.definition
        if isinstance(decl, rapid_ast.VarDeclarationAST):
            kind = "VAR"
        elif isinstance(decl, rapid_ast.PersDeclarationAST):
            kind = "PERS"
        else:
            kind = "CONST"
        name = identifier_name(decl.variable_instance.name)
        if name is None:
            return None
        return DataObject(
            name,
            kind,
            module=module,
            routine=routine,
            local=item.type == "LOCAL",
            task=item.type == "TASK",
            node=decl,
        )

    def check_module_attributes(self, node: Any) -> None:
        # 9.2 "An attribute may not be specified more than once. If present, attributes must
        # be specified in table order. The specification of noview excludes nostepin,
        # viewonly, and readonly (and vice versa). The specification of viewonly excludes
        # readonly (and vice versa)."
        names = [a.name for a in node.module_attribute]
        seen: list[str] = []
        for attr, name in zip(node.module_attribute, names):
            if name in seen:
                self.report(attr, "module-attribute", "module attribute %s repeated" % (name,))
            elif seen and MODULE_ATTRIBUTES.index(name) < MODULE_ATTRIBUTES.index(seen[-1]):
                self.report(
                    attr,
                    "module-attribute",
                    "module attribute %s must be specified before %s" % (name, seen[-1]),
                )
            seen.append(name)
        exclusions = [("NOVIEW", ("NOSTEPIN", "VIEWONLY", "READONLY")), ("VIEWONLY", ("READONLY",))]
        for name, excluded in exclusions:
            if name in names:
                for other in excluded:
                    if other in names:
                        self.report(
                            node.module_name,
                            "module-attribute",
                            "module attribute %s excludes %s" % (name, other),
                        )

    def check_robot_directives(self, module_nodes: Sequence[Any]) -> None:
        """the comment !robot: <model> names the robot model of the task: it must be a
        known model, outside the routines, the same in all the modules"""
        chosen: Optional[tuple[str, Any]] = None
        for module in module_nodes:
            for comment, in_routine in robot_comments(module):
                name = comment.comment[len(ROBOT_DIRECTIVE) :].strip()
                if in_routine:
                    self.report(
                        comment,
                        "robot-directive",
                        "!robot: is allowed only outside the routines",
                    )
                    continue
                # imported here: numpy and Pinocchio are needed only by the robot programs
                import robotmodel

                try:
                    robotmodel.find_model(name)
                except robotmodel.ModelError as error:
                    self.report(comment, "unknown-robot", str(error))
                    continue
                if chosen is None:
                    chosen = (name, comment)
                elif chosen[0].lower() != name.lower():
                    file, line = node_position(chosen[1])
                    self.report(
                        comment,
                        "robot-conflict",
                        "the task already moves the robot %s (%s:%s)" % (chosen[0], file, line),
                    )

    def check_module_names(self) -> None:
        # 2.20, 5.3, 9.2 "A module and a global module object (type, data object or routine)
        # may not share the same name."
        for key, module in self.modules.items():
            entry = self.global_objects.get(key)
            if entry is not None:
                self.report(
                    entry.node,
                    "module-name-clash",
                    "global %s '%s' has the same name as module %s"
                    % (describe(entry), entry.name, module.name),
                )

    # ------------------------------------------------------------- lookup

    def lookup(self, name: str, ctx: RoutineContext) -> Optional[Entry]:
        key = name.lower()
        for scope in reversed(ctx.scopes):
            if key in scope:
                return scope[key]
        if key in ctx.module.objects:
            return ctx.module.objects[key]
        if key in self.global_objects:
            return self.global_objects[key]
        return self.builtins.objects.get(key)

    def resolve_type_name(self, node: Any, ctx: RoutineContext) -> Optional[TypeInfo]:
        name = identifier_name(node)
        if name is None:
            return None
        entry = self.lookup(name, ctx)
        if entry is None:
            self.report(node, "unknown-type", "unknown data type '%s'" % (name,))
            return None
        if not isinstance(entry, TypeInfo):
            self.report(
                node, "not-a-type", "'%s' is a %s, not a data type" % (name, describe(entry))
            )
            return None
        return entry

    # ------------------------------------------------------------- type definitions

    def resolve_type_definition(self, info: TypeInfo) -> None:
        assert info.module is not None
        ctx = RoutineContext(info.module)
        definition = info.node
        if info.kind == "record":
            names: dict[str, Any] = {}
            for comp in definition.components:
                if not isinstance(comp, rapid_ast.RecordComponentDefAST):
                    continue
                cname = identifier_name(comp.record_component_name)
                if cname is None:
                    continue
                self.check_identifier(cname, comp.record_component_name)
                if cname.lower() in names:
                    self.report(
                        comp.record_component_name,
                        "duplicate-name",
                        "component '%s' repeated in record %s" % (cname, info.name),
                    )
                names[cname.lower()] = comp
                ctype = self.resolve_type_name(comp.data_type, ctx)
                info.components.append((cname, DataType(ctype) if ctype else None))
        else:
            target = self.resolve_type_name(definition.type_name, ctx)
            if target is not None and target is not info:
                # 2.15 "One alias type cannot be defined upon another alias type."
                if target.kind == "alias":
                    self.report(
                        definition.type_name,
                        "alias-of-alias",
                        "alias %s cannot be defined upon the alias type %s"
                        % (info.name, target.name),
                    )
                info.alias_of = target

    def value_class(self, t: Optional[DataType], seen: Optional[set[int]] = None) -> str:
        """2.16 Data type value classes: "value", "nonvalue" or "unknown" """
        if t is None:
            return "unknown"
        info = t.base
        if info.name.lower() in NON_VALUE_TYPES:
            return "nonvalue"
        if info.kind == "record":
            seen = seen or set()
            if id(info) in seen:
                return "unknown"
            seen.add(id(info))
            classes = [self.value_class(ct, seen) for _, ct in info.components]
            if "nonvalue" in classes:
                return "nonvalue"
            return "value"
        if info.kind in ("atomic",):
            return "value"
        return "unknown"

    # ------------------------------------------------------------- data declarations

    def resolve_data_type(self, obj: DataObject, ctx: RoutineContext) -> None:
        decl = obj.node
        info = self.resolve_type_name(decl.type, ctx)
        dims: list[Optional[int]] = []
        for dim in decl.variable_instance.size:
            value = self.const_value(dim, ctx)
            dims.append(int(value) if isinstance(value, (int, float)) else None)
        if info is not None:
            obj.type = DataType(info, tuple(dims))

    def check_data_declaration(self, obj: DataObject, ctx: RoutineContext) -> None:
        decl = obj.node
        vdef = decl.variable_instance
        if obj.routine is not None:
            # (module data objects are checked when registered)
            self.check_identifier(obj.name, vdef.name)
            # 2.18 "the local directive only may be used at module level (not inside a
            # routine)", "The task directive only may be used at module level"
            if obj.local:
                self.report(
                    decl, "local-in-routine", "LOCAL is allowed only for module data objects"
                )
            if obj.task:
                self.report(decl, "task-in-routine", "TASK is allowed only for module data objects")
            # 2.23 "persistents can only be declared at module level (not inside a routine)"
            if obj.kind == "PERS":
                self.report(
                    decl, "pers-in-routine", "persistent %s declared in a routine" % (obj.name,)
                )

        # 2.22 "array (of degree 1, 2, or 3)", "The dimension expression must represent an
        # integer value greater than 0."
        if len(vdef.size) > MAX_ARRAY_DEGREE:
            self.report(
                vdef.name,
                "array-degree",
                "array %s has degree %d, the maximum is %d"
                % (obj.name, len(vdef.size), MAX_ARRAY_DEGREE),
            )
        for dim in vdef.size:
            self.check_constant_expression(dim, ctx, "array dimension")
            dim_type = self.type_of(dim, ctx)
            if dim_type is not None and dim_type.base.name.lower() not in NUMERIC_TYPES:
                self.report(dim, "array-dimension", "array dimension must be a num value")
            value = self.const_value(dim, ctx)
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                if value != int(value) or value <= 0:
                    self.report(
                        dim,
                        "array-dimension",
                        "array dimension must be an integer greater than 0, found %s" % (value,),
                    )

        value = vdef.value
        # 2.24 "<constant definition> ::= <identifier> [...] ':=' <constant expression>"
        if obj.kind == "CONST" and value is None:
            self.report(vdef.name, "missing-value", "constant %s must have a value" % (obj.name,))
        # 2.23 "Local and task global persistents must be initialized"
        if obj.kind == "PERS" and value is None and (obj.local or obj.task):
            self.report(
                vdef.name,
                "missing-value",
                "%s persistent %s must have an initial value"
                % ("local" if obj.local else "task", obj.name),
            )
        if value is None or obj.type is None:
            return
        # 2.16 constant, persistent and variable with initialization: only value types
        if self.value_class(obj.type) == "nonvalue":
            self.report(
                vdef.name,
                "value-class",
                "%s %s of non-value type %s cannot be initialized"
                % (describe(obj), obj.name, obj.type),
            )
            return
        if obj.kind == "PERS":
            # 2.23 "[':=' <literal expression>]"
            self.check_literal_expression(value)
        else:
            # 2.22, 2.24 "':=' <constant expression>"
            self.check_constant_expression(value, ctx, "initial value of %s" % (obj.name,))
        self.check_value(value, obj.type, ctx, "initial value of %s" % (obj.name,))

    def check_constant_expression(self, node: Any, ctx: RoutineContext, what: str) -> None:
        """3.2 "A constant expression ... may not at any level contain variables, persistents
        or function calls!" """
        node = unwrap(node)
        if node is None:
            return
        if isinstance(node, rapid_ast.FunctionCallAST):
            self.report(
                node,
                "not-constant",
                "%s must be a constant expression, function calls are not allowed" % (what,),
            )
        elif isinstance(node, rapid_ast.VariableAST):
            obj = self.reference_object(node, ctx, quiet=True)
            if isinstance(obj, DataObject) and obj.kind != "CONST":
                self.report(
                    node,
                    "not-constant",
                    "%s must be a constant expression, %s %s is not a constant"
                    % (what, describe(obj), obj.name),
                )
            for index in node.index:
                self.check_constant_expression(index, ctx, what)
        elif isinstance(node, rapid_ast.AggregateAST):
            for member in node.expr:
                self.check_constant_expression(member, ctx, what)
        elif isinstance(node, rapid_ast.Operator1AST):
            self.check_constant_expression(node.par1, ctx, what)
        elif isinstance(node, rapid_ast.Operator2AST):
            self.check_constant_expression(node.par1, ctx, what)
            self.check_constant_expression(node.par2, ctx, what)

    def check_literal_expression(self, node: Any) -> None:
        """3.3 "It may only contain either a single literal value (+ or - may precede a
        numerical literal) or a single aggregate with members that in turn are literal
        expressions." """
        node = unwrap(node)
        if node is None or isinstance(node, rapid_ast.LiteralATS):
            return
        if isinstance(node, rapid_ast.Operator1AST) and node.operator in ("+", "-"):
            operand = unwrap(node.par1)
            if isinstance(operand, rapid_ast.LiteralATS) and isinstance(
                operand.value, (int, float)
            ):
                if not isinstance(operand.value, bool):
                    return
        if isinstance(node, rapid_ast.AggregateAST):
            for member in node.expr:
                self.check_literal_expression(member)
            return
        self.report(
            node,
            "not-literal",
            "the initial value of a persistent must be a literal expression",
        )

    def const_value(self, node: Any, ctx: RoutineContext) -> Any:
        """value of a constant numeric expression, None when it cannot be computed"""
        node = unwrap(node)
        try:
            if isinstance(node, rapid_ast.LiteralATS):
                return node.value
            if isinstance(node, rapid_ast.Operator1AST):
                value = self.const_value(node.par1, ctx)
                if not isinstance(value, (int, float)) or isinstance(value, bool):
                    return None
                return -value if node.operator == "-" else value if node.operator == "+" else None
            if isinstance(node, rapid_ast.Operator2AST):
                left = self.const_value(node.par1, ctx)
                right = self.const_value(node.par2, ctx)
                numbers = (int, float)
                if not (isinstance(left, numbers) and isinstance(right, numbers)):
                    return None
                if isinstance(left, bool) or isinstance(right, bool):
                    return None
                operations: dict[str, Any] = {
                    "+": lambda a, b: a + b,
                    "-": lambda a, b: a - b,
                    "*": lambda a, b: a * b,
                    "/": lambda a, b: a / b,
                    "DIV": lambda a, b: int(a / b),
                    "MOD": lambda a, b: a - b * int(a / b),
                }
                operation = operations.get(node.operator)
                return None if operation is None else operation(left, right)
            if isinstance(node, rapid_ast.VariableAST):
                if node.index or node.component is not None:
                    return None
                name = identifier_name(node.var)
                obj = self.lookup(name, ctx) if name else None
                if not isinstance(obj, DataObject) or obj.kind != "CONST" or obj.node is None:
                    return None
                if id(obj) in self.evaluating:
                    return None
                assert obj.module is not None
                self.evaluating.add(id(obj))
                try:
                    return self.const_value(
                        obj.node.variable_instance.value, RoutineContext(obj.module)
                    )
                finally:
                    self.evaluating.discard(id(obj))
        except (ZeroDivisionError, OverflowError, TypeError):
            return None
        return None

    # ------------------------------------------------------------- routines

    def resolve_routine_signature(self, routine: RoutineInfo) -> None:
        assert routine.module is not None
        ctx = RoutineContext(routine.module)
        decl = routine.node
        if routine.kind == "FUNC":
            info = self.resolve_type_name(decl.data_type, ctx)
            if info is not None:
                routine.return_type = DataType(info)
        if routine.kind == "TRAP":
            return
        group = 0
        for item in decl.parameter_list:
            if item is None:
                continue  # <PAR>
            if isinstance(item, rapid_ast.OptionalParameterDefinitionAST):
                group += 1
                alternatives = [item.parameter] + list(item.switchs)
                for alternative in alternatives:
                    param = self.parameter(alternative, ctx, routine)
                    if param is not None:
                        param.optional = True
                        param.group = group if len(alternatives) > 1 else None
                        routine.params.append(param)
            else:
                param = self.parameter(item, ctx, routine)
                if param is not None:
                    if param.switch:
                        # 5.2 "The special type switch may (only) be assigned to optional
                        # parameters"
                        self.report(
                            item,
                            "switch-not-optional",
                            "switch parameter %s must be optional (\\switch %s)"
                            % (param.name, param.name),
                        )
                    routine.params.append(param)

    def parameter(
        self, item: Any, ctx: RoutineContext, routine: RoutineInfo
    ) -> Optional[DataObject]:
        if isinstance(item, rapid_ast.SwitchParameterDefinitionAST):
            name = identifier_name(item.name)
            if name is None:
                return None
            return DataObject(name, "PARAM", None, routine.module, routine, node=item, switch=True)
        if not isinstance(item, rapid_ast.ParameterDefinitionAST):
            return None
        name = identifier_name(item.name)
        if name is None:
            return None
        mode = {"NORMAL": "IN", "VAR": "VAR", "PERS": "PERS", "INOUT": "INOUT"}.get(
            item.parameter_type, "IN"
        )
        info = self.resolve_type_name(item.type, ctx)
        dims: tuple[Optional[int], ...] = (None,) * (item.size or 0)
        return DataObject(
            name,
            "PARAM",
            DataType(info, dims) if info is not None else None,
            routine.module,
            routine,
            node=item,
            mode=mode,
        )

    def check_routine(self, routine: RoutineInfo) -> None:
        assert routine.module is not None
        decl = routine.node
        scope: dict[str, Entry] = {}
        ctx = RoutineContext(routine.module, routine, [scope])

        # 2.20 "Two routine data objects declared in the same routine may not have the same
        # name." (parameters are routine data objects)
        for param in routine.params:
            self.check_identifier(param.name, param.node)
            self.add_routine_object(scope, param, routine)
            # 2.16 non-value types only as var (or ref) parameters
            if (
                not param.switch
                and param.mode != "VAR"
                and self.value_class(param.type) == "nonvalue"
            ):
                self.report(
                    param.node,
                    "value-class",
                    "parameter %s of non-value type %s must be a VAR parameter"
                    % (param.name, param.type),
                )
        if routine.kind == "FUNC" and self.value_class(routine.return_type) == "nonvalue":
            # 5.5 "Functions can have (return) any value data type"
            self.report(
                decl.data_type,
                "value-class",
                "function %s cannot return the non-value type %s"
                % (routine.name, routine.return_type),
            )

        local_data: list[DataObject] = []
        for item in decl.data_definitions:
            obj = self.data_object(item, routine.module, routine)
            if obj is None:
                continue
            self.resolve_data_type(obj, ctx)
            self.add_routine_object(scope, obj, routine)
            local_data.append(obj)
        for obj in local_data:
            self.check_data_declaration(obj, ctx)

        handlers = [("body", decl.statement_list)]
        for name in ("routine_backward", "routine_error", "routine_undo"):
            handler = getattr(decl, name, None)
            if handler is not None:
                handlers.append((name[len("routine_") :], handler.statement_list))
        for index, (_, statement_list) in enumerate(handlers):
            self.collect_labels(statement_list, ctx, (index,))

        for index, (name, statement_list) in enumerate(handlers):
            ctx.handler = name
            self.check_statement_list(statement_list, ctx, (index,))

        if routine.kind != "TRAP" and decl.routine_error is not None:
            self.check_error_number_list(decl.routine_error, ctx)

        # 5.5 "The evaluation of a function must be terminated by a return statement"
        if routine.kind == "FUNC" and not ctx.has_return_value:
            self.report(
                decl.function_name,
                "missing-return",
                "function %s has no RETURN statement with a value" % (routine.name,),
                WARNING,
            )

    def add_routine_object(
        self, scope: dict[str, Entry], obj: DataObject, routine: RoutineInfo
    ) -> None:
        key = obj.name.lower()
        if key in scope:
            previous = scope[key]
            self.report(
                obj.node,
                "duplicate-name",
                "'%s' is already declared in routine %s as %s"
                % (obj.name, routine.name, describe(previous)),
            )
            return
        scope[key] = obj

    def check_error_number_list(self, handler: Any, ctx: RoutineContext) -> None:
        # 7.2 "<error number> ::= <num literal> | <entire constant> | <entire variable> |
        # <entire persistent>"
        for item in handler.error_number_list:
            if isinstance(item, rapid_ast.LiteralATS):
                self.check_error_number_value(item, item.value)
            elif isinstance(item, rapid_ast.IdentifierAST) and item.name is not None:
                entry = self.lookup(item.name, ctx)
                if entry is None:
                    self.report(
                        item, "undefined-name", "undefined error number '%s'" % (item.name,)
                    )
                elif not isinstance(entry, DataObject) or entry.kind not in (
                    "CONST",
                    "VAR",
                    "PERS",
                ):
                    self.report(
                        item,
                        "type-mismatch",
                        "error number '%s' must be a constant, variable or persistent"
                        % (item.name,),
                    )

    def check_error_number_value(self, node: Any, value: Any) -> None:
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            self.report(node, "error-number", "error number must be a num value")
        elif value != int(value) or not MIN_ERROR_NUMBER <= value <= MAX_ERROR_NUMBER:
            self.report(
                node,
                "error-number",
                "error number %s is out of the range %d..%d"
                % (value, MIN_ERROR_NUMBER, MAX_ERROR_NUMBER),
            )

    # ------------------------------------------------------------- labels

    def nested_lists(self, statement: Any) -> list[Any]:
        if isinstance(statement, rapid_ast.IfStatement):
            lists = [statement.statement_list]
            for elseif in statement.elseif_list:
                if elseif is not None and elseif.statement_list is not None:
                    lists.append(elseif.statement_list)
            lists.append(statement.else_statement_list)
            return lists
        if isinstance(statement, (rapid_ast.ForStatement, rapid_ast.WhileStatement)):
            return [statement.statement_list]
        if isinstance(statement, rapid_ast.TestStatement):
            return [c.statement_list for c in statement.cases if c is not None] + [
                statement.default
            ]
        return []

    def collect_labels(
        self, statement_list: Any, ctx: RoutineContext, path: tuple[int, ...]
    ) -> None:
        # 4.4 "Two labels declared in the same routine may not have the same name. A label may
        # not have the same name as a routine data object declared in the same routine."
        for statement in statements(statement_list):
            if isinstance(statement, rapid_ast.LabelAST):
                name = identifier_name(statement.name)
                if name is None:
                    continue
                self.check_identifier(name, statement.name)
                key = name.lower()
                if key in ctx.labels:
                    self.report(
                        statement.name, "duplicate-label", "label %s already declared" % (name,)
                    )
                    continue
                if key in ctx.scopes[0]:
                    self.report(
                        statement.name,
                        "label-name-clash",
                        "label %s has the same name as a routine data object" % (name,),
                    )
                ctx.labels[key] = (statement, path)
            for index, nested in enumerate(self.nested_lists(statement)):
                self.collect_labels(nested, ctx, path + (id(statement), index))

    # ------------------------------------------------------------- statements

    def check_statement_list(
        self, statement_list: Any, ctx: RoutineContext, path: tuple[int, ...]
    ) -> None:
        for statement in statements(statement_list):
            self.check_statement(statement, ctx, path)

    def check_statement(self, s: Any, ctx: RoutineContext, path: tuple[int, ...]) -> None:
        if isinstance(s, rapid_ast.AssignmentStatementAST):
            self.check_assignment(s, ctx)
        elif isinstance(s, rapid_ast.ProcedureCallAST):
            self.check_procedure_call(s, ctx)
        elif isinstance(s, rapid_ast.GotoStatementAST):
            self.check_goto(s, ctx, path)
        elif isinstance(s, rapid_ast.ReturnStatementAST):
            self.check_return(s, ctx)
        elif isinstance(s, rapid_ast.RaiseStatementAST):
            self.check_raise(s, ctx)
        elif isinstance(s, (rapid_ast.RetryStatementAST, rapid_ast.TrynextStatementAST)):
            # 4.11, 4.12 "can only appear in the error handler of a routine"
            if ctx.handler != "error":
                keyword = "RETRY" if isinstance(s, rapid_ast.RetryStatementAST) else "TRYNEXT"
                self.report(
                    s,
                    "outside-error-handler",
                    "%s is allowed only in an error handler" % (keyword,),
                )
        elif isinstance(s, rapid_ast.ConnectStatementAST):
            self.check_connect(s, ctx)
        elif isinstance(s, rapid_ast.IfStatement):
            self.check_condition(s.condition, ctx, "IF")
            lists = self.nested_lists(s)
            for elseif in s.elseif_list:
                if elseif is not None and elseif.condition is not None:
                    self.check_condition(elseif.condition, ctx, "ELSEIF")
            for index, nested in enumerate(lists):
                self.check_statement_list(nested, ctx, path + (id(s), index))
        elif isinstance(s, rapid_ast.WhileStatement):
            self.check_condition(s.condition, ctx, "WHILE")
            self.check_statement_list(s.statement_list, ctx, path + (id(s), 0))
        elif isinstance(s, rapid_ast.ForStatement):
            self.check_for(s, ctx, path)
        elif isinstance(s, rapid_ast.TestStatement):
            self.check_test(s, ctx, path)

    def check_condition(self, node: Any, ctx: RoutineContext, keyword: str) -> None:
        # 3.4 "A conditional expression ... The resulting type must be bool"
        t = self.type_of(node, ctx)
        if t is not None and (t.dims or t.base.name.lower() != "bool") and self.known(t):
            self.report(
                node, "condition-type", "%s condition must be bool, found %s" % (keyword, t)
            )

    def check_assignment(self, s: Any, ctx: RoutineContext) -> None:
        # 4.5 "The assignment target and the expression must have equal types. Note that the
        # assignment target must have value or semi-value data type"
        if s.dest is None or (isinstance(s.dest, rapid_ast.VariableAST) and s.dest.var is None):
            return  # <VAR>
        target_type = self.type_of(s.dest, ctx)
        obj = self.reference_object(s.dest, ctx, quiet=True)
        if isinstance(obj, DataObject):
            if obj.kind == "CONST":
                self.report(
                    s.dest, "assign-constant", "cannot assign to the constant %s" % (obj.name,)
                )
            elif obj.readonly:
                self.report(
                    s.dest,
                    "assign-readonly",
                    "cannot assign to the readonly %s %s" % (describe(obj), obj.name),
                )
            elif obj.switch:
                self.report(
                    s.dest,
                    "assign-switch",
                    "cannot assign to the switch parameter %s" % (obj.name,),
                )
        if target_type is not None and self.value_class(target_type) == "nonvalue":
            self.report(
                s.dest,
                "value-class",
                "cannot assign to %s of non-value type %s" % (obj.name if obj else "", target_type),
            )
            return
        if target_type is not None:
            self.check_value(s.source, target_type, ctx, "assignment")
        else:
            self.type_of(s.source, ctx)

    def check_goto(self, s: Any, ctx: RoutineContext, path: tuple[int, ...]) -> None:
        # 4.7 "A goto statement may not transfer control into a statement list."
        name = identifier_name(s.dest)
        if name is None:
            return
        label = ctx.labels.get(name.lower())
        if label is None:
            self.report(s.dest, "undefined-label", "undefined label %s" % (name,))
            return
        label_path = label[1]
        if path[: len(label_path)] != label_path:
            self.report(
                s.dest,
                "goto-into-list",
                "GOTO %s transfers control into another statement list" % (name,),
            )

    def check_return(self, s: Any, ctx: RoutineContext) -> None:
        # 4.8 "The expression type must be equal to the type of the function. Return
        # statements in procedures and traps must not include the return expression."
        routine = ctx.routine
        assert routine is not None
        if routine.kind == "FUNC":
            if s.result is None:
                self.report(
                    s, "return-value", "RETURN in function %s must have a value" % (routine.name,)
                )
            else:
                ctx.has_return_value = True
                if routine.return_type is not None:
                    self.check_value(s.result, routine.return_type, ctx, "return value")
                else:
                    self.type_of(s.result, ctx)
        elif s.result is not None:
            self.report(
                s,
                "return-value",
                "RETURN in %s %s cannot have a value" % (describe(routine), routine.name),
            )

    def check_raise(self, s: Any, ctx: RoutineContext) -> None:
        # 4.9 "A raise statement that includes an explicit error number ... must not appear in
        # the error handler of a routine. A raise statement with no error number may only
        # occur in the error handler of a routine"
        if s.error_number is None:
            if ctx.handler != "error":
                self.report(
                    s,
                    "outside-error-handler",
                    "RAISE without error number is allowed only in an error handler",
                )
            return
        if ctx.handler == "error":
            self.report(
                s,
                "raise-in-error-handler",
                "RAISE with an error number is not allowed in an error handler",
            )
        number = s.error_number
        if isinstance(number, rapid_ast.LiteralATS):
            self.check_error_number_value(number, number.value)
        elif isinstance(number, rapid_ast.IdentifierAST) and number.name is not None:
            entry = self.lookup(number.name, ctx)
            if entry is None:
                self.report(number, "undefined-name", "undefined data object '%s'" % (number.name,))
            elif not isinstance(entry, DataObject):
                self.report(
                    number,
                    "not-a-data-object",
                    "'%s' is a %s, not an error number" % (number.name, describe(entry)),
                )
            else:
                if (
                    entry.type is not None
                    and self.known(entry.type)
                    and (entry.type.dims or entry.type.base.name.lower() != "num")
                ):
                    self.report(
                        number,
                        "type-mismatch",
                        "error number %s must be num or errnum, found %s"
                        % (number.name, entry.type),
                    )
                if not entry.predefined:
                    value = self.const_value(rapid_ast.VariableAST(number, [], None), ctx)
                    if value is not None:
                        self.check_error_number_value(number, value)

    def check_connect(self, s: Any, ctx: RoutineContext) -> None:
        # 4.13 "The connect target must have num (or alias for num) type and must be (or
        # represent) a module variable (not a routine variable). If a parameter is used as
        # connect target it must be a VAR or INOUT/VAR parameter"
        target = s.connect_taget
        if isinstance(target, rapid_ast.VariableAST) and target.var is not None:
            t = self.type_of(target, ctx)
            obj = self.reference_object(target, ctx, quiet=True)
            if isinstance(obj, DataObject):
                if obj.kind == "PARAM":
                    valid = obj.mode in ("VAR", "INOUT")
                else:
                    valid = obj.kind == "VAR" and obj.routine is None and not obj.readonly
                if not valid:
                    self.report(
                        target,
                        "connect-target",
                        "CONNECT target must be a module variable or a VAR parameter, %s %s is not"
                        % (describe(obj), obj.name),
                    )
            if t is not None and (t.dims or t.base.name.lower() != "num"):
                self.report(
                    target,
                    "connect-target",
                    "CONNECT target must be num or intnum, found %s" % (t,),
                )
        name = identifier_name(s.trap)
        if name is not None:
            entry = self.lookup(name, ctx)
            if entry is None:
                self.report(s.trap, "undefined-routine", "undefined trap routine %s" % (name,))
            elif not isinstance(entry, RoutineInfo) or entry.kind != "TRAP":
                self.report(
                    s.trap,
                    "connect-trap",
                    "%s is a %s, not a trap routine" % (name, describe(entry)),
                )

    def check_for(self, s: Any, ctx: RoutineContext, path: tuple[int, ...]) -> None:
        # 4.16 "The loop variable is declared (with type num) by its appearance, has the scope
        # of the statement list, hides any other object with the same name, is readonly.
        # The from, to and step expressions must all have num (numeric) type."
        for keyword, expr in (("FROM", s.ifrom), ("TO", s.ito), ("STEP", s.istep)):
            if expr is None:
                continue
            t = self.type_of(expr, ctx)
            if (
                t is not None
                and self.known(t)
                and (t.dims or t.base.name.lower() not in NUMERIC_TYPES)
            ):
                self.report(
                    expr, "for-type", "FOR %s expression must be num, found %s" % (keyword, t)
                )
        name = identifier_name(s.loop_variable)
        scope: dict[str, Entry] = {}
        if name is not None:
            self.check_identifier(name, s.loop_variable)
            scope[name.lower()] = DataObject(
                name,
                "LOOP",
                self.builtins.type("num"),
                ctx.module,
                ctx.routine,
                node=s.loop_variable,
                readonly=True,
            )
        ctx.scopes.append(scope)
        try:
            self.check_statement_list(s.statement_list, ctx, path + (id(s), 0))
        finally:
            ctx.scopes.pop()

    def check_test(self, s: Any, ctx: RoutineContext, path: tuple[int, ...]) -> None:
        # 4.18 "The test expression can have any value or semi-value data type. The type of a
        # test value must be equal to the type of the test expression."
        t = self.type_of(s.expression, ctx)
        if t is not None and self.value_class(t) == "nonvalue":
            self.report(s.expression, "value-class", "TEST expression of non-value type %s" % (t,))
            t = None
        lists = self.nested_lists(s)
        for case in s.cases:
            if case is None or case.test_value is None:
                continue
            for value in case.test_value:
                if t is not None:
                    self.check_value(value, t, ctx, "CASE value")
                else:
                    self.type_of(value, ctx)
        for index, nested in enumerate(lists):
            self.check_statement_list(nested, ctx, path + (id(s), index))

    # ------------------------------------------------------------- routine calls

    def check_procedure_call(self, s: Any, ctx: RoutineContext) -> None:
        # 4.6 Procedure call
        if not isinstance(s.procedure, rapid_ast.IdentifierAST):
            # late binding: "% <expression> %", a string expression
            t = self.type_of(s.procedure, ctx)
            if t is not None and self.known(t) and (t.dims or t.base.name.lower() != "string"):
                self.report(
                    s.procedure,
                    "type-mismatch",
                    "late binding procedure name must be a string, found %s" % (t,),
                )
            for arg in s.arguments:
                if arg is not None and arg.argumentvalue is not None:
                    self.type_of(arg.argumentvalue, ctx)
            return
        name = s.procedure.name
        if name is None:
            return
        entry = self.lookup(name, ctx)
        if entry is None:
            self.report(s.procedure, "undefined-routine", "undefined procedure %s" % (name,))
            for arg in s.arguments:
                if arg is not None and arg.argumentvalue is not None:
                    self.type_of(arg.argumentvalue, ctx)
            return
        if not isinstance(entry, RoutineInfo) or entry.kind != "PROC":
            if isinstance(entry, RoutineInfo) and entry.kind == "TRAP":
                # 5.1 "A trap routine can never be explicitly called from RAPID code."
                self.report(
                    s.procedure, "trap-call", "the trap routine %s cannot be called" % (name,)
                )
            else:
                self.report(
                    s.procedure,
                    "not-a-procedure",
                    "%s is a %s, not a procedure" % (name, describe(entry)),
                )
            return
        self.check_arguments(s, entry, s.arguments, ctx)

    def check_arguments(
        self, call: Any, routine: RoutineInfo, args: list[Any], ctx: RoutineContext
    ) -> None:
        """3.11, 4.6, 5.2: arguments and parameters"""
        if any(a is None or a.type is None for a in args):
            return  # <ARG> placeholder
        if routine.special == "Present":
            self.check_present(call, args, ctx)
            return
        params = routine.params
        supplied: set[int] = set()
        groups: dict[int, str] = {}
        position = 0
        for arg in args:
            argname = identifier_name(arg.argumentname)
            if arg.type == "Required":
                # "A required argument is separated from a proceeding (if any) argument by ","
                # The parameter name may be included, or left out."
                index = position
                while index < len(params) and params[index].optional:
                    index += 1
                if index >= len(params):
                    self.report(
                        arg,
                        "argument-count",
                        "too many arguments for %s %s" % (describe(routine), routine.name),
                    )
                    if arg.argumentvalue is not None:
                        self.type_of(arg.argumentvalue, ctx)
                    continue
                param = params[index]
                if argname is not None and argname.lower() != param.name.lower():
                    self.report(
                        arg.argumentname,
                        "argument-name",
                        "argument %s does not match the parameter %s of %s"
                        % (argname, param.name, routine.name),
                    )
                supplied.add(index)
                position = index + 1
                self.check_argument_value(arg.argumentvalue, param, routine, ctx)
                continue
            # optional or conditional argument: "\name"
            if argname is None:
                continue
            index = next((i for i, p in enumerate(params) if p.name.lower() == argname.lower()), -1)
            if index < 0:
                self.report(
                    arg.argumentname,
                    "unknown-argument",
                    "%s %s has no parameter %s" % (describe(routine), routine.name, argname),
                )
                continue
            param = params[index]
            if not param.optional:
                self.report(
                    arg.argumentname,
                    "argument-name",
                    "parameter %s of %s is required, it is not written as \\%s"
                    % (param.name, routine.name, argname),
                )
                continue
            # "Optional arguments may be omitted but the order of the (present) arguments must
            # be the same as the order of the parameters."
            if index < position or index in supplied:
                self.report(
                    arg.argumentname,
                    "argument-order",
                    "argument \\%s is out of the parameter order of %s" % (argname, routine.name),
                )
            supplied.add(index)
            position = max(position, index + 1)
            if arg.type == "Conditional":
                # "Note that the specified parameter must be optional."
                obj = self.reference_object(arg.argumentvalue, ctx, quiet=False)
                if not (
                    isinstance(obj, DataObject)
                    and obj.kind == "PARAM"
                    and obj.optional
                    and obj.routine is ctx.routine
                ):
                    self.report(
                        arg,
                        "conditional-argument",
                        "conditional argument \\%s ? must refer to an optional parameter of %s"
                        % (argname, ctx.routine.name if ctx.routine else "the routine"),
                    )
                elif not param.switch and obj.type is not None and param.type is not None:
                    if not self.equal_types(param.type, obj.type):
                        self.report(
                            arg,
                            "type-mismatch",
                            "argument \\%s: expected %s, found %s"
                            % (argname, param.type, obj.type),
                        )
                continue
            # "Two or more parameters may be declared to mutually exclude each other, in which
            # case at most one of them may be present in the argument list."
            if param.group is not None:
                if param.group in groups:
                    self.report(
                        arg.argumentname,
                        "exclusive-arguments",
                        "arguments \\%s and \\%s exclude each other"
                        % (groups[param.group], argname),
                    )
                groups[param.group] = argname
            if param.switch:
                # "Switch arguments do therefore not include any argument expression."
                if arg.argumentvalue is not None:
                    self.report(
                        arg, "switch-value", "switch argument \\%s cannot have a value" % (argname,)
                    )
            elif arg.argumentvalue is None:
                self.report(
                    arg,
                    "missing-argument-value",
                    "argument \\%s needs a value (\\%s := ...)" % (argname, argname),
                )
            else:
                self.check_argument_value(arg.argumentvalue, param, routine, ctx)
        for index, param in enumerate(params):
            if not param.optional and index not in supplied:
                self.report(
                    call,
                    "missing-argument",
                    "missing argument for the required parameter %s of %s"
                    % (param.name, routine.name),
                )

    def check_present(self, call: Any, args: list[Any], ctx: RoutineContext) -> None:
        # 5.2 "The predefined function Present can be used to test the presence of an
        # optional parameter."
        if len(args) != 1 or args[0].type != "Required":
            self.report(
                call, "present-argument", "Present needs one optional parameter as argument"
            )
            return
        obj = self.reference_object(args[0].argumentvalue, ctx, quiet=False)
        if obj is None:
            return
        if not (
            isinstance(obj, DataObject)
            and obj.kind == "PARAM"
            and obj.optional
            and obj.routine is ctx.routine
        ):
            self.report(
                args[0],
                "present-argument",
                "Present argument must be an optional parameter of %s"
                % (ctx.routine.name if ctx.routine else "the routine",),
            )

    def check_argument_value(
        self, value: Any, param: DataObject, routine: RoutineInfo, ctx: RoutineContext
    ) -> None:
        if value is None:
            return
        what = "argument %s of %s" % (param.name, routine.name)
        if param.type is not None:
            self.check_value(value, param.type, ctx, what)
        else:
            self.type_of(value, ctx)
        # 5.2 Access modes: arguments legal for each access mode
        if param.mode == "IN":
            return
        obj = self.reference_object(value, ctx, quiet=True)
        if not isinstance(obj, DataObject):
            self.report(
                value,
                "argument-mode",
                "%s (%s parameter) must be a data object, not an expression" % (what, param.mode),
            )
            return
        allowed = True
        if obj.kind == "CONST" or obj.readonly:
            allowed = param.mode == "REF"
        elif param.mode == "VAR":
            if obj.kind == "PERS":
                allowed = False
            elif obj.kind == "PARAM":
                allowed = obj.mode != "PERS"
        elif param.mode == "PERS":
            if obj.kind in ("VAR", "LOOP"):
                allowed = False
            elif obj.kind == "PARAM":
                allowed = obj.mode in ("PERS", "INOUT")
        if not allowed:
            self.report(
                value,
                "argument-mode",
                "%s (%s parameter) cannot be the %s %s"
                % (what, param.mode, describe(obj), obj.name),
            )

    # ------------------------------------------------------------- expressions

    def known(self, t: DataType) -> bool:
        """type with known structure (unknown installed types are not checked)"""
        return t.base.kind in ("atomic", "record")

    def equal_types(self, expected: DataType, found: DataType) -> bool:
        """2.17 Equal type"""
        if expected.base.kind == "anytype" or found.base.kind == "anytype":
            return True
        if len(expected.dims) != len(found.dims):
            return False
        for a, b in zip(expected.dims, found.dims):
            if a is not None and b is not None and a != b:
                return False
        e, f = expected.base, found.base
        if e is f:
            return True
        names = {e.name.lower(), f.name.lower()}
        # num literals are used for dnum values
        if names <= set(NUMERIC_TYPES):
            return True
        if e.kind == "installed" and f.kind == "installed":
            return e.name.lower() == f.name.lower()
        return False

    def check_value(self, node: Any, expected: DataType, ctx: RoutineContext, what: str) -> None:
        found = self.type_of(node, ctx, expected)
        if found is None:
            return
        if not self.equal_types(expected, found):
            self.report(
                node, "type-mismatch", "%s: expected %s, found %s" % (what, expected, found)
            )

    def reference_object(self, node: Any, ctx: RoutineContext, quiet: bool) -> Optional[Entry]:
        """the entire data object referenced by a variable expression (a, a{i}, a.b)"""
        node = unwrap(node)
        while isinstance(node, rapid_ast.VariableAST) and isinstance(
            node.var, rapid_ast.VariableAST
        ):
            node = node.var
        if not isinstance(node, rapid_ast.VariableAST):
            return None
        name = identifier_name(node.var)
        if name is None:
            return None
        entry = self.lookup(name, ctx)
        if entry is None and not quiet:
            self.report(node.var, "undefined-name", "undefined data object '%s'" % (name,))
        return entry

    def type_of(
        self, node: Any, ctx: RoutineContext, expected: Optional[DataType] = None
    ) -> Optional[DataType]:
        """type of an expression, None when it cannot be determined (an error is already
        reported or the type is not known)"""
        node = unwrap(node)
        if node is None:
            return None  # <EXP>
        if isinstance(node, rapid_ast.LiteralATS):
            value = node.value
            if isinstance(value, bool):
                return self.builtins.type("bool")
            if isinstance(value, str):
                # 2.13 "A string may consist of 0 to 80 characters"
                if string_length(value) > MAX_STRING_LENGTH:
                    self.report(
                        node,
                        "string-too-long",
                        "string literal of %d characters, the maximum is %d"
                        % (string_length(value), MAX_STRING_LENGTH),
                    )
                return self.builtins.type("string")
            if expected is not None and expected.base.name.lower() == "dnum" and not expected.dims:
                return expected
            return self.builtins.type("num")
        if isinstance(node, rapid_ast.AggregateAST):
            return self.aggregate_type(node, ctx, expected)
        if isinstance(node, rapid_ast.VariableAST):
            return self.variable_type(node, ctx)
        if isinstance(node, rapid_ast.FunctionCallAST):
            return self.function_call_type(node, ctx)
        if isinstance(node, rapid_ast.Operator1AST):
            return self.unary_type(node, ctx, expected)
        if isinstance(node, rapid_ast.Operator2AST):
            return self.binary_type(node, ctx)
        return None

    def aggregate_type(
        self, node: Any, ctx: RoutineContext, expected: Optional[DataType]
    ) -> Optional[DataType]:
        # 3.10 "The data type of an aggregate is (must be able to be) determined by the
        # context. The data type of each aggregate member must be equal to the type of the
        # corresponding member of the determined type."
        if expected is None:
            self.report(
                node,
                "aggregate-type",
                "the data type of the aggregate cannot be determined by the context",
            )
            for member in node.expr:
                if not isinstance(unwrap(member), rapid_ast.AggregateAST):
                    self.type_of(member, ctx)
            return None
        if expected.dims:
            size = expected.dims[0]
            if size is not None and len(node.expr) != size:
                self.report(
                    node,
                    "aggregate-size",
                    "the aggregate has %d members, the array %s has %d elements"
                    % (len(node.expr), expected, size),
                )
            for member in node.expr:
                self.check_value(member, expected.element, ctx, "array element")
            return expected
        info = expected.base
        if info.kind == "record":
            if len(node.expr) != len(info.components):
                self.report(
                    node,
                    "aggregate-size",
                    "the aggregate has %d members, the record %s has %d components"
                    % (len(node.expr), expected, len(info.components)),
                )
            for member, (cname, ctype) in zip(node.expr, info.components):
                if ctype is not None:
                    self.check_value(member, ctype, ctx, "component %s of %s" % (cname, expected))
                else:
                    self.type_of(member, ctx)
            return expected
        if info.kind == "atomic":
            self.report(
                node, "aggregate-type", "an aggregate is not a value of type %s" % (expected,)
            )
            return None
        return None

    def variable_type(self, node: Any, ctx: RoutineContext) -> Optional[DataType]:
        # 3.6 Variables: entire variable, variable element, variable component
        if node.var is None:
            return None  # <VAR>
        if isinstance(node.var, rapid_ast.VariableAST):
            t = self.variable_type(node.var, ctx)
        else:
            name = identifier_name(node.var)
            if name is None:
                # 3.6 "The placeholder <ID> cannot be used to represent an entire variable."
                self.report(
                    node.var, "placeholder", "the placeholder <ID> cannot be used as a variable"
                )
                return None
            entry = self.lookup(name, ctx)
            if entry is None:
                self.report(node.var, "undefined-name", "undefined data object '%s'" % (name,))
                t = None
            elif not isinstance(entry, DataObject):
                self.report(
                    node.var,
                    "not-a-data-object",
                    "'%s' is a %s, not a data object" % (name, describe(entry)),
                )
                t = None
            elif entry.switch:
                # 5.2 "The domain of the switch type is empty and no value can be transferred
                # to a switch parameter."
                t = None
            else:
                t = entry.type
        for index in node.index:
            index_type = self.type_of(index, ctx)
            if (
                index_type is not None
                and self.known(index_type)
                and (index_type.dims or index_type.base.name.lower() not in NUMERIC_TYPES)
            ):
                self.report(
                    index, "index-type", "array index must be num, found %s" % (index_type,)
                )
        if node.index and t is not None:
            # 3.6 "The number of elements in the index list must fit the declared degree"
            if not t.dims:
                self.report(node, "not-an-array", "%s is not an array" % (t,))
                return None
            if len(node.index) != len(t.dims):
                self.report(
                    node,
                    "index-count",
                    "%d indexes for an array of degree %d" % (len(node.index), len(t.dims)),
                )
                return None
            # "An index value may not violate the declared dimension."
            for index, size in zip(node.index, t.dims):
                value = self.const_value(index, ctx)
                if (
                    isinstance(value, (int, float))
                    and not isinstance(value, bool)
                    and size is not None
                ):
                    if value < 1 or value > size:
                        self.report(
                            index,
                            "index-out-of-bounds",
                            "index %s is out of the dimension %d" % (value, size),
                        )
            t = DataType(t.info)
        if node.component is not None and t is not None:
            cname = identifier_name(node.component)
            if cname is None:
                # 3.6 "The placeholder <ID> cannot be used to represent a component name."
                self.report(
                    node.component,
                    "placeholder",
                    "the placeholder <ID> cannot be used as a component name",
                )
                return None
            if t.dims or t.base.kind != "record":
                if self.known(t) or t.dims:
                    self.report(
                        node.component,
                        "not-a-record",
                        "%s has no components, %s is not a record" % (cname, t),
                    )
                return None
            for comp_name, comp_type in t.base.components:
                if comp_name.lower() == cname.lower():
                    return comp_type
            self.report(
                node.component, "unknown-component", "record %s has no component %s" % (t, cname)
            )
            return None
        return t

    def function_call_type(self, node: Any, ctx: RoutineContext) -> Optional[DataType]:
        # 3.11 Function calls
        if not isinstance(node.function, rapid_ast.IdentifierAST):
            # 4.6 "late binding is available for procedure calls only, not for function calls"
            self.report(
                node, "late-binding-function", "late binding is not allowed for function calls"
            )
            return None
        name = node.function.name
        if name is None:
            return None
        entry = self.lookup(name, ctx)
        if entry is None:
            self.report(node.function, "undefined-routine", "undefined function %s" % (name,))
            for arg in node.arguments:
                if arg is not None and arg.argumentvalue is not None:
                    self.type_of(arg.argumentvalue, ctx)
            return None
        if not isinstance(entry, RoutineInfo) or entry.kind != "FUNC":
            self.report(
                node.function,
                "not-a-function",
                "%s is a %s, not a function" % (name, describe(entry)),
            )
            return None
        self.check_arguments(node, entry, node.arguments, ctx)
        return entry.return_type

    def unary_type(
        self, node: Any, ctx: RoutineContext, expected: Optional[DataType]
    ) -> Optional[DataType]:
        # 3.12 unary + - (num, dnum, pos), NOT (bool)
        t = self.type_of(node.par1, ctx, expected if node.operator != "NOT" else None)
        if t is None or not self.known(t):
            return None
        name = t.base.name.lower()
        if node.operator == "NOT":
            if t.dims or name != "bool":
                self.report(node, "operator-type", "NOT is not defined for %s" % (t,))
                return None
            return t
        if t.dims or name not in ("num", "dnum", "pos"):
            self.report(
                node, "operator-type", "unary %s is not defined for %s" % (node.operator, t)
            )
            return None
        # "If the operand has an alias data type, the result receives the alias base type"
        return DataType(t.base)

    def binary_type(self, node: Any, ctx: RoutineContext) -> Optional[DataType]:
        op = node.operator
        left_aggregate = isinstance(unwrap(node.par1), rapid_ast.AggregateAST)
        right_aggregate = isinstance(unwrap(node.par2), rapid_ast.AggregateAST)
        if left_aggregate and right_aggregate:
            self.report(
                node,
                "aggregate-type",
                "the data type of the aggregates cannot be determined by the context",
            )
            return None
        if left_aggregate:
            right = self.type_of(node.par2, ctx)
            left = self.type_of(node.par1, ctx, right) if right is not None else None
        else:
            left = self.type_of(node.par1, ctx)
            right = self.type_of(node.par2, ctx, left if right_aggregate else None)
        if left is None or right is None:
            return None
        if not (self.known(left) and self.known(right)):
            return None
        result = self.operator_result(op, left, right)
        if result is None:
            self.report(
                node,
                "operator-type",
                "operator %s is not defined for %s and %s" % (op, left, right),
            )
        return result

    def operator_result(self, op: str, left: DataType, right: DataType) -> Optional[DataType]:
        """3.12 Operators: legal operand types and result type"""
        boolean = self.builtins.type("bool")
        if op in EQUALITY_OPERATORS:
            # "Only value data types. Operands must have equal types." (arrays allowed)
            if self.equal_types(left, right) and self.value_class(left) != "nonvalue":
                return boolean
            return None
        if left.dims or right.dims:
            return None
        lname, rname = left.base.name.lower(), right.base.name.lower()
        numeric = lname in NUMERIC_TYPES and rname in NUMERIC_TYPES
        numeric_result = self.builtins.type("dnum" if "dnum" in (lname, rname) else "num")
        if op in LOGICAL_OPERATORS:
            return boolean if lname == rname == "bool" else None
        if op in RELATIONAL_OPERATORS:
            return boolean if numeric else None
        if op in ("DIV", "MOD"):
            return numeric_result if numeric else None
        if numeric:
            return numeric_result
        pos = DataType(left.base) if lname == "pos" else DataType(right.base)
        if op == "+":
            if lname == rname == "pos":
                return pos
            if lname == rname == "string":
                return DataType(left.base)
            return None
        if op == "-":
            return pos if lname == rname == "pos" else None
        if op == "*":
            if (lname, rname) in (("num", "pos"), ("pos", "num"), ("pos", "pos")):
                return pos
            if lname == rname == "orient":
                return DataType(left.base)
            return None
        if op == "/":
            return pos if (lname, rname) == ("pos", "num") else None
        return None


# ----------------------------------------------------------------- API


def validate(modules: Sequence[Any], quiet_files: Sequence[str] = ()) -> list[Diagnostic]:
    """validate the modules of a task (the parsed ModuleAST of all its files, standard
    modules included); the diagnostics of quiet_files are not returned"""
    quiet = {os.path.normpath(f) for f in quiet_files}
    diagnostics = Validator().validate(modules)
    return [d for d in diagnostics if os.path.normpath(d.file) not in quiet]


def standard_files() -> list[str]:
    base = os.path.dirname(os.path.abspath(__file__))
    return sorted(glob.glob(os.path.join(base, "default", "*.sys")))


def parse_files(paths: Sequence[str]) -> tuple[list[Any], list[Diagnostic]]:
    parser = rapid_parser.RAPIDParser(
        lex_optimize=True,
        yacc_debug=False,
        yacc_optimize=False,
        start_from="module_declaration_list",
    )
    modules: list[Any] = []
    errors: list[Diagnostic] = []
    for path in paths:
        with open(path, "r") as f:
            text = f.read()
        try:
            result = parser.parse(text, path, debuglevel=0)
        except ParseError as e:
            errors.append(Diagnostic(path, 0, ERROR, "syntax", str(e)))
            continue
        if result is not None:
            modules += result.module_list
    return modules, errors


def validate_files(
    paths: Sequence[str], standard: bool = True, check_standard: bool = False
) -> list[Diagnostic]:
    std = standard_files() if standard else []
    modules, errors = parse_files(list(std) + list(paths))
    if errors:
        return errors
    return validate(modules, () if check_standard else std)


def main(argv: Optional[Sequence[str]] = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description="static semantic checks of RAPID modules")
    parser.add_argument("files", nargs="+", metavar="FILE", help="RAPID modules of the task")
    parser.add_argument(
        "-s",
        "--nostandard",
        action="store_true",
        help="do not load the standard modules default/*.sys",
    )
    parser.add_argument(
        "--check-standard",
        action="store_true",
        help="report also the diagnostics of the standard modules",
    )
    args = parser.parse_args(argv)
    diagnostics = validate_files(args.files, not args.nostandard, args.check_standard)
    for d in diagnostics:
        print(d)
    errors = sum(1 for d in diagnostics if d.severity == ERROR)
    warnings = len(diagnostics) - errors
    if diagnostics:
        print("%d error(s), %d warning(s)" % (errors, warnings), file=sys.stderr)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
