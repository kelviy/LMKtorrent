#CSC3002F Group Assignment 2025
#Owners: Kelvin Wei, Liam de Saldanha, Mark Du Preez

from concurrent.futures import ThreadPoolExecutor
from socket import AF_INET, SOCK_STREAM, SOCK_DGRAM, socket
from datetime import timedelta, datetime
import struct
import sys
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
    
  #  ip_peer, port_peer = (input("Enter Peer ip and port number seperated by spaces (eg 123.123.31 12501):")).split(" ")
 #   port_peer = int(port_peer)
    
   # ip_tracker, port_tracker = (input("Enter Tracker ip and port number seperated by spaces (eg 123.123.31 12500):")).split(" ")
  #  port_tracker = int(port_tracker)

    folder_path = "./data/" #default folder path for now
    if len(sys.argv) > 2:
        peer_address = ("127.0.0.1",int(sys.argv[1]))#(ip_peer, port_peer)
    else:
        peer_address = ("127.0.0.1",int(sys.argv[1]))
    tracker_address = ("127.0.0.1",12500)#(ip_tracker, port_tracker)


    peer = Peer(peer_address, tracker_address, folder_path)
    peer.start_main_loop()

class Peer():


    
    # two states that a seeder can be in
    AVAILBLE_FOR_CONNECTION = 'available'
    CONNECTED = 'connected'
    AWAY = 'away'

    ping_interval = timedelta(seconds=5)
    
    def __init__(self, address, tracker_address , folder_path):
         
        self.state = Peer.AWAY
        self.state_lock = threading.Lock()
        self.last_check_in = datetime.now()

        self.address = address
        self.tracker_address = tracker_address

        self.folder_path = folder_path
        self.file_list_uploadable = {} 
        self.agreedToSeed = []
        self.numConSockets =0

       
        

        #self.address = (None,) #random generated at the moment
        self.max_parallel_seeders = 2 #idk if i can use this for max number of conSockets 
        self.max_conSockets = 2



        
        if len(sys.argv) > 2:
            file_names = os.listdir(folder_path)
            for name in file_names:
                file_size = os.path.getsize(self.folder_path + name)
                self.file_list_uploadable[name] = file_size
                self.agreedToSeed.append(name)

            print("File Dict:", self.file_list_uploadable)
            self.add_to_tracker()
            self.upload_file_info()
            self.seeding = True
            print("seeding")
        else:
            self.seeding = False
            print("not seeding")
        
        #file_list moved here for a chance for a seeder to upload there stuff
        self.seeder_list = self.get_seeder_list()  #stores a seeder_list
        self.file_list_downloadable = self.get_file_list()    #stores a dictionery of file_list. #!this needs to be different from the files we can seed and files we can download

        self.tcp_server_socket = socket(AF_INET, SOCK_STREAM)
        self.tcp_server_socket.bind(self.address)
        self.tcp_server_socket.listen(5)

        if len(sys.argv) > 2:# so Client doesnt ping if it isnt seeding
            # seperate thread to ping tracker
            ping_thread = threading.Thread(target=self.ping_tracker)
            ping_thread.start()
        else:
            print(f"Client wont be pinging till it seeds: {self.address} ")
        
    

    def start_main_loop(self):
        self.state = Peer.AVAILBLE_FOR_CONNECTION
        
        
        
        while True:

            #self.max_conSockets
            if  self.seeding  and len(self.agreedToSeed) >0:
                threading.Thread(target=self.upload).start()
                self.seeding = False#!

             #remeber need to upload leachers filelist and add to be pinged if they agree to being a seeder for a file
            new_seeder,new_file_name  = self.download()
            if new_seeder:
                self.seeding = True#!
                self.add_to_tracker()
                self.upload_file_info()
                ping_thread = threading.Thread(target=self.ping_tracker)
                ping_thread.start()
                print(f"{self.address} is now able to seed {new_file_name}")
            

            
            


    def send_file_part(self, leecher_socket: socket, file_req_info):
        """
        Sends file data requested 
        1. Computes the file chunk hash and sends it to the Peer
        2. Sends the file data
        3. Peer confirms that file data integrity is kept by computing it's own hash of the file data and checking if the hash sent equals the hash computed
        4. Peer sends back confirmation for the seeder to send the next file chunk
        """
        try:
            file_name, num_chunks, send_after = file_req_info
            file_chunk_list = []

            #reads section of file requested into memory
            start_file_position = send_after #-1 #have to -1 to get all bytes

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

                print(f"\rChunk {index}: Sent {len(file_chunk_list[index])} bytes. Hash computed size: {len(hash)}",end = "")

                response = leecher_socket.recv(15).decode()
                if response == Request.ACK:
                    index += 1
                elif response == Request.NOT_ACK:
                    print("\rFile Chunk Acknowledgement Failed... Resending", end="")
                else:
                     print("\rUnknown Response:", response, end="")

            print()
            print(f"Completed Sending File Chunk of {file_name}")

            with self.state_lock:
                self.state = Peer.AVAILBLE_FOR_CONNECTION
        except Exception as e:
            print()
            print(f"Exception in send file_thread. File is not sent correctly?\n{e}")
            with self.state_lock:
                self.state = Peer.AVAILBLE_FOR_CONNECTION


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
            time.sleep( max(0, (Peer.ping_interval - (duration) ).total_seconds()) )

    def add_to_tracker(self):
        message = Request.ADD_SEEDER+ "\n" + json.dumps(self.address)
        
        tracker_socket = socket(AF_INET, SOCK_DGRAM)
        tracker_socket.sendto(message.encode(), self.tracker_address)
        response, addr = tracker_socket.recvfrom(1024)
        print("Add to Tracker Result:", response.decode())
        tracker_socket.close()


    def upload_file_info(self):
        message = Request.UPLOAD_FILE_LIST + "\n" + json.dumps(self.file_list_uploadable)
        tracker_socket = socket(AF_INET, SOCK_DGRAM)
        tracker_socket.sendto(message.encode(), self.tracker_address)
        response, addr = tracker_socket.recvfrom(1024)
        print("Upload to Tracker Result:", response.decode())
        tracker_socket.close()
        

    #Start of Leacher methods
    def get_seeder_list(self):
        message = Request.REQUEST_SEEDER_LIST
        tracker_socket = socket(AF_INET, SOCK_DGRAM)
        tracker_socket.sendto(message.encode(), self.tracker_address)
        list, addr = tracker_socket.recvfrom(1024) #forcibly clsoed
        seeder_list = json.loads(list.decode())
        print("Obtained Seeder List:", seeder_list)
        response, addr = tracker_socket.recvfrom(1024)
        print("Seeder List Request Result:", response.decode())
        tracker_socket.close()
        return seeder_list


    def get_file_list(self):
        message = Request.REQUEST_FILE_LIST
        tracker_socket = socket(AF_INET, SOCK_DGRAM)
        tracker_socket.sendto(message.encode(), self.tracker_address)
        list, addr = tracker_socket.recvfrom(1024)
        file_list_downloadable = json.loads(list.decode())
        print("Obtained File List:", file_list_downloadable)
        response, addr = tracker_socket.recvfrom(1024)
        print("File List Request Result:", response.decode())
        tracker_socket.close()
        return file_list_downloadable

    def request_file(self, file_name):
        list_seeder_con = []

        # sends request to all potential seeders
        for ip, port in self.seeder_list:
            soc = socket(AF_INET, SOCK_STREAM)
            soc.connect((ip, port))

            soc.sendall(Request.REQUEST_CONNECTION.encode())
            response = soc.recv(1024).decode() #! stuck here

            if response == Request.CONNECTED:
                list_seeder_con.append(soc)

        # exits over the limit seeders
        if len(list_seeder_con) > self.max_parallel_seeders:
            for i in range(len(list_seeder_con) - self.max_parallel_seeders):
                soc = list_seeder_con.pop()
                soc.sendall(Request.EXIT)

        #calculate file chunk info
        file_size = self.file_list_downloadable[file_name]
        num_chunks, file_chunk_info_list = File.get_file_send_rule(file_size, len(list_seeder_con))

        file_parts = [None]*num_chunks

        if len(list_seeder_con) > 1:
            with ThreadPoolExecutor(max_workers=self.max_parallel_seeders) as thread_pool:
                futures = []

                for i in range(len(list_seeder_con)):
                    futures.append(thread_pool.submit(Peer.get_file_part, file_name, file_chunk_info_list[i][0], file_chunk_info_list[i][1], list_seeder_con[i] ,file_parts))

                for future in futures:
                    future.result()

        else:
            Peer.get_file_part(file_name, file_chunk_info_list[0][0], file_chunk_info_list[0][1], list_seeder_con[0],file_parts)

        os.makedirs("tmp", exist_ok=True)
        file_path = os.path.join("tmp", file_name)

        with open(file_path, mode='wb') as file:
            for part in file_parts:
                file.write(part)

        print(file_name + " downloaded succesfully!")


      
            
    #TODO: fix parallel download and sending
    def get_file_part(file_name, num_chunks, send_after, seeder_soc, file_parts):
        request = Request.REQUEST_FILE_CHUNK + "\n" + json.dumps([file_name, num_chunks, send_after])
        request = request.encode()

        #send_after/File.chunk_size will be a whole number.
        #As send_after = File.chunk_size*num_chunks
        
        num_chunks_to_skip = send_after//File.chunk_size

        seeder_soc.sendall(request)

        index = 0
        while index < num_chunks:
            # recieve hash and file
            received_header = seeder_soc.recv(struct.calcsize("i32s"))
            file_chunk_size, received_hash = struct.unpack("i32s", received_header)
            file_chunk = Request.myrecvall(seeder_soc, file_chunk_size, File.chunk_size)

            # computer and equate hashes
            file_hash = hashlib.sha256(file_chunk).digest()

            if file_hash == received_hash:
                print(f"\rChunk {index}: Received {len(file_chunk)} and hashes are equal",end="")
                
                file_parts[num_chunks_to_skip + index] = file_chunk
                index += 1
                seeder_soc.sendall(Request.ACK.encode())
            else:
                seeder_soc.sendall(Request.NOT_ACK.encode())
                print(f"\rChunk {index}: Hashes check failed. Not saving chunk... file size {len(file_chunk)}", end='')

        print()
        seeder_soc.close()

    #Liam's Methods
    def download(self):
        print(f"Files Available Type 'a' for all files:")
        file_list_temp = list(self.file_list_downloadable.keys())
        for index, file_name in enumerate(file_list_temp):
            print(f"{index}: {file_name} for size {self.file_list_downloadable[file_name]}")

        usr_ans = input("\nEnter desired file number seperated by spaces:\n")
        
        download_files_req = []
        if usr_ans.lower() == 'a':
            download_files_req = range(0, len(file_list_temp))
        else:
            download_files_req = usr_ans.split(" ")
        print("Requesting files...")
        for file_no in download_files_req:
            self.request_file(file_list_temp[int(file_no)]) 
        file_name =file_list_temp[int(usr_ans)]
        usr_ans = input(f"Would you like to seed {file_name} (y/n)\n")
        if usr_ans == "y":

            file_names = os.listdir(self.folder_path)#! leacher needs to download file into data 
            file_size = os.path.getsize(self.folder_path + file_name)
            self.file_list_uploadable[file_name] = file_size

            if len(self.agreedToSeed) == 0:
                self.seeding = True#!
                self.agreedToSeed.append(file_name)
                print(f"Seeding {file_name}")
                return True,file_name
            else:            
                return False,file_name
        else:
            print(f"Not seeding {file_name}")

    
    
    def upload(self):
            while True:
                client_socket, client_addr = self.tcp_server_socket.accept()
                self.numConSockets-=1
                # request information will be delimited by "\n"
                request = client_socket.recv(2048).decode().splitlines()


                match request[0]:
                    case Request.REQUEST_CONNECTION:
                        # returns connected or queue back to leecher. 
                        # connected means that the server will proceed to transfer the file
                        # queue means that the leecher is in the queue for their request
                        with self.state_lock:
                            if self.state == Peer.AVAILBLE_FOR_CONNECTION:
                                # encoded json string of a list containing file request info
                                # file_name, chunk start, chunk end, chunk size
                                self.state = Peer.CONNECTED
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
                                    self.state = Peer.AVAILBLE_FOR_CONNECTION
                                    client_socket.close()
                            else:
                                # close if not available
                                client_socket.sendall(Request.AWAY.encode())
                                client_socket.close()


if __name__ == "__main__":
    main()
