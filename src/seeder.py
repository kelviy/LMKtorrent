from socket import AF_INET, SOCK_STREAM, socket

IP = "127.0.0.1"
PORT = 12500

serverSocket = socket(AF_INET, SOCK_STREAM)
serverSocket.bind((IP, PORT))
serverSocket.listen(1)

print("The server is ready to receive")

while True:
    connectionSocket, addr = serverSocket.accept()
    print("Connect Received from", addr)

    sentence = connectionSocket.recv(1024).decode()
    capitalizedSentence = sentence.upper()
    print(f"Received: {sentence}")

    connectionSocket.send(capitalizedSentence.encode())
    connectionSocket.close()
