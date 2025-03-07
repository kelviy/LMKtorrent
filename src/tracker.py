from socket import socket, AF_INET, SOCK_DGRAM
from request import Request
from seederentity import SeederPeer
from datetime import datetime

def main():
    local_tracker = Tracker()
    local_tracker.start_main_loop()

class Tracker():
    def __init__(self):
        self.address = ("127.0.0.1",12500)
        self.udp_server_socket = socket(AF_INET, SOCK_DGRAM)
        self.udp_server_socket.bind(self.address)
        self.file_list = {}
        self.seeder_list = []

        print("Tracker is up!")

    def start_main_loop(self):
        while True:
            request, client_addr = self.udp_server_socket.recvfrom(1024)
            request = request.decode().splitlines()

            request[0] = request[0].split(" ")

            self.exec_request(request, client_addr)


    def exec_request(self,request, client_addr):
        match request[0][0]:
            case Request.NOTIFY_TRACKER:
                for seeder in self.seeder_list:
                    if seeder[0] == SeederPeer(client_addr):
                        seeder[1] = datetime.now()
                        print("Ping: " + client_addr)
            case Request.REQUEST_FILE:
                print()
            case Request.ADD_SEEDER:
                self.seeder_list.append([SeederPeer(client_addr),datetime.now()])
                request.pop(0)

                for file in request:
                    file = file.split(" ")
                    
                    if file[0] in self.file_list:

                        self.file_list[file[0]][1].append(client_addr)
                    else:
                        self.file_list[file[0]] = [file[1],[client_addr]]
                        print(file[0] + " " + file[1])
                
                self.udp_server_socket.sentto(Request.CON_EST.encode(),client_addr)
                
    
    def remove_inactive(self):
        seeder_index_list = []

        for index, seeder in reversed(enumerate(self.seeder_list)):
            duration = datetime.now() - seeder[1]

            if duration >= SeederPeer.expire_duration:
                print(f"Removing {seeder[0].address}")
                address = self.seeder_list.pop(index)[0].address

                for file in self.file_list.values():

                    for i, seeder_addr in enumerate(file[1]):
                        if (seeder_addr[0] == address[0] and seeder_addr[1] == address[1]):
                            file[1].pop(i)
                            break
            else:
                seeder[1] = datetime.now()

if __name__ == "__main__":
    main()