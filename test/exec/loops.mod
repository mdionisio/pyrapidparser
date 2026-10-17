MODULE loops
    ! executed by test_rapid2py.py: FOR statement (kernel manual 4.16)
    VAR num s := 0;
    VAR num i := 42;
    PROC main()
        s := 0;
        FOR i FROM 1 TO 5 DO
            s := s + i;
        ENDFOR
        !python:print("1..5", pyrapid.Symbols().GetSymbol("s").data.Get())
        s := 0;
        FOR k FROM 10 TO 1 STEP -3 DO
            s := s * 100 + k;
        ENDFOR
        !python:print("10..1 step -3", pyrapid.Symbols().GetSymbol("s").data.Get())
        s := 0;
        FOR k FROM 3 TO 1 DO
            s := s * 10 + k;
        ENDFOR
        !python:print("3..1", pyrapid.Symbols().GetSymbol("s").data.Get())
        ! the loop variable hides the module variable i
        !python:print("i", pyrapid.Symbols().GetSymbol("i").data.Get())
    ENDPROC
ENDMODULE
