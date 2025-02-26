from socket import socket, AF_INET, SOCK_STREAM

# 127.0.0.1 - ip address for loop back interface
serverName = "127.0.0.1"
PORT = 12500 
# SOCK_DGRAM - UDP
clientSocket = socket(AF_INET, SOCK_STREAM)
clientSocket.connect((serverName, PORT))

sentence = input("Input lowercase sentence: ")
clientSocket.send(sentence.encode())

modifiedSentence = clientSocket.recv(1024).decode()

print(f"From Server: {modifiedSentence}")

clientSocket.close()
