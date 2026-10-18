MODULE motion_path_reach
    ! executed by test_rapid2py.py: both end points of the line are reachable (the second
    ! with axis 1 on the opposite side) but the line passes through the column of axis 1,
    ! the shoulder singularity where the robot cannot go
    !robot: irb120_3_58
    CONST jointtarget jstart := [[-90, 30, 20, 0, 40, 0], [9E9, 9E9, 9E9, 9E9, 9E9, 9E9]];
    CONST jointtarget jend := [[90, 30, 20, 0, 40, 0], [9E9, 9E9, 9E9, 9E9, 9E9, 9E9]];
    VAR robtarget pstart;
    VAR robtarget pend;
    PROC main()
        pstart := CalcRobT(jstart, tool0);
        pend := CalcRobT(jend, tool0);
        TPWrite "start y " \Num:=Round(pstart.trans.y);
        TPWrite "end y " \Num:=Round(pend.trans.y);
        ConfL \Off;
        MoveAbsJ jend, v1000, fine, tool0;
        MoveAbsJ jstart, v1000, fine, tool0;
        MoveL pend, v200, fine, tool0;
        TPWrite "not reached";
    ENDPROC
ENDMODULE
