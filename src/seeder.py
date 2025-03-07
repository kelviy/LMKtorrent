from socket import AF_INET, SOCK_STREAM, SOCK_DGRAM, socket
from tracker import Request, Address, MetaData
import os
import json
import struct

def main():
    # specify folder to make available to leechers
    # folder_path = input("Enter folder path (absolute path or relative to running scripts):")
    folder_path = "./data/" #default folder path for nowa
    seeder_address = Address('127.0.0.1', 12501)
    tracker_address = Address('127.0.0.1', 12500)

    local_seeder = Seeder(seeder_address, tracker_address, folder_path)

    # ip, port = add_to_tracker(folder_path)
    # server_socket = socket(AF_INET, SOCK_STREAM)
    # server_socket.bind((ip, port))
    # server_socket.listen(1)
    #
    # while True:
    #     connectionSocket, addr = server_socket.accept()
    #     print("Connect Received from", addr)
    #
    #     send_file(connectionSocket)
    #     print("File is sent")
    #
    #     notify_tracker()


class Seeder():
    def __init__(self, address: Address, tracker_address : Address, folder_path: str):
        self.address = address
        self.folder_path = folder_path
        self.file_list = os.listdir(folder_path)
        self.tracker_address = Address("127.0.0.1", 12500)

    def send_file(self, leecher_socket: socket):
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

    def notify_tracker(self):
        client_socket = socket(AF_INET, SOCK_DGRAM)
        client_socket.bind(("127.0.0.1",12501))

        client_socket.sendto(Request.NOTIFY_TRACKER.encode(), self.tracker_address.get_con())
        client_socket.close()

    def add_to_tracker(self):
        """
        1. Will send a "Add_Seeder" request to add itself to the tracker
        2. Following message size will be sent with header
        3. Ackowledgement received
        4. message(data - file list) will be sent after an acknolwedgement from server
        """

        message = json.dumps(self.file_list).encode()
        message_size = len(message)

        header = struct.pack(Request.HEADER_FORMAT, Request.ADD_SEEDER.encode(), message_size)

        client_socket = socket(AF_INET, SOCK_DGRAM)
        client_socket.bind(("127.0.0.1", 12501))

        print(f"Sending Request to add this seeder to make with folder {self.folder_path} available")
        client_socket.sendto(header, self.tracker_address.get_con())

        response,_ = client_socket.recvfrom(20)
        status_message = struct.unpack(Request.STATUS_FORMAT, response)

        if status_message:
            print("Successfully added seeder to client")
            print("Uploading file list")

            client_socket.sendto(message, self.tracker_address.get_con())
        else:
            print("Unsuccessful with adding seeder")


        ip, port = client_socket.getsockname()
        client_socket.close()
        return ip, port

if __name__ == "__main__":
    main()
