#Mark Du Preez
#CSC3002F Group Assignment 2025
#Owners: Kelvin Wei, Liam de Saldanha, Mark Du Preez

from socket import socket, AF_INET, SOCK_STREAM, SOCK_DGRAM
from packet import Request, File
import ast
from multiprocessing import Process
import os

def main():
    leacher_ip_address = input("Enter IP address: ")
    leacher_port_num = int(input("Enter port number: "))
    file_name = input("Enter the name of the file that you want to download: ")
    leacher_addr = (leacher_ip_address,leacher_port_num)
    tracker_addr = ("127.0.0.1",12500)

    leacher = Leacher(leacher_addr, tracker_addr)
    leacher.request_file(file_name)

    #Write the file name and its size to a textfile file_list.txt in ./data/

class Leacher:
    def __init__(self, leacher_addr, tracker_addr):
        self.tracker_addr = tracker_addr
        self.leacher_addr = leacher_addr

    def request_file(self, file_name):
        udp_client_socket = socket(AF_INET, SOCK_DGRAM)
        udp_client_socket.bind(self.leacher_addr)
        request = (Request.REQUEST_FILE + " " + file_name).encode()
        
        udp_client_socket.sendto(request, self.tracker_addr)

        response, tracker_address = udp_client_socket.recvfrom(5120)
        udp_client_socket.close()

        response = response.decode()

        response = response.splitlines()

        request_response = response.pop(0)

        if (request_response == Request.FILE_FOUND):
            chunking_info = response.pop(0).split(" ")
            chunking_info = [int(x) for x in chunking_info]

            file_parts = [None]*chunking_info[0]

            for seeder in response:
                rule = seeder.split(" ")
                rule[0] = int(rule[0])
                rule[1] = int(rule[1])

                rule[2] = ast.literal_eval(rule[2])


            if len(response) > 1:
                downloaders = []

                for seeder in response:
                    process = Process(target=Leacher.get_file_part, args=(file_name,seeder[0],seeder[1],seeder[2],file_parts))
                    downloaders.append(process)

                    process.start()

                for process in downloaders:
                    process.join()
            else:
                Leacher.get_file_part(file_name, response[0][0], response[0][1],response[0][2],file_parts)

            os.makedirs("tmp", exist_ok=True)
            file_path = os.path.join("tmp", file_name)

            with open(file_path, mode='wb') as file:
                for part in file_parts:
                    file.write(part)

            print(file_name + " downloaded succesfully!")
        else:
            print("File not found!")

            

    def get_file_part(file_name, num_chunks, send_after, seeder_addr, file_parts):
        request = Request.get_file_part + " " + file_name + "\n" + str(num_chunks) + " " + str(send_after)
        request = request.encode()

        #send_after/File.chunk_size will be a whole number.
        #As send_after = File.chunk_size*num_chunks
        num_chunks_to_skip = int(send_after/File.chunk_size)

        client_socket = socket(AF_INET, SOCK_STREAM)
        client_socket.connect(seeder_addr)

        client_socket.send(request)

        for i in range(num_chunks):
            file_parts[num_chunks_to_skip + i] = client_socket.recv(File.chunk_size)

        client_socket.close()