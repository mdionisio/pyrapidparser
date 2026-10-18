MODULE stopmove
    ! executed by test_rapid2py.py: StopMove, StorePath, RestoPath, StartMove and ClearPath in
    ! the trap of an interrupt
    !robot: irb120_3_58
    CONST jointtarget jstart := [[0, 20, 10, 0, 40, 0], [9E9, 9E9, 9E9, 9E9, 9E9, 9E9]];
    CONST jointtarget jaway := [[30, 20, 10, 0, 40, 0], [9E9, 9E9, 9E9, 9E9, 9E9, 9E9]];
    CONST speeddata vslow := [60, 60, 5000, 1000];
    VAR robtarget pstart;
    VAR robtarget pnow;
    VAR intnum pause;
    VAR bool abandon := FALSE;
    TRAP on_pause
        StopMove;
        StorePath;
        pnow := CRobT();
        TPWrite "stopped at x " \Num:=Round(pnow.trans.x - pstart.trans.x);
        ! a movement on the new path
        MoveAbsJ jaway, v1000, fine, tool0;
        TPWrite "moved away";
        IF abandon THEN
            RestoPath;
            ClearPath;
            StartMove;
            TPWrite "path cleared";
        ELSE
            RestoPath;
            StartMove;
            TPWrite "resumed";
        ENDIF
    ENDTRAP
    PROC main()
        MoveAbsJ jstart, v1000, fine, tool0;
        pstart := CRobT();
        ConfL \Off;
        CONNECT pause WITH on_pause;
        ITimer \Single, 0.8, pause;
        ! 120 mm at 60 mm/s: the interrupt stops the movement at about 1/3
        MoveL Offs(pstart, 120, 0, 0), vslow, fine, tool0;
        pnow := CRobT();
        TPWrite "end x " \Num:=Round(pnow.trans.x - pstart.trans.x);
        ! the same, but the movement is abandoned
        abandon := TRUE;
        MoveAbsJ jstart, v1000, fine, tool0;
        CONNECT pause WITH on_pause;
        ITimer \Single, 0.8, pause;
        MoveL Offs(pstart, 120, 0, 0), vslow, fine, tool0;
        pnow := CRobT();
        TPWrite "abandoned: x " \Num:=Round(pnow.trans.x - pstart.trans.x);
    ENDPROC
ENDMODULE
