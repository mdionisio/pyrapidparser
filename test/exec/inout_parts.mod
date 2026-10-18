MODULE inout_parts
    ! executed by test_rapid2py.py with standard.sys: an element of an array and a component of a record are
    ! passed to an INOUT parameter (kernel manual 5.2)
    RECORD pair
        num a;
        num b;
    ENDRECORD
    VAR num arr{3} := [1, 2, 3];
    VAR pair p := [10, 20];
    VAR pair ps{2};
    VAR num i := 2;
    PROC double(INOUT num x)
        x := x * 2;
    ENDPROC
    FUNC bool half(INOUT num x)
        x := x / 2;
        RETURN TRUE;
    ENDFUNC
    PROC main()
        double arr{i};
        double p.b;
        ps{1} := [1, 2];
        double ps{1}.a;
        IF half(arr{3}) AND half(p.a) TPWrite "function";
        TPWrite "array " \Num:=arr{1} * 100 + arr{2} * 10 + arr{3};
        TPWrite "record " \Num:=p.a * 100 + p.b;
        TPWrite "array of records " \Num:=ps{1}.a * 10 + ps{1}.b;
    ENDPROC
ENDMODULE
