MODULE search
    ! executed by test_rapid2py.py (search.cfg, search.py): SearchL stores the position
    ! where the probe signal changes
    !robot: irb120_3_58
    CONST jointtarget jstart := [[0, 20, 10, 0, 40, 0], [9E9, 9E9, 9E9, 9E9, 9E9, 9E9]];
    CONST speeddata vslow := [50, 50, 5000, 1000];
    VAR robtarget pstart;
    VAR robtarget p0;
    VAR robtarget hit;
    PROC main()
        MoveAbsJ jstart, v1000, fine, tool0;
        pstart := CRobT();
        TPWrite "start x " \Num:=Round(pstart.trans.x);
        ConfL \Off;
        ! flying search to the destination (beyond the surface)
        SearchL diProbe, hit, Offs(pstart, 120, 0, 0), v100, tool0;
        TPWrite "flying: hit at x " \Num:=Round(hit.trans.x);
        p0 := CRobT();
        TPWrite "end x " \Num:=Round(p0.trans.x);
        MoveAbsJ jstart, v1000, fine, tool0;
        ! the robot stops at the hit
        SearchL \Stop, diProbe, hit, Offs(pstart, 120, 0, 0), vslow, tool0;
        p0 := CRobT();
        TPWrite "stop: hit at x " \Num:=Round(hit.trans.x);
        TPWrite "stopped before the end " \Bool:=(p0.trans.x < 560);
        TPWrite "stop distance is small " \Bool:=(p0.trans.x > hit.trans.x AND p0.trans.x < hit.trans.x + 10);
        MoveAbsJ jstart, v1000, fine, tool0;
        ! no hit: the destination is before the surface
        SearchL diProbe, hit, Offs(pstart, 20, 0, 0), v100, tool0;
        TPWrite "not reached";
    ERROR
        IF ERRNO = ERR_WHLSEARCH THEN
            TPWrite "no hit";
            already_active;
            RETURN;
        ENDIF
    ENDPROC
    PROC already_active()
        ! the signal is already active at the start (the probe is beyond the surface)
        MoveL Offs(pstart, 130, 0, 0), vslow, fine, tool0;
        SearchL diProbe, hit, Offs(pstart, 100, 0, 0), vslow, tool0;
        TPWrite "not reached";
    ERROR
        IF ERRNO = ERR_SIGSUPSEARCH THEN
            TPWrite "signal already active";
            RETURN;
        ENDIF
    ENDPROC
ENDMODULE
