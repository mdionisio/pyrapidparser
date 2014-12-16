MODULE syun1(SYSMODULE)
 ! ./rapid2py.py -e init -i ./test/test31.mod -r
 
 PERS tooldata gripper := [TRUE,[[0,0,0],[1,0,0,0]],[0.1,[0,0,0.001],[1,0,0,0],0,0,0]];
    
 PROC init()
    VAR robtarget r1 := [[ -1484.0, -1483.0, 973.0 ],[ 0.011458, 0.707014, -0.707014, 0.011458 ],[-2, 0, -3, 0],[ 9E+09,9E+09,9E+09,9E+09,9E+09,9E+09 ]];
    MoveL ToPoint:=r1, Speed:=v2000, Zone:=z1, Tool:=gripper ;
    MoveL r1, v2000, z1, gripper;
    MoveL [[ -1484.0, -1483.0, 973.0 ],[ 0.011458, 0.707014, -0.707014, 0.011458 ],[-2, 0, -3, 0],[ 9E+09,9E+09,9E+09,9E+09,9E+09,9E+09 ]], v2000, z1, gripper;
 ENDPROC
ENDMODULE