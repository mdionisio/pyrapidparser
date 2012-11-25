MODULE syun1
    PROC MAIN()
        VAR num val:= 1.0;
        VAR num val2;
        VAR string stmp;
        TPWrite "TPWrite", \Num:=val;
        
        stmp := ValToStr(val);
        TPWrite "ValToStr";
        TPWrite stmp;
        
        IF StrToVal(stmp, val2) THEN
            TPWrite "ok", \Num:=val2;
        ELSE
            TPWrite "ko";
        ENDIF
        TPWrite "NumToStr";
        TPWrite NumToStr(val, 1);
        TPWrite "NumToStr";
        TPWrite NumToStr(val, 1, \Exp);
    ENDPROC
ENDMODULE
