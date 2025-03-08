import math
from datetime import timedelta
import pickle

class MetaData():
    
    @staticmethod
    def encode(data) -> bytes:
        return pickle.dumps(data)

    @staticmethod
    def decode(data):
        return pickle.loads(data)

class File():
    """Stores file information"""

    send_chunk_size = 5000

    def __init__(self,file_name,file_size):
        self.file_name = file_name
        self.file_size = file_size
        self.seeder_list = []

    def get_seeder_list(self):
        return self.seeder_list
    
    def add_seeder(self, address):
        self.seeder_list.append(address)

    @staticmethod
    def get_specs(file_size, num_seeders):
        num_chunks = math.ceil(file_size/File.send_chunk_size)
        num_chunks_per_seeder = int(num_chunks)
    
class Request():
    #Sent by seeder to tracker with their file list below it in the format of:
    #   add_seeder
    #   <filename1> <size1>
    #   <filename2> <size2>
    ADD_SEEDER = "add_seeder"

    #Approximately every 5 minutes, the seeder will send the tracker a notify_tracker message to indicate that they are still active.
    NOTIFY_TRACKER = "notify_tracker"

    #Sent from tracker to seeder when a successfulc connection has been established.
    #Essentially, when the seeder's file list is recieved.
    CON_EST = "con_est"

    #Typically will say:
    #   "request_file video12.zip"
    #Used to ask seeder for a specific file that they have.
    #Built-in checking for if seeder has the file.
    REQUEST_FILE = "request_file"

    SEND_FILE = "send_file"

class SeederPeer():
    expire_duration = timedelta(minutes=10)
    
    def __init__(self, address):
        self.address = address
        self.file_list = []

    def add_file(self, file_name):
        self.file_list.append(file_name)

    def __eq__(self, other):
        return (self.address[0] == other.address[0]) and (self.address[1] == other.address[1])