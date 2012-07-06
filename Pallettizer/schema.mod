MODULE SCHEMA
    PROC INIT_SCHEMA()
        SchemaType_Valid := TRUE;
        
        ProductType.X := 100;
        ProductType.Y := 100;
        ProductType.Z := 100;
        ProductType.Weight := 1000;
        ProductType.Type := 1;
        
        GripperType := 1;
        TakeLine := 1;
        
        SchemaType_NSteps{ORDER_QUEUE} := 2;
        SchemaType_NSteps{MAIN_QUEUE} := 3;
        
        SchemaType_RunSteps{ORDER_QUEUE} := 1;
        SchemaType_RunSteps{MAIN_QUEUE} := 1;
        
        !Possible action
        ! OrderProd <number of product> <disposition>
        ! StopQueue
        ! StartQueue
        ! TakeProduct x y z rot
        ! PlaceProduct x x1 y y1 z z1 rot
        
        ActionType_Name{ORDER_QUEUE,1} := "OrderProd";
        ActionType_Name{ORDER_QUEUE,2} := "StopQueue";
        
        ActionType_Name{MAIN_QUEUE,1} := "TakeProduct 0 0 0 0";
        ActionType_Name{MAIN_QUEUE,2} := "StartQueue";
        ActionType_Name{MAIN_QUEUE,3} := "PlaceProduct 10 1 20 2 30 3 90";
    ENDPROC
ENDMODULE
