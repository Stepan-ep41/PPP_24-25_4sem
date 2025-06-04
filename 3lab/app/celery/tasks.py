import time, json

from app.celery.celery_app import celery_app
from app.celery.status import Status
from app.schemas.schemas import Graph, PathResult

from app.core.config import Config

from app.algorithms1 import tsp_bruteforce_alg, tsp_greedy_alg
    
from redis import Redis

import numpy as np
import itertools



@celery_app.task(bind=True, name='app.celery.tasks.sleep10')
def sleep10(self):
    # Открываем соединенеие с каналом Redis
    r = Redis(host=Config.REDIS_HOST, port=Config.REDIS_PORT, db=0)
    
    # Отправляем уведомление о начале работы над задачей
    result = {'task_id': self.request.id, 'status': Status.START}
    r.publish('notifications', json.dumps(result))
    
    # Имитируем долго выполяющийся алгоритм
    time.sleep(5)
    # Отправляем уведомление о прогрессе работы над задачей
    result = {'task_id': self.request.id, 'status': '50%'}
    r.publish('notifications', json.dumps(result))
    
    time.sleep(5)
    
    # Отправляем уведомление о выполнении задачи
    result = {'task_id': self.request.id, 'status': Status.STOP}
    r.publish('notifications', json.dumps(result))
    return result


@celery_app.task(bind=True, name='app.celery.tasks.tsp_bruteforce')
def tsp_bruteforce(self, nodes: list, edges: list):
    # Открываем соединенеие с каналом Redis
    r = Redis(host=Config.REDIS_HOST, port=Config.REDIS_PORT, db=0)
    
    # Отправляем уведомление о начале работы над задачей
    result = {'task_id': self.request.id, 'status': Status.START}
    r.publish('notifications', json.dumps(result))

    n = len(nodes)
    matrix = np.full(fill_value=np.inf, shape=(n, n))

    for i, j in edges:
        matrix[i-1, j-1] = 1
        matrix[j-1, i-1] = 1
    for i in range(n):
        matrix[i, i] = 0
        
    # Отправляем уведомление о завершении создания матрицы
    result = {'task_id': self.request.id, 'status': 'MATRIX_READY'}
    r.publish('notifications', json.dumps(result))
    
    # Выполняем алгоритм
    path, distance = tsp_bruteforce_alg(matrix=matrix, start=1)
            
    # Отправляем уведомление о завершении расчётов
    result = {'task_id': self.request.id, 'status': Status.STOP}
    r.publish('notifications', json.dumps(result))
    
    return {'path': path, 'total_distance': distance}
    

@celery_app.task(bind=True, name='app.celery.tasks.tsp_greedy')
def tsp_greedy(self, nodes: list, edges: list):
    # Открываем соединенеие с каналом Redis
    r = Redis(host=Config.REDIS_HOST, port=Config.REDIS_PORT, db=0)
    
    # Отправляем уведомление о начале работы над задачей
    result = {'task_id': self.request.id, 'status': Status.START}
    r.publish('notifications', json.dumps(result))

    n = len(nodes)
    matrix = np.full(fill_value=np.inf, shape=(n, n))

    for i, j in edges:
        matrix[i-1, j-1] = 1
        matrix[j-1, i-1] = 1
    for i in range(n):
        matrix[i, i] = 0
        
    # Отправляем уведомление о завершении создания матрицы
    result = {'task_id': self.request.id, 'status': 'MATRIX_READY'}
    r.publish('notifications', json.dumps(result))
    
    # Выполняем алгоритм
    path, distance = tsp_greedy_alg(matrix=matrix, start=1)
        
    # Отправляем уведомление о завершении расчётов
    result = {'task_id': self.request.id, 'status': Status.STOP}
    r.publish('notifications', json.dumps(result))
    
    return {'path': path, 'total_distance': distance}