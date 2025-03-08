import json

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
        print(self.seeder_list)
        return json.dumps(self.seeder_list).encode()

    @staticmethod
    def decode(data: bytes) -> tuple:
        data = json.loads(data.decode())
        return tuple(data)

