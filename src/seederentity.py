from datetime import timedelta

class SeederPeer():
    expire_duration = timedelta(minutes=10)
    
    def __init__(self, address):
        self.address = address
        self.file_list = []

    def add_file(self, file_name):
        self.file_list.append(file_name)

    def __eq__(self, other):
        return (self.address[0] == other.address[0]) and (self.address[1] == other.address[1])        