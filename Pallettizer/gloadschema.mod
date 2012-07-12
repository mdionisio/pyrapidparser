MODULE GLOADSCHEMA

    ! actionType Elements
    VAR string ActionType_Name{nQueueForSchema, MAX_STEP};
    
    
    ! schemaType Elements
    VAR bool SchemaType_Valid;      ! True if The Schema is valid
    VAR num SchemaType_NSteps{nQueueForSchema};     ! Number of Step for cicle
    VAR num SchemaType_RunSteps{nQueueForSchema};   ! if >0 Step from Start 
    
    VAR num TakeLine;
    VAR prodtype ProductType;
    VAR prodtype PalletType;
    VAR prodtype SheetType;
    VAR num GripperType;
    
ENDMODULE
