MODULE arguments
    ! executed by test_rapid2py.py: the positional arguments are the required
    ! parameters, the optional ones are named (kernel manual 5.2)
    VAR num r := 0;
    PROC show(num a \num b | num c, num d \num e)
        r := a * 1000 + d;
        IF Present(b) r := r + b * 100;
        IF Present(c) r := r + c * 10;
        IF Present(e) r := r + e;
        !python:print("r", pyrapid.Symbols().GetSymbol("r").data.Get())
    ENDPROC
    PROC main()
        show 1, 2;
        show 1 \b := 3, 2;
        show 1 \c := 4, 2 \e := 5;
    ENDPROC
ENDMODULE
