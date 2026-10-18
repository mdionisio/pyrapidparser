MODULE stdlib
    ! executed by test_rapid2py.py with standard.sys: arithmetic, string and counter routines
    VAR num n := 5;
    VAR num v := 0;
    VAR string s := "";
    VAR bool ok := FALSE;
    VAR clock timer;
    PROC main()
        Incr n;
        Decr n;
        Decr n;
        Add n, 10;
        TPWrite "counters " \Num:=n;
        TPWrite "abs " \Num:=Abs(-3.5);
        TPWrite "round " \Num:=Round(2.6);
        TPWrite "sqrt " \Num:=Sqrt(16);
        TPWrite "pow " \Num:=Pow(2, 10);
        TPWrite "exp " \Num:=Exp(0);
        TPWrite "trunc " \Num:=Trunc(2.9);
        TPWrite "trunc negative " \Num:=Trunc(-2.9);
        TPWrite "round half " \Num:=Round(2.5);
        TPWrite "round negative half " \Num:=Round(-2.5);
        TPWrite "round decimals " \Num:=Round(3.14159 \Dec:=2);
        TPWrite "trunc decimals " \Num:=Trunc(3.14159 \Dec:=3);
        s := "Robot Arm";
        TPWrite "len " \Num:=StrLen(s);
        TPWrite "part " + StrPart(s, 7, 3);
        TPWrite "match " \Num:=StrMatch(s, 1, "Arm");
        TPWrite "match none " \Num:=StrMatch(s, 1, "xyz");
        TPWrite "find " \Num:=StrFind(s, 1, " ");
        TPWrite "find not in set " \Num:=StrFind("123abc", 1, "0123456789" \NotInSet);
        TPWrite "numtostr " + NumToStr(3.14159, 2);
        TPWrite "numtostr exp " + NumToStr(1234.5, 1 \Exp);
        ok := StrToVal("12.5", v);
        TPWrite "strtoval " \Bool:=ok;
        TPWrite "value " \Num:=v;
        ok := StrToVal("not a value", v);
        TPWrite "strtoval invalid " \Bool:=ok;
        ClkReset timer;
        ClkStart timer;
        WaitTime 0.1;
        ClkStop timer;
        TPWrite "clock ok " \Bool:=(ClkRead(timer) >= 0.05);
    ENDPROC
ENDMODULE
