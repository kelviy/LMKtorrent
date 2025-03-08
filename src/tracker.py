#Mark Du Preez
#CSC3002F Group Assignment 2025
#Owners: Kelvin Wei, Liam de Saldanha, Mark Du Preez

from socket import socket, AF_INET, SOCK_DGRAM

from packet import SeederPeer, Request, File

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
            self.remove_inactive()
            request, client_addr = self.udp_server_socket.recvfrom(1024)
            request = request.decode().splitlines()

            request[0] = request[0].split(" ")


            self.exec_request(request, client_addr)


    def exec_request(self,request, client_addr):
        if (request[0][0] == Request.NOTIFY_TRACKER):

            for seeder in self.seeder_list:
                if seeder[0] == SeederPeer(client_addr):
                    seeder[1] = datetime.now()
                    print("Ping: " + str(client_addr))

        elif (request[0][0] == Request.REQUEST_FILE):

            if not(request[0][1] in self.file_list):
                self.udp_server_socket.sendto(Request.FILE_NOT_FOUND.encode(),client_addr)
            else:
                file_size = self.file_list[request[0][1]][0]
                seeder_list = self.file_list[request[0][1]][1]

                file_send_rule = File.get_file_send_rule(file_size, seeder_list)

                response = Request.FILE_FOUND + "\n"
                response += str(file_send_rule[0][0]) + " " + str(file_send_rule[0][1])

                for i in range(1, file_send_rule[0][1] + 1):
                    response += "\n" + str(file_send_rule[i][0]) + " " + str(file_send_rule[i][1]) + " " + str(file_send_rule[i][2])
                    
                response = response.encode()

                self.udp_server_socket.sendto(response,client_addr)

        elif (request[0][0] == Request.ADD_SEEDER):
            self.seeder_list.append([SeederPeer(client_addr),datetime.now()])
            request.pop(0)

            for file in request:
                file = file.split(" ")
                    
                if file[0] in self.file_list:

                    self.file_list[file[0]][1].append(client_addr)
                else:
                    self.file_list[file[0]] = [int(file[1]),[client_addr]]
                    print(file[0] + " " + file[1])
                
            self.udp_server_socket.sendto(Request.CON_EST.encode(),client_addr)
            print("Seeder added: " + str(client_addr))

        else:
            print(f"Request not recognised: {request[0][0]}")
                
    
    def remove_inactive(self):
        seeder_index_list = []

        for index, seeder in reversed(list(enumerate(self.seeder_list))):
            duration = datetime.now() - seeder[1]

            if duration >= SeederPeer.expire_duration:
                print(f"Removing {seeder[0].address}")
                address = self.seeder_list[index][0].address
                self.seeder_list.pop(index)

                for file in self.file_list.values():

                    for i, seeder_addr in enumerate(file[1]):
                        if (seeder_addr[0] == address[0] and seeder_addr[1] == address[1]):
                            file[1].pop(i)
                            break
            else:
                seeder[1] = datetime.now()

if __name__ == "__main__":
    main()