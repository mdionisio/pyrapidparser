MODULE motion
    ! executed by test_rapid2py.py: motion instructions on the ABB IRB 120
    !robot: irb120_3_58
    CONST jointtarget jhome := [[0, 0, 0, 0, 30, 0], [9E9, 9E9, 9E9, 9E9, 9E9, 9E9]];
    CONST robtarget p10 := [[400, -100, 400], [0, 0, 1, 0], [-1, 0, -1, 0], [9E9, 9E9, 9E9, 9E9, 9E9, 9E9]];
    PERS tooldata tgripper := [TRUE, [[0, 0, 100], [1, 0, 0, 0]], [1, [0, 0, 50], [1, 0, 0, 0], 0, 0, 0]];
    VAR robtarget p;
    VAR jointtarget j;
    PROC main()
        MoveAbsJ jhome, v1000, fine, tool0;
        p := CRobT();
        TPWrite "home ", \Pos := p.trans;
        p := CalcRobT(jhome, tgripper);
        TPWrite "gripper ", \Pos := p.trans;
        MoveJ p10, v1000, z10, tgripper;
        ! the linear movements change the quadrant of axis 1
        ConfL \Off;
        MoveL Offs(p10, 0, 200, 0), v200, fine, tgripper;
        MoveL Offs(p10, 0, 200, -100), v100, fine, tgripper \WObj := wobj0;
        MoveC Offs(p10, 50, 150, -100), Offs(p10, 0, 100, -100), v100, fine, tgripper;
        p := CRobT(\Tool := tgripper);
        TPWrite "end ", \Pos := p.trans;
        j := CJointT();
        p := CalcRobT(j, tgripper);
        TPWrite "calc ", \Pos := p.trans;
    ENDPROC
ENDMODULE
