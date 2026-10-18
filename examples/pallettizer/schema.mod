MODULE SCHEMA
    ! Palletizing schemas, one for each place line: product, pallet, pick line and
    ! the commands of the two queues (see maintask.mod):
    !
    !     OrderProd [ <number of products>, <disposition> ]
    !     StopQueue <queue>
    !     StartQueue <queue>
    !     TakeProduct [ x, y, z, rot ]          offset from the pick point
    !     PlaceProduct [ type, x, acc_x, y, acc_y, z, acc_z, rot, (second product) ]
    !         x, y: center of the product in the pallet frame, z: bottom of the
    !         product from the top of the pallet, rot: degrees around z; the robot
    !         comes from the point displaced of acc_x, acc_y, acc_z
    !     OrderPallet, TakePallet, PlacePallet, ExitPallet, TakeSheet, PlaceSheet
    !
    ! The ORDER queue starts paused: the MAIN queue starts it after the pallet order.
    PROC INIT_SCHEMA(num nsch)
        SchemaType_Valid := TRUE;

        PalletType.X := 800;
        PalletType.Y := 1200;
        PalletType.Z := 150;
        PalletType.Weight := 25000;
        PalletType.Type := 1;

        SheetType.X := 800;
        SheetType.Y := 1200;
        SheetType.Z := 3;
        SheetType.Weight := 100;
        SheetType.Type := 1;

        GripperType := 1;
        SchemaType_RunSteps{ORDER_QUEUE} := 1;
        SchemaType_RunSteps{MAIN_QUEUE} := 1;

        TEST nsch
        CASE 1:
            ! line 1: boxes 400 x 400 x 250, 2 layers of 6
            ProductType.X := 400;
            ProductType.Y := 400;
            ProductType.Z := 250;
            ProductType.Weight := 12000;
            ProductType.Type := 1;
            TakeLine := 1;
            SchemaType_NSteps{ORDER_QUEUE} := 2;
            SchemaType_NSteps{MAIN_QUEUE} := 27;
            ActionType_Name{ORDER_QUEUE, 1} := "OrderProd [ 12, 1 ]";
            ActionType_Name{ORDER_QUEUE, 2} := "StopQueue 1";
            ActionType_Name{MAIN_QUEUE, 1} := "OrderPallet";
            ActionType_Name{MAIN_QUEUE, 2} := "StartQueue 1";
            ActionType_Name{MAIN_QUEUE, 3} := "TakeProduct [ 0, 0, 0, 0 ]";
            ActionType_Name{MAIN_QUEUE, 4} := "PlaceProduct [ 1, 600, -40, 200, 40, 0, 40, 0, 0, 0, 0, 0, 0, 0, 0]";
            ActionType_Name{MAIN_QUEUE, 5} := "TakeProduct [ 0, 0, 0, 0 ]";
            ActionType_Name{MAIN_QUEUE, 6} := "PlaceProduct [ 1, 600, -40, 600, 40, 0, 40, 0, 0, 0, 0, 0, 0, 0, 0]";
            ActionType_Name{MAIN_QUEUE, 7} := "TakeProduct [ 0, 0, 0, 0 ]";
            ActionType_Name{MAIN_QUEUE, 8} := "PlaceProduct [ 1, 600, -40, 1000, 40, 0, 40, 0, 0, 0, 0, 0, 0, 0, 0]";
            ActionType_Name{MAIN_QUEUE, 9} := "TakeProduct [ 0, 0, 0, 0 ]";
            ActionType_Name{MAIN_QUEUE, 10} := "PlaceProduct [ 1, 200, -40, 200, 40, 0, 40, 0, 0, 0, 0, 0, 0, 0, 0]";
            ActionType_Name{MAIN_QUEUE, 11} := "TakeProduct [ 0, 0, 0, 0 ]";
            ActionType_Name{MAIN_QUEUE, 12} := "PlaceProduct [ 1, 200, -40, 600, 40, 0, 40, 0, 0, 0, 0, 0, 0, 0, 0]";
            ActionType_Name{MAIN_QUEUE, 13} := "TakeProduct [ 0, 0, 0, 0 ]";
            ActionType_Name{MAIN_QUEUE, 14} := "PlaceProduct [ 1, 200, -40, 1000, 40, 0, 40, 0, 0, 0, 0, 0, 0, 0, 0]";
            ActionType_Name{MAIN_QUEUE, 15} := "TakeProduct [ 0, 0, 0, 0 ]";
            ActionType_Name{MAIN_QUEUE, 16} := "PlaceProduct [ 1, 600, -40, 200, 40, 250, 40, 0, 0, 0, 0, 0, 0, 0, 0]";
            ActionType_Name{MAIN_QUEUE, 17} := "TakeProduct [ 0, 0, 0, 0 ]";
            ActionType_Name{MAIN_QUEUE, 18} := "PlaceProduct [ 1, 600, -40, 600, 40, 250, 40, 0, 0, 0, 0, 0, 0, 0, 0]";
            ActionType_Name{MAIN_QUEUE, 19} := "TakeProduct [ 0, 0, 0, 0 ]";
            ActionType_Name{MAIN_QUEUE, 20} := "PlaceProduct [ 1, 600, -40, 1000, 40, 250, 40, 0, 0, 0, 0, 0, 0, 0, 0]";
            ActionType_Name{MAIN_QUEUE, 21} := "TakeProduct [ 0, 0, 0, 0 ]";
            ActionType_Name{MAIN_QUEUE, 22} := "PlaceProduct [ 1, 200, -40, 200, 40, 250, 40, 0, 0, 0, 0, 0, 0, 0, 0]";
            ActionType_Name{MAIN_QUEUE, 23} := "TakeProduct [ 0, 0, 0, 0 ]";
            ActionType_Name{MAIN_QUEUE, 24} := "PlaceProduct [ 1, 200, -40, 600, 40, 250, 40, 0, 0, 0, 0, 0, 0, 0, 0]";
            ActionType_Name{MAIN_QUEUE, 25} := "TakeProduct [ 0, 0, 0, 0 ]";
            ActionType_Name{MAIN_QUEUE, 26} := "PlaceProduct [ 1, 200, -40, 1000, 40, 250, 40, 0, 0, 0, 0, 0, 0, 0, 0]";
            ActionType_Name{MAIN_QUEUE, 27} := "ExitPallet";
        CASE 2:
            ! line 2: boxes 400 x 300 x 150, a layer of 8 and a layer of 6 turned of 90 degrees
            ProductType.X := 400;
            ProductType.Y := 300;
            ProductType.Z := 150;
            ProductType.Weight := 8000;
            ProductType.Type := 2;
            TakeLine := 2;
            SchemaType_NSteps{ORDER_QUEUE} := 2;
            SchemaType_NSteps{MAIN_QUEUE} := 31;
            ActionType_Name{ORDER_QUEUE, 1} := "OrderProd [ 14, 1 ]";
            ActionType_Name{ORDER_QUEUE, 2} := "StopQueue 1";
            ActionType_Name{MAIN_QUEUE, 1} := "OrderPallet";
            ActionType_Name{MAIN_QUEUE, 2} := "StartQueue 1";
            ActionType_Name{MAIN_QUEUE, 3} := "TakeProduct [ 0, 0, 0, 0 ]";
            ActionType_Name{MAIN_QUEUE, 4} := "PlaceProduct [ 1, 600, -40, 150, 40, 0, 40, 0, 0, 0, 0, 0, 0, 0, 0]";
            ActionType_Name{MAIN_QUEUE, 5} := "TakeProduct [ 0, 0, 0, 0 ]";
            ActionType_Name{MAIN_QUEUE, 6} := "PlaceProduct [ 1, 600, -40, 450, 40, 0, 40, 0, 0, 0, 0, 0, 0, 0, 0]";
            ActionType_Name{MAIN_QUEUE, 7} := "TakeProduct [ 0, 0, 0, 0 ]";
            ActionType_Name{MAIN_QUEUE, 8} := "PlaceProduct [ 1, 600, -40, 750, 40, 0, 40, 0, 0, 0, 0, 0, 0, 0, 0]";
            ActionType_Name{MAIN_QUEUE, 9} := "TakeProduct [ 0, 0, 0, 0 ]";
            ActionType_Name{MAIN_QUEUE, 10} := "PlaceProduct [ 1, 600, -40, 1050, 40, 0, 40, 0, 0, 0, 0, 0, 0, 0, 0]";
            ActionType_Name{MAIN_QUEUE, 11} := "TakeProduct [ 0, 0, 0, 0 ]";
            ActionType_Name{MAIN_QUEUE, 12} := "PlaceProduct [ 1, 200, -40, 150, 40, 0, 40, 0, 0, 0, 0, 0, 0, 0, 0]";
            ActionType_Name{MAIN_QUEUE, 13} := "TakeProduct [ 0, 0, 0, 0 ]";
            ActionType_Name{MAIN_QUEUE, 14} := "PlaceProduct [ 1, 200, -40, 450, 40, 0, 40, 0, 0, 0, 0, 0, 0, 0, 0]";
            ActionType_Name{MAIN_QUEUE, 15} := "TakeProduct [ 0, 0, 0, 0 ]";
            ActionType_Name{MAIN_QUEUE, 16} := "PlaceProduct [ 1, 200, -40, 750, 40, 0, 40, 0, 0, 0, 0, 0, 0, 0, 0]";
            ActionType_Name{MAIN_QUEUE, 17} := "TakeProduct [ 0, 0, 0, 0 ]";
            ActionType_Name{MAIN_QUEUE, 18} := "PlaceProduct [ 1, 200, -40, 1050, 40, 0, 40, 0, 0, 0, 0, 0, 0, 0, 0]";
            ActionType_Name{MAIN_QUEUE, 19} := "TakeProduct [ 0, 0, 0, 0 ]";
            ActionType_Name{MAIN_QUEUE, 20} := "PlaceProduct [ 1, 550, -40, 200, 40, 150, 40, 90, 0, 0, 0, 0, 0, 0, 0]";
            ActionType_Name{MAIN_QUEUE, 21} := "TakeProduct [ 0, 0, 0, 0 ]";
            ActionType_Name{MAIN_QUEUE, 22} := "PlaceProduct [ 1, 550, -40, 600, 40, 150, 40, 90, 0, 0, 0, 0, 0, 0, 0]";
            ActionType_Name{MAIN_QUEUE, 23} := "TakeProduct [ 0, 0, 0, 0 ]";
            ActionType_Name{MAIN_QUEUE, 24} := "PlaceProduct [ 1, 550, -40, 1000, 40, 150, 40, 90, 0, 0, 0, 0, 0, 0, 0]";
            ActionType_Name{MAIN_QUEUE, 25} := "TakeProduct [ 0, 0, 0, 0 ]";
            ActionType_Name{MAIN_QUEUE, 26} := "PlaceProduct [ 1, 250, -40, 200, 40, 150, 40, 90, 0, 0, 0, 0, 0, 0, 0]";
            ActionType_Name{MAIN_QUEUE, 27} := "TakeProduct [ 0, 0, 0, 0 ]";
            ActionType_Name{MAIN_QUEUE, 28} := "PlaceProduct [ 1, 250, -40, 600, 40, 150, 40, 90, 0, 0, 0, 0, 0, 0, 0]";
            ActionType_Name{MAIN_QUEUE, 29} := "TakeProduct [ 0, 0, 0, 0 ]";
            ActionType_Name{MAIN_QUEUE, 30} := "PlaceProduct [ 1, 250, -40, 1000, 40, 150, 40, 90, 0, 0, 0, 0, 0, 0, 0]";
            ActionType_Name{MAIN_QUEUE, 31} := "ExitPallet";
        DEFAULT:
            SchemaType_Valid := FALSE;
        ENDTEST
    ENDPROC
ENDMODULE
