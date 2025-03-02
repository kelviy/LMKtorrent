from socket import socket, AF_INET, SOCK_STREAM
from tracker import Address

def main():
    """
    - Assume contacted tracker and obtained necessary data
    - IP Address: 127.0.0.1 (loop back interface) & Port: 12500
    - File: 1 zip file
    """

    download_file()

def get_metadata(tracker=Address("127.0.0.1", 12500)):
    """
    Downloads metadata from specified tracker information

  
    """
    pass


def download_file(seeder=Address("127.0.0.1", 12500)):
    soc = socket(AF_INET, SOCK_STREAM)
    soc.connect(seeder.get_con())

    file_part = soc.recv(1024)

    sentence = input("Input lowercase sentence: ")
    soc.send(sentence.encode())

    modifiedSentence = soc.recv(1024).decode()

    print(f"From Server: {modifiedSentence}")

    soc.close()

if __name__ == "__main__":
    main()


