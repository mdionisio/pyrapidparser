MODULE demo
    ! osj6, the 3D printed robot with oblique swivel joints: the joints at 45 degrees
    ! fold the tube, then the robot draws on a table with a pen.
    !
    ! From the project folder:
    !   python rapid2py.py -e demo.main -i examples/osj6/demo.mod -d out -f demo.py -r
    ! with the log of the movements and the robot in the browser:
    !   PYRAPID_MOTION_LOG=1 PYRAPID_VIEWER=meshcat python rapid2py.py ... -r
    !robot: osj6

    ! pen: 100 mm long along z of the flange, 20 g
    PERS tooldata tpen := [TRUE, [[0, 0, 100], [1, 0, 0, 0]], [0.02, [0, 0, 50], [1, 0, 0, 0], 0, 0, 0]];
    ! table: the corner of the drawing area, 50 mm above the floor
    PERS wobjdata wtable := [FALSE, TRUE, "", [[180, -50, 50], [1, 0, 0, 0]], [[0, 0, 0], [1, 0, 0, 0]]];

    ! the tube straight up: a singular position (all the joint axes in one plane)
    CONST jointtarget jstraight := [[0, 0, 0, 0, 0, 0], [9E9, 9E9, 9E9, 9E9, 9E9, 9E9]];
    ! home: the arm bent forward, the flange looking ahead
    CONST jointtarget jhome := [[0, -90, -45, 45, 90, 0], [9E9, 9E9, 9E9, 9E9, 9E9, 9E9]];
    ! each oblique joint turned by 180 degrees bends the tube by 90 degrees
    CONST jointtarget jbend2 := [[0, 180, 0, 0, 0, 0], [9E9, 9E9, 9E9, 9E9, 9E9, 9E9]];
    CONST jointtarget jzigzag := [[0, 180, 0, 180, 0, 0], [9E9, 9E9, 9E9, 9E9, 9E9, 9E9]];
    CONST jointtarget jspiral := [[0, -90, -90, -90, -90, 0], [9E9, 9E9, 9E9, 9E9, 9E9, 9E9]];
    ! above the table: a solution of the inverse kinematics that draws the square and the
    ! circle without crossing a singularity or a limit of the axes
    CONST jointtarget jready := [[0, -12, 77, -179, -91, -16], [9E9, 9E9, 9E9, 9E9, 9E9, 9E9]];
    ! corners of a 100 mm square on the table, the pen pointing down
    CONST robtarget pa := [[0, 0, 0], [0, 0, 1, 0], [0, 0, 0, 0], [9E9, 9E9, 9E9, 9E9, 9E9, 9E9]];
    CONST robtarget pb := [[100, 0, 0], [0, 0, 1, 0], [0, 0, 0, 0], [9E9, 9E9, 9E9, 9E9, 9E9, 9E9]];
    CONST robtarget pc := [[100, 100, 0], [0, 0, 1, 0], [0, 0, 0, 0], [9E9, 9E9, 9E9, 9E9, 9E9, 9E9]];
    CONST robtarget pd := [[0, 100, 0], [0, 0, 1, 0], [0, 0, 0, 0], [9E9, 9E9, 9E9, 9E9, 9E9, 9E9]];
    ! circle of radius 30 mm in the middle of the square
    CONST robtarget pcenter := [[50, 50, 0], [0, 0, 1, 0], [0, 0, 0, 0], [9E9, 9E9, 9E9, 9E9, 9E9, 9E9]];

    VAR robtarget pnow;

    PROC main()
        ! the joints: straight, one joint at 180 degrees, two joints, all the joints at
        ! 90 degrees, home
        MoveAbsJ jstraight, v1000, fine, tool0;
        MoveAbsJ jbend2, v1000, fine, tool0;
        MoveAbsJ jzigzag, v1000, fine, tool0;
        MoveAbsJ jspiral, v1000, fine, tool0;
        MoveAbsJ jhome, v1000, fine, tool0;

        ! the confdata of the ABB arms (cf1, cf4, cf6, cfx) does not describe the
        ! solutions of this robot: the linear movements take the solution nearest to
        ! the current position
        ConfL \Off;

        ! above the first corner, then down to the table
        MoveAbsJ jready, v1000, fine, tool0;
        MoveL Offs(pa, 0, 0, 30), v100, fine, tpen \WObj := wtable;
        MoveL pa, v40, fine, tpen \WObj := wtable;
        ! the square, with fly-by corners
        MoveL pb, v40, z5, tpen \WObj := wtable;
        MoveL pc, v40, z5, tpen \WObj := wtable;
        MoveL pd, v40, z5, tpen \WObj := wtable;
        MoveL pa, v40, fine, tpen \WObj := wtable;
        MoveL Offs(pa, 0, 0, 30), v100, fine, tpen \WObj := wtable;

        ! the circle: two half circles
        MoveL Offs(pcenter, -30, 0, 30), v100, z5, tpen \WObj := wtable;
        MoveL Offs(pcenter, -30, 0, 0), v40, fine, tpen \WObj := wtable;
        MoveC Offs(pcenter, 0, -30, 0), Offs(pcenter, 30, 0, 0), v40, fine, tpen \WObj := wtable;
        MoveC Offs(pcenter, 0, 30, 0), Offs(pcenter, -30, 0, 0), v40, fine, tpen \WObj := wtable;
        MoveL Offs(pcenter, -30, 0, 30), v100, fine, tpen \WObj := wtable;
        pnow := CRobT(\Tool := tpen \WObj := wtable);
        TPWrite "pen at ", \Pos := pnow.trans;

        MoveAbsJ jhome, v1000, fine, tool0;
    ENDPROC
ENDMODULE
