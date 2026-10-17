MODULE errrecovery
    ! error recovery point with long jump (RAPID kernel manual, 7.2)
    CONST errnum escape := 56;
    VAR num counter := 0;
    PROC main()
        routine1;
    ERROR (56, ERR_DIVZERO)
        counter := counter + 1;
        RETRY;
    ENDPROC
    PROC routine1()
        RAISE escape;
    ERROR
        RAISE;
    ENDPROC
ENDMODULE
