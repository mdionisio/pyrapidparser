MODULE SCHEMA
    PROC INIT_SCHEMA()
        SchemaType_Valid := TRUE;
        
        ProductType.X := 100;
        ProductType.Y := 100;
        ProductType.Z := 100;
        ProductType.Weight := 1000;
        ProductType.Type := 1;
        
        
        PalletType.X := 1200;
        PalletType.Y := 800;
        PalletType.Z := 150;
        PalletType.Weight := 3000;
        PalletType.Type := 1;
        
        SheetType.X := 1200;
        SheetType.Y := 800;
        SheetType.Z := 3;
        SheetType.Weight := 100;
        SheetType.Type := 1;
        
        
        GripperType := 1;
        TakeLine := 1;
        
        SchemaType_NSteps{ORDER_QUEUE} := 2;
        SchemaType_NSteps{MAIN_QUEUE} := 9;
        
        SchemaType_RunSteps{ORDER_QUEUE} := 1;
        SchemaType_RunSteps{MAIN_QUEUE} := 1;
        
        !Possible action
        ! OrderProd <number of product> <disposition>
        ! StopQueue <queue>
        ! StartQueue <queue>
        ! TakeProduct x y z rot
        ! PlaceProduct type x x1 y y1 z z1 rot x x1 y y1 z z1 rot
        ! OrderPallet
        ! TakePallet
        ! PlacePallet
        ! ExitPallet
        ! TakeSheet
        ! PlaceSheet
        
        
        ActionType_Name{ORDER_QUEUE,1} := "OrderProd [ 3, 2 ]";
        ActionType_Name{ORDER_QUEUE,2} := "StopQueue 1";
        
        ActionType_Name{MAIN_QUEUE,1} := "ExitPallet";
        ActionType_Name{MAIN_QUEUE,2} := "OrderPallet";
        ActionType_Name{MAIN_QUEUE,3} := "TakePallet";
        ActionType_Name{MAIN_QUEUE,4} := "PlacePallet";
        ActionType_Name{MAIN_QUEUE,5} := "StartQueue 1";
        ActionType_Name{MAIN_QUEUE,6} := "TakeProduct [ 0, 0, 0, 0 ]";
        ActionType_Name{MAIN_QUEUE,7} := "StartQueue 1";
        ActionType_Name{MAIN_QUEUE,8} := "PlaceProduct [ 1, 10, 1, 20, 2, 30, 3, 90, 0, 0, 0, 0, 0, 0, 0]";
        ActionType_Name{MAIN_QUEUE,9} := "ExitPallet";
    ENDPROC
ENDMODULE
