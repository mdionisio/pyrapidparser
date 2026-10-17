MODULE errors
    ! executed by test_rapid2py.py: error handlers (kernel manual 7.1)
    VAR num tries := 0;
    VAR num r := 0;
    PROC main()
        r := Safediv(10, 0);
        !python:print("safediv", pyrapid.Symbols().GetSymbol("r").data.Get())
        r := RetryTwice();
        !python:print("retry", pyrapid.Symbols().GetSymbol("r").data.Get())
        Propagate;
    ERROR
        !python:print("propagated", pyrapid.Symbols().GetSymbol("ERRNO").data.Get())
        RETURN;
    ENDPROC
    FUNC num Safediv(num x, num y)
        IF y = 0 RAISE 10;
        RETURN x / y;
    ERROR
        ! RETURN in the error handler returns to the caller with the value
        RETURN -1;
    ENDFUNC
    FUNC num RetryTwice()
        ! RETRY executes again the statement that caused the error
        IF tries < 2 RAISE 11;
        RETURN tries;
    ERROR
        tries := tries + 1;
        RETRY;
    ENDFUNC
    PROC Propagate()
        RAISE 12;
    ERROR
        RAISE;
    ENDPROC
ENDMODULE
