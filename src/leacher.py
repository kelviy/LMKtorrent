#CSC3002F Group Assignment 2025
#Owners: Kelvin Wei, Liam de Saldanha, Mark Du Preez

"""
Leecher gets metadata from the tracker and downloads files from the seeder
Leecher support parallel downloading from multiple seeders
"""

from socket import socket, AF_INET, SOCK_STREAM, SOCK_DGRAM
from concurrent.futures import ThreadPoolExecutor
import hashlib, os, json, struct, sys
from packet import Request, File

def main():
    # Defaults
    tracker_addr = ("127.0.0.1", 12500)
    download_folder = "./tmp/"

    # Manual input if you put something in cli.
    if len(sys.argv) == 1:
        print("Using Default arguments: \nTRACKER: (ip: 127.0.0.1, port: 12500)\nDownload folder: `./tmp/`")
    else:
        ip_tracker, port_tracker = (input("Enter Tracker ip and port number seperated by spaces (eg 127.0.0.1 12500):")).split(" ")
        tracker_addr = (ip_tracker, int(port_tracker))
        download_folder = input("Enter download folder path (absolute path or relative to running scripts):")

    # Start leecher.
    local_leacher = Leacher(tracker_addr, download_folder)


    # Choose file download selection.
    print(f"Files Available Type 'a' for all files:")
    file_list_temp = list(local_leacher.file_list.keys())
    for index, file_name in enumerate(file_list_temp):
        print(f"{index}: {file_name} with size {local_leacher.file_list[file_name]}")

    usr_ans = input("\nEnter desired file number seperated by spaces:\n")

    # Build download list.
    download_files_req = []
    if usr_ans.lower() == 'a':
        download_files_req = range(0, len(file_list_temp))
    else:
        download_files_req = usr_ans.split(" ")

    # Download files.
    for file_no in download_files_req:
        local_leacher.request_file(file_list_temp[int(file_no)]) 


class Leacher:
    def __init__(self, tracker_addr, download_path):
        # Logging functionality
        self.logger = File.get_logger("leacher", "./logs/leacher.log")

        self.tracker_address = tracker_addr
        self.download_path = download_path
        # Stores a seeder_list.
        self.seeder_list = self.get_seeder_list()
        # Stores a dictionery of file_list.
        self.file_list = self.get_file_list()

        self.address = (None,) #random generated at the moment
        self.max_parallel_seeders = 5
        
        self.logger.debug("Leacher contents: " + str(self.__dict__))

    def get_seeder_list(self):
        # Retrieves the seeder_list from the tracker.
        message = Request.REQUEST_SEEDER_LIST
        tracker_socket = socket(AF_INET, SOCK_DGRAM)
        tracker_socket.sendto(message.encode(), self.tracker_address)
        list, addr = tracker_socket.recvfrom(1024)
        seeder_list = json.loads(list.decode())
        print("Obtained Seeder List:", seeder_list)
        self.logger.info("Obtained Seeder List:" + str(seeder_list))
        response, addr = tracker_socket.recvfrom(1024)
        print("Seeder List Request Result:", response.decode())
        self.logger.info("Seeder List Request Result: " + str(response.decode()))
        tracker_socket.close()
        return seeder_list

    def get_file_list(self):
        # Retrieves the file_list from the tracker.
        message = Request.REQUEST_FILE_LIST
        tracker_socket = socket(AF_INET, SOCK_DGRAM)
        tracker_socket.sendto(message.encode(), self.tracker_address)
        list, addr = tracker_socket.recvfrom(1024)
        file_list = json.loads(list.decode())
        print("Obtained File List:", file_list)
        self.logger.debug("Obtained File List: " + str(file_list))
        response, addr = tracker_socket.recvfrom(1024)
        print("File List Request Result:", response.decode())
        self.logger.debug("File List Request Result: " + str(response.decode()))
        tracker_socket.close()
        return file_list

    def request_file(self, file_name, progress_callback=None):
        #refresh seeders
        self.seeder_list = self.get_seeder_list()

        list_seeder_con = []

        # sends request to all potential seeders
        for ip, port in self.seeder_list:
            soc = socket(AF_INET, SOCK_STREAM)
            soc.settimeout(1)
            try:
                soc.connect((ip, port))

                soc.sendall(Request.REQUEST_CONNECTION.encode())
                response = soc.recv(1024).decode()

                if response == Request.CONNECTED:
                    list_seeder_con.append(soc)
            except Exception as e:
                print(e)

        # Exits over the limit seeders.
        if len(list_seeder_con) > self.max_parallel_seeders:
            print("Connected:", len(list_seeder_con), "....Closing:", len(list_seeder_con) - self.max_parallel_seeders, "sockets")
            self.logger.debug("Connected %s ...Closing: %s sockets", len(list_seeder_con), len(list_seeder_con) - self.max_parallel_seeders)
            for _ in range(len(list_seeder_con) - self.max_parallel_seeders):
                soc = list_seeder_con.pop()
                soc.sendall(Request.EXIT_CONNECTION.encode())
                soc.close()

        # Calculate file chunk info.
        file_size = self.file_list[file_name]

        # Get num_chunks for file total
        # file_chunk_info_list returns a list containing file_chunk information to send to each seeder.
        num_chunks, file_chunk_info_list = File.get_file_send_rule(file_size, len(list_seeder_con))

        file_parts = [None]*num_chunks

        if len(list_seeder_con) > 1:
            with ThreadPoolExecutor(max_workers=self.max_parallel_seeders) as thread_pool:
                futures = []

                for i, soc in enumerate(list_seeder_con):
                    # Get seeder info for GUI.
                    seeder_info = self.seeder_list[i]
                    # Use a helper function to capture the current values correctly.
                    def make_callback(i, seeder_info):
                        return lambda current, total: progress_callback(file_name, i, current, total, tuple(seeder_info)) if progress_callback else None
                    # Local GUI method.
                    local_progress_callback = local_progress_callback = make_callback(i, seeder_info)
                    # Add to thread_pool.
                    futures.append(thread_pool.submit(
                        self.get_file_part,
                        file_name,
                        file_chunk_info_list[i][0],
                        file_chunk_info_list[i][1],
                        list_seeder_con[i],
                        file_parts,
                        local_progress_callback
                    ))

                for future in futures:
                    future.result()
        else:
            # Remain single threaded.
            # Single connection case – pass seeder info from the first entry.
            def single_cb(current, total):
                if progress_callback:
                    progress_callback(file_name, 0, current, total, tuple(self.seeder_list[0]))
            self.get_file_part(file_name, file_chunk_info_list[0][0], file_chunk_info_list[0][1], list_seeder_con[0], file_parts, single_cb)

        os.makedirs(self.download_path, exist_ok=True)
        file_path = os.path.join(self.download_path, file_name)

        with open(file_path, mode='wb') as file:
            for part in file_parts:
                file.write(part)

        print(file_name + " downloaded succesfully!")
        self.logger.debug(str(file_name) + " download successfully")

    def get_file_part(self, file_name, num_chunks, send_after, seeder_soc, file_parts, progress_callback=None):
        # Retrieve a certain range of file chunks from a seeder from a certain starting point (send_after) of the file.
        request = Request.REQUEST_FILE_CHUNK + "\n" + json.dumps([file_name, num_chunks, send_after])
        request = request.encode()

        # send_after/File.chunk_size will be a whole number.
        # send_after = File.chunk_size*num_chunks
        num_chunks_to_skip = send_after//File.chunk_size

        seeder_soc.sendall(request)

        index = 0
        while index < num_chunks:
            # Receive hash and file.
            
            received_header = seeder_soc.recv(struct.calcsize("i32s"))
            file_chunk_size, received_hash = struct.unpack("i32s", received_header)
            file_chunk = Request.myrecvall(seeder_soc, file_chunk_size, File.chunk_size)

            # Computes and equates hashes.
            file_hash = hashlib.sha256(file_chunk).digest()

            if file_hash == received_hash:
                print(f"\rChunk {index}: Received {len(file_chunk)} and hashes are equal", end='', flush=True)
                self.logger.debug("Chunk " + str(index)+ ": Received " + str(len(file_chunk)) + " and hashes are equal")
                file_parts[num_chunks_to_skip + index] = file_chunk
                index += 1
                
                #GUI Display
                if progress_callback:
                    progress_callback(index, num_chunks)

                seeder_soc.sendall(Request.ACK.encode())
            else:
                seeder_soc.sendall(Request.NOT_ACK.encode())
                print(f"\rChunk {index}: Hashes check failed. Not saving chunk... file size {len(file_chunk)}", end='', flush=True)
                self.logger.debug("Chunk " + str(index)+ ": Hashes check failed. Not saving chunk... file size " + str(len(file_chunk)))

        print()
  
        seeder_soc.close()

if __name__ == "__main__":
    main()