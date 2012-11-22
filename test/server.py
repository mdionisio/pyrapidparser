import socket
# crea un socket INET di tipo STREAM
serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# associa il socket a un host pubblico
# e a una delle porte ben-note
serversocket.bind(("0.0.0.0", 2000))
# diventa un socket server
serversocket.listen(5)



while 1:
    # accetta le connessioni dall'esterno
    (SocketClient, address) = serversocket.accept()
    print "Connection received"
    
    print "received data:"+SocketClient.recv(1024)
    print "Send Data"
    SocketClient.send("Hello from Server")
    print "Close"
    SocketClient.close()
