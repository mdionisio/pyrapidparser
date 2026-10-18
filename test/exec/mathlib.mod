MODULE mathlib
    ! executed by test_rapid2py.py with standard.sys: trigonometry, vectors, poses, bits
    ! and strings of the library (run/pyrapid_lib.py)
    VAR num b := 5;
    VAR pose t;
    VAR pose u;
    VAR pos v;
    VAR orient o;
    PROC main()
        TPWrite "sin " \Num:=Round(Sin(30) * 1000);
        TPWrite "cos " \Num:=Round(Cos(60) * 1000);
        TPWrite "tan " \Num:=Round(Tan(45) * 1000);
        TPWrite "asin " \Num:=Round(ASin(0.5));
        TPWrite "acos " \Num:=Round(ACos(0.5));
        TPWrite "atan " \Num:=Round(ATan(1));
        TPWrite "atan2 " \Num:=Round(ATan2(1, -1));
        TPWrite "max min " \Num:=Max(3, 7) * 10 + Min(3, 7);
        TPWrite "distance " \Num:=Distance([0, 0, 0], [3, 4, 12]);
        TPWrite "dot " \Num:=DotProd([1, 2, 3], [4, 5, 6]);
        v := CrossProd([1, 0, 0], [0, 1, 0]);
        TPWrite "cross ", \Pos:=v;
        TPWrite "magnitude " \Num:=VectMagn([2, 3, 6]);
        ! a pose: 90 degrees around z, then 100 mm along x
        t := [[100, 0, 0], [0.707107, 0, 0, 0.707107]];
        v := PoseVect(t, [10, 0, 0]);
        TPWrite "posevect ", \Pos:=v;
        u := PoseMult(t, t);
        TPWrite "posemult x " \Num:=Round(u.trans.x);
        TPWrite "posemult y " \Num:=Round(u.trans.y);
        u := PoseMult(t, PoseInv(t));
        TPWrite "pose inverse " \Num:=Round(u.trans.x) + Round(u.trans.y) + Round(u.trans.z);
        o := NOrient([2, 0, 0, 0]);
        TPWrite "norient " \Num:=o.q1;
        o := OrientZYX(30, 20, 10);
        TPWrite "euler z " \Num:=Round(EulerZYX(\Z, o));
        TPWrite "euler y " \Num:=Round(EulerZYX(\Y, o));
        TPWrite "euler x " \Num:=Round(EulerZYX(\X, o));
        TPWrite "bitand " \Num:=BitAnd(12, 10);
        TPWrite "bitor " \Num:=BitOr(12, 10);
        TPWrite "bitxor " \Num:=BitXOr(12, 10);
        TPWrite "bitneg " \Num:=BitNeg(15);
        TPWrite "lsh " \Num:=BitLSh(3, 2);
        TPWrite "rsh " \Num:=BitRSh(12, 2);
        TPWrite "bitcheck " \Bool:=BitCheck(5, 3);
        BitSet b, 2;
        BitClear b, 1;
        TPWrite "bitset bitclear " \Num:=b;
        TPWrite "dectohex " + DecToHex("255");
        TPWrite "hextodec " \Num:=HexToDec("FF");
        TPWrite "bytetostr hex " + ByteToStr(171 \Hex);
        TPWrite "bytetostr bin " + ByteToStr(5 \Bin);
        TPWrite "strtobyte " \Num:=StrToByte("11" \Bin);
        TPWrite "strmemb " \Bool:=StrMemb("a1", 2, STR_DIGIT);
        TPWrite "strorder " \Bool:=StrOrder("FIRST", "SECOND", STR_UPPER);
        TPWrite "strorder prefix " \Bool:=StrOrder("FIRSTB", "FIRST", STR_UPPER);
        TPWrite "strmap " + StrMap("hello", "el", "ip");
        TPWrite "rand in range " \Bool:=(Rand() >= 0 AND Rand() <= RAND_MAX);
        TPWrite "time " \Bool:=(GetTime(\Hour) < 24 AND StrLen(CTime()) = 8 AND StrLen(CDate()) = 10);
    ENDPROC
ENDMODULE
