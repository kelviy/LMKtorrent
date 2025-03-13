#CSC3002F Group Assignment 2025
#Owners: Kelvin Wei, Liam de Saldanha, Mark Du Preez

import sys
from leacher import Leacher
from seeder import Seeder
import os

def main():
    #1. input seeder and tracker details (have to start beforehand) - can be done with `auto_run.sh` and killed with `auto_run.sh kill`
    #2. start gui
    #3. ask where to store files
    #4. download
    #5. Ask to seed

    #defaults
    tracker_addr = ("127.0.0.1", 12500)

    # cli GUI for now
    # manual input if put something in cli
    if len(sys.argv) == 1:
        print("Using Default arguments: \nTRACKER: (ip: 127.0.0.1, port: 12500)")
    else:
        ip_tracker, port_tracker = (input("Enter Tracker ip and port number seperated by spaces (eg 127.0.0.1 12500):")).split(" ")
        tracker_addr = (ip_tracker, int(port_tracker))

    # start
    # default folder of ./tmp/
    local_peer = Peer(tracker_addr,'./tmp/')
    local_peer.download_files()
    local_peer.start_main_loop()


class Peer:
    LEECHER = 'leecher'
    SEEDER = 'seeder'
    ALL_FILES = 'all_files'
    PARTIAL_FILES = 'partial_files'

    MENU = """-------MENU--------
    1. Download Files
    2. Start Seeding
    q. Quit
    """
    def __init__(self, tracker_addr, download_path=None):
        # If no download folder is given, ask via CLI; otherwise use the given path.
        if download_path is None:
            download_folder = input(f"Enter download folder path (default './tmp/' will be chosen if left blank):")
            if download_folder == "":
                download_folder = "./tmp/"
        else:
            download_folder = download_path
        print(f"You have chosen: ({download_folder})")

        self.leecher = Leacher(tracker_addr, download_folder)
        self.seeder = None
        self.state = Peer.LEECHER


    def start_main_loop(self):
        # called after download file is done

        while True:
            print(Peer.MENU)
            usr_ans = input("Enter option: ")

            match (usr_ans.lower()):
                case "1":
                    self.download_files()
                case "2":
                    if self.check_all_files():
                        addr = ("127.0.0.1", 12501)
                        usr_addr = input("Enter IP and Port seperated by space (If nothing is typed then using default ('127.0.0.1', 12501)): ")
                        if usr_addr != "":
                            usr_ip, port = usr_addr.split()
                            addr = (usr_ip, int(port))

                        self.change_to_seeder(addr)
                        # will not stop. Need to exit whole program to stop
                        self.seeder.start_main_loop()
                    else:
                        print("You need to download all files")
                # case "3":
                #     self.change_download_folder()
                case "q":
                    break


    def change_to_seeder(self, addr):
        if (self.state == Peer.SEEDER):
            print("Seeder can't to change to seeder")
            return
        self.seeder = Seeder(addr, self.leecher.tracker_address, self.leecher.download_path)

    def download_files(self):        
        # Choose file download selection
        #cli gui for now
        print(f"Files Available Type 'a' for all files:")
        file_list_temp = list(self.leecher.file_list.keys())
        for index, file_name in enumerate(file_list_temp):
            print(f"{index}: {file_name} with size {self.leecher.file_list[file_name]}")

        usr_ans = input("\nEnter desired file number seperated by spaces:\n")

        # build download list
        download_files_req = []
        if usr_ans.lower() == 'a':
            download_files_req = range(0, len(file_list_temp))
        else:
            download_files_req = usr_ans.split(" ")

        # download files
        for file_no in download_files_req:
            self.leecher.request_file(file_list_temp[int(file_no)]) 

    def get_download_upload_folder(self):
        if self.state == Peer.SEEDER:
            return self.seeder.folder_path
        else:
            return self.leecher.download_path

    def check_all_files(self):
        file_names = os.listdir(self.get_download_upload_folder())

        if self.state == Peer.LEECHER:
            for file in self.leecher.file_list.keys():
                if not(file in file_names):
                    return False
            return True
        else:
            for file in self.seeder.file_list.keys():
                if not(file in file_names):
                    return False
            return True
        
    def change_download_folder(self):
        print("Your current folder:", self.get_download_upload_folder)
        if self.state == Peer.LEECHER:
            usr_folder = input("Your folder path: ")
            self.leecher.download_path = usr_folder
        else:
            print("Your cannot change folder for seeder")

    def download_files_gui(self, selected_files, progress_callback=None):
        """
        Download the given list of file names using an optional progress_callback.
        This method is meant to be used by the GUI.
        """
        for file_name in selected_files:
            self.leecher.request_file(file_name, progress_callback=progress_callback)

if __name__ == "__main__":
    main()