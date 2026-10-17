import socket

# create an INET socket of type STREAM
serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# bind the socket to a public host
# and to a port
serversocket.bind(("0.0.0.0", 2000))
# become a server socket
serversocket.listen(5)


while 1:
    # accept the incoming connections
    (SocketClient, address) = serversocket.accept()
    print("Connection received")

    print("received data:" + SocketClient.recv(1024).decode())
    print("Send Data")
    SocketClient.send(b"Hello from Server")
    print("Close")
    SocketClient.close()
