import socket
import os
import json
from protocol import size_snd_rcv_protocol


class client:
    def __init__(self, HOST, PORT, protocol_handler):
        self.protocol_handler = protocol_handler
        self.HOST = HOST
        self.PORT = PORT   


    def run(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((self.HOST, self.PORT))
            
            while True:
                inpt = input()
                if inpt=='\get_dir_info': # Команда 1
                    print('client - 1')
                    self.get_dir_info(s)
                    
                if inpt[:3]=='\cd': # Команда 2
                    print('client - 2')
                    self.ch_server_dir(s, inpt[3:])
                    
                if inpt[:9]=='\makedirs': # Команда 3
                    print('client - 3')
                    self.create_ch_server_dir(s, inpt[:9])
                    
                if inpt=='\close': # Команда -1
                    print('client - -1')
                    self.protocol_handler.send(s, '-1'.encode())
                    s.close()
                    break
                    
                # self.protocol_handler.send(s, inpt.encode())
                
                
    def get_dir_info(self, server):
        self.protocol_handler.send(server, '1'.encode())
        dir_info = json.loads(self.protocol_handler.recv(server))
        self.render_json(dir_info)
        print(self.render_str)
    
    
    def ch_server_dir(self, server, path):
        self.protocol_handler.send(server, '2'.encode())
        path = path[1:] if path[0]==' ' else path
        self.protocol_handler.send(server, path.encode())
        status = self.protocol_handler.recv(server).decode()
        print(status)
        if status=='400':
            print('INVALID DIR NAME!!!')
        if status=='404' and input(f'Вы хотите создать новую папку с названием {path} и установить её как корневую? (1/0): ')=='1':
            self.create_ch_server_dir(server, path)
                
                
    def create_ch_server_dir(self, server, path):
        self.protocol_handler.send(server, '3'.encode())
        path = path[1:] if path[0]==' ' else path
        self.protocol_handler.send(server, path.encode())
        status = self.protocol_handler.recv(server).decode()
        print(status)
        if status=='400':
            print('INVALID DIR NAME!!!')
            
            
    def render_json(self, data):
        self.render_str = './\n'
        self.render_json_(data, os.path.join('./'))
        
        
    def render_json_(self, data, path, depth=1):
            def branch(depth):
                return '|   '*(depth-1) + '|—— '
                        
            for dir in data[path]['dirs']:
                path_ = os.path.join(path, dir)
                self.render_str = self.render_str + branch(depth) + path_ + '\n'
                self.render_json_(data, path_, depth+1)
            for file in data[path]['files']:
                self.render_str = self.render_str + branch(depth) + file + '\n'



if __name__ == '__main__':
    HOST = 'localhost'
    PORT = 12345
    c = client(HOST=HOST, PORT=PORT, protocol_handler=size_snd_rcv_protocol())
    c.run()