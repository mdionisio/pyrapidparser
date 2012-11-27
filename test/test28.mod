MODULE test
    
    PROC client()
        VAR rawbytes raw_data;
        VAR num integer:=1;
        VAR num integer_out:=0;
        VAR num float:=2.0;
        VAR num float_out:=0.0;
        VAR string string1:="test";
        VAR string string1_out:="";
        VAR byte byte1;
        VAR num pos1:=1;
        VAR num pos2:=1;
        VAR num pos3:=1;
        VAR num pos4:=1;
        
        ClearRawBytes raw_data;
        PackRawBytes integer, raw_data \Network, pos1, \IntX :=DINT;
        pos2 :=  RawBytesLen(raw_data)+1;
        UnPackRawBytes raw_data, \Network, pos1, integer_out, \IntX := DINT;
        
        PackRawBytes float, raw_data, pos2, \Float4;
        pos3 :=  RawBytesLen(raw_data)+1;
        UnPackRawBytes raw_data, pos2, float_out, \Float4;
        
        PackRawBytes string1, raw_data, pos3, \ASCII;
        pos4 :=  RawBytesLen(raw_data)+1;
        UnPackRawBytes raw_data, pos3, string1_out, \ASCII:=(pos4-pos3);
        
        TPWrite "POS1:",\Num:=pos1;
        TPWrite "INT IN", \Num:=integer;
        TPWrite "INT OUT", \Num:=integer_out;
        
        TPWrite "POS2:",\Num:=pos2;
        TPWrite "FLOAT IN", \Num:=float;
        TPWrite "FLOAT OUT", \Num:=float_out;
        
        TPWrite "POS3:",\Num:=pos3;
        TPWrite "string IN "+string1;
        TPWrite "string OUT "+string1_out;
        
        TPWrite "POS4:",\Num:=pos4;
        
    ENDPROC
    
ENDMODULE