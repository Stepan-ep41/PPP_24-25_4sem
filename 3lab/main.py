from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import uvicorn

import asyncio
import redis.asyncio as redis
from contextlib import asynccontextmanager

import json

import random
import string

import sqlite3

from app.api.endpoints import FastApiConfig
from app.schemas.schemas import *
from app.celery.celery_app import REDIS_BROKER
from app.celery.status import Status
from app.websocket.endpoints import WebsocketConfig

from app.celery.tasks import sleep10, tsp_bruteforce, tsp_greedy



#####################################################################################################################################################################

DB_PATH = 'app/db/3lab_database.db'


class gen_token:
    def __init__(self):
        self.all_gen = []
        # Все буквы латиницы (и заглавные, и строчные) + все цифры
        self.symbols = string.ascii_letters + string.digits
        
    
    def gen_token(self):
        token = self.gen_token_()
        while token in self.all_gen:
            token = self.gen_token_()
        self.all_gen.append(token)
        return token
            
            
    def gen_token_(self):
        return''.join(random.sample(self.symbols, 12))
    

token_generator = gen_token()
        

#################################################### ОБРАБОТКА ВСЕХ ПОЛЬЗОВАТЕЛЕЙ #########################################################################################

# Менеджер подключений для поддержки большого количества пользователей
class ConnectionManager:
    def __init__(self):
        self.connections = {}
        self.tasks = {}


    async def connect(self, ws: WebSocket, email: str, token: str):
        await ws.accept()
        print(f'NEW USER: {email} <---> {token}')
        await ws.send_text(token)
        
        self.connections[token] = ws


    def disconnect(self, ws: WebSocket, email: str, token: str):
        try:
            self.connections.pop(token)
            print(f'DISCNNCT: {email} <---> {token}')
        except Exception:
            pass


    async def broadcast(self, msg: dict):
        text = json.dumps(msg)
        task_id, status = msg['task_id'], msg['status']
        
        ################################### Подключаемся к БД для получения инфы id задачи -> токен пользователя #################################
        # connection = sqlite3.connect(DB_PATH)
        # cursor = connection.cursor()
        # cursor.execute('SELECT * FROM Tasks WHERE task_id = ?', (task_id, ))
        # row = cursor.fetchone()
        # if row:
        #     task_id, token = row
        
        token = self.tasks[task_id]
        
        ###########################################################################################################################################
        
        print(f'RUNNING:  task({task_id}): == {status:^{14}} ==')
        
        try:
            ws = self.connections[token]
            await ws.send_text(text)
        except Exception:
            pass
        
        # Удаляем записи о таске, если она выполнена
        if status==Status.STOP:
            try:
                self.tasks.pop(task_id)
            except Exception:
                pass
        #     cursor.execute('SELECT * FROM Tasks WHERE task_id = ?', (task_id, ))
        #     rows = cursor.fetchall()
        #     if rows:
        #         cursor.execute('DELETE FROM Tasks WHERE task_id = ?', (task_id, ))
        #     connection.commit()
        # connection.close()


manager = ConnectionManager()



############################################### ПОДКЛЮЧЕНИЕ FASTAPI - REDIS+CELERY ##############################################################################################

# Асинхронный lifespan manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Подключение к Redis при старте - записываем в app.state!!!
    app.state.redis = redis.from_url(REDIS_BROKER, decode_responses=True)
    print("✅ Подключение к Redis установлено")
    
    asyncio.create_task(main_loop())
    yield  # Здесь работает FastAPI
    
    # Закрытие подключения при остановке
    await app.state.redis.close()
    print("🔌 Подключение к Redis закрыто")



############################################### СОЗДАНИЕ, ЗАПУСК FASTAPI И ОСНОВНОГО ЦИКЛА ОБРАБОТКИ СОБЫТИЙ ##############################################################################################

# Теперь можно и приложение создать
app = FastAPI(lifespan=lifespan)


# Основной цикл обработки событий
async def main_loop():
    sub = app.state.redis.pubsub()
    # Подписываемся на канал уведомлений
    await sub.subscribe(WebsocketConfig.NOTIFICATIONS)
    while True:
        msg = await sub.get_message(ignore_subscribe_messages=True, timeout=None)
        if msg and msg["data"]:
            data = json.loads(msg["data"])
            await manager.broadcast(data)
        await asyncio.sleep(0.01)  # Лайфхак, чтобы не перегружать процессор



################################################ ПОДКЛЮЧЕНИЕ CLIENT - FASTAPI #############################################################################################

# Подключаем клиента по WebSocket
# Для этого сидим на канале 'notifications' и каждого 'постучавшегося' отводим к менеджеру
@app.websocket(f'/ws/{WebsocketConfig.NOTIFICATIONS}')
async def ws_client(ws: WebSocket, email: str):
    # Ждём подключения клиента
    token = token_generator.gen_token()
    await manager.connect(ws, email, token)
    # Пока не дисконнект получаем сообщения от клиента
    try:
        while True:
            # pass
            await ws.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(ws, email, token)



################################################################### ЗАПРОСЫ, РАБОТАЮЩИЕ С CELERY+REDIS ################################################################################

# ТЕСТ работы FastApi в связке с Redis+Celery
@app.post("/tasks/sleep10")
async def run_parse(user_task: UserTask):
    # Получаем токен пользователя, который прислали вместе с задачей
    token = user_task.token
    task = sleep10.delay()
    task_id = task.id
    
    ######### Заносим в БД инфу, что такая-то задача принадлежит такому-то токену ########
    # connection = sqlite3.connect(DB_PATH)
    # cursor = connection.cursor()
    # cursor.execute('INSERT INTO Tasks (task_id, token) VALUES (?, ?)', (task_id, token))
    # connection.commit()
    # row = cursor.fetchone()
    # print(row)
    # connection.close()
    
    manager.tasks[task_id] = token
    
    #######################################################################################
    
    return {"task_id": task_id}


@app.post(FastApiConfig.SHORTEST_PATH_ENDPOINT+'bruteforce/')
async def run_tsp_slow(graph_task: GraphTask):
    token = graph_task.token
    graph = graph_task.graph
    
    task = tsp_bruteforce.delay(graph.nodes, graph.edges)
    task_id = task.id
    
    manager.tasks[task_id] = token
    
    rez = task.get()
    await asyncio.sleep(0.1)

    return rez


@app.post(FastApiConfig.SHORTEST_PATH_ENDPOINT+'greedy/')
async def run_tsp_fast(graph_task: GraphTask):
    token = graph_task.token
    graph = graph_task.graph
    
    task = tsp_greedy.delay(graph.nodes, graph.edges)
    task_id = task.id
    
    manager.tasks[task_id] = token
    
    rez = task.get()
    await asyncio.sleep(0.1)

    return rez


############################################################## РАБОТА С ПОЛЬЗВАТЕЛЕМ - FASTAPI #########################################################

@app.get('/')
async def root():
    return {'message': 'This is my 3rd lab!!! I can\'t believe!'}


@app.post(FastApiConfig.SIGN_UP_ENDPOINT)
async def sing_up(user: User):
    # Переменные для токена и id
    id = None
    logged_user = {}
    
    # Подключаемся к бд
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()
    
    # Запрос на поиск пользователя по почте
    cursor.execute('SELECT * FROM Users WHERE email = ?', (user.email,))
    # Получаем все записи по запросу
    rows = cursor.fetchall()
    if not rows:
        # Запрос на добавление новую строку 
        cursor.execute('INSERT INTO Users (email, password) VALUES (?, ?)', (user.email, user.password))
        # Добавляю в словарь для return
        connection.commit()
        #Получаю id
        cursor.execute('SELECT id FROM Users WHERE email = ? AND password = ?', (user.email, user.password))
        id = cursor.fetchall()[0][0]
        # Словарь для возврата в return
        logged_user['id'] = id
        logged_user['email'] = user.email
    
    else:
        logged_user['id'] = ''
        logged_user['email'] = ''
        return {}
        
    connection.close()
    
    return {'id': logged_user['id'], 'email': logged_user['email']}


@app.post(FastApiConfig.LOGIN_ENDPOINT)
async def login(user: User):
    # Переменные для токена и id
    id = None
    logged_user = {}
    
    # Подкючаемся к бд
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()
    # Запрос на поиск пользователя по паролю и почте
    cursor.execute('SELECT * FROM Users WHERE email = ? AND password = ?', (user.email,user.password))
    # Получем данные о единственном пользователе
    rows = cursor.fetchone()
    
    connection.close()
    
    if rows:
        id, email, password = rows
        # Добавляю ответ
        logged_user['id'] = id
        logged_user['email'] = user.email
        
    else:
        logged_user['id'] = ''
        logged_user['email'] = ''
        return {}
        
    # Возвращаем инфу о пользователе
    return {'id': logged_user['id'], 'email': logged_user['email']}



################################################################### ЗАПУСК ############################################################################

if __name__ == '__main__':
    uvicorn.run(app, host=FastApiConfig.IP, port=FastApiConfig.PORT)
