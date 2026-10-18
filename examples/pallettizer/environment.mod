MODULE ENVIRONMENT
!robot: irb460_110_240
    ! The cell of the palletizer: robot ABB IRB 460 (4 axes), two product pick lines
    ! (conveyors), two pallet stations, a gripper. This module has the data of the
    ! cell taught on the robot and the I/O signals of the equipment (EIO.cfg); the
    ! cell itself is simulated by cell.py.
    !
    ! Layout (base frame of the robot, mm): the pick lines at +110 and -110 degrees,
    ! the pallet stations at +40 (place line 1) and -40 degrees (place line 2).

    ! number of pallets that each place line fills before the program ends,
    ! 0 = never ends
    PERS num nPalletsToDo := 1;

    ! height of the approach above the pick and place points
    CONST num nApproach := 300;

    ! the gripper: 250 mm under the flange, TCP at its bottom face
    PERS tooldata tGripper := [TRUE, [[0, 0, 250], [1, 0, 0, 0]], [60, [0, 0, 120], [1, 0, 0, 0], 0, 0, 0]];

    ! park position: rax_1, rax_2, rax_3, rax_6 (4 axis robot)
    CONST jointtarget jHome := [[0, 0, 30, 0, 0, 0], [9E9, 9E9, 9E9, 9E9, 9E9, 9E9]];

    ! product pick lines: the center of the product on the end of the conveyor, the
    ! direction of the conveyor (degrees around z)
    CONST pos PickPoint{nPROD_PICKLINE} := [[-581.4, 1597.5, 700], [-581.4, -1597.5, 700]];
    CONST num PickAngle{nPROD_PICKLINE} := [110, -110];

    ! pallet stations: the work object is at the corner of the pallet, x points away
    ! from the robot (800 mm), y along the station (1200 mm)
    PERS wobjdata wPallet1 := [FALSE, TRUE, "", [[1304.9, 311.7, 0], [0.939693, 0, 0, 0.342020]], [[0, 0, 0], [1, 0, 0, 0]]];
    PERS wobjdata wPallet2 := [FALSE, TRUE, "", [[533.6, -1231.0, 0], [0.939693, 0, 0, -0.342020]], [[0, 0, 0], [1, 0, 0, 0]]];

    FUNC wobjdata PalletWObj(num nPlaceLine)
        IF nPlaceLine = 1 THEN
            RETURN wPallet1;
        ENDIF
        RETURN wPallet2;
    ENDFUNC

    ! TCP on the top of a product of height nHeight on the pick point, the gripper
    ! pointing down along the conveyor
    FUNC robtarget PickTarget(num nPickLine, num nHeight)
        VAR robtarget target := [[0, 0, 0], [1, 0, 0, 0], [0, 0, 0, 0], [9E9, 9E9, 9E9, 9E9, 9E9, 9E9]];
        target.trans := PickPoint{nPickLine};
        target.trans.z := target.trans.z + nHeight;
        target.rot := OrientZYX(PickAngle{nPickLine}, 180, 0);
        RETURN target;
    ENDFUNC

    ! TCP on the top of a product placed at x, y (center) and z (bottom, from the top of
    ! the pallet) in the pallet frame, rotated of rot degrees
    FUNC robtarget PlaceTarget(num x, num y, num z, num rot, num nPalletHeight, num nHeight)
        VAR robtarget target := [[0, 0, 0], [1, 0, 0, 0], [0, 0, 0, 0], [9E9, 9E9, 9E9, 9E9, 9E9, 9E9]];
        target.trans := [x, y, nPalletHeight + z + nHeight];
        target.rot := OrientZYX(rot, 180, 0);
        RETURN target;
    ENDFUNC

    ! I/O of the equipment (EIO.cfg)

    PROC GripperClose()
        SetDO doGripper, 1;
        WaitDI diGripperClosed, 1;
    ENDPROC

    PROC GripperOpen()
        SetDO doGripper, 0;
        WaitDI diGripperClosed, 0;
    ENDPROC

    ! the pick line delivers nCount products, one at a time on the pick point
    PROC OrderProducts(num nPickLine, num nCount)
        TEST nPickLine
        CASE 1:
            SetGO goOrderCount1, nCount;
            PulseDO doOrder1;
        CASE 2:
            SetGO goOrderCount2, nCount;
            PulseDO doOrder2;
        ENDTEST
    ENDPROC

    FUNC bool ProductPresent(num nPickLine)
        TEST nPickLine
        CASE 1:
            RETURN diProduct1 = 1;
        CASE 2:
            RETURN diProduct2 = 1;
        ENDTEST
        RETURN FALSE;
    ENDFUNC

    ! an empty pallet is requested on the station
    PROC RequestPallet(num nPlaceLine)
        TEST nPlaceLine
        CASE 1:
            PulseDO doPalletIn1;
        CASE 2:
            PulseDO doPalletIn2;
        ENDTEST
    ENDPROC

    FUNC bool PalletPresent(num nPlaceLine)
        TEST nPlaceLine
        CASE 1:
            RETURN diPallet1 = 1;
        CASE 2:
            RETURN diPallet2 = 1;
        ENDTEST
        RETURN FALSE;
    ENDFUNC

    ! the full pallet leaves the station
    PROC SendPallet(num nPlaceLine)
        TEST nPlaceLine
        CASE 1:
            PulseDO doPalletOut1;
            WaitDI diPallet1, 0;
        CASE 2:
            PulseDO doPalletOut2;
            WaitDI diPallet2, 0;
        ENDTEST
    ENDPROC
ENDMODULE
