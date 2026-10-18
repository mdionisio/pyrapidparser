MODULE records
    ! executed by test_rapid2py.py: assignment of records copies the value
    CONST pos origin := [1, 2, 3];
    VAR pos a := [1, 2, 3];
    VAR pos b;
    VAR pose p1 := [[1, 2, 3], [1, 0, 0, 0]];
    VAR pose p2;
    VAR num ax;
    ! an array of records initialized with an aggregate
    CONST pos points{2} := [[1, 2, 3], [4, 5, 6]];
    VAR num bx;
    PROC main()
        b := a;
        b.x := 10;
        ax := a.x;
        bx := b.x;
        !python:print("pos", pyrapid.Symbols().GetSymbol("ax").data.Get(), pyrapid.Symbols().GetSymbol("bx").data.Get())
        p2 := p1;
        p2.trans.y := 20;
        ax := p1.trans.y;
        bx := p2.trans.y;
        !python:print("pose", pyrapid.Symbols().GetSymbol("ax").data.Get(), pyrapid.Symbols().GetSymbol("bx").data.Get())
        b := origin;
        b.z := 30;
        ax := origin.z;
        bx := b.z;
        !python:print("const", pyrapid.Symbols().GetSymbol("ax").data.Get(), pyrapid.Symbols().GetSymbol("bx").data.Get())
        ax := points{2}.y;
        bx := points{1}.z;
        !python:print("array", pyrapid.Symbols().GetSymbol("ax").data.Get(), pyrapid.Symbols().GetSymbol("bx").data.Get())
    ENDPROC
ENDMODULE
