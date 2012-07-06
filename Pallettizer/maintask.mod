


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
    
    
    FUNC bool CommandCanBeExecuted(todoType command)
        RETURN TRUE;
    ENDFUNC
    
    ! This function return the action that has to be done
    !
    FUNC todoType AThereIsSomethingToDo()
        VAR todoType res;
        VAR num i;
        VAR num j;
        
        FOR i FROM 1 TO nPLACELINE STEP 1 DO
            IF r_SchemaType_Valid{i} THEN
                FOR j FROM 1 TO nQueueForSchema STEP 1 DO
                    
                    res.nProdLine := i;
                    res.nQueue := j;
                    res.nStep := r_SchemaType_RunSteps{i, j};
                    
                    IF CommandCanBeExecuted(res) THEN
                        RETURN res;
                    ENDIF
                    
                    !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
                ENDFOR
            ENDIF
        ENDFOR
        res.nProdLine := -1;
        res.nQueue := -1;
        res.nStep := -1;
        RETURN res;
    ENDFUNC
    
    ! This function return True if there is almost one line running
    !
    FUNC bool AThereIsSomethingRunning()
        VAR num i;
        FOR i FROM 1 TO nPLACELINE STEP 1 DO
            IF r_SchemaType_Valid{i} THEN
                RETURN TRUE;
            ENDIF
        ENDFOR
        RETURN FALSE;
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
    
    
    
    PROC ALoadSchema( num nsch \switch Update)
        VAR num i;
        VAR num j;
        TPWrite "UNLOAD 1";
        UnLoad FilePath:="schema.mod";
        TPWrite "LOAD 1";
        Load FilePath:="schema.mod";
        TPWrite "INIT MODULE";
        %"INIT_SCHEMA"%;
        
        r_SchemaType_Valid{nsch} := SchemaType_Valid;
        IF r_SchemaType_Valid{nsch}=TRUE THEN
            TPWrite "RUNNING SCHEMA:",\Num:=nsch;
            r_ProductType{nsch} := ProductType;
            
            r_GripperType{nsch} := GripperType;
            
            r_TakeLine{nsch} := TakeLine;
            
            FOR j FROM 1 TO nQueueForSchema STEP 1 DO
                r_SchemaType_NSteps{nsch, j} := SchemaType_NSteps{j};
                
                r_SchemaType_RunSteps{nsch, j} := SchemaType_RunSteps{j};
                
                FOR i FROM 1 TO r_SchemaType_NSteps{nsch, j} STEP 1 DO
                    r_ActionType_Name{nsch, j, i} := ActionType_Name{j, i};
                ENDFOR
            ENDFOR
        ENDIF
        
        !TPWrite "TEST INIT SCHEMA", \Bool:=SchemaType_Valid;
        
        TPWrite "UNLOAD 2";
        UnLoad FilePath:="schema.mod";
        
        TPWrite "END ALoadSchema";
        ! todo aggiungere gestione errore per UnLoad
        ! todo aggiungere gestione errore per Load
        
        ERROR
            TPWrite "ERRORE IN ALOADSCHEMA";
            IF ERRNO = ERR_UNLOAD  THEN
                TPWrite "ERRORE UNLOAD";
                TRYNEXT;
            ELSEIF (ERRNO = ERR_REFUNKPRC) OR (ERRNO = ERR_CALLPROC)  THEN
                TPWrite "Errore loading schema";
                SchemaType_Valid := False;
                TRYNEXT;
            ENDIF

    ENDPROC
    
    PROC AResetAllSchemas()
        LOCAL VAR num i;
        LOCAL VAR num j;
        LOCAL VAR num k;
        
        TPWrite "RESET ALL SCHEMAS";
        
        FOR i FROM 1 TO nPLACELINE STEP 1 DO
            TPWrite "Stop Schema ", \Num:=i;
            r_SchemaType_Valid{i} := FALSE;
            
            FOR j FROM 1 TO nQueueForSchema STEP 1 DO
                r_SchemaType_NSteps{i, j} := 0;
                r_SchemaType_RunSteps{i, j} := 0;
                FOR k FROM 1 TO MAX_STEP STEP 1 DO
                    r_ActionType_Name{i, j, k} := "";
                ENDFOR
            ENDFOR
            
            r_ProductType{i} := [0, 0, 0, 0, 0];
            r_GripperType{i} := 0;
            r_TakeLine{i} := 0;
            
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
            IF (ActionToDo.nProdLine<>-1) AND (ActionToDo.nQueue<>-1) AND (ActionToDo.nStep<>-1) THEN
                TPWrite "DO ACTION ON LINE "+NumToStr(ActionToDo.nProdLine,10) + " QUEUE "+NumToStr(ActionToDo.nQueue,10) + " STEP " + NumToStr(ActionToDo.nStep,10);
                bDoneSomething := TRUE;
                
                TPWrite "Do Step:"+r_ActionType_Name{ActionToDo.nProdLine, ActionToDo.nQueue, ActionToDo.nStep};
                
                !go to next step
                
                r_SchemaType_RunSteps{ActionToDo.nProdLine, ActionToDo.nQueue} := ActionToDo.nStep+1;
                IF (r_SchemaType_RunSteps{ActionToDo.nProdLine, ActionToDo.nQueue} > r_SchemaType_NSteps{ActionToDo.nProdLine, ActionToDo.nQueue} ) THEN
                    TPWrite "Go to next pallet for queue:", \Num := ActionToDo.nQueue;
                    r_SchemaType_RunSteps{ActionToDo.nProdLine, ActionToDo.nQueue} := 1;
                ENDIF
            
            ENDIF
            
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
