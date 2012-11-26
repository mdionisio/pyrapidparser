MODULE test
    
    PROC client()
        VAR rawbytes raw_data;
        VAR num integer:=1;
        VAR num integer_out:=0;
        VAR num float:=2.0;
        VAR num float_out:=0.0;
        VAR string string1:="test";
        VAR byte byte1;
        VAR num pos1:=1;
        VAR num pos2:=1;
        
        ClearRawBytes raw_data;
        PackRawBytes integer, raw_data, pos1, \IntX :=DINT;
        pos2 :=  RawBytesLen(raw_data)+1;
        UnPackRawBytes raw_data, pos1, integer_out, \IntX := DINT;
        
        PackRawBytes float, raw_data, pos2, \Float4;
        UnPackRawBytes raw_data, pos2, float_out, \IntX := DINT;
        
        TPWrite "POS1:",\Num:=pos1;
        TPWrite "INT IN", \Num:=integer;
        TPWrite "INT OUT", \Num:=integer_out;
        
        TPWrite "POS2:",\Num:=pos2;
        TPWrite "FLOAT IN", \Num:=float;
        TPWrite "FLOAT OUT", \Num:=float_out;
        
    ENDPROC
    
ENDMODULE