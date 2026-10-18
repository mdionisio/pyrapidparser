MODULE motion_more
    ! executed by test_rapid2py.py (motion_more.cfg, motion_more.sim.py): AccSet, VelSet and
    ! the movements that set an output
    !robot: irb120_3_58
    CONST jointtarget jstart := [[0, 20, 10, 0, 40, 0], [9E9, 9E9, 9E9, 9E9, 9E9, 9E9]];
    VAR robtarget p0;
    PROC main()
        MoveAbsJ jstart, v1000, fine, tool0;
        p0 := CRobT();
        ConfL \Off;
        ! the same movement: programmed speed, then 50 percent, then slower accelerations
        MoveL Offs(p0, 60, 0, 0), v200, fine, tool0;
        MoveL p0, v200, fine, tool0;
        VelSet 50, 1000;
        MoveL Offs(p0, 60, 0, 0), v200, fine, tool0;
        MoveL p0, v200, fine, tool0;
        ! the maximum speed of the TCP
        VelSet 100, 100;
        MoveL Offs(p0, 60, 0, 0), v200, fine, tool0;
        VelSet 100, 5000;
        AccSet 30, 100;
        MoveL p0, v200, fine, tool0;
        AccSet 100, 100;
        ! the output at the end of the movement, at the corner of a fly-by point
        MoveLDO Offs(p0, 60, 0, 0), v200, fine, tool0, doGlue, 1;
        TPWrite "after MoveLDO";
        MoveLDO Offs(p0, 60, 20, 0), v200, z20, tool0, doPaint, 1;
        MoveL p0, v200, fine, tool0;
        TPWrite "after the fly-by point";
        MoveJDO p0, v200, fine, tool0, doGlue, 0;
    ENDPROC
ENDMODULE
