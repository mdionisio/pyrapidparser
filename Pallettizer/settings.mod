MODULE SETTINGS
    RECORD prodtype
        num X;
        num Y;
        num Z;
        num Weight;
        num Type;
    ENDRECORD
    
    CONST num nQueueForSchema := 2;
    CONST num MAIN_QUEUE := 2;
    CONST num ORDER_QUEUE := 1;
    CONST num MAX_STEP := 500;
    
    
    
    CONST num nPROD_PICKLINE    := 2;         ! number of product picking points
    CONST num nPLACELINE := 2;         ! number of place points
    
    CONST num nSHEET_PICKLINE := 1; ! number of poit from piking sheets
    CONST num nPALLET_PICKLINE := 0; ! number of poit from piking pallets
    
    
    !!! SCHEMAS
    
    ! actionType Elements
    VAR string r_ActionType_Name{nPLACELINE, nQueueForSchema, MAX_STEP};
    
    
    ! schemaType Elements
    VAR bool r_SchemaType_Valid{nPLACELINE};
    VAR num r_SchemaType_NSteps{nPLACELINE, nQueueForSchema};
    VAR num r_SchemaType_RunSteps{nPLACELINE, nQueueForSchema};
    VAR prodtype r_ProductType{nPLACELINE};
    VAR prodtype r_PalletType{nPLACELINE};
    VAR prodtype r_SheetType{nPLACELINE};
    VAR num r_GripperType{nPLACELINE};
    VAR num r_TakeLine{nPLACELINE};
    
    VAR bool r_QueuePaused{nPLACELINE, nQueueForSchema};
ENDMODULE
