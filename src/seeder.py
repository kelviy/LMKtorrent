from socket import AF_INET, SOCK_STREAM, SOCK_DGRAM, socket
from tracker import Request
from tracker import Address, MetaData

def main():
    ip, port = add_to_tracker()
    server_socket = socket(AF_INET, SOCK_STREAM)
    server_socket.bind((ip, port))
    server_socket.listen(1)

    while True:
        connectionSocket, addr = server_socket.accept()
        print("Connect Received from", addr)

        send_file(connectionSocket)
        print("File is sent")

        notify_tracker()


    # serverSocket = socket(AF_INET, SOCK_STREAM)
    # serverSocket.bind((IP, PORT))
    # serverSocket.listen(1)
    #
    # print("The server is ready to receive")
    #
    # while True:
    #     connectionSocket, addr = serverSocket.accept()
    #     print("Connect Received from", addr)
    #
    #     sentence = connectionSocket.recv(1024).decode()
    #     capitalizedSentence = sentence.upper()
    #     print(f"Received: {sentence}")
    #
    #     connectionSocket.send(capitalizedSentence.encode())
    #     connectionSocket.close()

def send_file(leecher_socket: socket):
    with open(f'data/{MetaData.file_name}', mode='rb') as file:
        file_part = file.read(MetaData.send_chunk_size)
        count =0
        while file_part:
            # leecher_socket.send(bool.to_bytes(True))
            sent = leecher_socket.send(file_part)
            print(f"{count}: {sent}")
            count += 1
            file_part = file.read(MetaData.send_chunk_size)

        # print("Sent false")
        # leecher_socket.send(bool.to_bytes(False))


def notify_tracker(tracker=Address("127.0.0.1", 12500)):
    client_socket = socket(AF_INET, SOCK_DGRAM)
    client_socket.bind(("127.0.0.1",12501))

    client_socket.sendto(Request.NOTIFY_TRACKER.encode(), tracker.get_con())
    client_socket.close()

def add_to_tracker(tracker=Address("127.0.0.1", 12500)):
    client_socket = socket(AF_INET, SOCK_DGRAM)
    client_socket.bind(("127.0.0.1",12501))

    print("Sending Request to add this seeder")
    client_socket.sendto(Request.ADD_SEEDER.encode(), tracker.get_con())
    response, server_addr = client_socket.recvfrom(1024)
    print(response.decode())

    ip, port = client_socket.getsockname()
    client_socket.close()
    return ip, port

if __name__ == "__main__":
    main()
