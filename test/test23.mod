MODULE syun1
    FUNC num deg2rad(num deg)
        RETURN deg * pi / 180;
    ENDFUNC

    LOCAL FUNC num rad2deg(num rad)
        RETURN rad * 180 / pi;
    ENDFUNC

    FUNC robjoint deg2rad_robjoint(robjoint deg)
        VAR robjoint rad;
        rad.rax_1 := deg2rad(deg.rax_1);
        rad.rax_2 := deg2rad(deg.rax_2);
        rad.rax_3 := deg2rad(deg.rax_3);
        rad.rax_4 := deg2rad(deg.rax_4);
        rad.rax_5 := deg2rad(deg.rax_5);
        rad.rax_6 := deg2rad(deg.rax_6);

        RETURN rad;
    ENDFUNC

    PROC main()

    ENDPROC
ENDMODULE