from client import client
from server import server
from protocol import size_snd_rcv_protocol
import threading
import time


HOST = input('Введите хост: ')
PORT = int(input('Введите порт: '))


s = server(HOST=HOST, PORT=PORT, protocol_handler=size_snd_rcv_protocol())
c = client(HOST=HOST, PORT=PORT, protocol_handler=size_snd_rcv_protocol())

    
t_s = threading.Thread(target=s.run, args=[])
t_c = threading.Thread(target=c.run, args=[])
t_s.start()
time.sleep(1)
t_c.start()
t_c.join()
t_s.join()