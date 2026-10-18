MODULE operator
    ! executed by test_rapid2py.py with standard.sys: messages and stop of the program
    PROC main()
        TPErase;
        ErrWrite \I, "Information", "the program starts" \RL2:="second line";
        ErrWrite \W, "Warning", "a reason";
        TPWrite "before Stop";
        Stop;
        TPWrite "not reached";
    ENDPROC
ENDMODULE
