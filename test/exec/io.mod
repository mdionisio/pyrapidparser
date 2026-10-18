MODULE io
    ! executed by test_rapid2py.py: I/O signals of io.cfg (no robot: real time)
    VAR bool late := FALSE;
    VAR num value;
    PROC main()
        SetDO doLamp, 1;
        TPWrite "lamp ", \Num:=DOutput(doLamp);
        ! a signal in value context: its value (kernel manual 2.16)
        IF doLamp = 1 TPWrite "semi-value";
        value := doLamp;
        Reset doLamp;
        TPWrite "lamp ", \Num:=doLamp;
        TPWrite "value ", \Num:=value;
        SetGO goCount, 5;
        TPWrite "count ", \Num:=GOutput(goCount);
        ! the input is set by the world, here a Python line
        !python:pyrapid.IO.set("diReady", 1)
        WaitDI diReady, 1;
        TPWrite "ready ", \Bool:=TestDI(diReady);
        WaitDI diReady, 0 \MaxTime:=0.05 \TimeFlag:=late;
        TPWrite "WaitDI timeout ", \Bool:=late;
        WaitUntil diReady = 1;
        WaitUntil DInput(diReady) = 0 \MaxTime:=0.05 \TimeFlag:=late;
        TPWrite "WaitUntil timeout ", \Bool:=late;
        PulseDO \PLength:=0.05, doLamp;
        TPWrite "pulse ", \Num:=doLamp;
        WaitUntil doLamp = 0;
        TPWrite "after the pulse ", \Num:=doLamp;
        WaitDI diReady, 0 \MaxTime:=0.05;
        TPWrite "not reached";
    ERROR
        IF ERRNO = ERR_WAIT_MAXTIME THEN
            TPWrite "ERR_WAIT_MAXTIME";
            RETURN;
        ENDIF
    ENDPROC
ENDMODULE
