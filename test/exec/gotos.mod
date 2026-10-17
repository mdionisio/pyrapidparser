MODULE gotos
    ! executed by test_rapid2py.py: GOTO and labels (kernel manual 4.4, 4.7)
    VAR num i := 0;
    VAR num n := 0;
    VAR num r := 0;
    PROC main()
        ! backward jump: a loop made with GOTO
        i := 0;
        again:
        i := i + 1;
        IF i < 5 GOTO again;
        !python:print("loop", pyrapid.Symbols().GetSymbol("i").data.Get())
        ! forward jump
        GOTO skip;
        i := 100;
        skip:
        !python:print("skip", pyrapid.Symbols().GetSymbol("i").data.Get())
        ! out of nested WHILE and FOR
        n := 0;
        WHILE TRUE DO
            FOR k FROM 1 TO 10 DO
                n := n + 1;
                IF n = 7 THEN
                    GOTO out;
                ENDIF
            ENDFOR
        ENDWHILE
        out:
        !python:print("out", pyrapid.Symbols().GetSymbol("n").data.Get())
        ! label in a nested statement list
        IF TRUE THEN
            r := 0;
            inner:
            r := r + 1;
            IF r < 3 GOTO inner;
        ENDIF
        !python:print("inner", pyrapid.Symbols().GetSymbol("r").data.Get())
        handler;
        !python:print("handler", pyrapid.Symbols().GetSymbol("r").data.Get())
        ExitHandler;
        !python:print("after error", pyrapid.Symbols().GetSymbol("r").data.Get())
    ENDPROC
    PROC handler()
        ! GOTO through a statement with an error handler: it is not an error
        r := 10;
        GOTO done;
        r := 20;
        done:
    ERROR
        r := 30;
    ENDPROC
    PROC ExitHandler()
        ! labels in the error handler
        RAISE 5;
    ERROR
        r := 0;
        count:
        r := r + 1;
        IF r < 4 GOTO count;
        TRYNEXT;
    ENDPROC
ENDMODULE
