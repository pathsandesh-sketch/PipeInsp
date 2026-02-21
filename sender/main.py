import socket
import struct
import pickle
from config import SERVER_IP, PORT

class Streamer:
    def __init__(self):
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect((SERVER_IP, PORT))

    def send_frame(self, frame):
        data = pickle.dumps(frame)
        message = struct.pack("Q", len(data)) + data
        self.client_socket.sendall(message)

    def close(self):
        self.client_socket.close()
