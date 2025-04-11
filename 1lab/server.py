import socket
import os
import json
from protocol import size_snd_rcv_protocol


class server:
    def __init__(self, HOST, PORT, protocol_handler):
        self.protocol_handler = protocol_handler
        self.HOST = HOST
        self.PORT = PORT
        
        
    def run(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((self.HOST, self.PORT))
            self.create_info_file()
            
            s.listen()
            while True:
                client, addr = s.accept()
                self.handle_client(client)
                
        


    def handle_client(self, client):
        while True:
            recv_data = self.protocol_handler.recv(client).decode()
            if recv_data=='1':
                dir_info = self.load_info_file()
                self.protocol_handler.send(client, json.dumps(dir_info).encode())
            
            if recv_data=='2':
                dir_name = self.protocol_handler.recv(client)
                status = self.ch_server_dir(dir_name)
                self.protocol_handler.send(client, status.encode())
                
            if recv_data=='3':
                dir_name = self.protocol_handler.recv(client)
                status = self.create_ch_server_dir(dir_name)
                self.protocol_handler.send(client, status.encode())
                
            if recv_data=='-1':
                break
            
            print('Server -', recv_data)
            
        client.close()
                
                
    def get_dir_info(self):
        rez = {}
        for root, dirs, files in os.walk('./'):
            rez[root] = {}
            rez[root]['dirs'] = []
            rez[root]['files'] = []
            for dir in dirs:
                rez[root]['dirs'].append(dir)
            for file in files:
                rez[root]['files'].append(file)
        return rez
    
    
    def ch_server_dir(self, path):
        try:
            old_path = os.getcwd()
            os.chdir(path)
            self.delete_info_file(old_path)
            self.create_info_file()
        except FileNotFoundError:
            return '404' # Ошибка клинта - такой папки не существует
        except OSError:
            return '400' # Ошибка клиента - неправильное название
        return '200' # Успех
                    
                    
    def create_ch_server_dir(self, path):
        try:
            old_path = os.getcwd()
            os.makedirs(path)
            os.chdir(path)
            self.delete_info_file(old_path)
            self.create_info_file()
        except OSError:
            return '400' # Ошибка клиента - неправильное название
        return '200' # Успех
    
    
    def create_info_file(self):
        path = os.path.join('./', 'dir_info.json')
        with open(path, 'w') as f:
            dir_info = self.get_dir_info()
            json.dump(dir_info, f)
        return path
    
    
    def load_info_file(self):
        path = os.path.join('./', 'dir_info.json')
        with open(path, 'r') as f:
            dir_info = json.load(f)
        return dir_info


    def delete_info_file(self, path):
        path = os.path.join(path, 'dir_info.json')
        os.remove(path)        
    

if __name__ == '__main__':
    HOST = input('Введите хост: ')
    PORT = int(input('Введите порт: '))
    s = server(HOST=HOST, PORT=PORT, protocol_handler=size_snd_rcv_protocol())
    s.run()