from ctypes import sizeof
import datetime
import socket
import sys
import time
from typing import List


def data_generator(byte_size: int):
    byte_size = byte_size - 34
    output = []
    while byte_size > 0:
        if byte_size > 65535:
            output.append(b"0" * 65535)
            byte_size -= 65535
        else:
            output.append(b"0" * byte_size)
            byte_size = 0
    return output


def main():
    Server("127.0.0.1", 8080).start_server()


class Server:
    def __init__(self, host: str, port: int) -> None:
        self.host: str = host
        self.port: int = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.test_data_size = 100 * 1000 * 1000  # 100 MB
        self.test_data: List[bytes] = data_generator(self.test_data_size)
        self.real_data_size = 0
        for t in self.test_data:
            self.real_data_size += sys.getsizeof(t)

    def listen(self):
        self.sock.bind((self.host, self.port))
        self.sock.listen(1)

    def accept(self):
        return self.sock.accept()

    def close(self):
        self.sock.close()

    def start_server(self):
        self.listen()
        print("Listening...")
        while True:
            client_sock, client_addr = self.accept()
            print(f"Accepted connection from {client_addr}")
            chrono = datetime.datetime.now()
            print(sys.getsizeof(self.test_data))
            for i, t in enumerate(self.test_data):
                print(i)
                client_sock.send(t)
            client_sock.close()
            final_time = datetime.datetime.now() - chrono
            print(
                f"Sent {self.real_data_size /1000/1000} MB in {final_time}. Speed : {(self.real_data_size / 1000 / 1000) / (final_time.total_seconds())} MB/s"
            )

    def __del__(self):
        self.close()


if __name__ == "__main__":
    main()
