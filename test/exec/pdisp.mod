MODULE pdisp
    ! executed by test_rapid2py.py: program displacement (the position is read without it
    ! with PDispOff; with it CRobT gives the programmed position)
    !robot: irb120_3_58
    CONST jointtarget jstart := [[0, 20, 10, 0, 40, 0], [9E9, 9E9, 9E9, 9E9, 9E9, 9E9]];
    VAR robtarget p0;
    VAR robtarget p;
    PROC main()
        MoveAbsJ jstart, v1000, fine, tool0;
        p0 := CRobT();
        ConfL \Off;
        ! displace the programmed points by 30 mm in x and 20 mm in y
        PDispSet [[30, 20, 0], [1, 0, 0, 0]];
        MoveL p0, v200, fine, tool0;
        p := CRobT();
        TPWrite "programmed x " \Num:=Round(p.trans.x - p0.trans.x);
        p := ORobT(p0);
        TPWrite "ORobT x " \Num:=Round(p.trans.x - p0.trans.x);
        PDispOff;
        p := CRobT();
        TPWrite "real x " \Num:=Round(p.trans.x - p0.trans.x);
        TPWrite "real y " \Num:=Round(p.trans.y - p0.trans.y);
        ! the displacement that makes p0 the current position, shifted by [10, 0, 40]
        MoveL Offs(p0, 10, 0, 40), v200, fine, tool0;
        PDispOn p0, tool0;
        MoveL Offs(p0, 0, 10, 0), v200, fine, tool0;
        PDispOff;
        p := CRobT();
        TPWrite "PDispOn x " \Num:=Round(p.trans.x - p0.trans.x);
        TPWrite "PDispOn y " \Num:=Round(p.trans.y - p0.trans.y);
        TPWrite "PDispOn z " \Num:=Round(p.trans.z - p0.trans.z);
    ENDPROC
ENDMODULE
