#CSC3002F Group Assignment 2025
#Owners: Kelvin Wei, Liam de Saldanha, Mark Du Preez

import sys

def main():
    #1. input seeder and tracker details (have to start beforehand) - can be done with `auto_run.sh` and killed with `auto_run.sh kill`
    #2. start gui
    #3. ask where to store files
    #4. download
    #5. Ask to seed

    #defaults
    tracker_addr = ("127.0.0.1", 12500)
    download_folder = "./tmp/"

    # manual input if put something in cli
    if len(sys.argv) == 1:
        print("Using Default arguments: \nTRACKER: (ip: 127.0.0.1, port: 12500)")
    else:
        ip_tracker, port_tracker = (input("Enter Tracker ip and port number seperated by spaces (eg 127.0.0.1 12500):")).split(" ")
        tracker_addr = (ip_tracker, int(port_tracker))


class Peer:
    def __init__():
        pass

if __name__ == "__main__":
    main()