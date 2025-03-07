import math
from metadata import MetaData

class File():
    """Stores file information"""

    def __init__(self,file_name,file_size):
        self.file_name = file_name
        self.file_size = file_size
        self.seeder_list = []

    def get_seeder_list(self):
        return self.seeder_list
    
    def add_seeder(self, address):
        self.seeder_list.append(address)