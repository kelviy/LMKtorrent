
def main():
    pass

class Address():
    """
    Stores ip address and port number for seeder, leecher, tracker... 
    """
    def __init__(self, ip: str, port: int):
        self.ip = ip
        self.port = port

    def get_con(self) -> tuple:
        return self.ip, self.port

if __name__ == "__main__":
    pass
