#CSC3002F Group Assignment 2025
#Owners: Kelvin Wei, Liam de Saldanha, Mark Du Preez

from socket import AF_INET, SOCK_STREAM, SOCK_DGRAM, socket
from datetime import timedelta, datetime
import threading
import hashlib
import json
import os
import time
from packet import Request, File

def main():
    # current_dir = os.getcwd()
    # parent_dir = os.path.dirname(current_dir)
    # file_path = os.path.join(parent_dir, 'data', 'file_list.txt')

    # specify folder to make available to leechers
    # folder_path = input("Enter folder path (absolute path or relative to running scripts):")
    port = eval(input("Enter port (default 12501):"))
    folder_path = "./data/" #default folder path for nowa
    seeder_address = ('127.0.0.1', port)
    tracker_address = ('127.0.0.1', 12500)

    local_seeder = Seeder(seeder_address, tracker_address, folder_path)
    local_seeder.start_main_loop()

class Seeder():
    # two states that a seeder can be in
    AVAILBLE_FOR_CONNECTION = 'available'
    CONNECTED = 'connected'
    AWAY = 'away'

    ping_interval = timedelta(seconds=5)

    def __init__(self, address, tracker_address , folder_path):
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
                            response = client_socket.recv(2048).decode().splitlines()
                            if response[0] == Request.REQUEST_FILE_CHUNK:
                                # creates a new thread to send the file_part
                                # files info list format:
                                #  [file_name, num_chunks, send_after]
                                file_request_info = json.loads(response[1])
                                client_thread = threading.Thread(target=self.send_file_part, args=(client_socket, file_request_info))
                                client_thread.start()
                            else:
                                # close if client did not acknowledge
                                print("Client did not request file chunk. Closing socket")
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
                hash = hashlib.sha256(file_chunk_list[index]).digest()
                leecher_socket.sendall(hash)
                leecher_socket.sendall(file_chunk_list[index])

                print(f"{index}: Sent {len(file_chunk_list[index])} bytes. Hash computed: {hash}")

                response = leecher_socket.recv(2048).decode()
                if response == Request.ACK:
                    index += 1
                elif response == Request.ERROR:
                    print("File Acknowledgement Failed... Resending")
                else:
                    print("Unknown Response:", response)

            print("Completed Sending File Chunk")

            with self.state_lock:
                self.state = Seeder.AVAILBLE_FOR_CONNECTION
        except Exception:
            print("Exception in send file_thread. File is not sent correctly?")
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
        tracker_socket.close()


    def upload_file_info(self):
        message = Request.UPLOAD_FILE_LIST + "\n" + json.dumps(self.file_list)
        tracker_socket = socket(AF_INET, SOCK_DGRAM)
        tracker_socket.sendto(message.encode(), self.tracker_address)
        response, addr = tracker_socket.recvfrom(1024)
        print("Upload to Tracker Result:", response.decode())
        tracker_socket.close()
        

        # message = json.dumps(self.file_list).encode()
        # message_size = len(message)

        # header = struct.pack(Request.HEADER_FORMAT, Request.ADD_SEEDER.encode(), message_size)

        # client_socket = socket(AF_INET, SOCK_DGRAM)
        # client_socket.bind(("127.0.0.1", 12501))

        # print(f"Sending Request to add this seeder to make with folder {self.folder_path} available")
        # client_socket.sendto(header, self.tracker_address.get_con())

        # response,_ = client_socket.recvfrom(1)
        # status_message = struct.unpack(Request.STATUS_FORMAT, response)

        # if status_message:
        #     print("Successfully added seeder to client")
        #     print("Uploading file list")
            
        #     data_addr = Address("127.0.0.1", 11000)
        #     client_socket.sendto(message, data_addr.get_con())
        # else:
        #     print("Unsuccessful with adding seeder")


        # ip, port = client_socket.getsockname()
        # client_socket.close()
        # return ip, port
    
    # def send_file(self, connection_socket):
    #     request = connection_socket.recv(1024)

    #     request = request.decode()
    #     request = request.splitlines()

    #     request[0] = request[0].split(" ")
    #     request[1] = request[1].split(" ")
    #     request[1][0] = int(request[1][0])
    #     request[1][1] = int(request[1][1])

    #     if request[0][0] == Request.GET_FILE_PART:
    #         with open(os.path.join(os.path.dirname(os.getcwd()), 'data', request[0][1]), mode = 'rb') as file:
    #             file.read(request[1][1])

    #             for i in range(request[1][0]):
    #                 connection_socket.send(file.read(File.chunk_size))

    #         leacher_addr = connection_socket.getpeername()

    #         print("File parts sent to " + str(leacher_addr))  

    #     else:
    #         print("Unknown request: " + request[0][0])

    #     connection_socket.close()    

if __name__ == "__main__":
    main()
