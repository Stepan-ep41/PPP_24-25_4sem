from client import client
from server import server
from protocol import size_snd_rcv_protocol
import threading


HOST = 'localhost'
PORT = 12345


s = server(HOST=HOST, PORT=PORT, protocol_handler=size_snd_rcv_protocol())
c = client(HOST=HOST, PORT=PORT, protocol_handler=size_snd_rcv_protocol())

    
t_s = threading.Thread(target=s.run, args=[]) # Почему так? Потому что self - это на самом деле первый аргумент
t_c = threading.Thread(target=c.run, args=[]) # А это второй вариант той же записи
t_s.start()
# time.sleep(1) # Чтоб сервер успел запуститься
t_c.start()
t_c.join() # Ждем завершения потоков
t_s.join()