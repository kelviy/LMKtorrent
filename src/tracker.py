#CSC3002F Group Assignment 2025
#Owners: Kelvin Wei, Liam de Saldanha, Mark Du Preez

"""
Runs the tracker
Acts as a UDP server with simple receive, process request and send back info loop
Acts as a source of meta data information for leecher and seeder to get and upload information to
"""

from socket import socket, AF_INET, SOCK_DGRAM
from datetime import datetime, timedelta
import json, sys
from packet import Request, File

def main():
    # Defaults.
    tracker_addr = ("127.0.0.1", 12500)

    # Manual input if put something in cli.
    if len(sys.argv) == 1:
        print("Using Default arguments: \nTRACKER: (ip: 127.0.0.1, port: 12500)")
    else:
        ip_tracker, port_tracker = (input("Enter Tracker ip and port number seperated by spaces (eg 127.0.0.1 12500):")).split(" ")
        tracker_addr = (ip_tracker, int(port_tracker))

    # Starts tracker.
    local_tracker = Tracker(tracker_addr)
    local_tracker.start_main_loop()

class Tracker():
    def __init__(self, tracker_addr):

        # Logging functionality
        self.logger = File.get_logger("tracker"+str(tracker_addr), "./logs/tracker.log")

        self.address = tracker_addr
        self.udp_server_socket = socket(AF_INET, SOCK_DGRAM)
        self.udp_server_socket.bind(self.address)

        self.seeder_time_out = timedelta(minutes=10)
        self.file_list = {}
        # Elements stored as:
        # [seeder_addr: tuple, last_check_time: datatime]
        self.seeder_list = []

        self.logger.debug("Tracker contents: " + str(self.__dict__))

        print("Tracker is up")

    def start_main_loop(self):
        while True:
            self.remove_inactive()

            # Receive payload of header and additional information delimited by \n.
            payload, client_addr = self.udp_server_socket.recvfrom(1024)
            payload = payload.decode().splitlines()
            # First element is the header

            # Debug info.
            print("Connection Received from:", client_addr)
            self.logger.debug("Connection Received from:" + str(client_addr))
            print("Request Message:", payload[0])
            self.logger.debug("Request Message:" + str(payload[0]))
            print("Payload information:", payload)
            self.logger.debug("Payload information:" + str(payload))
            
            # Send in payload containing header and additional information to exec function.
            # exec_request function returns a string containing error if a problem has occured. 
            # else return True when request completed correctly.
            exec_info = self.exec_request(payload, client_addr)
            if exec_info == True:
                 self.udp_server_socket.sendto(Request.SUCCESS.encode(), client_addr)
            else:
                print("Error:", exec_info)
                self.logger.error("Error: " + str(exec_info))
                self.udp_server_socket.sendto(f"{Request.ERROR}\n{exec_info}".encode(), client_addr)
                 
    def exec_request(self, payload, client_addr):
        # Execute request received by the tracker found in the first element of the payload.
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
                  self.logger.error("Request not recognised: " + str(payload[0]))

    def add_seeder(self, client_address, payload):
        # Adds seeder to the seeder_list along with its last check.
        last_check = datetime.now()
        address = json.loads(payload)

        #checks for unique seeders
        for seeder in self.seeder_list:
             if seeder[0] == address:
                  return "Seeder is already Registered"
             
        self.seeder_list.append([address, last_check])
        print("Added: ", address, ".... Request from:", client_address)
        self.logger.info("Added: " + str(address) + ".... Request from: " + str(client_address))
        self.logger.debug("Tracker Instance: " + str(self.__dict__))
        return True

    def update_file_list(self, payload):
        # Updates file_list.
        self.file_list = json.loads(payload)
        print("Successfully updated file list")
        self.logger.info("Successfully updated file list")
        self.logger.debug("Tracker Instance: " + str(self.__dict__))
        return True 

    def send_seeder_list(self, client_address):
        # Sends seeder_list to leecher.
        seeder_only_list = []
        for seeder in self.seeder_list:
            seeder_only_list.append(seeder[0])

        # Encodes the list of a (list containing ip and port) using json.dumps to string.
        self.udp_server_socket.sendto(json.dumps(seeder_only_list).encode(), client_address)
        print("Sent seeder list to:", client_address)
        self.logger.info("Sent seeder list to: " + str(client_address))
        return True
    
    def send_file_list(self, client_address):
        # Sends file_list to leecher.
        self.udp_server_socket.sendto(json.dumps(self.file_list).encode(), client_address)
        print("Sent File List to:", client_address)
        self.logger.info("Sent File List to: "+ str(client_address))
        return True

    def ping_tracker(self, client_addr_udp, client_addr_tcp):
        # Is invoked when tracker is ping and their last checked is updated.
        client_addr_tcp = json.loads(client_addr_tcp)
        
        for seeder in self.seeder_list:
            if seeder[0] == client_addr_tcp:
                seeder[1] = datetime.now()
                print("Ping Received from:", client_addr_udp, "... to update ping time on", client_addr_tcp)
                self.logger.info("Ping Received from: " + str(client_addr_udp) + " ... to update ping time on " + str(client_addr_tcp))
                self.logger.debug("Tracker Instance: " + str(self.__dict__))
                return True
        return "Seeder ID not in found with registed seeders"
    
    def remove_inactive(self):
        # List comprehension for filtering inactive seeders out (seeders that haven't responded within time_out period).
        self.seeder_list = [seeder for seeder in self.seeder_list if (datetime.now() - seeder[1]) <= self.seeder_time_out]

if __name__ == "__main__":
    main()