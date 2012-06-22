MODULE syun1
    PROC MAIN()
        VAR num val:= 1;
        TPWrite "TPWrite", \Num:=val;
        
        TPWrite "ValToStr";
        TPWrite ValToStr(val);
        TPWrite "NumToStr";
        TPWrite NumToStr(val, 1);
        TPWrite "NumToStr";
        TPWrite NumToStr(val, 1, \Exp);
    ENDPROC
ENDMODULE
