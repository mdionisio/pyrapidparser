MODULE test
    LOCAL PROC client1(num pippo)
        TPWrite "pippo:", \Num:=pippo;
        RAISE ERR_MODULE;
    ENDPROC
    
    LOCAL PROC client()
        client1 5;
        ERROR
            TPWrite "Error:", \Num:=ERRNO;
            RAISE;
        UNDO
            TPWrite "Undo";
    ENDPROC
    
ENDMODULE