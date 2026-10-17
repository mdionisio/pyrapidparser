MODULE forward
    ! executed by test_rapid2py.py: routines called before their declaration
    VAR num r := 0;
    PROC main()
        later 5;
        !python:print("later 5 ->", pyrapid.Symbols().GetSymbol("r").data.Get())
        r := twice(4);
        !python:print("twice(4) ->", pyrapid.Symbols().GetSymbol("r").data.Get())
    ENDPROC
    PROC later(num value)
        r := value + 1;
    ENDPROC
    FUNC num twice(num value)
        RETURN value * 2;
    ENDFUNC
ENDMODULE
