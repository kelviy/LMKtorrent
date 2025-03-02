from datetime import datetime, timedelta
from socket import socket, AF_INET, SOCK_DGRAM

def main():
    def exec_request(request):
        match request:
            case Request.ADD_SEEDER:
                ip = connection_socket.recv(1024).decode()
                port = connection_socket.recv(1024).decode()

                seeder_info.add_seeder(ip, port)

                connection_socket.send(Request.SUCCESS.encode())

    IP = "127.0.0.1"
    PORT = 12500
    seeder_info = SeederInfo()

    server_socket = socket(AF_INET, SOCK_DGRAM)
    server_socket.bind((IP, PORT))
    server_socket.listen(5)

    print("Tracker is up")

    while True:
        connection_socket, addr = server_socket.accept()
        print("Connect Received from", addr)

        request = connection_socket.recv(1024).decode()

        exec_request(request)

        connection_socket.send(Request.SUCCESS.encode())
        connection_socket.close()

            
class Request():
    ADD_SEEDER = 'add_seeder'
    UPDATE_SEEDER = 'update_seeder'
    REQUEST_METADATA = 'request_meta'

    SUCCESS = 'success'

class Address():
    """
    Stores ip address and port number for seeder, leecher, tracker... 
    """
    def __init__(self, ip: str, port: int):
        self.ip = ip
        self.port = port

    def __eq__(self, other):
        if other.ip == self.ip and other.port == self.port:
            return True
        return False

    def get_con(self) -> tuple:
        return self.ip, self.port

class MetaData():
    """ 
    MetaData that is sent to the leecher
    """
    # 12.7 MB (below number is in bytes)
    file_size = 12_665_642
    file_name = "Senior Lab - Computer Science Building - UCT video venue finder.zip"
    # 1 MB
    send_chunk_size = 1_000_000

    def __init__(self, seeder_list: list):
        # a list of seeders. Check element of the list is a tuple containing ip address and port number [ip, port]
        self.seeder_list = seeder_list 

    # TODO: Encode and Decode Implementation
    def encode(self):
        pass

    def decode(self):
        pass

class SeederInfo():
    """
    Responsible for keeping active seeders
    """
    expire_duration = timedelta(minutes=30)

    def __init__(self, seeder_list=[]):
        self.seeder_list = seeder_list 

    def add_seeder(self, ip, port):
        last_check = datetime.now()
        self.seeder_list.append((Address(ip, port), last_check))

    def seeder_update_check(self, seeder_address: Address):
        for seeder in self.seeder_list:
            if seeder[0] == seeder_address:
                seeder[1] = datetime.now()
                return
        print("Uknown Seeder. Unable to Update")
        return

    def remove_inactive(self):
        for index, seeder in enumerate(self.seeder_list):
            duration = seeder[1] - datetime.now()
            if duration > SeederInfo.expire_duration:
                self.seeder_list.pop(index)


if __name__ == "__main__":
    main()
