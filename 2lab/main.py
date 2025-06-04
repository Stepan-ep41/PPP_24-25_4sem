from fastapi import FastAPI
import uvicorn

import random
import string

import sqlite3

from app.api.endpoints import FastApiConfig
from app.schemas.schemas import *



#####################################################################################################################################################################

app = FastAPI()
DB_PATH = 'app/db/2lab_database.db'


def gen_token():
    # Все буквы латиницы (и заглавные, и строчные) + все цифры
    symbols = string.ascii_letters + string.digits
    
    return ''.join(random.sample(symbols, 12))



#####################################################################################################################################################################

@app.get('/')
async def root():
    return {'message': 'This is my 2nd lab!!!'}


logged_user = {'id': '', 'email': ''}

@app.post(FastApiConfig.SIGN_UP_ENDPOINT)
async def sing_up(user: User):
    # Переменные для токена и id
    token, id = None, None
    
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
        token = gen_token()
        # Словарь для возврата в return
        logged_user['id'] = id
        logged_user['email'] = user.email
    
    else:
        logged_user['id'] = ''
        logged_user['email'] = ''
        return {}
        
    connection.close()
    
    return {'id': logged_user['id'], 'email': logged_user['email'], 'token': token}


@app.post(FastApiConfig.LOGIN_ENDPOINT)
async def login(user: User):
    # Переменные для токена и id
    token, id = None, None
    # Пустой словарь на случай, если такой пользователь уже есть
    cur_user = {}
    
    # Подкючаемся к бд
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()
    # Запрос на поиск пользователя по паролю и почте
    cursor.execute("SELECT * FROM Users WHERE email = ? AND password = ?", (user.email,user.password))
    # Получем данные о единственном пользователе
    rows = cursor.fetchone()
    
    connection.close()
    
    if rows:
        id, email, password = rows
        # Генерирую токен
        token = gen_token()
        # Добавляю ответ
        logged_user['id'] = id
        logged_user['email'] = user.email
        
    else:
        logged_user['id'] = ''
        logged_user['email'] = ''
        return {}
        
    # Возвращаем инфу о пользователе
    return {'id': logged_user['id'], 'email': logged_user['email'], 'token': token}


@app.get(FastApiConfig.USERS_ME_ENDPOINT)
async def users_me():
    return logged_user



@app.post(FastApiConfig.SHORTEST_PATH_ENDPOINT)
async def calculate():
    pass



if __name__ == '__main__':
    uvicorn.run(app, host=FastApiConfig.IP, port=FastApiConfig.PORT)
