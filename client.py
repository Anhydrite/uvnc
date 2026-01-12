import socket


class Client:
    def __init__(self, host: str, port: int) -> None:
        self.host: str = host
        self.port: int = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        print("Init ready ! ")

    def connect(self):
        print(f"Connecting to {self.host}:{self.port}...")
        self.sock.connect((self.host, self.port))
        print("Connected !")

    def send(self, data: bytes):
        self.sock.send(data)

    def recv(self):
        return self.sock.recv(1024 * 1000 * 1000)


import sys


def main():
    client = Client("127.0.0.1", 8080)

    client.connect()
    data = b""
    counter = 1
    while True:
        u = client.recv()
        print(counter)
        if not u:
            break
        data += u
        counter += 1
    b = sys.getsizeof(data)
    print(f"Downloaded {b} bytes")


if __name__ == "__main__":
    main()
