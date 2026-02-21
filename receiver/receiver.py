import socket
import struct
import pickle
from config import PORT, BUFFER_SIZE

class Receiver:
    def __init__(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind(("0.0.0.0", PORT))
        self.server_socket.listen(1)
        print("Waiting for connection...")
        self.conn, self.addr = self.server_socket.accept()
        print(f"Connected to {self.addr}")
        self.data = b""
        self.payload_size = struct.calcsize("Q")

    def receive_frame(self):
        while len(self.data) < self.payload_size:
            self.data += self.conn.recv(BUFFER_SIZE)

        packed_msg_size = self.data[:self.payload_size]
        self.data = self.data[self.payload_size:]
        msg_size = struct.unpack("Q", packed_msg_size)[0]

        while len(self.data) < msg_size:
            self.data += self.conn.recv(BUFFER_SIZE)

        frame_data = self.data[:msg_size]
        self.data = self.data[msg_size:]

        frame = pickle.loads(frame_data)
        return frame
