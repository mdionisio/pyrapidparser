MODULE interrupts
    ! executed by test_rapid2py.py (interrupts.cfg): traps of signal and timer interrupts
    VAR intnum alarm;
    VAR intnum tick;
    VAR num alarms := 0;
    VAR num ticks := 0;
    VAR bool late := FALSE;
    TRAP on_alarm
        alarms := alarms + 1;
        TPWrite "alarm" \Num:=alarms;
    ENDTRAP
    TRAP on_tick
        ticks := ticks + 1;
        TPWrite "tick" \Num:=ticks;
    ENDTRAP
    PROC main()
        CONNECT alarm WITH on_alarm;
        ISignalDI diAlarm, 1, alarm;
        CONNECT tick WITH on_tick;
        ITimer 0.2, tick;
        ! the trap runs while the program waits
        WaitTime 0.7;
        TPWrite "ticks after 0.7 s " \Num:=ticks;
        IDelete tick;
        ! the trap of the signal runs between two statements
        !python:pyrapid.IO.set("diAlarm", 1)
        TPWrite "after the signal";
        !python:pyrapid.IO.set("diAlarm", 0)
        !python:pyrapid.IO.set("diAlarm", 1)
        TPWrite "second alarm";
        ! no interrupt while ISleep
        ISleep alarm;
        !python:pyrapid.IO.set("diAlarm", 0)
        !python:pyrapid.IO.set("diAlarm", 1)
        TPWrite "asleep";
        IWatch alarm;
        !python:pyrapid.IO.set("diAlarm", 0)
        !python:pyrapid.IO.set("diAlarm", 1)
        TPWrite "watching";
        ! IDisable delays the traps until IEnable
        IDisable;
        !python:pyrapid.IO.set("diAlarm", 0)
        !python:pyrapid.IO.set("diAlarm", 1)
        TPWrite "disabled";
        IEnable;
        TPWrite "enabled";
        ! a trap interrupts a wait
        !python:pyrapid.IO.set("diAlarm", 0)
        CONNECT tick WITH on_tick;
        ITimer \Single, 0.05, tick;
        WaitDI diAlarm, 1 \MaxTime:=0.2 \TimeFlag:=late;
        TPWrite "wait ended " \Bool:=late;
        TPWrite "INTNO set " \Bool:=(INTNO = tick);
    ENDPROC
ENDMODULE
