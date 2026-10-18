MODULE demo
    ! ABB IRB 120 drawing on a table with a pen: joint, linear and circular movements,
    ! stop points and fly-by points.
    ! The model of ROS-Industrial has the inertial data: the log shows the torques.
    !
    ! From the project folder:
    !   python rapid2py.py -e demo.main -i examples/irb120/demo.mod -d out -f demo.py -r
    ! with the log of the movements and the robot in the browser:
    !   PYRAPID_MOTION_LOG=1 PYRAPID_VIEWER=meshcat python rapid2py.py ... -r
    !robot: irb120_3_58

    ! pen: 120 mm long along z of the flange, 0.3 kg
    PERS tooldata tpen := [TRUE, [[0, 0, 120], [1, 0, 0, 0]], [0.3, [0, 0, 60], [1, 0, 0, 0], 0, 0, 0]];
    ! table: the corner of the drawing area, 200 mm above the base
    PERS wobjdata wtable := [FALSE, TRUE, "", [[300, -200, 200], [1, 0, 0, 0]], [[0, 0, 0], [1, 0, 0, 0]]];

    CONST jointtarget jhome := [[0, 0, 0, 0, 30, 0], [9E9, 9E9, 9E9, 9E9, 9E9, 9E9]];
    CONST jointtarget jwave := [[-60, 20, -20, 90, 60, 180], [9E9, 9E9, 9E9, 9E9, 9E9, 9E9]];
    ! corners of a 150 mm square on the table, the pen pointing down
    CONST robtarget pa := [[0, 0, 0], [0, 0, 1, 0], [-1, 0, -1, 0], [9E9, 9E9, 9E9, 9E9, 9E9, 9E9]];
    CONST robtarget pb := [[150, 0, 0], [0, 0, 1, 0], [-1, 0, -1, 0], [9E9, 9E9, 9E9, 9E9, 9E9, 9E9]];
    CONST robtarget pc := [[150, 150, 0], [0, 0, 1, 0], [-1, 0, -1, 0], [9E9, 9E9, 9E9, 9E9, 9E9, 9E9]];
    CONST robtarget pd := [[0, 150, 0], [0, 0, 1, 0], [-1, 0, -1, 0], [9E9, 9E9, 9E9, 9E9, 9E9, 9E9]];
    ! circle of radius 50 mm in the middle of the square
    CONST robtarget pcenter := [[75, 75, 0], [0, 0, 1, 0], [-1, 0, -1, 0], [9E9, 9E9, 9E9, 9E9, 9E9, 9E9]];

    VAR robtarget pnow;
    VAR jointtarget jnow;

    PROC main()
        ! joint movements: home, a pose with all the axes moved, home again
        MoveAbsJ jhome, v1000, fine, tool0;
        MoveAbsJ jwave, v1000, fine, tool0;
        MoveAbsJ jhome, v1000, fine, tool0;
        jnow := CJointT();

        ! above the first corner, then down to the table
        MoveJ Offs(pa, 0, 0, 50), v1000, z10, tpen \WObj := wtable;
        MoveL pa, v100, fine, tpen \WObj := wtable;
        ! the square
        MoveL pb, v200, fine, tpen \WObj := wtable;
        MoveL pc, v200, fine, tpen \WObj := wtable;
        MoveL pd, v200, fine, tpen \WObj := wtable;
        MoveL pa, v200, fine, tpen \WObj := wtable;
        ! a smaller square with fly-by corners: the program continues before each
        ! corner, the robot rounds it within 20 mm without stopping
        MoveL Offs(pa, 25, 25, 0), v200, fine, tpen \WObj := wtable;
        MoveL Offs(pb, -25, 25, 0), v200, z20, tpen \WObj := wtable;
        MoveL Offs(pc, -25, -25, 0), v200, z20, tpen \WObj := wtable;
        MoveL Offs(pd, 25, -25, 0), v200, z20, tpen \WObj := wtable;
        MoveL Offs(pa, 25, 25, 0), v200, fine, tpen \WObj := wtable;
        MoveL Offs(pa, 0, 0, 50), v200, fine, tpen \WObj := wtable;

        ! the circle: two half circles
        MoveJ Offs(pcenter, -50, 0, 50), v1000, z10, tpen \WObj := wtable;
        MoveL Offs(pcenter, -50, 0, 0), v100, fine, tpen \WObj := wtable;
        MoveC Offs(pcenter, 0, -50, 0), Offs(pcenter, 50, 0, 0), v100, fine, tpen \WObj := wtable;
        MoveC Offs(pcenter, 0, 50, 0), Offs(pcenter, -50, 0, 0), v100, fine, tpen \WObj := wtable;
        MoveL Offs(pcenter, -50, 0, 50), v200, fine, tpen \WObj := wtable;

        ! the pen tilted by 30 degrees around its own y axis (axis 4 stays positive,
        ! the configuration of the robtarget: ConfL does not stop the program)
        MoveL RelTool(Offs(pcenter, 0, 0, 50), 0, 0, 0 \Ry := -30), v100, fine, tpen \WObj := wtable;
        WaitTime 1;
        pnow := CRobT(\Tool := tpen \WObj := wtable);
        TPWrite "tilted pen at", \Pos := pnow.trans;

        MoveAbsJ jhome, v1000, fine, tool0;
    ENDPROC
ENDMODULE
