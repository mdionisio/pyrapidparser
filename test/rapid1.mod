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
        TPWrite "test1";
        a5 := 1;
    ENDPROC
    
    PROC TEST2(VAR num p1)
        TPWrite "test2";
        a5 := 2;
    ENDPROC
    
    PROC TEST3(bool b1)
        TPWrite "test3";
        a5 := 3;
    ENDPROC
    
    PROC TEST4(num p1)
        TPWrite "test4";
        a5 := 4;
    ENDPROC
    
    PROC TEST5(VAR num p1, VAR num p2{*})
        VAR num p10 := 1;
        VAR num p11{3} := [ 10, 30, 50 ];
        VAR prova p12 := [ 100 ];
        VAR prova p13{3};
        TPWrite "test5";
        TPWrite "p1",\Num:=p1;
        TPWrite "p2.1",\Num:=p2{1};
        TPWrite "p2.2",\Num:=p2{2};
        TPWrite "p2.3",\Num:=p2{3};
        
        p2{3} := p2{3} +1;
        p2{2} := p2{2} +1;
        p2{1} := p2{1} +1;
    ENDPROC
    
    PROC TEST6(num p1, num p2{*})
        VAR num p10 := 1;
        VAR num p11{3} := [ 10, 30, 50 ];
        VAR prova p12 := [ 100 ];
        VAR prova p13{3};
        TPWrite "test6";
        TPWrite "p1",\Num:=p1;
        TPWrite "p2.1",\Num:=p2{1};
        TPWrite "p2.2",\Num:=p2{2};
        TPWrite "p2.3",\Num:=p2{3};
        p2{3} := p2{3} +1;
        p2{2} := p2{2} +1;
        p2{1} := p2{1} +1;
    ENDPROC
    
    PROC TEST7(VAR prova p1)
        TPWrite "test7";
        TPWrite "p1",\Num:=p1.usecount;
        p1.usecount := 1;
    ENDPROC
    
    PROC TEST8(prova p1)
        TPWrite "test8";
        TPWrite "p1",\Num:=p1.usecount;
        p1.usecount := 1;
    ENDPROC
    
    
    
    PROC PIPPO(VAR num p1, VAR num p2{*})
        VAR num p10 := 1;
        VAR num p11{3} := [ 10, 30, 50 ];
        VAR prova p12 := [ 100 ];
        VAR prova p13{3};
        
        p10 := Dim(p2, 1);
        TPWrite "PIPPO";
        TPWrite "size of p2",\Num:=p10;
        
        TPWrite "p1",\Num:=p1;
        TPWrite "p2.1",\Num:=p2{1};
        TPWrite "p2.2",\Num:=p2{2};
        TPWrite "p2.3",\Num:=p2{3};
        
        p2{3} := p2{3} +1;
        p2{2} := p2{2} +1;
        p2{1} := p2{1} +1;
        
        p1 := 2;
        a5 := 1;
        a5 := 1+2*3;
        a5 := (1+2)*3;
        TPWrite "a5",\Num:=a5;
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
        
        TPWrite "a5",\Num:=a5;
        TEST1;
        TPWrite "a5",\Num:=a5;
        TEST2 a5;
        TPWrite "a5",\Num:=a5;
        TEST3 TRUE;
        TPWrite "a5",\Num:=a5;
        TEST4 a5;
        TPWrite "a5",\Num:=a5;
    ENDPROC
    
    FUNC num FUNC1()
        VAR num i:=1;
        WHILE (i < 10) DO
            TPWrite "in while",\Num:=i;
            i := i + 1;
        ENDWHILE
        RETURN 1;
    ENDFUNC
    
    FUNC num FUNC2(num a)
        VAR bool b;
        VAR num i;
        
        b:=Present(a);
        TPWrite "test preset",\Bool:=b;
        TPWrite "for limit",\Num:=a;
        FOR i FROM 1 TO a STEP 1 DO
            TPWrite "in for",\Num:=i;
        ENDFOR
        RETURN a;
    ENDFUNC
    
    
    PROC MAINPROC()
    !python:print "main"
        VAR num pnum := 1;
        VAR num pvec{3} := [ 11, 21, 31 ];
        
        VAR pos pos1 := [1,2,3];
        TPWrite "pos1.x", \Num:=pos1.x;
        TPWrite "pos1.y", \Num:=pos1.y;
        TPWrite "pos1.z", \Num:=pos1.z;
        pos1.x := 100;
        TPWrite "pos1.x", \Num:=pos1.x;
        
        PIPPO pnum, pvec;
        
        TPWrite "pnum", \Num:=pnum;
        
        pnum := FUNC1();
        TPWrite "pnum", \Num:=pnum;
        pnum := FUNC2(2);
        TPWrite "pnum", \Num:=pnum;
        
        TEST6 1, [1, 2, 3];
        
        TEST5 pnum, pvec;
        TPWrite "pnum", \Num:=pnum;
        TPWrite "pvec.1", \Num:=pvec{1};
        TPWrite "pvec.2", \Num:=pvec{2};
        TPWrite "pvec.3", \Num:=pvec{3};
        
        TEST6 pnum, pvec;
        TPWrite "pnum", \Num:=pnum;
        TPWrite "pvec.1", \Num:=pvec{1};
        TPWrite "pvec.2", \Num:=pvec{2};
        TPWrite "pvec.3", \Num:=pvec{3};
        
        TEST8 pp1;
        TPWrite "pp1", \Num:=pp1.usecount;
        
        TEST7 pp1;
        TPWrite "pp1", \Num:=pp1.usecount;
        
        PIPPO pnum, pvec;
        TPWrite "pnum", \Num:=pnum;
        TPWrite "pvec.1", \Num:=pvec{1};
        TPWrite "pvec.2", \Num:=pvec{2};
        TPWrite "pvec.3", \Num:=pvec{3};
        
        
        TEST pnum
        CASE 1,2,3 :
        !python:print "test 1 2 3"
        CASE 4 :
        !python:print "test 4"
        DEFAULT :
        !python:print "test default"
        ENDTEST
        
        TPWrite "WaitTime 10";
        !!WaitTime 10;
        TPWrite "WaitTime Time:=10";
        !WaitTime Time:=10;
        TPWrite "WaitTime \InPos, 10";
        !WaitTime \InPos, 10;
        TPWrite "WaitTime \InPos, 10";
        !WaitTime \InPos, Time:=10;
        
        TPWrite "PROVAAAAAAAAAAAAAAAAAAAAAA";
        TPWrite "PROVAAAAAAAAAAAAAAAAAAAAAA", \Pos:=pos1;

    ENDPROC
ENDMODULE
