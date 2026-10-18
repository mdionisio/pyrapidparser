MODULE motion_end_reach
    ! executed by test_rapid2py.py: a target outside the working area of the IRB 120
    ! (reach 580 mm) stops the program
    !robot: irb120_3_58
    VAR robtarget p;
    PROC main()
        MoveAbsJ [[0, 20, 10, 0, 40, 0], [9E9, 9E9, 9E9, 9E9, 9E9, 9E9]], v1000, fine, tool0;
        p := CRobT();
        MoveJ Offs(p, 100, 0, 0), v1000, fine, tool0;
        TPWrite "inside the reach";
        MoveL Offs(p, 600, 0, 0), v100, fine, tool0;
        TPWrite "not reached";
    ENDPROC
ENDMODULE
