MODULE nocase
    ! executed by test_rapid2py.py: names written with different cases
    RECORD Item
        num Count;
    ENDRECORD
    VAR item it := [1];
    VAR num Counter := 0;
    proc Main()
        COUNTER := counter + 1;
        It.COUNT := IT.count + 1;
        add_value VALUE := 10 \Twice;
        !python:print("counter", pyrapid.Symbols().GetSymbol("counter").data.Get())
        !python:print("count", pyrapid.Symbols().GetSymbol("IT").data.GetElem("count").Get())
    ENDPROC
    PROC Add_Value(num Value \switch TWICE)
        IF present(twice) THEN
            counter := counter + value * 2;
        ELSE
            counter := counter + value;
        ENDIF
    ENDPROC
ENDMODULE
