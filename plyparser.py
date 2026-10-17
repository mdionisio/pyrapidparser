# -----------------------------------------------------------------
# plyparser.py
#
# PLYParser class and other utilites for simplifying programming
# parsers with PLY
#
# Copyright (C) 2008-2011, Eli Bendersky
# License: BSD
# -----------------------------------------------------------------
from typing import TYPE_CHECKING, Any, NoReturn, Optional

if TYPE_CHECKING:
    from rapid_lexer import RAPIDLexer


class Coord(object):
    """Coordinates of a syntactic element. Consists of:
    - File name
    - Line number
    - (optional) column number, for the Lexer
    """

    def __init__(self, file: str, line: int, column: Optional[int] = None) -> None:
        self.file = file
        self.line = line
        self.column = column

    def __str__(self) -> str:
        str = "%s:%s" % (self.file, self.line)
        if self.column:
            str += ":%s" % self.column
        return str


class ParseError(Exception):
    pass


class PLYParser(object):
    rapidlex: "RAPIDLexer"

    def _create_opt_rule(self, rulename: str) -> None:
        """Given a rule name, creates an optional ply.yacc rule
        for it. The name of the optional rule is
        <rulename>_opt
        """
        optname = rulename + "_opt"

        def optrule(self: Any, p: Any) -> None:
            p[0] = p[1]

        optrule.__doc__ = "%s : empty\n| %s" % (optname, rulename)
        optrule.__name__ = "p_%s" % optname
        setattr(self.__class__, optrule.__name__, optrule)

    def _coord(self, lineno: int, column: Optional[int] = None) -> Coord:
        return Coord(file=self.rapidlex.filename, line=lineno, column=column)

    def _parse_error(self, msg: str, coord: Any) -> NoReturn:
        raise ParseError("%s: %s" % (coord, msg))
