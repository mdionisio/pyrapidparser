MODULE syun1
!./rapid2py.py -e main -i ./test/test32.mod -r -s
    PROC print ( string String \ num Num | bool Bool | pos Pos | orient Orient )
        !python:val = pyrapid.Symbols().GetSymbol("String").data.Get()
        
        IF Present(Num) THEN
            !python:val = val + " Num: " + str(pyrapid.Symbols().GetSymbol("Num").data.Get())
        ELSEIF Present(Bool) THEN
            !python:val = val + " Bool: " + str(pyrapid.Symbols().GetSymbol("Bool").data.Get())
        ELSEIF Present(Pos) THEN
            !python:val = val + " Pos: " + ",".join([ str(pyrapid.Symbols().GetSymbol("Pos").data.GetElem("x").Get()), 
            !python:                                 str(pyrapid.Symbols().GetSymbol("Pos").data.GetElem("y").Get()), 
            !python:                                 str(pyrapid.Symbols().GetSymbol("Pos").data.GetElem("z").Get())])
        ELSEIF Present(Orient) THEN
            !python:val = val + " Orient: " + ",".join([ str(pyrapid.Symbols().GetSymbol("Orient").data.GetElem("q1").Get()), 
            !python:                                    str(pyrapid.Symbols().GetSymbol("Orient").data.GetElem("q2").Get()), 
            !python:                                    str(pyrapid.Symbols().GetSymbol("Orient").data.GetElem("q3").Get()), 
            !python:                                    str(pyrapid.Symbols().GetSymbol("Orient").data.GetElem("q4").Get())])
        ENDIF
        !python:print( "'"+val+"'" )
    ENDPROC
    
    FUNC num T1()
        print "T1";
        RETURN 1;
    ENDFUNC
    
    LOCAL FUNC num LT1()
        print "LOCAL T1";
        RETURN 1;
    ENDFUNC


    PROC main()
    
      VAR num app;
      app := T1();
      app := LT1();

    ENDPROC
ENDMODULE