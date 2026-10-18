MODULE misc
    ! executed by test_rapid2py.py with standard.sys: pi, dnum functions, booked errors,
    ! data by name
    VAR errnum err_mine;
    VAR num counter := 5;
    VAR num copy := 0;
    VAR string text := "abc";
    PROC main()
        TPWrite "pi " \Num:=Round(pi * 10000);
        TPWrite "dnum " \Num:=AbsDnum(-2.5) + SqrtDnum(16) + PowDnum(2, 3);
        TPWrite "round " \Num:=RoundDnum(2.567 \Dec:=1);
        TPWrite "to str " + DnumToStr(3.14159, 3);
        TPWrite "num " \Num:=DnumToNum(NumToDnum(7));
        GetDataVal "counter", copy;
        TPWrite "GetDataVal " \Num:=copy;
        SetDataVal "counter", 42;
        TPWrite "SetDataVal " \Num:=counter;
        BookErrNo err_mine;
        ErrRaise "MYERR", err_mine, "my error";
        TPWrite "not reached";
    ERROR
        IF ERRNO = err_mine THEN
            TPWrite "booked error";
            RETURN;
        ENDIF
    ENDPROC
ENDMODULE
