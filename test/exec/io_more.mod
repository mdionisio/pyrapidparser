MODULE io_more
    ! executed by test_rapid2py.py with standard.sys: more I/O instructions (io_more.cfg)
    VAR signaldi other;
    VAR bool late := FALSE;
    PROC main()
        InvertDO doValve;
        TPWrite "inverted " \Num:=DOutput(doValve);
        InvertDO doValve;
        TPWrite "inverted again " \Num:=DOutput(doValve);
        SetAO aoSpeed, 7.5;
        WaitAO aoSpeed, \GT, 5 \MaxTime:=0.5;
        TPWrite "analog output " \Num:=AOutput(aoSpeed);
        !python:pyrapid.IO.set("aiLevel", 2)
        WaitAI aiLevel, \LT, 3 \MaxTime:=0.5;
        WaitAI aiLevel, \GT, 3 \MaxTime:=0.05 \TimeFlag:=late;
        TPWrite "analog input timeout " \Bool:=late;
        SetGO goMode, 3;
        WaitGO goMode, 3;
        TPWrite "group " \Num:=GOutputDnum(goMode);
        TPWrite "valid " \Bool:=ValidIO(diSensor);
        AliasIO "diSensor", other;
        !python:pyrapid.IO.set("diSensor", 1)
        TPWrite "alias " \Num:=DInput(other);
        IODisable "d652", 5;
        IOEnable "d652", 5;
    ENDPROC
ENDMODULE
