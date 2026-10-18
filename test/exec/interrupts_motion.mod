MODULE interrupts_motion
    ! executed by test_rapid2py.py (interrupts_motion.cfg, interrupts_motion.sim.py): the
    ! traps run in the time of the robot while a movement is executed
    !robot: irb120_3_58
    CONST jointtarget jstart := [[0, 20, 10, 0, 40, 0], [9E9, 9E9, 9E9, 9E9, 9E9, 9E9]];
    CONST speeddata vslow := [60, 60, 5000, 1000];
    VAR robtarget pnow;
    VAR intnum touch;
    VAR intnum tick;
    VAR intnum half;
    VAR triggdata midway;
    VAR robtarget pstart;
    TRAP on_touch
        pnow := CRobT();
        TPWrite "touched at " \Num:=Round(pnow.trans.x);
    ENDTRAP
    TRAP on_half
        TPWrite "midway";
    ENDTRAP
    TRAP on_tick
        TPWrite "tick";
    ENDTRAP
    PROC main()
        MoveAbsJ jstart, v1000, fine, tool0;
        pstart := CRobT();
        ConfL \Off;
        CONNECT touch WITH on_touch;
        ISignalDI diProbe, 1, touch;
        CONNECT tick WITH on_tick;
        ITimer 0.5, tick;
        CONNECT half WITH on_half;
        TriggInt midway, 1 \Time, half;
        ! 120 mm at 60 mm/s: the surface (x = 450) is touched after 36 mm
        TriggL Offs(pstart, 120, 0, 0), vslow, midway, fine, tool0;
        TPWrite "end of the movement";
    ENDPROC
ENDMODULE
