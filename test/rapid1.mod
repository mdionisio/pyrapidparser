MODULE syun1
! pippo
    LOCAL ALIAS num pippo;
    ALIAS num pippo1;
    LOCAL RECORD prova
        num usecount;
    ENDRECORD
    CONST prova p1 := [ 100 ];
    VAR prova pp1 := [ 100 ];
    CONST num n1 := p1.usecount;
    CONST num c1:=10;
    CONST num c2:=c1+1;
    VAR num a1:=1;
    CONST num a3{3} := [ 10, 30, 50 ];
    LOCAL VAR num a4:=12;
    VAR num a5 := a3{2};
    VAR string s1:="pippo";
    VAR bool b := TRUE;
    
    PROC TEST1()
    !python:print "test1"
        a5 := 1;
    ENDPROC
    
    PROC TEST2(VAR num p1)
    !python:print "test2"
        a5 := 2;
    ENDPROC
    
    PROC TEST3(bool b1)
    !python:print "test3"
        a5 := 3;
    ENDPROC
    
    PROC TEST4(num p1)
    !python:print "test4"
        a5 := 4;
    ENDPROC
    
    PROC TEST5(VAR num p1, VAR num p2{*})
        VAR num p10 := 1;
        VAR num p11{3} := [ 10, 30, 50 ];
        VAR prova p12 := [ 100 ];
        VAR prova p13{3};
        !python:print "test5"
        !python:print "p1"
        !python:print pyrapid.Symbols().GetSymbol("p1").data.Get()
        !python:print "p2 .1"
        !python:print pyrapid.Symbols().GetSymbol("p2").data.GetElem(1).Get()
        !python:print "p2 .2"
        !python:print pyrapid.Symbols().GetSymbol("p2").data.GetElem(2).Get()
        !python:print "p2 .3"
        !python:print pyrapid.Symbols().GetSymbol("p2").data.GetElem(3).Get()
        p2{3} := p2{3} +1;
        p2{2} := p2{2} +1;
        p2{1} := p2{1} +1;
    ENDPROC
    
    PROC TEST6(num p1, num p2{*})
        VAR num p10 := 1;
        VAR num p11{3} := [ 10, 30, 50 ];
        VAR prova p12 := [ 100 ];
        VAR prova p13{3};
        !python:print "test6"
        !python:print "p1"
        !python:print pyrapid.Symbols().GetSymbol("p1").data.Get()
        !python:print "p2 .1"
        !python:print pyrapid.Symbols().GetSymbol("p2").data.GetElem(1).Get()
        !python:print "p2 .2"
        !python:print pyrapid.Symbols().GetSymbol("p2").data.GetElem(2).Get()
        !python:print "p2 .3"
        !python:print pyrapid.Symbols().GetSymbol("p2").data.GetElem(3).Get()
        p2{3} := p2{3} +1;
        p2{2} := p2{2} +1;
        p2{1} := p2{1} +1;
    ENDPROC
    
    PROC TEST7(VAR prova p1)
        !python:print "test7"
        !python:print "p1"
        !python:print pyrapid.Symbols().GetSymbol("p1").data.GetElem("usecount").Get()
        p1.usecount := 1;
    ENDPROC
    
    PROC TEST8(prova p1)
        !python:print "test8"
        !python:print "p1"
        !python:print pyrapid.Symbols().GetSymbol("p1").data.GetElem("usecount").Get()
        p1.usecount := 1;
    ENDPROC
    
    
    
    PROC PIPPO(VAR num p1, VAR num p2{*})
        VAR num p10 := 1;
        VAR num p11{3} := [ 10, 30, 50 ];
        VAR prova p12 := [ 100 ];
        VAR prova p13{3};
        !python:print "pippo"
        !python:print "p1"
        !python:print pyrapid.Symbols().GetSymbol("p1").data.Get()
        !python:print "p2 .1"
        !python:print pyrapid.Symbols().GetSymbol("p2").data.GetElem(1).Get()
        !python:print "p2 .2"
        !python:print pyrapid.Symbols().GetSymbol("p2").data.GetElem(2).Get()
        !python:print "p2 .3"
        !python:print pyrapid.Symbols().GetSymbol("p2").data.GetElem(3).Get()
        p2{3} := p2{3} +1;
        p2{2} := p2{2} +1;
        p2{1} := p2{1} +1;
        
        p1 := 2;
        a5 := 1;
        a5 := 1+2*3;
        a5 := (1+2)*3;
        !python:print pyrapid.Symbols().GetSymbol("a5").data.Get()
        p11{2} := a5;
        p12.usecount := p11{2};
        p13{1}.usecount :=p12.usecount;
        p13{2}.usecount :=p13{1}.usecount;
        IF b THEN
            a5 := 2;
        ELSEIF B = FALSE THEN
            a6 := 3;
        ELSE
            a5 := 6;
        ENDIF
        
        IF b = TRUE THEN
            a5 := 2;
        ENDIF
        
        !python:print pyrapid.Symbols().GetSymbol("a5").data.Get()
        TEST1;
        !python:print pyrapid.Symbols().GetSymbol("a5").data.Get()
        TEST2 a5;
        !python:print pyrapid.Symbols().GetSymbol("a5").data.Get()
        TEST3 TRUE;
        !python:print pyrapid.Symbols().GetSymbol("a5").data.Get()
        TEST4 a5;
        !python:print pyrapid.Symbols().GetSymbol("a5").data.Get()
    ENDPROC
    
    FUNC num FUNC1()
        VAR num i:=1;
        WHILE (i < 10) DO
            !python:print "in while"
            !python:print pyrapid.Symbols().GetSymbol("i").data.Get()
            i := i + 1;
        ENDWHILE
        RETURN 1;
    ENDFUNC
    
    FUNC num FUNC2(num a)
        VAR num i;
        FOR i FROM 1 TO a STEP 1 DO
            !python:print "in for"
            !python:print pyrapid.Symbols().GetSymbol("i").data.Get()
            !python:print pyrapid.Symbols().GetSymbol("a").data.Get()
            !python:print "--"
        ENDFOR
        RETURN a;
    ENDFUNC
    
    PROC MAINPROC()
    !python:print "main"
        VAR num pnum := 1;
        VAR num pvec{3} := [ 11, 21, 31 ];
        !python:print "pnum"
        !python:print pyrapid.Symbols().GetSymbol("pnum").data.Get()
        
        pnum := FUNC1();
        !python:print "pnum after func1"
        !python:print pyrapid.Symbols().GetSymbol("pnum").data.Get()
        pnum := FUNC2(2);
        !python:print "pnum after func2"
        !python:print pyrapid.Symbols().GetSymbol("pnum").data.Get()
        
        TEST6 1, [1, 2, 3];
        
        TEST5 pnum, pvec;
        !python:print "pnum"
        !python:print pyrapid.Symbols().GetSymbol("pnum").data.Get()
        !python:print "pvec .1"
        !python:print pyrapid.Symbols().GetSymbol("pvec").data.GetElem(1).Get()
        !python:print "pvec .2"
        !python:print pyrapid.Symbols().GetSymbol("pvec").data.GetElem(2).Get()
        !python:print "pvec .3"
        !python:print pyrapid.Symbols().GetSymbol("pvec").data.GetElem(3).Get()
        
        TEST6 pnum, pvec;
        !python:print "pnum"
        !python:print pyrapid.Symbols().GetSymbol("pnum").data.Get()
        !python:print "pvec .1"
        !python:print pyrapid.Symbols().GetSymbol("pvec").data.GetElem(1).Get()
        !python:print "pvec .2"
        !python:print pyrapid.Symbols().GetSymbol("pvec").data.GetElem(2).Get()
        !python:print "pvec .3"
        !python:print pyrapid.Symbols().GetSymbol("pvec").data.GetElem(3).Get()
        
        TEST8 pp1;
        !python:print "pp1"
        !python:print pyrapid.Symbols().GetSymbol("pp1").data.GetElem("usecount").Get()
        
        TEST7 pp1;
        !python:print "pp1"
        !python:print pyrapid.Symbols().GetSymbol("pp1").data.GetElem("usecount").Get()
        
        PIPPO pnum, pvec;
        !python:print "pnum"
        !python:print pyrapid.Symbols().GetSymbol("pnum").data.Get()
        !python:print "pvec .1"
        !python:print pyrapid.Symbols().GetSymbol("pvec").data.GetElem(1).Get()
        !python:print "pvec .2"
        !python:print pyrapid.Symbols().GetSymbol("pvec").data.GetElem(2).Get()
        !python:print "pvec .3"
        !python:print pyrapid.Symbols().GetSymbol("pvec").data.GetElem(3).Get()
        
        
        TEST pnum
        CASE 1,2,3 :
        !python:print "test 1 2 3"
        CASE 4 :
        !python:print "test 4"
        DEFAULT :
        !python:print "test default"
        ENDTEST

    ENDPROC
ENDMODULE
