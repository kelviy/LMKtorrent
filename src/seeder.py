#Mark Du Preez
#CSC3002F Group Assignment 2025
#Owners: Kelvin Wei, Liam de Saldanha, Mark Du Preez

from socket import AF_INET, SOCK_STREAM, SOCK_DGRAM, socket
from packet import Request
from datetime import timedelta, datetime
import os

def main():
    ip_address = input("Enter IP address: ")
    port_num = int(input("Enter port number: "))

    seeder_address = (ip_address, port_num)
    tracker_address = ("127.0.0.1", 12500)

    seeder = Seeder(seeder_address, tracker_address)

    connected = seeder.add_seeder()

    if connected:
        seeder.start_main_loop()



class Seeder():

    request_interval = timedelta(minutes=5)

    def __init__(self,seeder_addr,tracker_addr):
        self.seeder_addr = seeder_addr
        self.tracker_addr = tracker_addr
        self.tracker_client_socket = socket(AF_INET, SOCK_DGRAM)
        self.tracker_client_socket.bind(self.seeder_addr)
        self.seeder_server_socket = socket(AF_INET,SOCK_STREAM)
        self.seeder_server_socket.bind(self.seeder_addr)
        self.last_check_in = datetime.now()

        current_dir = os.getcwd()
        parent_dir = os.path.dirname(current_dir)
        file_path = os.path.join(parent_dir, 'data', 'file_list.txt')

        with open(file_path, mode='r') as file:
            self.file_list = file.read()
        
    def start_main_loop(self):
        self.seeder_server_socket.listen(10)
        num_requests = 0

        while True:
            connection_socket, leacher_addr = self.seeder_server_socket.accept()
            num_requests += 1

            self.send_file(connection_socket)

            if (datetime.now()-self.last_check_in) >= self.request_interval:
                self.notify_tracker()
            

    def add_seeder(self):
        request = (Request.ADD_SEEDER + '\n' + self.file_list).encode()
        self.tracker_client_socket.sendto(request, self.tracker_addr)

        answer, tracker_address  = self.tracker_client_socket.recvfrom(1024)
        
        if answer.decode() == Request.CON_EST:
            return True
        else:
            return False
        
    def notify_tracker(self):
        request = Request.NOTIFY_TRACKER.encode()
        self.tracker_client_socket.sendto(request,self.tracker_addr)
        self.last_check_in = datetime.now()
    #def send_file(file_name):

        

if __name__ == "__main__":
    main()
