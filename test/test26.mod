MODULE test
    LOCAL PROC client()
        VAR socketdev socket1;
        VAR string received_string;
        
        SocketCreate socket1;
        SocketConnect socket1, "127.0.0.1", 2000;
        SocketSend socket1, \Str:="Hello from Client";
        SocketReceive socket1, \Str:=received_string;
        SocketClose socket1;
        TPWrite received_string;
        ERROR
            TPWrite "Error";
        UNDO
            TPWrite "Undo";
    ENDPROC
    
ENDMODULE