


MODULE MAINTASK
!python rapid2py.py -i Pallettizer/schema.mod -s -f schema.py
!python rapid2py.py -e MAIN -i Pallettizer/settings.mod -i Pallettizer/gloadschema.mod -i Pallettizer/schema.mod -i Pallettizer/maintask.mod -f pallettizer.py -r
!
!

    ! this type contain the action that has to be done
    ! if nProdLine=-1 or nQueue=-1 or nStep=-1 means nothing to do
    LOCAL RECORD todoType
        num nProdLine;
        num nQueue;
        num nStep;
    ENDRECORD


    !  GLOBAL VARIABLE
    VAR bool bContinueExecution := TRUE;
    
    !  GLOBAL VARIABLE USED IN AUTOMATIC
    
    VAR bool A_bForceLoadSchemas := FALSE;
    
    !  GLOBAL VARIABLE USED IN MANUAL
    
    
    FUNC bool HasToRun()
        RETURN bContinueExecution;
    ENDFUNC
    
    FUNC bool IsAutomatic()
        RETURN TRUE;
    ENDFUNC
    
    ! robot go in parking position and waith to arrive there
    PROC GoHome()
        TPWrite "GO TO PARK";
    ENDPROC
    
    ! This function return the action that has to be done
    !
    FUNC todoType AThereIsSomethingToDo()
        VAR todoType res;
        res.nProdLine := -1;
        res.nQueue := -1;
        res.nStep := -1;
        RETURN res;
    ENDFUNC
    
    ! This function return True if there is almost one line running
    !
    FUNC bool AThereIsSomethingRunning()
        RETURN TRUE;
    ENDFUNC
    
    PROC ASetLoadSchema()
        A_bForceLoadSchemas := TRUE;
    ENDPROC
    
    PROC AResetLoadSchema()
        A_bForceLoadSchemas := FALSE;
    ENDPROC
    
    FUNC bool ASchemasHasToBeLoaded()
        RETURN A_bForceLoadSchemas;
    ENDFUNC
    
    
    
    PROC ALoadSchema( num nsch \switch DisableOnError)
        UnLoad FilePath:="schema.mod";
        Load FilePath:="schema.mod";
        !INIT_SCHEMA;
        !TPWrite "TEST INIT SCHEMA", \Bool:=SchemaType_Valid;
        UnLoad FilePath:="schema.mod";
        ! todo aggiungere gestione errore per UnLoad
        ! todo aggiungere gestione errore per Load
    ENDPROC
    
    PROC AResetAllSchemas()
        LOCAL VAR num i;
        
        TPWrite "RESET ALL SCHEMAS";
        
        FOR i FROM 1 TO nPLACELINE STEP 1 DO
            TPWrite "Stop Schema ", \Num:=i;
            r_SchemaType_Valid{i} := FALSE;
            ! todo delete schema
        ENDFOR
        ! todo gestione errore del delete schema
    ENDPROC
    
    PROC ALoadSchemas()
        LOCAL VAR num i;
        
        TPWrite "LOAD/RELOAD ALL SCHEMAS";
        
        FOR i FROM 1 TO nPLACELINE STEP 1 DO
            ALoadSchema i;
        ENDFOR
        
        TPWrite "END LOAD/RELOAD ALL SCHEMAS";
        
    ENDPROC
    
    ! This is the task that make the real job
    !
    PROC MAIN_AUTOMATIC()
        CONST num nDescheduleTime := 1.0;
        LOCAL VAR bool bAutomaticContineExecution := TRUE;
        LOCAL VAR clock cTimeDoNothing;
        LOCAL VAR bool bDoneSomething;
        LOCAL VAR todoType ActionToDo;
        
        ClkReset cTimeDoNothing;
        ClkStart cTimeDoNothing;
        
        TPWrite "START AUTOMATIC TASK";
        
        GoHome;                     ! go to park
        ASetLoadSchema;        ! set to load schema when it will be possible
        AResetAllSchemas;        ! stop all schemas
        
        WHILE bAutomaticContineExecution DO
            bDoneSomething := FALSE;
        
            ! check action to do
            IF ASchemasHasToBeLoaded() THEN
                ClkReset cTimeDoNothing;
                AResetLoadSchema;
                ALoadSchemas; ! load or reload all the schemas
                bDoneSomething := TRUE;
            ENDIF
            
            ActionToDo := AThereIsSomethingToDo();
            !if (ActionToDo.nProdLine!=-1) AND (ActionToDo.nQueue!=-1) AND (ActionToDo.nStep!=-1) THEN
                !TPWrite ("DO ACTION ON LINE "+NumToStr(ActionToDo.nProdLine) + " QUEUE "+NumToStr(ActionToDo.nQueue) + " STEP " + NumToStr(ActionToDo.nStep));
                !bDoneSomething := TRUE;
            !ENDIF
            
            IF bDoneSomething=FALSE THEN
                TPWrite "Nothing to do";
                IF ClkRead(cTimeDoNothing)>5 THEN           ! if there is nothing to do for more than 5 seconds park the robot
                    ClkReset cTimeDoNothing;
                    GoHome;                     ! go to park
                ENDIF
                WaitTime Time:=nDescheduleTime;         !deschedule process
            ENDIF
        
            bAutomaticContineExecution := AThereIsSomethingRunning();
        ENDWHILE
        
        
        TPWrite "END AUTOMATIC TASK";
    ENDPROC
    
    ! this is the test loop
    !
    PROC MAIN_MANUAL()
        TPWrite "START TEST";
        !
        ! perform test
        !
        TPWrite "END TEST";
    ENDPROC
    
    ! MAIN PROGRAM
    ! this has to be configured to work in the main task as a single loop
    PROC MAIN()
        ! loop foreever
        WHILE HasToRun() DO
        
            IF IsAutomatic() THEN
                ! if the system is in automatic 
                ! means that the palletizer loop is working
                MAIN_AUTOMATIC ;
            ELSE
                ! if the system is in manual 
                ! means that the test loop is working
                MAIN_MANUAL ;
            ENDIF
            
            ! wait to avoit to loop too quick and to be sure that
            ! the main will be stopped with the robot velocity = 0
            WaitTime \InPos, 1;         
            
        ENDWHILE
    ENDPROC
    
ENDMODULE
