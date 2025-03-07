import math
from metadata import Metadata

class File():
    """Stores file information"""

def __init__(self,file_name,file_size):
    self.file_name = file_name
    self.file_size = file_size

    self.num_chunks = math.ceil(file_size/Metadata.send_chunk_size)
    chunk_list: list[FileChunk]

    for i in range(self.num_chunks):
        chunk_list.append(i+1)

class FileChunk():

    def __init__(self, chunk_num):
        self.chunk_num

    