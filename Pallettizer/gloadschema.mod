MODULE GLOADSCHEMA

    ! actionType Elements
    VAR string ActionType_Name{nQueueForSchema, MAX_STEP};
    
    
    ! schemaType Elements
    VAR bool SchemaType_Valid;
    VAR num SchemaType_NSteps{nQueueForSchema};
    VAR num SchemaType_RunSteps{nQueueForSchema};
    
ENDMODULE