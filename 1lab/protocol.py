import socket
import struct


class size_snd_rcv_protocol():
    def __init__(self):
        self.part_size = 8
        self.max_I = 2**32-1
    
    
    def recv(self, connected_socket):
        data = connected_socket.recv(struct.calcsize('I'))
        data_size = 0
        data_size_, = struct.unpack('I', data)
        data_size += data_size_
        # print(f'1st data recieved {data_size}')
        while data_size_==self.max_I: # Проверка, не является ли пришедшее инфо о размерах посылки намёком на то, что посылка большая
            data = connected_socket.recv(struct.calcsize('I'))
            data_size_, = struct.unpack('I', data)
            data_size += data_size_
        
        read = 0
        rez_data = b''
        while read < data_size:
            size_ = min(self.part_size, data_size-read)
            # size_ = data_size
            rez_data += connected_socket.recv(size_)
            # print(f'recieved data {rez_data}')
            read += size_
            # print(read, data_size)
            
        return rez_data        
    
    
    def send(self, connected_socket, data):
        # print(f'data to send {data}')
        data_enc = data
        data_size = len(data_enc)
        # print(data_size)
        while data_size > self.max_I-1:
            connected_socket.send(struct.pack('I', self.max_I))
            data_size = data_size - self.max_I
        else:
            connected_socket.send(struct.pack('I', data_size))
            
        connected_socket.sendall(data_enc)