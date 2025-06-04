import numpy as np
import itertools

from app.schemas.schemas import Graph, PathResult



def tsp_bruteforce_alg(matrix, start=1):
    start -= 1
    n = len(matrix)
    min_cost = float('inf')
    best_path = None

    # Перебираем все перестановки городов, кроме начального
    for perm in itertools.permutations(range(n)):
        if perm[0] != start:
            continue  # начинаем с фиксированного города

        cost = 0
        current = perm[0]
        for city in perm[1:]:
            cost += matrix[current][city]
            current = city
        cost += matrix[current][perm[0]]  # вернуться в начало

        if cost < min_cost:
            min_cost = cost
            best_path = perm

    best_path = [_+1 for _ in best_path]

    return best_path, min_cost


def tsp_greedy_alg(matrix, start=1):
    start -= 1
    n = len(matrix)
    visited = [False] * n
    path = [start]
    visited[start] = True
    current = start
    total_cost = 0

    for _ in range(n - 1):
        next_city = -1
        min_dist = float('inf')

        # Ищем ближайший непосещённый город
        for city in range(n):
            if not visited[city] and matrix[current][city] < min_dist:
                min_dist = matrix[current][city]
                next_city = city

        path.append(next_city)
        visited[next_city] = True
        total_cost += min_dist
        current = next_city

    # Вернуться в начальный город
    total_cost += matrix[current][start]

    path = [_+1 for _ in path]

    return path, total_cost