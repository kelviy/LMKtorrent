import json
from packet import Address, Request, MetaData
from datetime import datetime, timedelta
from socket import socket, AF_INET, SOCK_DGRAM
import struct
from seeder import Seeder

def main():
    local_tracker = Tracker()
    local_tracker.start_main_loop()


class Tracker():
    def __init__(self):
        self.seeder_info = SeederInfo()

        self.address = Address("127.0.0.1", 12500)
        self.udp_server_socket = socket(AF_INET, SOCK_DGRAM)
        self.udp_server_socket.bind(self.address.get_con())

        print("Tracker is up")

    def start_main_loop(self):
        while True:
            header, client_addr = self.udp_server_socket.recvfrom(20)
            client_addr = Address(client_addr[0], client_addr[1])
            request, message_size = struct.unpack(Request.HEADER_FORMAT, header)
            request = request.decode().replace("\x00", "")
            print("Connect Received from", client_addr)
            print("Msg:", request, "; next message size", message_size)
            
            # new thread
            self.seeder_info.remove_inactive()
           
            print(self.exec_request(request, message_size, client_addr))
            
          
    def exec_request(self, request, message_size, client_addr) -> bool:
        match request:
            case Request.ADD_SEEDER:
                return self.add_seeder(client_addr, message_size)
            case Request.NOTIFY_TRACKER:
                self.seeder_info.seeder_update_check(client_addr)
                print("Updated ", client_addr)
                return True
            case Request.REQUEST_METADATA:
                meta = MetaData(self.seeder_info.get_seeder_list())
                self.udp_server_socket.sendto(meta.encode(), client_addr.get_con())
                print("Sent Meta Data to:", client_addr)
                return True


        return False

    def add_seeder(self, client_address, message_size):
        self.seeder_info.add_seeder(client_address)
        print("Added ", client_address)
        self.udp_server_socket.sendto(struct.pack(Request.STATUS_FORMAT, True), client_address.get_con())
        
        #udp_data_socket
        udp_data_socket = socket(AF_INET, SOCK_DGRAM)
        data_address = Address("127.0.0.1", 11000)
        udp_data_socket.bind(data_address.get_con())

        data, client_addr = udp_data_socket.recvfrom(message_size)
        
        udp_data_socket.close()

        file_list = json.loads(data.decode())
        
        if Address(client_addr[0], client_addr[1]) == client_address:
            self.seeder_info.update_file_list(client_address, file_list)
            print("Uploaded File List:", file_list)
            return True
        
        return False

class SeederInfo():
    """
    Responsible for keeping active seeders and their info
    """
    expire_duration = timedelta(minutes=10)

    def __init__(self):
        self.seeder_list = []

    def add_seeder(self, address: Address):
        last_check = datetime.now()
        temp_seeder = Seeder(address, None, None)
        self.seeder_list.append([temp_seeder, last_check])

    def update_file_list(self, address: Address, file_list):
        for seeder in self.seeder_list:
            if seeder[0].equal_address(address):
                seeder[0].file_list = file_list
                return True
        return False

    def seeder_update_check(self, seeder_address: Address):
        for seeder in self.seeder_list:
            if seeder[0].equal_address(seeder_address):
                seeder[1] = datetime.now()
                return True
        print("Unknown Seeder. Unable to Update")
        return False

    def remove_inactive(self):
        for index, seeder in reversed(tuple(enumerate(self.seeder_list))):
            duration = datetime.now() - seeder[1]
            if duration > SeederInfo.expire_duration:
                print(f"Removing {seeder}")
                self.seeder_list.pop(index)

    def get_seeder_list(self):
        seeder_list = []
        for seeder in self.seeder_list:
            seeder_list.append(seeder[0].get_meta_info())
        return seeder_list

if __name__ == "__main__":
    main()
