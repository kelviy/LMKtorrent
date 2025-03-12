from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from socket import AF_INET, SOCK_DGRAM, SOCK_STREAM, socket
import struct
from PyQt5.QtWidgets import QInputDialog
from packet import File, Request


class Leacher():

    def __init__(self, tracker_addr, download_path):
        #logging functionality
        #self.logger = File.get_logger("leacher", "./logs/leacher.log")

        self.tracker_address = tracker_addr
        self.download_path = download_path
        self.seeder_list = self.get_seeder_list()  #stores a seeder_list
        self.file_list_downloadable = self.get_file_list()    #stores a dictionery of file_list

        self.address = (None,) #random generated at the moment
        self.max_parallel_seeders = 2
        self.agreedToSeed = []
        self.seeder = ""
        
        #self.logger.debug("Leacher contents: " + str(self.__dict__))





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

        #Todo: need to add check for if files are available in seeder, maybe add another element to seederlist or make dic

        # sends request to all potential seeders
        for ip, port in self.seeder_list:
            soc = socket(AF_INET, SOCK_STREAM)
            soc.connect((ip, port))

            soc.sendall(Request.REQUEST_CONNECTION.encode())
            
            response = soc.recv(1024).decode() 
            
           

            if response == Request.CONNECTED:
                list_seeder_con.append(soc)
            elif response == Request.AWAY:
                print(f"Seeder {ip}:{port} is away")
                soc.close()
                return
#! error might be due to checking list not in loop
        # exits over the limit seeders
        if len(list_seeder_con) > self.max_parallel_seeders:
            for i in range(len(list_seeder_con) - self.max_parallel_seeders):
                soc = list_seeder_con.pop()
                soc.sendall(Request.EXIT.encode())
                soc.close()# might close before soc sends
                
        else: 
            soc.sendall(Request.WITHIN_LIMIT.encode())

            response = soc.recv(1024).decode() 
            if response == Request.CONNECTED:
                print("Succesfully connected to seeder")
            

        #calculate file chunk info
        file_size = self.file_list_downloadable[file_name]
        num_chunks, file_chunk_info_list = File.get_file_send_rule(file_size, len(list_seeder_con))

        file_parts = [None]*num_chunks
       
        if len(list_seeder_con) > 1:
            with ThreadPoolExecutor(max_workers=self.max_parallel_seeders) as thread_pool:
                futures = []

                for i in range(len(list_seeder_con)):
                    futures.append(thread_pool.submit(Leacher.get_file_part, file_name, file_chunk_info_list[i][0], file_chunk_info_list[i][1], list_seeder_con[i] ,file_parts))

                for future in futures:
                    future.result()

        else:
            Leacher.get_file_part(file_name, file_chunk_info_list[0][0], file_chunk_info_list[0][1], list_seeder_con[0],file_parts)

        os.makedirs("tmp", exist_ok=True)# if stuff breaks turn this into tmp
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
    

    def download(self):
        print(f"Files Available Type 'a' for all files:")
        file_list_temp = list(self.file_list_downloadable.keys())
        for index, file_name in enumerate(file_list_temp):
            print(f"{index}: {file_name} for size {self.file_list_downloadable[file_name]}")
        #usr_ans = self.ui.cmb_fileList.currentIndex()
        #usr_ans, ok = QInputDialog.getText(None, "Download File", "Enter desired file number separated by spaces (or 'a' for all files):")
        usr_ans = input("\nEnter desired file number seperated by spaces:\n")
        
        download_files_req = []
        #if usr_ans.lower() == 'a':
        if usr_ans == "a":#self.ui.cmb_fileList.count()-1
            download_files_req = range(0, len(file_list_temp))
        else:
            download_files_req = str(usr_ans).split(" ")
        print("Requesting files...")
        for file_no in download_files_req:
            self.request_file(file_list_temp[int(file_no)]) 
        if  usr_ans == "a":
            #usr_ans_2, ok = QInputDialog.getText(None, "Download File", "Would you like to seed all files (y/n)")
       
            usr_ans_2 = input(f"Would you like to seed all files (y/n)\n")
        else:
            file_name =file_list_temp[int(usr_ans)]
            #usr_ans_2, ok = QInputDialog.getText(None, "Download File", f"Would you like to seed {file_name} (y/n)")
       
            usr_ans_2 = input(f"Would you like to seed {file_name} (y/n)\n")
        if usr_ans_2 == "y":
            if usr_ans == "a":
                if len(self.agreedToSeed) == 0:
                    self.seeding = True
                for i in file_list_temp:
                    file_name = i
                    file_names = os.listdir(self.download_path)#! leacher needs to download file into data 
                    file_size = os.path.getsize(self.download_path + file_name)
                    #self.file_list_uploadable[file_name] = file_size
                    self.agreedToSeed.append(file_name)
                    print(f"Seeding {file_name}")
                if self.seeding:
                    self.seeding = True
                    if usr_ans == "a":
                        return True,"all files"
                    return True,file_name
                else:            
                    return False,file_name
            else:    
                file_names = os.listdir(self.download_path)#! leacher needs to download file into data 
                file_size = os.path.getsize(self.download_path + file_name)
                #self.file_list_uploadable[file_name] = file_size
                
                
                self.seeding = True
                    
                return True,file_name
                
        else:
            if usr_ans =="a":
                print(f"Not seeding all files")
                return False,file_name
            else:

                print(f"Not seeding {file_name}")
                return False,file_name
     