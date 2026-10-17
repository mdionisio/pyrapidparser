MODULE operators
    ! executed by test_rapid2py.py: each !python: line prints a result
    VAR num a := 10;
    VAR num b := 3;
    VAR num c := 2;
    VAR num r;
    VAR bool t := TRUE;
    VAR bool f := FALSE;
    VAR bool rb;
    PROC main()
        r := a - b - c;
        !python:print("a - b - c =", pyrapid.Symbols().GetSymbol("r").data.Get())
        r := a / b / c;
        !python:print("a / b / c =", round(pyrapid.Symbols().GetSymbol("r").data.Get(), 4))
        r := -a + b;
        !python:print("-a + b =", pyrapid.Symbols().GetSymbol("r").data.Get())
        r := a * (b + c);
        !python:print("a * (b + c) =", pyrapid.Symbols().GetSymbol("r").data.Get())
        rb := NOT f OR t;
        !python:print("NOT f OR t =", pyrapid.Symbols().GetSymbol("rb").data.Get())
        rb := NOT t AND f;
        !python:print("NOT t AND f =", pyrapid.Symbols().GetSymbol("rb").data.Get())
    ENDPROC
ENDMODULE
