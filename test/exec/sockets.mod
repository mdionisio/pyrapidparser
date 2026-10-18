MODULE sockets
    ! executed by test_rapid2py.py with standard.sys: the socket instructions on the
    ! loopback interface; a Python thread plays the client of the server of the program
    VAR socketdev server;
    VAR socketdev client;
    VAR socketdev outgoing;
    VAR num port := 0;
    VAR string request := "";
    VAR string address := "";
    PROC main()
        !python:import socket, threading
        !python:probe = socket.socket()
        !python:probe.bind(("127.0.0.1", 0))
        !python:pyrapid.Symbols().GetSymbol("port").data.Set(probe.getsockname()[1])
        !python:probe.close()
        !python:def peer(port):
        !python:    import time
        !python:    for _ in range(100):
        !python:        try:
        !python:            c = socket.create_connection(("127.0.0.1", port))
        !python:            break
        !python:        except OSError:
        !python:            time.sleep(0.05)
        !python:    c.sendall(b"ping")
        !python:    replies.append(c.recv(100).decode())
        !python:    c.close()
        !python:replies = []
        !python:thread = threading.Thread(target=peer, args=(pyrapid.Symbols().GetSymbol("port").data.Get(),))
        !python:thread.start()
        SocketCreate server;
        TPWrite "created " \Bool:=(SocketGetStatus(server) = SOCKET_CREATED);
        SocketBind server, "127.0.0.1", port;
        TPWrite "bound " \Bool:=(SocketGetStatus(server) = SOCKET_BOUND);
        SocketListen server;
        TPWrite "listening " \Bool:=(SocketGetStatus(server) = SOCKET_LISTENING);
        SocketAccept server, client \ClientAddress:=address \Time:=10;
        TPWrite "connected " \Bool:=(SocketGetStatus(client) = SOCKET_CONNECTED);
        TPWrite "from " + address;
        SocketReceive client \Str:=request \Time:=10;
        TPWrite "request " + request;
        SocketSend client \Str:="pong";
        SocketClose client;
        !python:thread.join()
        !python:print("peer received", replies[0], flush=True)
        TPWrite "closed " \Bool:=(SocketGetStatus(client) = SOCKET_CLOSED);
        SocketClose server;
        ! no client: the accept times out
        SocketCreate outgoing;
        SocketBind outgoing, "127.0.0.1", port;
        SocketListen outgoing;
        SocketAccept outgoing, client \Time:=0.2;
        TPWrite "after the timeout";
        SocketClose outgoing;
        ! connection refused: nobody listens on the port any more; TRYNEXT of the error
        ! handler skips the instruction
        SocketCreate outgoing;
        SocketConnect outgoing, "127.0.0.1", port \Time:=2;
        TPWrite "after the failed connection";
    ERROR
        IF ERRNO = ERR_SOCK_TIMEOUT THEN
            TPWrite "error timeout";
        ELSEIF ERRNO = ERR_SOCK_CONNREF THEN
            TPWrite "error connection refused";
        ENDIF
        SocketClose outgoing;
        TRYNEXT;
    ENDPROC
ENDMODULE
