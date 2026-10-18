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
    PERS wobjdata wtable := [FALSE, TRUE, "", [[250, -50, 50], [1, 0, 0, 0]], [[0, 0, 0], [1, 0, 0, 0]]];

    ! the tube straight up: a singular position (all the joint axes in one plane)
    CONST jointtarget jstraight := [[0, 0, 0, 0, 0, 0], [9E9, 9E9, 9E9, 9E9, 9E9, 9E9]];
    ! home: the arm bent forward, the flange looking ahead
    CONST jointtarget jhome := [[0, -90, -45, 45, 90, 0], [9E9, 9E9, 9E9, 9E9, 9E9, 9E9]];
    ! each oblique joint turned by 180 degrees bends the tube by 90 degrees
    CONST jointtarget jbend2 := [[0, 180, 0, 0, 0, 0], [9E9, 9E9, 9E9, 9E9, 9E9, 9E9]];
    CONST jointtarget jzigzag := [[0, 180, 0, 180, 0, 0], [9E9, 9E9, 9E9, 9E9, 9E9, 9E9]];
    CONST jointtarget jspiral := [[0, -90, -90, -90, -90, 0], [9E9, 9E9, 9E9, 9E9, 9E9, 9E9]];
    ! above the table: a solution of the inverse kinematics that draws the square and the
    ! inscribed circle without crossing a singularity or a limit of the axes
    CONST jointtarget jready := [[-40, 2, 79, -91, 102, -56], [9E9, 9E9, 9E9, 9E9, 9E9, 9E9]];
    ! corners of a 100 mm square on the table, the pen pointing down
    CONST robtarget pa := [[0, 0, 0], [0, 0, 1, 0], [0, 0, 0, 0], [9E9, 9E9, 9E9, 9E9, 9E9, 9E9]];
    CONST robtarget pb := [[100, 0, 0], [0, 0, 1, 0], [0, 0, 0, 0], [9E9, 9E9, 9E9, 9E9, 9E9, 9E9]];
    CONST robtarget pc := [[100, 100, 0], [0, 0, 1, 0], [0, 0, 0, 0], [9E9, 9E9, 9E9, 9E9, 9E9, 9E9]];
    CONST robtarget pd := [[0, 100, 0], [0, 0, 1, 0], [0, 0, 0, 0], [9E9, 9E9, 9E9, 9E9, 9E9, 9E9]];
    ! center of the square: the inscribed circle has radius 50 mm
    CONST robtarget pcenter := [[50, 50, 0], [0, 0, 1, 0], [0, 0, 0, 0], [9E9, 9E9, 9E9, 9E9, 9E9, 9E9]];

    VAR robtarget pnow;

    PROC main()
        ! the joints: straight, one joint at 180 degrees, two joints, all the joints at
        ! 90 degrees, home
        TPWrite "1. joints: the tube straight up, all the axes at 0 (singular position)";
        MoveAbsJ jstraight, v1000, fine, tool0;
        TPWrite "2. joints: axis 2 at 180 degrees, the tube bends by 90 degrees";
        MoveAbsJ jbend2, v1000, fine, tool0;
        TPWrite "3. joints: axes 2 and 4 at 180 degrees, a zig-zag";
        MoveAbsJ jzigzag, v1000, fine, tool0;
        TPWrite "4. joints: axes 2 - 5 at -90 degrees, a spiral";
        MoveAbsJ jspiral, v1000, fine, tool0;
        TPWrite "5. joints: home, the arm bent forward";
        MoveAbsJ jhome, v1000, fine, tool0;

        ! the confdata of the ABB arms (cf1, cf4, cf6, cfx) does not describe the
        ! solutions of this robot: the linear movements take the solution nearest to
        ! the current position
        ConfL \Off;

        TPWrite "6. joints, then linear: above the table, the pen down on a corner";
        MoveAbsJ jready, v1000, fine, tool0;
        MoveL Offs(pa, 0, 0, 30), v100, fine, tpen \WObj := wtable;
        MoveL pa, v40, fine, tpen \WObj := wtable;

        TPWrite "7. linear: the edges of the 100 mm square, stop at each corner";
        MoveL pb, v40, fine, tpen \WObj := wtable;
        MoveL pc, v40, fine, tpen \WObj := wtable;
        MoveL pd, v40, fine, tpen \WObj := wtable;
        MoveL pa, v40, fine, tpen \WObj := wtable;

        TPWrite "8. linear: the square again, fly-by corners rounded within 30 mm";
        MoveL pb, v40, z30, tpen \WObj := wtable;
        MoveL pc, v40, z30, tpen \WObj := wtable;
        MoveL pd, v40, z30, tpen \WObj := wtable;
        MoveL pa, v40, fine, tpen \WObj := wtable;

        TPWrite "9. linear: the pen up, to the middle of the lower edge, down";
        MoveL Offs(pa, 0, 0, 30), v100, z5, tpen \WObj := wtable;
        MoveL Offs(pcenter, 0, -50, 30), v100, z5, tpen \WObj := wtable;
        MoveL Offs(pcenter, 0, -50, 0), v40, fine, tpen \WObj := wtable;

        TPWrite "10. circular: the circle inscribed in the square, two half circles";
        MoveC Offs(pcenter, 50, 0, 0), Offs(pcenter, 0, 50, 0), v40, fine, tpen \WObj := wtable;
        MoveC Offs(pcenter, -50, 0, 0), Offs(pcenter, 0, -50, 0), v40, fine, tpen \WObj := wtable;

        TPWrite "11. linear: the pen up";
        MoveL Offs(pcenter, 0, -50, 30), v100, fine, tpen \WObj := wtable;

        pnow := CRobT(\Tool := tpen \WObj := wtable);
        TPWrite "pen at ", \Pos := pnow.trans;

        TPWrite "12. joints: home";
        MoveAbsJ jhome, v1000, fine, tool0;
    ENDPROC
ENDMODULE
