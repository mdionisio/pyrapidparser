


MODULE MAINTASK
!python rapid2py.py -i Pallettizer/schema.mod -s -f schema.py
!python rapid2py.py -e MAIN -i Pallettizer/settings.mod -i Pallettizer/gloadschema.mod -i Pallettizer/schema.mod -i Pallettizer/maintask.mod -f pallettizer.py -r
!
!


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
    
    ! This function has to return TRUE only if there is almost one production line on
    !
    FUNC bool AThereIsSomethingToDo()
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
    
    PROC LoadSchema( num nsch )
        UnLoad FilePath:="schema.mod";
        Load FilePath:="schema.mod";
        INIT_SCHEMA;
        !TPWrite "TEST INIT SCHEMA", \Bool:=SchemaType_Valid;
        UnLoad FilePath:="schema.mod";
        ! todo aggiungere gestione errore per UnLoad
    ENDPROC
    
    PROC ALoadSchemas()
        LOCAL VAR num i;
        
        TPWrite "LOAD/RELOAD ALL SCHEMAS";
        
        FOR i FROM 1 TO nPLACELINE STEP 1 DO
            LoadSchema i;
        ENDFOR
        
        TPWrite "END LOAD/RELOAD ALL SCHEMAS";
        
    ENDPROC
    
    ! This is the task that make the real job
    !
    PROC MAIN_AUTOMATIC()
        CONST num nDescheduleTime := 1.0;
        LOCAL VAR bool bAutomaticContineExecution := TRUE;
        LOCAL VAR clock cTimeDoNothing;
        ClkReset cTimeDoNothing;
        ClkStart cTimeDoNothing;
        
        TPWrite "START AUTOMATIC TASK";
        
        GoHome;                     ! go to park
        ASetLoadSchema;         ! set to load schema when it will be possible
        
        WHILE bAutomaticContineExecution DO
        
            ! check action to do
            IF ASchemasHasToBeLoaded() THEN
                ClkReset cTimeDoNothing;
                AResetLoadSchema;
                ALoadSchemas; ! load or reload all the schemas
            ELSE
                TPWrite "Nothing to do";
                IF ClkRead(cTimeDoNothing)>5 THEN           ! if there is nothing to do for more than 5 seconds park the robot
                    ClkReset cTimeDoNothing;
                    GoHome;                     ! go to park
                ENDIF
                WaitTime Time:=nDescheduleTime;         !deschedule process
            ENDIF
        
            bAutomaticContineExecution := AThereIsSomethingToDo();
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
