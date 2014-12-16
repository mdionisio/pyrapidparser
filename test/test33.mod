MODULE syun1
!./rapid2py.py -e main -i ./test/test33.mod -r -s
    
    
    LOCAL FUNC num LT1()
        RETURN 1;
    ENDFUNC
    
    LOCAL PROC LP1()
        
    ENDPROC


    PROC main()
    
      VAR num app;
      LOCAL VAR num app1;
      app := LT1();
      app1 := LT1();
      LP1;

    ENDPROC
ENDMODULE