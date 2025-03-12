#CSC3002F Group Assignment 2025
#Owners: Kelvin Wei, Liam de Saldanha, Mark Du Preez

from socket import AF_INET, SOCK_STREAM, SOCK_DGRAM, socket
from datetime import timedelta, datetime
import threading
import hashlib
import json
import os
import time
import struct
import sys
import logging
from packet import Request, File

def main():
    #defaults
    folder_path = "./data/"
    seeder_address = ("127.0.0.1", 12501)
    tracker_address = ("127.0.0.1", 12500)

    # manual input if add something to arguments in cli
    if (len(sys.argv) == 1): 
        print("Using default parameters:\n seeder file path: './data/'\nSEEDER: (ip: 127.0.0.1, port: 12501)\nTRACKER: (ip: 127.0.0.1, port: 12500)")
    else:
        ip_seeder, port_seeder = (input("Enter Seeder ip and port number seperated by spaces (eg 127.0.0.1 12501):")).split(" ")
        seeder_address = (ip_seeder, int(port_seeder))
        ip_tracker, port_tracker = (input("Enter Tracker ip and port number seperated by spaces (eg 127.0.0.1 12500):")).split(" ")
        tracker_address = (ip_tracker, int(port_tracker))
        folder_path = input("Enter folder path (absolute path or relative to running scripts):")

    # Starts Seeder
    local_seeder = Seeder(seeder_address, tracker_address, folder_path)
    local_seeder.start_main_loop()

class Seeder():
    # two states that a seeder can be in
    AVAILBLE_FOR_CONNECTION = 'available'
    CONNECTED = 'connected'
    AWAY = 'away'

    ping_interval = timedelta(minutes=2)

    def __init__(self, address, tracker_address , folder_path):
         #logging functionality
        self.logger = File.get_logger("seeder"+str(address), f"./logs/seeder{address}.log")

        self.state = Seeder.AWAY
        self.state_lock = threading.Lock()
        self.last_check_in = datetime.now()

        self.address = address
        self.tracker_address = tracker_address

        self.folder_path = folder_path
        self.file_list = {}

        file_names = os.listdir(folder_path)
        for name in file_names:
            file_size = os.path.getsize(self.folder_path + name)
            self.file_list[name] = file_size

        print("File Dict:", self.file_list)

        self.add_to_tracker()
        self.upload_file_info()

        self.tcp_server_socket = socket(AF_INET, SOCK_STREAM)
        self.tcp_server_socket.bind(self.address)
        self.tcp_server_socket.listen(5)

        # seperate thread to ping tracker
        ping_thread = threading.Thread(target=self.ping_tracker)
        ping_thread.start()

        self.logger.debug("Seeder contents: " + str(self.__dict__))


    def start_main_loop(self):
        self.state = Seeder.AVAILBLE_FOR_CONNECTION

        while True:
            client_socket, client_addr = self.tcp_server_socket.accept()
            # request information will be delimited by "\n"
            request = client_socket.recv(2048).decode().splitlines()

            match request[0]:
                case Request.REQUEST_CONNECTION:
                    # returns connected or queue back to leecher. 
                    # connected means that the server will proceed to transfer the file
                    # queue means that the leecher is in the queue for their request
                    with self.state_lock:
                        if self.state == Seeder.AVAILBLE_FOR_CONNECTION:
                            # encoded json string of a list containing file request info
                            # file_name, chunk start, chunk end, chunk size
                            self.state = Seeder.CONNECTED
                            client_socket.sendall(Request.CONNECTED.encode())
                            response = client_socket.recv(1024).decode().splitlines()
                            if response[0] == Request.REQUEST_FILE_CHUNK:
                                # creates a new thread to send the file_part
                                # files info list format:
                                #  [file_name, num_chunks, send_after]
                                file_request_info = json.loads(response[1])
                                client_thread = threading.Thread(target=self.send_file_part, args=(client_socket, file_request_info))
                                client_thread.start()
                            elif response[0] == Request.EXIT_CONNECTION:
                                # close if client did not acknowledge
                                print("Client requested to close connection. Closing socket")
                                self.logger.debug("Client requested to close connection. Closing socket")
                                self.state = Seeder.AVAILBLE_FOR_CONNECTION
                                client_socket.close()
                        else:
                            # close if not available
                            client_socket.sendall(Request.AWAY.encode())
                            client_socket.close()


    def send_file_part(self, leecher_socket: socket, file_req_info):
        """
        Sends file data requested 
        1. Computes the file chunk hash and sends it to the leacher
        2. Sends the file data
        3. Leacher confirms that file data integrity is kept by computing it's own hash of the file data and checking if the hash sent equals the hash computed
        4. Leacher sends back confirmation for the seeder to send the next file chunk
        """
        try:
            file_name, num_chunks, send_after = file_req_info
            file_chunk_list = []

            #reads section of file requested into memory
            start_file_position = send_after
            with open(f'data/{file_name}', mode='rb') as file:
                file.seek(start_file_position)
                for _ in range(num_chunks):
                    file_part = file.read(File.chunk_size)
                    file_chunk_list.append(file_part)

            index = 0
            while index < num_chunks:
                chunk_size = len(file_chunk_list[index])
                hash = hashlib.sha256(file_chunk_list[index]).digest()
                header = struct.pack("i32s", chunk_size, hash)
                leecher_socket.sendall(header)
                leecher_socket.sendall(file_chunk_list[index])

                print(f"\rChunk {index}: Sent {len(file_chunk_list[index])} bytes. Hash computed size: {len(hash)}", end="", flush=True)
                self.logger.debug("Chunk " + str(index) + ": Sent " + str(len(file_chunk_list[index])) + " bytes. Hash computed size: " + str(len(hash)))

                response = leecher_socket.recv(15).decode()
                if response == Request.ACK:
                    index += 1
                elif response == Request.NOT_ACK:
                    print("\rFile Chunk Acknowledgement Failed... Resending", end="", flush=True)
                    self.logger.debug("File Chunk Acknowledgement Failed... Resending")
                else:
                    print("\rUnknown Response:", response, end="", flush=True)
                    self.logger.debug("Unknonw Response: " + str(response))

            print()
            print(f"Completed Sending File Chunk of {file_name}")
            self.logger.debug("Completed Sending File Chunk of " + str(file_name))

            with self.state_lock:
                self.state = Seeder.AVAILBLE_FOR_CONNECTION
        except Exception as e:
            print()
            print(f"Exception in send file_thread. File is not sent correctly?\n{e}")
            self.logger.debug("Exception in send file_thread. File is not sent correctly?" + str(e))
            with self.state_lock:
                self.state = Seeder.AVAILBLE_FOR_CONNECTION


    def ping_tracker(self):
        while(True):
            # sends a ping with tcp details
            tracker_socket = socket(AF_INET, SOCK_DGRAM)
            message = Request.PING_TRACKER + "\n" + json.dumps(self.address)
            tracker_socket.sendto(message.encode(), self.tracker_address)
            response, addr = tracker_socket.recvfrom(1024)
            print("Ping Result:", response.decode())
            self.logger.debug("Ping Result: " + str(response.decode()))
            tracker_socket.close()

            duration = datetime.now()-self.last_check_in
            self.last_check_in = datetime.now()
            time.sleep( max(0, (Seeder.ping_interval - (duration) ).total_seconds()) )

    def add_to_tracker(self):
        message = Request.ADD_SEEDER+ "\n" + json.dumps(self.address)
        
        tracker_socket = socket(AF_INET, SOCK_DGRAM)
        tracker_socket.sendto(message.encode(), self.tracker_address)
        response, addr = tracker_socket.recvfrom(1024)
        print("Add to Tracker Result:", response.decode())
        self.logger.debug("Add to Tracker Result: " + str(response.decode()))
        tracker_socket.close()


    def upload_file_info(self):
        message = Request.UPLOAD_FILE_LIST + "\n" + json.dumps(self.file_list)
        tracker_socket = socket(AF_INET, SOCK_DGRAM)
        tracker_socket.sendto(message.encode(), self.tracker_address)
        response, addr = tracker_socket.recvfrom(1024)
        print("Upload to Tracker Result:", response.decode())
        self.logger.debug("Upload to Tracker Result:" + str(response.decode()))
        tracker_socket.close()
        

if __name__ == "__main__":
    main()
