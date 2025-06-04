import websockets
import httpx

import json

import asyncio

import sys
import os
from prompt_toolkit import PromptSession
from prompt_toolkit.patch_stdout import patch_stdout

from app.core.config import Config
from app.websocket.endpoints import WebsocketConfig
from app.api.endpoints import FastApiConfig


class AsyncClient:
    def __init__(self):
        self.fastapi_url = f'http://{Config.IP}:{Config.PORT}'
        self.ws_url = f'ws://{Config.IP}:{Config.PORT}/ws/{WebsocketConfig.NOTIFICATIONS}'
         
        self.token = ''
        self.email = ''
        
        self.condition = True
        
        self.session = PromptSession()
        
        self.commands = [
            'login',
            'sign_up',
            'exit',
            'solve',
            'sleep10'
        ]


    async def notification(self, type:str, message: str):
        with patch_stdout():
            print(f'[{type}]: {message}')
            sys.stdout.flush()


    async def safe_print(self, message: str):
        with patch_stdout():
            prefix = f"[{self.email.split('@')[0]} <---> {self.token}]" if self.token else "[anon <---> anon]"
            print(f"{prefix} --> {message}\n", end="")
        

    async def ws_listen(self):
        while self.condition:
                try:
                    if self.email:
                        # Подключение к каналу Websocket
                        async with websockets.connect(f'{self.ws_url}?email={self.email}') as ws:
                            token = await ws.recv()
                            self.token = token
                            await self.notification('CONNECTION', f'CONNECTION ESTABLISHED: {self.email} <---> {self.token}\n\n{"="*50}\n')
                            async for message in ws:
                                data = json.loads(message)
                                await self.notification('NOTIFICATION', json.dumps(data, ensure_ascii=False))

                    else:
                        # Чтобы не зажирать cpu и не уходить в бесконечный цикл
                        await asyncio.sleep(0.01)

                except Exception as e:
                    await self.notification('ERROR', f'WebSocket error: {str(e)}')
                    # Задержка перед повторной попыткой
                    await asyncio.sleep(5)
                
                
    async def login(self):
        email = await self.session.prompt_async('Email: ')
        password = await self.session.prompt_async('Password: ')
        # Асинхронная работа с сервером HTTP
        async with httpx.AsyncClient() as client:
            try:
                # Отправляем запрос
                response = await client.post(
                    f"{self.fastapi_url}{FastApiConfig.LOGIN_ENDPOINT}",
                    json={'email': email, 'password': password}
                )
                
                # Обработка статусов запроса
                if response.status_code == 200:
                    data = response.json()
                    self.email = data['email']
                    await self.notification('CONNECTION', 'Login succeeded! Please, wait for your token!')
                else:
                    await self.notification('ERROR', f'{response.text}')
                    
            except Exception as e:
                await self.notification('ERROR', f'CONN ERROR: {str(e)}')
    
    
    async def sign_up(self):
        email = await self.session.prompt_async('Email: ')
        password = await self.session.prompt_async('Password: ')
        # Асинхронная работа с сервером HTTP
        async with httpx.AsyncClient() as client:
            try:
                # Отправляем запрос
                response = await client.post(
                    f"{self.fastapi_url}{FastApiConfig.SIGN_UP_ENDPOINT}",
                    json={'email': email, 'password': password}
                )
                
                # Обработка статусов запроса
                if response.status_code == 200:
                    data = response.json()
                    self.email = data['email']
                    await self.connection('CONNECTION', 'Registraion and Login succeeded! Please, wait for your token!')
                else:
                    await self.notification('ERROR', f'{response.text}')
                    
            except Exception as e:
                await self.notification('ERROR', f'CONN ERROR: {str(e)}')
    
    
    async def solve(self):
        # Получаем граф текстом или 
        graph = await self.session.prompt_async('Graph (type PATH to import graph): ')
        if graph=='PATH':
            path = await self.session.prompt_async('Path: ')
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    graph = json.load(f)
            except Exception:
                raise Exception('Wrong file!')
        else:
            try:
                graph = json.loads(graph)
            except Exception:
                raise Exception('Invalid input')
        algorithm = await self.session.prompt_async('Algotirhm (bruteforce/greedy): ')
        
        # Асинхронная работа с сервером HTTP
        async with httpx.AsyncClient() as client:
            try:
                # Разрешаем вызывать задачи ТОЛЬКО авторизованным пользователям - иначе всё зависло
                if not self.token:
                    raise Exception('Login first!') 
                # Отправляем запрос
                response = await client.post(
                    f"{self.fastapi_url}{FastApiConfig.SHORTEST_PATH_ENDPOINT}{algorithm}/",
                    json = {'token': self.token, 'graph': graph['graph']},
                )
                # Постим ответ
                await self.notification('RESULT', response.json())
                    
            except Exception as e:
                await self.notification('ERROR', f'ERROR: {str(e)}')
    
    
    # Тестовая комманда, вызывающая тестовую функцию sleep10
    async def sleep10(self):
        # Асинхронная работа с сервером HTTP
        async with httpx.AsyncClient() as client:
            try:
                # Разрешаем вызывать задачи ТОЛЬКО авторизованным пользователям - иначе всё зависло
                if not self.token:
                    raise Exception('Login first!') 
                # Отправляем запрос
                response = await client.post(
                    f"{self.fastapi_url}/tasks/sleep10",
                    json = {'token': self.token},
                )
                    
            except Exception as e:
                await self.notification('ERROR', f'ERROR: {str(e)}')
    
    
    def exit(self):
        self.condition = False
        sys.exit()
    
    
    async def get_command(self):
        while self.condition:
            try:
                command = await self.session.prompt_async(
                    f'Enter command ({"/".join(self.commands)}): ',
                    refresh_interval=0.1
                )

                if command in self.commands:
                    await eval(f'self.{command}')()
                else:
                    await self.safe_print(f'Invalid command!\nUse one of available ones: {", ".join(self.commands)}!')
                    
            except KeyboardInterrupt:
                await self.exit()
            except Exception as e:
                await self.notification('ERROR', f'ERROR: {str(e)}')
                
    
    async def run(self):
        # Слушаем, что говорит пользователь
        self.input_task = asyncio.create_task(self.get_command())
        # Слушаем, что говорят по сокету
        self.ws_task = asyncio.create_task(self.ws_listen())
        
        await asyncio.gather(
            self.ws_task,
            self.input_task,
            return_exceptions=True
        )
        

if __name__ == "__main__": 
    client = AsyncClient()
    try:
        asyncio.run(client.run())
    except KeyboardInterrupt:
        pass