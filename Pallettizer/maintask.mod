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
    
    LOCAL RECORD TakeProdType
        num x;
        num y;
        num z;
        num rot;
    ENDRECORD
    
    LOCAL RECORD PlateProdType
        num type;
        num x1;
        num acc_x1;
        num y1;
        num acc_y1;
        num z1;
        num acc_z1;
        num rot1;
        num x2;
        num acc_x2;
        num y2;
        num acc_y2;
        num z2;
        num acc_z2;
        num rot2;
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
        !todo
        WaitTime Time:=1;
    ENDPROC
    
    FUNC bool IsPalletExiting(num nProdLine)
        RETURN r_PalletExiting{nProdLine};
    ENDFUNC
    
    PROC SetPalletExiting(num nProdLine)
        r_PalletExiting{nProdLine} := TRUE;
    ENDPROC
    
    PROC ResetPalletExiting(num nProdLine)
        r_PalletExiting{nProdLine} := FALSE;
    ENDPROC
    
    FUNC bool IsTakeProduct(string command, VAR num x, VAR num y, VAR num z, VAR num rot)
        VAR num spacepos;
        VAR string basecommand;
        VAR string tmp;
        VAR PlateProdType prod := [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0];
        CONST string command_to_find := "PlaceProduct";
        
        spacepos := StrFind(command, 1, " ");
        
        IF spacepos = (StrLen(command_to_find)+1) THEN
            basecommand := StrPart(command, 1, StrLen(command_to_find));
            IF basecommand = command_to_find THEN
                tmp := StrPart(command, spacepos+1, StrLen(command)-spacepos-1);
                IF StrToVal(tmp, prod) THEN
                    x := prod.x;
                    y := prod.y;
                    z := prod.z;
                    rot := prod.rot;
                    
                    
                    RETURN TRUE;
                ENDIF
            ENDIF
        ENDIF
        RETURN FALSE;
    ENDFUNC
    
    FUNC bool IsPlaceProduct(string command, VAR num index, VAR num x{*}, VAR num y{*}, VAR num z{*}, VAR num rot{*}, VAR num acc_x{*}, VAR num acc_y{*}, VAR num acc_z{*})
        VAR num spacepos;
        VAR string basecommand;
        VAR string tmp;
        VAR TakeProdType prod := [0, 0, 0, 0];
        CONST string command_to_find := "TakeProduct";
        
        spacepos := StrFind(command, 1, " ");
        
        IF spacepos = (StrLen(command_to_find)+1) THEN
            basecommand := StrPart(command, 1, StrLen(command_to_find));
            IF basecommand = command_to_find THEN
                tmp := StrPart(command, spacepos+1, StrLen(command)-spacepos-1);
                IF StrToVal(tmp, prod) THEN
                    index := prod.type;
                    x{1} := prod.x1;
                    x{2} := prod.x2;
                    
                    y{1} := prod.y1;
                    y{2} := prod.y2;
                    
                    z{1} := prod.z1;
                    z{2} := prod.z2;
                    
                    rot{1} := prod.rot1;
                    rot{2} := prod.rot2;
                    
                    acc_x{1} := prod.acc_x1;
                    acc_x{2} := prod.acc_x2;
                    
                    acc_y{1} := prod.acc_y1;
                    acc_y{2} := prod.acc_y2;
                    
                    acc_z{1} := prod.acc_z1;
                    acc_z{2} := prod.acc_z2;
                    
                    RETURN TRUE;
                ENDIF
            ENDIF
        ENDIF
        RETURN FALSE;
    ENDFUNC
    
    FUNC bool IsOrderProduct(string command, VAR num nprod, VAR num disposition)
        VAR num spacepos;
        VAR string basecommand;
        VAR string tmp;
        VAR num prod{2} := [0, 0];
        CONST string command_to_find := "OrderProd";
        
        spacepos := StrFind(command, 1, " ");
        
        IF spacepos = (StrLen(command_to_find)+1) THEN
            basecommand := StrPart(command, 1, StrLen(command_to_find));
            IF basecommand = command_to_find THEN
                tmp := StrPart(command, spacepos+1, StrLen(command)-spacepos-1);
                IF StrToVal(tmp, prod) THEN
                    nprod := prod{1};
                    disposition := prod{2};
                    RETURN TRUE;
                ENDIF
            ENDIF
        ENDIF
        RETURN FALSE;
    ENDFUNC
    
    FUNC bool IsStartQueue(string command, VAR num queue)
        VAR num spacepos;
        VAR string basecommand;
        VAR string tmp;
        CONST string command_to_find := "StartQueue";
        
        spacepos := StrFind(command, 1, " ");
        
        IF spacepos = (StrLen(command_to_find)+1) THEN
            basecommand := StrPart(command, 1, StrLen(command_to_find));
            IF basecommand = command_to_find THEN
                tmp := StrPart(command, spacepos+1, StrLen(command)-spacepos-1);
                IF StrToVal(tmp, queue) THEN
                    RETURN TRUE;
                ENDIF
            ENDIF
        ENDIF
        RETURN FALSE;
    ENDFUNC
    
    FUNC bool IsStopQueue(string command, VAR num queue)
        VAR num spacepos;
        VAR string basecommand;
        VAR string tmp;
        CONST string command_to_find := "StopQueue";
        
        spacepos := StrFind(command, 1, " ");
        IF spacepos = (StrLen(command_to_find)+1) THEN
            basecommand := StrPart(command, 1, StrLen(command_to_find));
            IF basecommand = command_to_find THEN
                tmp := StrPart(command, spacepos+1, StrLen(command)-spacepos-1);
                IF StrToVal(tmp, queue) THEN
                    RETURN TRUE;
                ENDIF
            ENDIF
        ENDIF
        RETURN FALSE;
    ENDFUNC
    
    
    FUNC bool IsOrderPallet(string command)
        CONST string command_to_find := "OrderPallet";
        
        IF command = command_to_find THEN
            RETURN TRUE;
        ELSE
            RETURN FALSE;
        ENDIF
    ENDFUNC
    
    FUNC bool IsTakePallet(string command)
        CONST string command_to_find := "TakePallet";
        
        IF command = command_to_find THEN
            RETURN TRUE;
        ELSE
            RETURN FALSE;
        ENDIF
    ENDFUNC
    
    FUNC bool IsPlacePallet(string command)
        CONST string command_to_find := "PlacePallet";
        
        IF command = command_to_find THEN
            RETURN TRUE;
        ELSE
            RETURN FALSE;
        ENDIF
    ENDFUNC
    
    FUNC bool IsExitPallet(string command)
        CONST string command_to_find := "ExitPallet";
        
        IF command = command_to_find THEN
            RETURN TRUE;
        ELSE
            RETURN FALSE;
        ENDIF
    ENDFUNC
    
    FUNC bool IsTakeSheet(string command)
        CONST string command_to_find := "TakeSheet";
        
        IF command = command_to_find THEN
            RETURN TRUE;
        ELSE
            RETURN FALSE;
        ENDIF
    ENDFUNC
    
    FUNC bool IsPlaceSheet(string command)
        CONST string command_to_find := "PlaceSheet";
        
        IF command = command_to_find THEN
            RETURN TRUE;
        ELSE
            RETURN FALSE;
        ENDIF
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
        
        ! add backup schema
        
        UnLoad FilePath:="schema.mod";
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
        
        UnLoad FilePath:="schema.mod";
        
        r_QueuePaused{nsch, ORDER_QUEUE} := TRUE;
        r_QueuePaused{nsch, MAIN_QUEUE} := FALSE;

        !add undo wuth restore backup
        
        ERROR
            TPWrite "ERRORE IN ALOADSCHEMA";
            IF ERRNO = ERR_UNLOAD  THEN
                TPWrite "ERRORE UNLOAD";
                TRYNEXT;
            ELSEIF (ERRNO = ERR_REFUNKPRC) OR (ERRNO = ERR_CALLPROC)  THEN
                TPWrite "Errore loading schema";
                SchemaType_Valid := False;
                IF Present(Update) THEN
                    RAISE;
                ELSE
                    TRYNEXT;
                ENDIF
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
                r_QueuePaused{i, j} := FALSE;
                r_SchemaType_NSteps{i, j} := 0;
                r_SchemaType_RunSteps{i, j} := 0;
                FOR k FROM 1 TO MAX_STEP STEP 1 DO
                    r_ActionType_Name{i, j, k} := "";
                ENDFOR
            ENDFOR
            
            r_ProductType{i} := [0, 0, 0, 0, 0];
            r_PalletType{i} := [0, 0, 0, 0, 0];
            r_SheetType{i} := [0, 0, 0, 0, 0];
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
    
    PROC AStartQueue(num nProdLine, num nQueue)
        TPWrite "IsStartQueue on queue:", \Num:=nQueue ;
        r_QueuePaused{nProdLine, nQueue} := FALSE;
    ENDPROC
    
    PROC AStopQueue(num nProdLine, num nQueue)
        TPWrite "IsStopQueue on queue:", \Num:=nQueue ;
        r_QueuePaused{nProdLine, nQueue} := TRUE;
    ENDPROC
    
    PROC AOrderProduct(num nProdLine, num nProd, num Dispo)
        TPWrite "ORDER PRODUCT";
        TPWrite "LINE:",\Num:=nProdLine;
        TPWrite "SRC LINE:",\Num:=r_TakeLine{nProdLine};
        TPWrite "nprod:",\Num:=nProd;
        TPWrite "disp:",\Num:=Dispo;
    ENDPROC
    
    PROC AOrderPallet(num nProdLine)
        TPWrite "ORDER PALLET";
        TPWrite "LINE:",\Num:=nProdLine;
    ENDPROC
    
    PROC ATakePallet(num nProdLine)
        TPWrite "TAKE PALLET";
        TPWrite "LINE:",\Num:=nProdLine;
        !todo
        WaitTime Time:=1;
    ENDPROC
    
    PROC APlacePallet(num nProdLine)
        TPWrite "PLACE PALLET";
        TPWrite "LINE:",\Num:=nProdLine;
        !todo
        WaitTime Time:=1;
    ENDPROC
    
    PROC AExitPallet(num nProdLine)
        TPWrite "EXIT PALLET";
        TPWrite "LINE:",\Num:=nProdLine;
        SetPalletExiting nProdLine;
    ENDPROC
    
    PROC ATakeSheet(num nProdLine)
        TPWrite "TAKE Sheet";
        TPWrite "LINE:",\Num:=nProdLine;
    ENDPROC
    
    PROC APlaceSheet(num nProdLine)
        TPWrite "PLACE Sheet";
        TPWrite "LINE:",\Num:=nProdLine;
    ENDPROC
    
    
    PROC ATakeProd(num nProdLine, num x, num y, num z, num rot)
        TPWrite "PLACE TAKE Prod";
        TPWrite "LINE:",\Num:=nProdLine;
        TPWrite "X:",\Num:=x;
        TPWrite "Y:",\Num:=y;
        TPWrite "Z:",\Num:=z;
        TPWrite "rot:",\Num:=rot;
    ENDPROC
    
    PROC APlaceSingleProd(num nProdLine, num x, num y, num z, num rot, num acc_x, num acc_y, num acc_z)
        TPWrite "PLACE Single Prod";
        TPWrite "LINE:",\Num:=nProdLine;
        TPWrite "X:",\Num:=x;
        TPWrite "Y:",\Num:=y;
        TPWrite "Z:",\Num:=z;
        TPWrite "rot:",\Num:=rot;
        TPWrite "acc X:",\Num:=acc_x;
        TPWrite "acc Y:",\Num:=acc_y;
        TPWrite "acc Z:",\Num:=acc_z;
    ENDPROC
    
    PROC APlaceDoubleProd(num nProdLine, num x{*}, num y{*}, num z{*}, num rot{*}, num acc_x{*}, num acc_y{*}, num acc_z{*})
        TPWrite "PLACE Double Prod";
        TPWrite "LINE:",\Num:=nProdLine;
        TPWrite "X:",\Num:=x{1};
        TPWrite "Y:",\Num:=y{1};
        TPWrite "Z:",\Num:=z{1};
        TPWrite "rot:",\Num:=rot{1};
        TPWrite "acc X:",\Num:=acc_x{1};
        TPWrite "acc Y:",\Num:=acc_y{1};
        TPWrite "acc Z:",\Num:=acc_z{1};
        
        TPWrite "X:",\Num:=x{2};
        TPWrite "Y:",\Num:=y{2};
        TPWrite "Z:",\Num:=z{2};
        TPWrite "rot:",\Num:=rot{2};
        TPWrite "acc X:",\Num:=acc_x{2};
        TPWrite "acc Y:",\Num:=acc_y{2};
        TPWrite "acc Z:",\Num:=acc_z{2};
    ENDPROC
    
    
    FUNC bool CommandCanBeExecuted(todoType command)
        VAR string fullcommand;
        VAR num param_queue1;
        VAR num param_queue2;
        VAR num param_queue3;
        VAR num param_queue4;
        
        VAR num v_param_queue1{2};
        VAR num v_param_queue2{2};
        VAR num v_param_queue3{2};
        VAR num v_param_queue4{2};
        VAR num v_param_queue5{2};
        VAR num v_param_queue6{2};
        VAR num v_param_queue7{2};
        
        IF r_QueuePaused{command.nProdLine, command.nQueue} THEN
            RETURN FALSE;
        ELSE
            fullcommand := r_ActionType_Name{command.nProdLine, command.nQueue, command.nStep};
        
            IF IsStartQueue(fullcommand, param_queue1) THEN
                RETURN TRUE;
            ELSEIF IsStopQueue(fullcommand, param_queue1) THEN
                RETURN TRUE;
            ELSEIF IsOrderProduct(fullcommand, param_queue1, param_queue2) THEN
                RETURN TRUE;
            ELSEIF IsOrderPallet(fullcommand) THEN
                IF IsPalletExiting(command.nProdLine) THEN
                    RETURN FALSE;
                ENDIF
                !TODO NO PALLET PRESENT
                RETURN TRUE;
            ELSEIF IsTakePallet(fullcommand) THEN
                IF IsPalletExiting(command.nProdLine) THEN
                    RETURN FALSE;
                ENDIF
                !TODO NO PALLET PRESENT
                RETURN TRUE;
            ELSEIF IsPlacePallet(fullcommand) THEN
                IF IsPalletExiting(command.nProdLine) THEN
                    RETURN FALSE;
                ENDIF
                !TODO NO PALLET PRESENT
                RETURN TRUE;
            ELSEIF IsExitPallet(fullcommand) THEN
                RETURN TRUE;
            ELSEIF IsTakeSheet(fullcommand) THEN
                RETURN TRUE;
            ELSEIF IsPlaceSheet(fullcommand) THEN
                RETURN TRUE;
            ELSEIF IsTakeProduct(fullcommand, param_queue1, param_queue2, param_queue3, param_queue4) THEN
                RETURN TRUE;
            ELSEIF IsPlaceProduct(fullcommand, param_queue1, v_param_queue1, v_param_queue2, v_param_queue3, v_param_queue4, v_param_queue5, v_param_queue6, v_param_queue7) THEN
                RETURN TRUE;
            ELSE
                TPWrite "command not yet supported and so can not be done: "+fullcommand ;
                RETURN FALSE;
            ENDIF
        ENDIF
        RETURN FALSE;
    ENDFUNC
    
    PROC AExecute(todoType command)
        VAR string fullcommand;
        VAR num param_queue1;
        VAR num param_queue2;
        VAR num param_queue3;
        VAR num param_queue4;
        
        VAR num v_param_queue1{2};
        VAR num v_param_queue2{2};
        VAR num v_param_queue3{2};
        VAR num v_param_queue4{2};
        VAR num v_param_queue5{2};
        VAR num v_param_queue6{2};
        VAR num v_param_queue7{2};
        
        fullcommand := r_ActionType_Name{command.nProdLine, command.nQueue, command.nStep};
        
        IF IsStartQueue(fullcommand, param_queue1) THEN
            AStartQueue command.nProdLine, param_queue1;
        ELSEIF IsStopQueue(fullcommand, param_queue1) THEN
            AStopQueue command.nProdLine, param_queue1;
        ELSEIF IsOrderProduct(fullcommand, param_queue1, param_queue2) THEN
            AOrderProduct command.nProdLine, param_queue1, param_queue2;
        ELSEIF IsOrderPallet(fullcommand) THEN
            AOrderPallet command.nProdLine;
        ELSEIF IsTakePallet(fullcommand) THEN
            ATakePallet command.nProdLine;
        ELSEIF IsPlacePallet(fullcommand) THEN
            APlacePallet command.nProdLine;
        ELSEIF IsExitPallet(fullcommand) THEN
            AExitPallet command.nProdLine;
        ELSEIF IsTakeSheet(fullcommand) THEN
            ATakeSheet command.nProdLine;
        ELSEIF IsPlaceSheet(fullcommand) THEN
            APlaceSheet command.nProdLine;
        ELSEIF IsTakeProduct(fullcommand, param_queue1, param_queue2, param_queue3, param_queue4) THEN
            ATakeProd command.nProdLine, param_queue1, param_queue2, param_queue3, param_queue4;
        ELSEIF IsPlaceProduct(fullcommand, param_queue1, v_param_queue1, v_param_queue2, v_param_queue3, v_param_queue4, v_param_queue5, v_param_queue6, v_param_queue7) THEN
            IF param_queue1=1 THEN
                APlaceSingleProd command.nProdLine, v_param_queue1{1}, v_param_queue2{1}, v_param_queue3{1}, v_param_queue4{1}, v_param_queue5{1}, v_param_queue6{1}, v_param_queue7{1};
            ELSEIF param_queue1=2 THEN
                APlaceDoubleProd command.nProdLine, v_param_queue1, v_param_queue2, v_param_queue3, v_param_queue4, v_param_queue5, v_param_queue6, v_param_queue7;
            ELSE
                TPWrite "ERRORE: "+fullcommand ;
            ENDIF
        ELSE
            TPWrite "command not yet supported: "+fullcommand ;
        ENDIF

    ENDPROC
    
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
    
    PROC GlobalReset()
        VAR num i;
        FOR i FROM 1 TO nPLACELINE STEP 1 DO
            r_PalletExiting{i} := FALSE;
        ENDFOR
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
        
        GlobalReset;
        
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
                
                AExecute ActionToDo;
                
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
