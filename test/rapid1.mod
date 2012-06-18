MODULE syun1
! pippo
    LOCAL ALIAS num pippo;
    ALIAS num pippo1;
    LOCAL RECORD prova
        num usecount;
    ENDRECORD
    CONST prova p1 := [ 100 ];
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
        a5 := 100;
    ENDPROC
    
    PROC TEST2(VAR num p1)
        a5 := 100;
    ENDPROC
    
    PROC TEST3(bool b1)
        a5 := 100;
    ENDPROC
    
    PROC TEST4(num p1)
        a5 := 100;
    ENDPROC
    
    PROC PIPPO(VAR num p1, VAR num p2{*})
        VAR num p10 := 1;
        VAR num p11{3} := [ 10, 30, 50 ];
        VAR prova p12 := [ 100 ];
        VAR prova p13{3};
        
        a5 := 1;
        a5 := 1+2*3;
        a5 := (1+2)*3;
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
        
        TEST1;
        TEST2 a5;
        TEST4 a5;
        TEST3 TRUE;
    ENDPROC
ENDMODULE
