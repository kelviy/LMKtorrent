import json
from datetime import datetime, timedelta
from socket import socket, AF_INET, SOCK_DGRAM
import struct

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
            header, client_addr = self.udp_server_socket.recvfrom(1024)
            request, message_size = struct.unpack(Request.HEADER_FORMAT, header)
            print("Connect Received from", client_addr)
            print("Msg:", request)
            
            # new thread
            self.seeder_info.remove_inactive()
           
            # new thread
            self.exec_request(request, message_size, client_addr)
            
            # code for sending success
            # self.udp_server_socket.sendto(struct.pack(Request.STATUS_FORMAT, True), client_addr)
          
    def exec_request(self, request, message_size, client_addr) -> bool:
        match request:
            case Request.ADD_SEEDER:
                return self.add_seeder(client_addr, message_size)
            case Request.NOTIFY_TRACKER:
                self.seeder_info.seeder_update_check(Address(client_addr[0], client_addr[1]))
                print("Updated", client_addr)
                return True
            case Request.REQUEST_METADATA:
                meta = MetaData(self.seeder_info.get_seeder_list())
                self.udp_server_socket.sendto(meta.encode(), client_addr)
                print("Sent Meta Data to:", client_addr)
                return True


        return False

    def add_seeder(self, client_address, message_size):
        self.seeder_info.add_seeder(client_address[0], client_address[1])
        print("Added", client_address)
        self.udp_server_socket.sendto(struct.pack(Request.STATUS_FORMAT, True), client_address)

        self.udp_server_socket.recvfrom(message_size)
        return True


class Request():
    ADD_SEEDER = 'add_seeder'
    NOTIFY_TRACKER = 'notify_tracker'
    REQUEST_METADATA = 'request_meta'


    HEADER_FORMAT = '16si'
    STATUS_FORMAT = '?'

class Address():
    """
    Stores ip address and port number for seeder, leecher, tracker... 
    """
    def get_con(self) -> tuple:
        return self.ip, self.port

    def __init__(self, ip: str, port: int):
        self.ip = ip
        self.port = port
    
    def __eq__(self, other):
        if other.ip == self.ip and other.port == self.port:
            return True
        return False

    def __repr__(self):
        return f"Address({self.ip}, {self.port})"
   

class MetaData():
    """ 
    MetaData that is sent to the leecher
    """
    # 12.7 MB (below number is in bytes)
    file_size = 12_665_642
    file_name = "video.zip"
    # 1 MB
    send_chunk_size = 5_000

    def __init__(self, seeder_list: list):
        # a list of seeders. Check element of the list is a tuple containing ip address and port number [ip, port]
        self.seeder_list = seeder_list 

    def encode(self) -> bytes:
        return json.dumps(self.seeder_list).encode()

    @staticmethod
    def decode(data: bytes) -> tuple:
        data = json.loads(data.decode())
        return tuple(data)

class SeederInfo():
    """
    Responsible for keeping active seeders and their info
    """
    expire_duration = timedelta(minutes=10)

    def __init__(self, seeder_list=[]):
        self.seeder_list = seeder_list 

    def add_seeder(self, ip, port):
        last_check = datetime.now()
        self.seeder_list.append([Address(ip, port), last_check])

    def seeder_update_check(self, seeder_address: Address):
        for seeder in self.seeder_list:
            if seeder[0] == seeder_address:
                seeder[1] = datetime.now()
                return True
        print("Unknown Seeder. Unable to Update")
        return False

    def remove_inactive(self):
        for index, seeder in enumerate(self.seeder_list):
            duration = datetime.now() - seeder[1]
            if duration > SeederInfo.expire_duration:
                print(f"Removing {seeder}")
                self.seeder_list.pop(index)

    def get_seeder_list(self):
        seeder_list = []
        for seeder in self.seeder_list:
            seeder_list.append(seeder[0].get_con())
        return seeder_list

if __name__ == "__main__":
    main()
