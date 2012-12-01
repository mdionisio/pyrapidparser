MODULE test
    
    PROC client()
        VAR num found;
        found := StrMatch("Robotics",1,"bo");
        TPWrite "found:", \Num:=found;
    ENDPROC
    
ENDMODULE