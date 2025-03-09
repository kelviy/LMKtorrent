#Mark Du Preez
#CSC3002F Group Assignment 2025
#Owners: Kelvin Wei, Liam de Saldanha, Mark Du Preez

from socket import AF_INET, SOCK_STREAM, SOCK_DGRAM, socket
from packet import Request, File
from datetime import timedelta, datetime
import os
import ast
from concurrent.futures import ThreadPoolExecutor
import threading

def main():
    ip_address = input("Enter IP address: ")
    port_num = int(input("Enter port number: "))

    peer_address = (ip_address, port_num)
    tracker_address = ("127.0.0.1", 12500)

    seeder = Peer(peer_address, tracker_address)

    connected = seeder.add_seeder()

    if connected:
        seeder.start_main_loop()
    else:
        print("Oof!")



class Peer():

    request_interval = timedelta(minutes=5)

    def __init__(self,seeder_addr,tracker_addr):
        self.seeder_addr = seeder_addr
        self.tracker_addr = tracker_addr
        self.udp_client_socket = socket(AF_INET, SOCK_DGRAM) #talking to server
        self.udp_client_socket.bind(self.seeder_addr)
        self.seeder_server_socket = socket(AF_INET,SOCK_STREAM)# establishing server socket for connecting with Peer
        self.seeder_server_socket.bind(self.seeder_addr)
        self.last_check_in = datetime.now()
        self.numConSockets = 0

        current_dir = os.getcwd()
        parent_dir = os.path.dirname(current_dir)
        file_path = os.path.join(parent_dir, 'data', 'file_list.txt')
        print(file_path)
        with open(file_path, mode='r') as file:
            self.file_list = file.read()#gets seeder file list
        
    def start_main_loop(self):
        self.seeder_server_socket.listen(10)
        
        while True:
            
            download = input("Do you want to download a file? (y/n)\n")
            if download == 'y':

              t1 =  threading.Thread(target=self.download).start()
            if self.numConSockets <1:# make sure we dont create infinite conSockets waiting for leachers
                threading.Thread(target=self.await_leach).start()
                self.numConSockets += 1
            else: 
                print("Too many conSocket threads")
            

    def add_seeder(self):
        request = (Request.ADD_SEEDER + '\n' + self.file_list).encode()
        self.udp_client_socket.sendto(request, self.tracker_addr)

        answer, tracker_address  = self.udp_client_socket.recvfrom(1024)
        
        if answer.decode() == Request.CON_EST:
            return True
        else:
            return False
        
    def notify_tracker(self):
        request = Request.NOTIFY_TRACKER.encode()
        self.udp_client_socket.sendto(request,self.tracker_addr)
        self.last_check_in = datetime.now()
    
    def send_file(self, connection_socket):
        request = connection_socket.recv(1024)

        request = request.decode()
        request = request.splitlines()

        request[0] = request[0].split(" ")
        request[1] = request[1].split(" ")
        request[1][0] = int(request[1][0])
        request[1][1] = int(request[1][1])

        if request[0][0] == Request.GET_FILE_PART:
            with open(os.path.join(os.path.dirname(os.getcwd()), 'data', request[0][1]), mode = 'rb') as file:
                file.read(request[1][1])

                for i in range(request[1][0]):
                    connection_socket.send(file.read(File.chunk_size))

            Peer_addr = connection_socket.getpeername()

            print("File parts sent to " + str(Peer_addr))  

        else:
            print("Unknown request: " + request[0][0])

        connection_socket.close()    
    #Peer methods from here on
    def get_file_part(file_name, num_chunks, send_after, seeder_addr, file_parts):
        request = Request.GET_FILE_PART + " " + file_name + "\n" + str(num_chunks) + " " + str(send_after)
        request = request.encode()

        #send_after/File.chunk_size will be a whole number.
        #As send_after = File.chunk_size*num_chunks
        print(type(send_after))
        num_chunks_to_skip = send_after//File.chunk_size

        client_socket = socket(AF_INET, SOCK_STREAM)
        client_socket.connect(seeder_addr)

        client_socket.send(request)

        for i in range(num_chunks):
            file_parts[num_chunks_to_skip + i] = client_socket.recv(File.chunk_size)

        client_socket.close()


    def request_file(self, file_name):
        
        request = (Request.REQUEST_FILE + " " + file_name).encode()
        
        self.udp_client_socket.sendto(request, self.tracker_addr)

        response, tracker_address = self.udp_client_socket.recvfrom(5120)
     #   self.udp_client_socket.close() #dunno why we closing

        response = response.decode()

        print(response)

        response = response.splitlines()

        request_response = response.pop(0)

        if (request_response == Request.FILE_FOUND):
            chunking_info = response.pop(0).split(" ")
            chunking_info = [int(x) for x in chunking_info]

            file_parts = [None]*chunking_info[0]

            for i in range(len(response)):
                line = response[i]
                response[i] = []
                response[i].append(int(line[0:line.find(" ")]))
                line = line[line.find(" ")+1:]
                #print(response[i][0])
                response[i].append(int(line[0:line.find(" ")]))
                line = line[line.find(" ") + 1:]
                #print(response[i][1])

                response[i].append(ast.literal_eval(line))


            if len(response) > 1:
                downloaders = []

                with ThreadPoolExecutor(max_workers=8) as thread_pool:##
                    futures = []

                    for seeder in response:
                        futures.append(thread_pool.submit(Peer.get_file_part, file_name, seeder[0], seeder[1], seeder[2] ,file_parts))

                    for future in futures:
                        future.result()#join for thread

            else:
                print(type(response[0][1]))
                Peer.get_file_part(file_name, int(response[0][0]), int(response[0][1]),response[0][2],file_parts)

            os.makedirs("tmp", exist_ok=True)
            file_path = os.path.join("tmp", file_name)

            with open(file_path, mode='wb') as file:
                for part in file_parts:
                    file.write(part)

            print(file_name + " downloaded succesfully!")
            
            
            #Don't forget to write file names and sizes to text file
        else:
            print("File not found!")
    
    def download(self):# might not even need this method could add directly into loop however does keep loop less cluttered
        print("choose file to download")
        print("1. video.zip")#make dynamic later
        num = input("Enter file number: ")
        self.request_file("video.zip")#will code dynamically later
        self.add_seeder()
       # return "video1.zip"#will code dynamically later
    
    def await_leach(self):
        connection_socket, Peer_addr = self.seeder_server_socket.accept()

        self.send_file(connection_socket)

        if (datetime.now()-self.last_check_in) >= self.request_interval:
            self.notify_tracker()
        self.numConSockets -= 1
        


if __name__ == "__main__":
    main()
