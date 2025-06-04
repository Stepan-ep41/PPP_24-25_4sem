from pydantic import BaseModel


# Схема для пользователя
class User(BaseModel):
    email: str
    password: str


# Схема для графа
class Graph(BaseModel):
    nodes: list[int]
    edges: list[list[int]]


# Схема для запроса
class GraphTask(BaseModel):
    token: str
    graph: Graph
    

# Схема для ответа - результата работы алгоритма
class PathResult(BaseModel):
    path: list[int]
    total_distance: int


# Схема для отправки данных о пользователе, заказавшем задачу
class UserTask(BaseModel):
    token: str