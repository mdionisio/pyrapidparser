MODULE trigger
    ! executed by test_rapid2py.py (trigger.cfg, trigger.sim.py): outputs set along a
    ! linear movement of 100 mm at 100 mm/s
    !robot: irb120_3_58
    CONST jointtarget jstart := [[0, 20, 10, 0, 40, 0], [9E9, 9E9, 9E9, 9E9, 9E9, 9E9]];
    VAR triggdata glue;
    VAR triggdata paint;
    VAR triggdata stopped;
    VAR robtarget p0;
    PROC main()
        MoveAbsJ jstart, v1000, fine, tool0;
        p0 := CRobT();
        ConfL \Off;
        ! 30 mm before the end
        TriggIO glue, 30 \DOp:=doGlue, 1;
        ! 20 mm after the start
        TriggIO paint, 20 \Start \DOp:=doPaint, 1;
        TriggL Offs(p0, 100, 0, 0), v100, glue \T2:=paint, fine, tool0;
        TPWrite "first movement";
        ! the end of the movement is the origin of the second one: back, with a time and
        ! an equipment lag (0.1 s of 100 mm/s: 10 mm earlier)
        TriggIO glue, 0.2 \Time \DOp:=doGlue, 0;
        TriggEquip paint, 40, 0.1 \DOp:=doPaint, 0;
        TriggL p0, v100, glue \T2:=paint, fine, tool0;
        TPWrite "second movement";
    ENDPROC
ENDMODULE
