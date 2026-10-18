MODULE motion_singular
    ! executed by test_rapid2py.py: a linear movement near a wrist singularity stops the
    ! program (the controller sweeps the axes 4 and 6; here SingArea \Off is not simulated)
    !robot: irb120_3_58
    CONST jointtarget jsing := [[0, 20, 10, 30, 0, -30], [9E9, 9E9, 9E9, 9E9, 9E9, 9E9]];
    VAR robtarget p;
    VAR robtarget pstart;
    VAR robtarget pend;
    PROC main()
        ! the position with axis 5 at 0, passed at a distance of 2 mm by a vertical line
        p := CalcRobT(jsing, tool0);
        pstart := Offs(p, -1.715, 1.029, -60);
        pend := Offs(p, -1.715, 1.029, 60);
        ConfJ \Off;
        ConfL \Off;
        MoveJ pstart, v1000, fine, tool0;
        TPWrite "at the start";
        MoveL pend, v100, fine, tool0;
        TPWrite "not reached";
    ENDPROC
ENDMODULE
