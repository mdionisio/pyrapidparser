MODULE syun1(SYSMODULE)
! my comment
RECORD pippo
 num numero;
 string string;
ENDRECORD
ALIAS num another_num;
LOCAL ALIAS num another_num1;
VAR pippo p1;
VAR num p2 := p1.numero;
VAR num p3 := p2;
VAR num p4{3} := [ 1.2, p1.numero, p3  ] ;
VAR num p5 := func();
VAR num p6 := func(1);
VAR num p7 := func(1, p6);
VAR num p7 := func(par1 := 1);
VAR num p8 := func(\par1);
VAR num p9 := func(\par1 := 2);
VAR num p10 := func(\par1 ? a);
PERS pippo p11;
CONST pippo p12;
PROC ppippo()
VAR num local_p1 := 1;
local_p1 := 3;
ENDPROC
PROC ppippo1(VAR num p1)
VAR num p:=1;
ppippo 2;
IF p1=2 THEN
p := 1;
ELSEIF p1=3 THEN
p := 2;
ELSE
p := 0;
ENDIF
RETURN;
ENDPROC
ENDMODULE
