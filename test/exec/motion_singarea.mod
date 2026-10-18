MODULE motion_singarea
    ! executed by test_rapid2py.py: the line of motion_singular.mod, that goes near a wrist
    ! singularity, with SingArea \Wrist: the TCP follows the line, the wrist axes are
    ! joint interpolated and the orientation of the tool changes a little
    !robot: irb120_3_58
    CONST jointtarget jsing := [[0, 20, 10, 30, 0, -30], [9E9, 9E9, 9E9, 9E9, 9E9, 9E9]];
    VAR robtarget p;
    VAR robtarget pstart;
    VAR robtarget pend;
    VAR robtarget pnow;
    PROC main()
        p := CalcRobT(jsing, tool0);
        pstart := Offs(p, -1.715, 1.029, -60);
        pend := Offs(p, -1.715, 1.029, 60);
        ConfJ \Off;
        ConfL \Off;
        MoveJ pstart, v1000, fine, tool0;
        SingArea \Wrist;
        MoveL pend, v100, fine, tool0;
        pnow := CRobT();
        TPWrite "end x " \Num:=Round(pnow.trans.x - pend.trans.x);
        TPWrite "end z " \Num:=Round(pnow.trans.z - pend.trans.z);
        ! the orientation as programmed again: the controller stops (here, as with SingArea
        ! \Off the axes would sweep)
        SingArea \Off;
        MoveL pstart, v100, fine, tool0;
        TPWrite "not reached";
    ENDPROC
ENDMODULE
