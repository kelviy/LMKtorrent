#CSC3002F Group Assignment 2025
#Owners: Kelvin Wei, Liam de Saldanha, Mark Du Preez

from socket import socket
import math

class File():
    """Stores file information"""

    chunk_size = 5 * 1000

    @staticmethod
    def get_file_send_rule(file_size, seeder_list):
        # Used in seeder exec send (gets the )
        num_chunks = math.ceil(file_size/File.chunk_size)
        num_chunks_per_seeder = num_chunks//len(seeder_list)
        add_chunks = num_chunks % len(seeder_list)

        file_send_rule = []

        file_send_rule.append((num_chunks, len(seeder_list)))

        start_sending_from = 0

        for i in range(len(seeder_list)):
            if i == (len(seeder_list) - 1):
                file_send_rule.append((num_chunks_per_seeder+add_chunks, start_sending_from, seeder_list[i]))

            else:
                file_send_rule.append((num_chunks_per_seeder, start_sending_from, seeder_list[i]))
                start_sending_from += num_chunks_per_seeder*File.chunk_size

        return file_send_rule

class Request():
    # Information is sent in a string delimited by \n

    ## TRACKER
    #Sent by seeder to register with the tracker. (Tracker stores seeder info)
    # Format: <type> \n (tcp_address)
    ADD_SEEDER = "add_seeder"
    # Sent by seeder to update ping time of seeder
    # Format: <type> \n (tcp_address) 
    PING_TRACKER = "ping_tracker"
    # Sent by leecher to request seeder_list
    REQUEST_SEEDER_LIST = 'request_seeder_list'
    # Sent by the seeder to upload a file info list (Changes files info)
    UPLOAD_FILE_LIST = 'upload_file_list'
    # Sent by leecher to request file list
    REQUEST_FILE_LIST = 'request_file_list'
    #Approximately every 5 minutes, the seeder will send the tracker a notify_tracker message to indicate that they are still active.
    # (not used at the moment) Sent from (1)tracker -> seeder / (2)leacher -> tracker that TCP server is ready to receive
    TCP_PERMIT = "tcp_permit"

    ## SEEDER
    #Sent from seeder to leecher when a successful connection has been established.
    CONNECTED = "connected"
    # Sent from seeder to leecher to indicate that it cannot connect at the moment
    AWAY = 'away'
    # (not used at the moment) Sent from seeder to leacher to inform that the seeder has put the leecher in a queue
    QUEUE = 'queue'

    ## LEECHER
    #Used by leacher to ask for connection to seeder
    REQUEST_CONNECTION = "request_connection"
    #Used to ask seeder for a specific file chunk that they have.
    #Typically will say:
    #   "request_file_chunk \n [file_name, num_chunks, send_after]"
    REQUEST_FILE_CHUNK = "send_file_chunk"
    # Sent by leecher to seeder to ask to ask to leave queue or leave connection
    EXIT = "exit"

     # request execution encounted errors
    # Has the format:
    #   "error <error message>"
    # - error message can be that the file hasn't been found
    ERROR = "error"
    # request completed without any problems
    SUCCESS = "success"
    # acknowledgement that file received successfully
    ACK = "acknolwedgement"

    # ensuring all data in tcp is received
    @staticmethod
    def recvall(socket: socket, message_size, chunk_size=File.chunk_size):
        total_bytes_received = bytes()

        while len(total_bytes_received) < message_size:
            current_bytes_received = socket.recv(min(message_size-len(total_bytes_received), chunk_size))
            total_bytes_received += current_bytes_received

        return total_bytes_received
