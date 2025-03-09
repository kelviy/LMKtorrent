from socket import AF_INET, SOCK_STREAM, SOCK_DGRAM, socket
from packet import Request, Address, MetaData
import os
import json
import struct
import hashlib

def main():
    # specify folder to make available to leechers
    # folder_path = input("Enter folder path (absolute path or relative to running scripts):")
    folder_path = "./data/" #default folder path for nowa
    seeder_address = Address('127.0.0.1', 12501)
    tracker_address = Address('127.0.0.1', 12500)

    local_seeder = Seeder(seeder_address, tracker_address, folder_path)
    ip, port = local_seeder.add_to_tracker()
    server_socket = socket(AF_INET, SOCK_STREAM)
    server_socket.bind((ip, port))
    server_socket.listen(1)

    while True:
        connectionSocket, addr = server_socket.accept()
        print("Connect Received from", addr)

        local_seeder.send_file(connectionSocket)
        print("File is sent")

        local_seeder.notify_tracker()


class Seeder():
    def __init__(self, address: Address, tracker_address , folder_path):
        self.address = address
        self.folder_path = folder_path
        if folder_path != None:
            self.file_list = os.listdir(folder_path)
            self.tracker_address = Address("127.0.0.1", 12500)

    def send_file_part(self, leecher_socket: socket, file_name, chunk_start, chunk_end, chunk_size = MetaData.send_chunk_size):
        """
        Sends file data requested 
        1. Computes the file chunk hash and sends it to the leacher
        2. Sends the file data
        3. Leacher confirms that file data integrity is kept by computing it's own hash of the file data and checking if the hash sent equals the hash computed
        4. Leacher sends back confirmation for the seeder to send the next file chunk
        """
        file_chunk_list = []

        #reads section of file requested into memory
        start_file_position = chunk_size * chunk_start 
        with open(f'data/{file_name}', mode='rb') as file:
            for _ in range(chunk_end-chunk_start):
                file.seek(start_file_position)
                file_part = file.read(MetaData.send_chunk_size)
                file_chunk_list.append(file_part)

        index = 0
        while index < len(file_chunk_list):
            hash = hashlib.sha256(file_chunk_list[index]).digest()
            leecher_socket.sendall(hash)
            leecher_socket.sendall(file_chunk_list[index])
            

            leecher_socket.recv(



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
        header = struct.pack(Request.HEADER_FORMAT, Request.NOTIFY_TRACKER.encode(), -1)
        client_socket.sendto(header, self.tracker_address.get_con())
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

        response,_ = client_socket.recvfrom(1)
        status_message = struct.unpack(Request.STATUS_FORMAT, response)

        if status_message:
            print("Successfully added seeder to client")
            print("Uploading file list")
            
            data_addr = Address("127.0.0.1", 11000)
            client_socket.sendto(message, data_addr.get_con())
        else:
            print("Unsuccessful with adding seeder")


        ip, port = client_socket.getsockname()
        client_socket.close()
        return ip, port

    def equal_address(self, address: Address):
        return address == self.address

    def get_meta_info(self):
        return self.address.get_con(), self.file_list

if __name__ == "__main__":
    main()
