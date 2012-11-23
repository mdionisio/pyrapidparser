MODULE test
    LOCAL PROC server()
    
        VAR socketdev temp_socket;
        VAR socketdev client_socket;
        VAR string received_string;
        VAR string client_address;
        
        SocketCreate temp_socket;
        SocketBind temp_socket, "127.0.0.1", 2000;
        SocketListen temp_socket;
        SocketAccept temp_socket, client_socket, \ClientAddress:=client_address;
        TPWrite client_address;
        SocketClose temp_socket;
        SocketReceive client_socket, \Str:=received_string;
        TPWrite received_string;
        SocketSend client_socket, \Str:="Hello from Server";
        SocketClose client_socket;
        
    ENDPROC
    
ENDMODULE