MODULE motion_reach
    ! executed by test_rapid2py.py: reach, axis limits and wrist singularity of the IRB 120
    ! with the movements that do not stop the program
    !robot: irb120_3_58
    CONST jointtarget jsing := [[0, 20, 10, 30, 0, -30], [9E9, 9E9, 9E9, 9E9, 9E9, 9E9]];
    VAR robtarget p;
    VAR jointtarget j;
    VAR errnum e;
    PROC main()
        e := 0;
        ! axes 4 and 6 in line (axis 5 at 0): a singular position can be reached by a joint
        ! movement and the kinematics find it again
        MoveAbsJ jsing, v1000, fine, tool0;
        p := CRobT();
        MoveJ Offs(p, 0, 0, 0), v1000, fine, tool0;
        j := CalcJointT(p, tool0);
        TPWrite "axis 5 at the singularity " \Num:=Round(j.robax.rax_5);
        ! the manual (CalcJointT): at a wrist singularity axis 4 is set to 0
        TPWrite "axis 4 at the singularity " \Num:=Round(j.robax.rax_4);
        TPWrite "axis 6 at the singularity " \Num:=Round(j.robax.rax_6);
        ! joint interpolation goes through the singularity
        MoveAbsJ [[0, 20, 10, 30, 20, -30], [9E9, 9E9, 9E9, 9E9, 9E9, 9E9]], v1000, fine, tool0;
        MoveAbsJ [[0, 20, 10, 30, -20, -30], [9E9, 9E9, 9E9, 9E9, 9E9, 9E9]], v1000, fine, tool0;
        p := CRobT();
        TPWrite "joint movement through axis 5 = 0 " \Num:=Round(p.trans.x);
        ! outside the working area: ERR_OUTSIDE_REACH
        p := Offs(p, 2000, 0, 0);
        j := CalcJointT(p, tool0);
        TPWrite "not reached";
    ERROR
        IF ERRNO = ERR_OUTSIDE_REACH THEN
            TPWrite "outside reach";
            p := CRobT();
            ! another configuration of axis 1: the position is reachable but not as asked
            p.robconf.cf1 := 2;
            j := CalcJointT(p, tool0 \ErrorNumber := e);
            TPWrite "configuration not possible " \Bool := (e = ERR_ROBLIMIT);
            p := CRobT();
            e := 0;
            j := CalcJointT(p, tool0 \ErrorNumber := e);
            TPWrite "no error " \Bool := (e = 0);
        ENDIF
        RETURN;
    ENDPROC
ENDMODULE
