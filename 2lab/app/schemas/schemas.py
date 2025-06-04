from pydantic import BaseModel


# Схема для пользователя
class User(BaseModel):
    email: str
    password: str

# Схема для графа
class Graph(BaseModel):
    nodes: list[float]
    edges: list[list[float]]
    

# Схема для ответа - результата работы алгоритма
class PathResult(BaseModel):
    path: list[float]
    total_distance: float
