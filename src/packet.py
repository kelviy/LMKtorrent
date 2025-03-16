#CSC3002F Group Assignment 2025
#Owners: Kelvin Wei, Liam de Saldanha, Mark Du Preez

from socket import socket
import math, logging

class File():
    #Class which represents the file entity and a method to generate a send rule for a particular file, given its size and the number of seeders available.

    chunk_size = 5 * 1024

    @staticmethod
    def get_file_send_rule(file_size, list_size):
        # Used to generate a file send (rule) which instructs leacher on how to retrieve file chunks and instructs seeder on what to send.
        num_chunks = math.ceil(file_size/File.chunk_size)
        num_chunks_per_seeder = num_chunks//list_size
        add_chunks = num_chunks % list_size

        file_send_rule = []

        start_sending_from = 0

        for i in range(list_size):
            if i == (list_size - 1):
                #Add the additional chunk on the last send (seeder).
                file_send_rule.append((num_chunks_per_seeder+add_chunks, start_sending_from))

            else:
                file_send_rule.append((num_chunks_per_seeder, start_sending_from))
                start_sending_from += num_chunks_per_seeder*File.chunk_size

        return num_chunks, file_send_rule
    
    @staticmethod
    def get_logger(name, log_file, level=logging.DEBUG):
        #Returns a log of tracker, seeders and leechers on the network.
        logger = logging.getLogger(name)        
        logger.setLevel(logging.DEBUG)

        # Create a file handler with a unique filename.
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        # Define log format.
        formatter = logging.Formatter('%(asctime)s-%(name)s:%(levelname)s->>%(message)s')
        file_handler.setFormatter(formatter)
        # Add handler to the logger.
        logger.addHandler(file_handler)

        return logger
    
class Request():
    # Information is sent in a string delimited by \n.

    ## TRACKER
    # Sent by seeder to register with the tracker. (Tracker stores seeder info).
    # Format: <type> \n (tcp_address)
    ADD_SEEDER = "add_seeder"
    # Sent by seeder to update ping time of seeder.
    # Format: <type> \n (tcp_address)
    PING_TRACKER = "ping_tracker"
    # Sent by leecher to request seeder_list.
    REQUEST_SEEDER_LIST = 'request_seeder_list'
    # Sent by the seeder to upload a file info list (changes file's info).
    UPLOAD_FILE_LIST = 'upload_file_list'
    # Sent by leecher to request file list.
    REQUEST_FILE_LIST = 'request_file_list'

    ## SEEDER
    # Sent from seeder to leecher when a successful connection has been established.
    CONNECTED = "connected"
    # Sent from seeder to leecher to indicate that it cannot connect at the moment.
    AWAY = 'away'

    ## LEECHER
    # Used by leacher to ask for connection to seeder.
    REQUEST_CONNECTION = "request_connection"
    # Used to ask seeder for a specific file chunk that they have.
    # Typically will say:
    #   "request_file_chunk \n [file_name, num_chunks, send_after]"
    REQUEST_FILE_CHUNK = "send_file_chunk"
    # Sent by leecher to seeder to ask to ask to leave queue or leave connection.
    EXIT_CONNECTION = "exit_connection"

    # Request execution encounted errors
    # Has the format:
    #   "error <error message>"
    # Error message can be that the file hasn't been found.
    ERROR = "error"
    # Request completed without any problems.
    SUCCESS = "success"
    # Acknowledgement that file received successfully.
    ACK = "acknolwedgement"
    # Not acknowledged.
    NOT_ACK = "error_notacknol"

    # Ensuring all data in tcp is received.
    # Receives the chunks via the TCP socket between leecher and seeder.
    @staticmethod
    def myrecvall(soc: socket, message_size, chunk_size=File.chunk_size):
        chunks = []
        bytes_recd = 0

        while bytes_recd < message_size:
            chunk = soc.recv(min(message_size - bytes_recd, 2048))
            if chunk == b'':
                raise RuntimeError("socket connection broken")
            chunks.append(chunk)
            bytes_recd = bytes_recd + len(chunk)
        return b''.join(chunks)