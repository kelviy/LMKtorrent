#CSC3002F Group Assignment 2025
#Owners: Kelvin Wei, Liam de Saldanha, Mark Du Preez

from socket import socket, AF_INET, SOCK_DGRAM
from datetime import datetime, timedelta
from packet import Request
import json

def main():
  #  ip_tracker, port_tracker = (input("Enter Tracker ip and port number seperated by spaces (eg 123.123.31 12500):")).split(" ")
   # port_tracker = int(port_tracker)
  #  tracker_addr = (ip_tracker, port_tracker)
    
    tracker_addr = ("127.0.0.1",12500)
    local_tracker = Tracker(tracker_addr)
    local_tracker.start_main_loop()

class Tracker():
    def __init__(self, tracker_addr):
        self.address = tracker_addr
        self.udp_server_socket = socket(AF_INET, SOCK_DGRAM)
        self.udp_server_socket.bind(self.address)

        self.seeder_time_out = timedelta(minutes=10)
        self.file_list = {}
        # Elements stored as:
        # [seeder_addr: tuple, last_check_time: datatime]
        self.seeder_list = []
        self.leacher_list = []

        print("Tracker is up")

    def start_main_loop(self):
        while True:
            self.remove_inactive()

            # potential problem (add_seeder) if file list data is too large (can switch to tcp instead)

            # receive payload of header and additional information delimited by \n
            # TODO: add additional tcp connection for file transfer. 
            payload, client_addr = self.udp_server_socket.recvfrom(1024)
            payload = payload.decode().splitlines()
            # first element is the header

            #debug info
            print("Connection Received from:", client_addr)
            print("Request Message:", payload[0])
            print("Payload information:", payload)
            
            # send in payload containing header and additional information to exec function
            # exec_request function returns a string containing error if a problem has occured. 
            # Else return True when request completed correctly.
            exec_info = self.exec_request(payload, client_addr)
            if exec_info == True:
                 self.udp_server_socket.sendto(Request.SUCCESS.encode(), client_addr)
            else:
                print("Error:", exec_info)
                self.udp_server_socket.sendto(f"{Request.ERROR}\n{exec_info}".encode(), client_addr)
                 
          
    def exec_request(self, payload, client_addr):
        match payload[0]:
            case Request.ADD_SEEDER:
                return self.add_seeder(client_addr, payload[1])
            case Request.UPLOAD_FILE_LIST:
                return self.update_file_list(payload[1])
            case Request.REQUEST_SEEDER_LIST:
                return self.send_seeder_list(client_addr)
            case Request.REQUEST_FILE_LIST:
                return self.send_file_list(client_addr)
            case Request.PING_TRACKER:
               return self.ping_tracker(client_addr, payload[1])
            case _:
                  print(f"Request not recognised: {payload[0]}")

    def add_seeder(self, client_address, payload):
        last_check = datetime.now()
        address = json.loads(payload)

        #checks for unique seeders
        for seeder in self.seeder_list:
             if seeder[0] == address:
                  return "Seeder is already Registered"
             
        self.seeder_list.append([address, last_check])
        print("Added: ", address, ".... Request from:", client_address)
        return True
    

    def add_leacher(self, client_address, payload):
        last_check = datetime.now()
        address = json.loads(payload)

        #checks for unique leachers
        for seeder in self.leacher_list:
             if seeder[0] == address:
                  return "Leacher is already Registered"
             
        self.leacher_list.append([address, last_check])
        print("Added: ", address, ".... Request from:", client_address)
        return True


    def update_file_list(self, payload):
        self.file_list = json.loads(payload)

        # for file_str in payload:
        #     file_info = file_str.split(" ")
            
        #     #checks for unique files
        #     if file_info[0] in self.file_list:
        #         return "File names are not unique"
        #     else:
        #          self.file_list[file_info[0]] = file_info[1]
        
        print("Successfully updated file list")
        return True 

    def send_seeder_list(self, client_address):
        seeder_only_list = []
        for seeder in self.seeder_list:
            seeder_only_list.append(seeder[0])

        # encodes the list of a (list containing ip and port) using json.dumps to string
        self.udp_server_socket.sendto(json.dumps(seeder_only_list).encode(), client_address)
        print("Sent seeder list to:", client_address)
        return True
    
    def send_file_list(self, client_address):
        self.udp_server_socket.sendto(json.dumps(self.file_list).encode(), client_address)
        print("Sent File List to:", client_address)
        return True

    def ping_tracker(self, client_addr_udp, client_addr_tcp):
        client_addr_tcp = json.loads(client_addr_tcp)
        
        for seeder in self.seeder_list:
            if seeder[0] == client_addr_tcp:
                seeder[1] = datetime.now()
                print("Ping Received from:", client_addr_udp, "... to update ping time on", client_addr_tcp)
                return True
        return "Seeder ID not in found with registed seeders"
    
    def remove_inactive(self):
        # list comprehension for filtering inactive seeders out (seeders that haven't responded within time_out period)
        self.seeder_list = [seeder for seeder in self.seeder_list if (datetime.now() - seeder[1]) <= self.seeder_time_out]

if __name__ == "__main__":
    main()
