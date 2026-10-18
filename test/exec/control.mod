MODULE control
    ! executed by test_rapid2py.py with standard.sys: IF, TEST, WHILE, recursion,
    ! RETURN and ExitCycle (kernel manual 4)
    VAR num total := 0;
    PROC show(string label, num value)
        TPWrite label \Num:=value;
    ENDPROC
    FUNC string size(num x)
        IF x < 0 THEN
            RETURN "negative";
        ELSEIF x = 0 THEN
            RETURN "zero";
        ELSEIF x < 10 THEN
            RETURN "small";
        ELSE
            RETURN "large";
        ENDIF
    ENDFUNC
    FUNC string kind(num x)
        TEST x
        CASE 1, 3, 5:
            RETURN "odd";
        CASE 2, 4:
            RETURN "even";
        DEFAULT:
            RETURN "other";
        ENDTEST
    ENDFUNC
    FUNC num factorial(num n)
        IF n <= 1 RETURN 1;
        RETURN n * factorial(n - 1);
    ENDFUNC
    PROC main()
        TPWrite size(-5) + " " + size(0) + " " + size(7) + " " + size(70);
        TPWrite kind(1) + " " + kind(4) + " " + kind(9);
        TEST "b"
        CASE "a":
            TPWrite "case a";
        CASE "b", "c":
            TPWrite "case b or c";
        ENDTEST
        ! the loop ends when the condition is false at the test
        WHILE total < 100 DO
            total := total * 2 + 1;
        ENDWHILE
        show "while ", total;
        ! the condition is false from the start: the body never runs
        WHILE FALSE DO
            TPWrite "never";
        ENDWHILE
        show "factorial 6 ", factorial(6);
        ! logical operators: AND, OR, XOR, NOT
        TPWrite "logic " \Bool:=((total > 100 AND total < 200) OR FALSE);
        TPWrite "xor " \Bool:=(TRUE XOR TRUE);
        TPWrite "not " \Bool:=NOT (total = 127);
        show "div mod ", (17 DIV 5) * 10 + (17 MOD 5);
        ExitCycle;
        TPWrite "after ExitCycle";
    ENDPROC
ENDMODULE
