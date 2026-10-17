MODULE strings
    ! executed by test_rapid2py.py: string literals of the kernel manual 2.7
    VAR string s;
    PROC main()
        s := "Contains a "" character";
        !python:print(repr(pyrapid.Symbols().GetSymbol("s").data.Get()))
        s := "Contains a \\ character";
        !python:print(repr(pyrapid.Symbols().GetSymbol("s").data.Get()))
        s := "x\41y\07";
        !python:print(repr(pyrapid.Symbols().GetSymbol("s").data.Get()))
    ENDPROC
ENDMODULE
