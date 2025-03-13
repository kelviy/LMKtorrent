#CSC3002F Group Assignment 2025
#Owners: Kelvin Wei, Liam de Saldanha, Mark Du Preez

import sys
import threading

#from my_gui import MainWindow, Ui_MainWindow
from leacher import Leacher
from PYQT_GUI import Ui_MainWindow
from seeder import Seeder
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QInputDialog

def main():
    # current_dir = os.getcwd()
    # parent_dir = os.path.dirname(current_dir)
    # file_path = os.path.join(parent_dir, 'data', 'file_list.txt')

    # specify folder to make available to leechers
    # folder_path = input("Enter folder path (absolute path or relative to running scripts):")
    
  #  ip_peer, port_peer = (input("Enter Peer ip and port number seperated by spaces (eg 123.123.31 12501):")).split(" ")
 #   port_peer = int(port_peer)
    
   # ip_tracker, port_tracker = (input("Enter Tracker ip and port number seperated by spaces (eg 123.123.31 12500):")).split(" ")
  #  port_tracker = int(port_tracker)
    
    app = QtWidgets.QApplication([])
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    
    folder_path = "./data/" #default folder path for now

    if len(sys.argv) > 2:
        peer_address = ("127.0.0.1",int(sys.argv[1]))#(ip_peer, port_peer)
    else:
        peer_address = ("127.0.0.1",int(sys.argv[1]))
    tracker_address = ("127.0.0.1",12500)#(ip_tracker, port_tracker)


    peer = Peer(peer_address, tracker_address, folder_path,ui,app)
    ui.setPeer(peer)
    
    
    threading.Thread(target=peer.start_main_loop).start()
    
     
    sys.exit(app.exec_())

class Peer():

    
    def __init__(self, address, tracker_address , folder_path):
        self.seeding = False
        self.file_list_downloadable = {}
        self.isLeacher = False
        if len(sys.argv) > 2:
            self.seeder = Seeder(address, tracker_address, folder_path)
            self.ui.update_file_list(self.seeder.file_list)
            print("seeding")
            self.seeding = True
        else:
            self.leacher = Leacher(tracker_address, folder_path)
            self.ui.update_file_list(self.leacher.file_list)
            self.file_list_downloadable = self.leacher.file_list
            self.isLeacher = True
            print(f"Client wont be pinging till it seeds: {self.leacher.address} ")
            print("not seeding")
        
       


    def start_main_loop(self):
        
            
        lock = threading.Lock()
        if self.seeding:
            self.seeder.state = Seeder.AVAILBLE_FOR_CONNECTION
        while True:
            with lock:

                
                    
                
                if  self.seeding:
                    
                    threading.Thread(target=self.seeder.upload).start()
                    self.seeding = False

             #remeber need to upload leachers filelist and add to be pinged if they agree to being a seeder for a file
            
                
                
            
    def reSeeding(self):
        address = self.giveLeacherAddress()
        self.seeder= Seeder(address, self.leacher.tracker_address, self.leacher.download_path)
        self.seeder.state = Seeder.AVAILBLE_FOR_CONNECTION
        
        
        self.ui.update_file_list(self.seeder.file_list_uploadable)
        self.seeding = True
        print(f"{address} is now able to seed ")
    

    def giveLeacherAddress(self):
        address, ok = QInputDialog.getText(None, "Leacher Address", "Enter the leacher address and port (e.g., \"127.0.0.1\" 12500):")
        address = address.split(" ")
        return (address[0] , int(address[1]))
    
    def download(self):
        new_seeder,new_file_name  = self.leacher.download(self.ui.cmb_fileList)
        if new_seeder:
            self.reSeeding()
            self.seeding = True
        

if __name__ == "__main__":
    main()
