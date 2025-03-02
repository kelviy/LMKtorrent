from socket import socket, AF_INET, SOCK_STREAM, SOCK_DGRAM
from tracker import Address, MetaData, Request
import os

def main():
    """
    - Assume contacted tracker and obtained necessary data
    - IP Address: 127.0.0.1 (loop back interface) & Port: 12500
    - File: 1 zip file
    """

    seeder_list = get_metadata()

    for ip, port in seeder_list:
        if download_file(Address(ip, port)):
            break


def get_metadata(tracker=Address("127.0.0.1", 12500)):
    """
    Downloads metadata from specified tracker information
    """
    client_socket = socket(AF_INET, SOCK_DGRAM)
    client_socket.sendto(Request.REQUEST_METADATA.encode(), tracker.get_con())

    seeder_list, server_addr = client_socket.recvfrom(1024)
    seeder_list = MetaData.decode(seeder_list)
    return seeder_list

def download_file(seeder=Address("127.0.0.1", 12500)):
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


