#Mark Du Preez
#CSC3002F Group Assignment 2025
#Owners: Kelvin Wei, Liam de Saldanha, Mark Du Preez
import math
from datetime import timedelta

class File():
    """Stores file information"""

    chunk_size = 5000

    @staticmethod
    def get_file_send_rule(file_size, seeder_list):
        num_chunks = math.ceil(file_size/File.chunk_size)
        num_chunks_per_seeder = int(num_chunks/len(seeder_list))
        add_chunks = num_chunks % len(seeder_list)

        file_send_rule = []

        file_send_rule.append((num_chunks, len(seeder_list)))

        start_sending_from = 0

        for i in range(len(seeder_list)):
            if i == (len(seeder_list) - 1):
                file_send_rule.append([num_chunks_per_seeder+add_chunks, start_sending_from, seeder_list[i]])

            else:
                file_send_rule.append([num_chunks_per_seeder, start_sending_from, seeder_list[i]])
                start_sending_from += num_chunks_per_seeder*File.chunk_size

        return file_send_rule

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

    FILE_NOT_FOUND = "file_not_found"

    FILE_FOUND = "file_found"

    GET_FILE_PART = "get_file_part"

class SeederPeer():
    expire_duration = timedelta(minutes=10)
    
    def __init__(self, address):
        self.address = address
        self.file_list = []

    def add_file(self, file_name):
        self.file_list.append(file_name)

    def __eq__(self, other):
        return (self.address[0] == other.address[0]) and (self.address[1] == other.address[1])

