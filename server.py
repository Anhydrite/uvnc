import atexit
from ctypes import sizeof
import datetime
import itertools
from queue import Empty, Queue
import select
import socket
import sys
from threading import Thread
import time
from typing import Dict, List, Tuple, cast

import client


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
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.test_data_size = 5000 * 1000 * 1000  # 100 MB
        self.test_data: List[bytes] = data_generator(self.test_data_size)
        self.real_data_size = 0
        for t in self.test_data:
            self.real_data_size += sys.getsizeof(t)
        self.threads = {}
        self.read_buffers_by_client: Dict[int, Queue] = {}
        self.write_buffers_by_client: Dict[int, Queue] = {}
        atexit.register(self.close)
        self.counter = itertools.count()

    def get_client_id(self):
        return next(self.counter)

    def listen(self):
        self.sock.bind((self.host, self.port))
        self.sock.listen(1)

    def accept(self):
        return self.sock.accept()

    def close(self):
        self.sock.close()

    def handle_connection(self, client_sock: socket.socket, client_addr: Tuple[str, int]):
        client_id = self.get_client_id()
        client_thread = Thread(target=self.receive_routine, args=(client_sock, client_addr, client_id))
        self.threads[client_id] = client_thread
        self.read_buffers_by_client[client_id] = Queue()
        self.write_buffers_by_client[client_id] = Queue()
        client_thread.start()

    def receive_routine(self, client_sock: socket.socket, client_addr: Tuple[str, int], client_id: int):
        client_sock.setblocking(False)
        while True:
            self.read_routine(client_sock, client_addr, client_id)
            self.write_routine(client_sock, client_addr, client_id)
            time.sleep(0.01)

    def read_routine(self, client_sock: socket.socket, client_addr: Tuple[str, int], client_id: int):
        read_polling = select.poll()
        read_polling.register(client_sock.fileno(), select.POLLIN)
        poll_result: List[Tuple[int, int]] = read_polling.poll(0)
        if not poll_result:
            return

        inc_data = client_sock.recv(65535)
        if inc_data == b"":
            print(f"Client {client_addr} disconnected")
            raise Exception("Client disconnected")

        print(f"Received data ({sys.getsizeof(inc_data)} bytes) from {client_addr} : {inc_data.decode()}")
        self.read_buffers_by_client[client_id].put_nowait(inc_data)
        read_polling.unregister(client_sock.fileno())

    def write_routine(self, client_sock: socket.socket, client_addr: Tuple[str, int], client_id: int):
        try:
            outgoing_data = self.write_buffers_by_client[client_id].get_nowait()
        except Empty:
            return
        client_sock.sendall(outgoing_data)
        print(f"Sent data ({sys.getsizeof(outgoing_data)} bytes) to {client_addr} : {outgoing_data.decode()}")

    def start_server(self):
        self.listen()
        print("Listening...")
        while True:
            client_sock, client_addr = self.accept()
            client_sock = cast(socket.socket, client_sock)
            client_addr = cast(Tuple[str, int], client_addr)
            print(client_addr)
            self.handle_connection(client_sock, client_addr)
            print(f"Accepted connection from {client_addr}")
            # chrono = datetime.datetime.now()
            # print(sys.getsizeof(self.test_data))
            # for i, t in enumerate(self.test_data):
            #     print(i)
            #     client_sock.send(t)
            # client_sock.close()
            # final_time = datetime.datetime.now() - chrono
            # print(
            #     f"Sent {self.real_data_size /1000/1000} MB in {final_time}. Speed : {(self.real_data_size / 1000 / 1000) / (final_time.total_seconds())} MB/s"
            # )

    def __del__(self):
        self.close()


if __name__ == "__main__":
    main()
