MODULE motion_axis_limit
    ! executed by test_rapid2py.py: a joint target outside the limits of an axis stops
    ! the program (the axis 2 of the IRB 120 moves from -110 to 110 degrees)
    !robot: irb120_3_58
    PROC main()
        MoveAbsJ [[0, 100, 0, 0, 0, 0], [9E9, 9E9, 9E9, 9E9, 9E9, 9E9]], v1000, fine, tool0;
        TPWrite "axis 2 at 100";
        MoveAbsJ [[0, 120, 0, 0, 0, 0], [9E9, 9E9, 9E9, 9E9, 9E9, 9E9]], v1000, fine, tool0;
        TPWrite "not reached";
    ENDPROC
ENDMODULE
