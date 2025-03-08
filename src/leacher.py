from socket import socket, AF_INET, SOCK_STREAM, SOCK_DGRAM
from packet import Address, MetaData, Request
import os
import struct

def main():
    """
    - Assume contacted tracker and obtained necessary data
    - IP Address: 127.0.0.1 (loop back interface) & Port: 12500
    - File: 1 zip file
    """
    local_leacher = Leacher()
    local_leacher.get_metadata()

    print(f"Files Available : ")
    for index, file_name in enumerate(local_leacher.seeder_list[0][1]):
        print(f"{index}: {file_name}")

    
    usr_ans = input("\nEnter desired file number seperated by spaces - choose video.zip only for now:\n")

    print(usr_ans)

    
    download_files_req = usr_ans.split(" ")

    for file_no in download_files_req:
        local_leacher.download_file(local_leacher.seeder_list[0][1][int(file_no)],local_leacher.seeder_list[0][0]) 

    #print files and ask user for which file/files

    # for ip, port in local_leacher.seeder_list:
    #     if local_leacher.download_file(Address(ip, port)):
    #         break

class Leacher:
    def __init__(self):
        self.tracker_address = Address("127.0.0.1", 12500)

    def get_metadata(self):
        """
        Downloads metadata from specified tracker information
        """
        client_socket = socket(AF_INET, SOCK_DGRAM)
        header = struct.pack(Request.HEADER_FORMAT, Request.REQUEST_METADATA.encode(), -1)
        client_socket.sendto(header, self.tracker_address.get_con())

        seeder_list, server_addr = client_socket.recvfrom(1024)
        self.seeder_list = MetaData.decode(seeder_list)
        
        for i in range(len(self.seeder_list)):
            self.seeder_list[i][0] = Address(self.seeder_list[i][0][0], self.seeder_list[i][0][1])

    def download_file(self, file_name, seeder=Address("127.0.0.1", 12500)):
        soc = socket(AF_INET, SOCK_STREAM)
        soc.connect(seeder.get_con())

        os.makedirs('./tmp', exist_ok=True)

        with open(f'tmp/{MetaData.file_name}', mode='wb') as file:
            
            # flag = bool.from_bytes(soc.recv(1))
            remainingBytes = MetaData.file_size
            count = 0
            # while flag:
            while remainingBytes > 0:
                file_part = soc.recv(MetaData.send_chunk_size)
                print(f"{count}: {len(file_part)}")
                count+= 1
                file.write(file_part)
                remainingBytes -= MetaData.send_chunk_size
                # flag = bool.from_bytes(soc.recv(1))
                # print(flag)
        print("Successfully downloaded file")
        soc.close()
        return True

if __name__ == "__main__":
    main()


