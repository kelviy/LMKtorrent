#CSC3002F Group Assignment 2025
#Owners: Kelvin Wei, Liam de Saldanha, Mark Du Preez

from socket import socket, AF_INET, SOCK_STREAM, SOCK_DGRAM
from packet import Request, File
from concurrent.futures import ThreadPoolExecutor
import hashlib
import os
import json
import struct

from tracker import Tracker

def main():
    """
    - IP Address: 127.0.0.1 (loop back interface) & Port: 12500
    """
    #Mark's Code
    # leacher_ip_address = input("Enter IP address: ")
    # leacher_port_num = int(input("Enter port number: "))
    # file_name = input("Enter the name of the file that you want to download: ")
    # leacher_addr = (leacher_ip_address,leacher_port_num)
    # tracker_addr = ("127.0.0.1",12500)

    # leacher = Leacher(leacher_addr, tracker_addr)
    # leacher.request_file(file_name)

    # #Write the file name and its size to a textfile file_list.txt in ./data/

    ip_tracker, port_tracker = (input("Enter Tracker ip and port number seperated by spaces (eg 123.123.31 12500):")).split(" ")
    port_tracker = int(port_tracker)
    tracker_addr = (ip_tracker, port_tracker)

    local_leacher = Leacher(tracker_addr)

    print(f"Files Available : ")
    file_list_temp = list(local_leacher.file_list.keys())
    for index, file_name in enumerate(file_list_temp):
        print(f"{index}: {file_name} for size {local_leacher.file_list[file_name]}")

    usr_ans = input("\nEnter desired file number seperated by spaces:\n")
    
    download_files_req = usr_ans.split(" ")

    for file_no in download_files_req:
        local_leacher.request_file(file_list_temp[int(file_no)]) 


class Leacher:
    def __init__(self, tracker_addr):
        self.tracker_address = tracker_addr
        self.seeder_list = self.get_seeder_list()  #stores a seeder_list
        self.file_list = self.get_file_list()    #stores a dictionery of file_list

        self.address = (None,) #random generated at the moment
        self.max_parallel_seeders = 2


    def get_seeder_list(self):
        message = Request.REQUEST_SEEDER_LIST
        tracker_socket = socket(AF_INET, SOCK_DGRAM)
        tracker_socket.sendto(message.encode(), self.tracker_address)
        list, addr = tracker_socket.recvfrom(1024)
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
        file_list = json.loads(list.decode())
        print("Obtained File List:", file_list)
        response, addr = tracker_socket.recvfrom(1024)
        print("File List Request Result:", response.decode())
        tracker_socket.close()
        return file_list

    def request_file(self, file_name):
        list_seeder_con = []

        # sends request to all potential seeders
        for ip, port in self.seeder_list:
            soc = socket(AF_INET, SOCK_STREAM)
            soc.connect((ip, port))

            soc.sendall(Request.REQUEST_CONNECTION.encode())
            response = soc.recv(1024).decode()

            if response == Request.CONNECTED:
                list_seeder_con.append(soc)

        # exits over the limit seeders
        if len(list_seeder_con) > self.max_parallel_seeders:
            for i in range(len(list_seeder_con) - self.max_parallel_seeders):
                soc = list_seeder_con.pop()
                soc.sendall(Request.EXIT)

        #calculate file chunk info
        file_size = self.file_list[file_name]
        file_chunk_info_list = File.get_file_send_rule(file_size, list_seeder_con)

        num_chunks = file_chunk_info_list[0][0]
        file_chunk_info_list = file_chunk_info_list[1:]
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

        os.makedirs("tmp", exist_ok=True)
        file_path = os.path.join("tmp", file_name)

        with open(file_path, mode='wb') as file:
            for part in file_parts:
                file.write(part)

        print(file_name + " downloaded succesfully!")


        # os.makedirs('./tmp', exist_ok=True)

        # with open(f'tmp/{MetaData.file_name}', mode='wb') as file:
            
        #     # flag = bool.from_bytes(soc.recv(1))
        #     remainingBytes = MetaData.file_size
        #     count = 0
        #     # while flag:
        #     while remainingBytes > 0:
        #         file_part = soc.recv(MetaData.send_chunk_size)
        #         print(f"{count}: {len(file_part)}")
        #         count+= 1
        #         file.write(file_part)
        #         remainingBytes -= MetaData.send_chunk_size
        #         # flag = bool.from_bytes(soc.recv(1))
        #         # print(flag)
        # print("Successfully downloaded file")
        # soc.close()
        # return True

    # def request_file(self, file_name):
        
    #     request = (Request.REQUEST_FILE + " " + file_name).encode()
        
    #     self.udp_client_socket.sendto(request, self.tracker_addr)

    #     response, tracker_address = self.udp_client_socket.recvfrom(5120)
    #     self.udp_client_socket.close()

    #     response = response.decode()

    #     print(response)

    #     response = response.splitlines()

    #     request_response = response.pop(0)

    #     if (request_response == Request.FILE_FOUND):
    #         chunking_info = response.pop(0).split(" ")
    #         chunking_info = [int(x) for x in chunking_info]

    #         file_parts = [None]*chunking_info[0]

    #         for i in range(len(response)):
    #             line = response[i]
    #             response[i] = []
    #             response[i].append(int(line[0:line.find(" ")]))
    #             line = line[line.find(" ")+1:]
    #             #print(response[i][0])
    #             response[i].append(int(line[0:line.find(" ")]))
    #             line = line[line.find(" ") + 1:]
    #             #print(response[i][1])

    #             response[i].append(ast.literal_eval(line))


    #         if len(response) > 1:
    #             downloaders = []

    #             for seeder in response:
    #                 process = Thread(target=Leacher.get_file_part, args=(file_name,seeder[0],seeder[1],seeder[2],file_parts))
    #                 downloaders.append(process)

    #                 process.start()

    #             for process in downloaders:
    #                 process.join()
    #         else:
    #             print(type(response[0][1]))
    #             Leacher.get_file_part(file_name, int(response[0][0]), int(response[0][1]),response[0][2],file_parts)

    #         os.makedirs("tmp", exist_ok=True)
    #         file_path = os.path.join("tmp", file_name)

    #         with open(file_path, mode='wb') as file:
    #             for part in file_parts:
    #                 file.write(part)

    #         print(file_name + " downloaded succesfully!")
    #     else:
    #         print("File not found!")

            
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

            # computer and equate hashe
            file_hash = hashlib.sha256(file_chunk).digest()

            if file_hash == received_hash:
                print(f"{index}: Received {len(file_chunk)}")
                print("hashes are equal")
                file_parts[num_chunks_to_skip + index] = file_chunk
                index += 1
                seeder_soc.sendall(Request.ACK.encode())
            else:
                seeder_soc.sendall(Request.NOT_ACK.encode())
                print(f"{index}: File failed. Not saving chunk... file size {len(file_chunk)}")
  
        seeder_soc.close()

if __name__ == "__main__":
    main()