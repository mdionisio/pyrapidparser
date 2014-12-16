MODULE syun1(SYSMODULE)

PERS string cnstNoStepIn := "ohno";

PERS speeddata cur_vel := [5, 500, 5000, 1000];
PERS zonedata cur_zone := z1;
PERS tooldata hotwirez := [TRUE,[[0,0,0],[1,0,0,0]],[0.1,[0,0,0.001],[1,0,0,0],0,0,0]];

! shell name: shell_000
PROC shell_000( string strNoStepIn )
    ! <<< group name: grouped_faces_000 >>>
    ! ruled surface 001
    MoveL [[ -1484.0, -1483.0, 973.0 ],[ 0.011458, 0.707014, -0.707014, 0.011458 ],[-2, 0, -3, 0],[ 9E+09,9E+09,9E+09,9E+09,9E+09,9E+09 ]],cur_vel, cur_zone, hotwirez;
    ! ruled surface 003
ENDPROC

PROC run()
    ConfJ \Off;
    ConfL \Off;
    shell_000 cnstNoStepIn;
    ConfJ \On;
    ConfL \On;
ENDPROC

PROC main()
cur_zone := z1;
    ! run the toolpath
    run;
ENDPROC

ENDMODULE