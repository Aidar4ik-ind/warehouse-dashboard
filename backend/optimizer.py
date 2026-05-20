from pulp import *
import json

def solve_optimization(data):
    """
    data: dict с полями:
        - product_demands: list [d1..d7]
        - zone_capacities: list [cap1..cap7]
        - time_matrix: list of lists 7x7 (необязательно, используем стандартную)
        - allowed_matrix: list of lists 7x7 (необязательно)
    """
    # Параметры по умолчанию из ВКР (Таблица П.Д + экспертные оценки времени)
    # Индексы: товары T1..T7, зоны Z1..Z7
    default_capacities = [1000, 1500, 1200, 2000, 3000, 2500, 1800]
    # Матрица времени размещения (мин на 100 кг) - экспертная оценка
    default_time = [
        [5, 6, 99, 99, 99, 7, 99],  # T1
        [5, 5, 8, 99, 99, 6, 99],  # T2
        [99, 7, 99, 9, 99, 8, 99], # T3
        [99, 6, 7, 8, 99, 7, 99],  # T4
        [99, 8, 7, 8, 9, 99, 10],  # T5
        [99, 99, 9, 8, 7, 99, 9],  # T6
        [4, 5, 99, 99, 99, 99, 6]   # T7
    ]
    # Матрица допустимости (1 - можно, 0 - нельзя)
    default_allowed = [
        [1,1,0,0,0,1,0],
        [1,1,1,0,0,1,0],
        [0,1,0,1,0,1,0],
        [0,1,1,1,0,1,0],
        [0,1,1,1,1,0,1],
        [0,0,1,1,1,0,1],
        [1,1,0,0,0,0,1]
    ]
    
    capacities = data.get('zone_capacities', default_capacities)
    time_matrix = data.get('time_matrix', default_time)
    allowed = data.get('allowed_matrix', default_allowed)
    demands = data.get('product_demands', [500, 800, 600, 700, 1200, 900, 400])  # пример
    
    I = len(demands)   # 7 товаров
    J = len(capacities) # 7 зон
    
    # Создаём модель
    model = LpProblem("Warehouse_Optimization", LpMinimize)
    
    # Переменные x[i][j] (неотрицательные)
    x = [[LpVariable(f"x_{i}_{j}", lowBound=0) for j in range(J)] for i in range(I)]
    
    # Целевая функция: сумма x[i][j] * time_matrix[i][j]
    model += lpSum(x[i][j] * time_matrix[i][j] for i in range(I) for j in range(J) if allowed[i][j] == 1)
    
    # Ограничения: сумма по i <= capacity[j] для каждой зоны j
    for j in range(J):
        model += lpSum(x[i][j] for i in range(I) if allowed[i][j] == 1) <= capacities[j]
    
    # Ограничения: сумма по j = demand[i] для каждого товара i
    for i in range(I):
        model += lpSum(x[i][j] for j in range(J) if allowed[i][j] == 1) == demands[i]
    
    # Решаем
    solver = PULP_CBC_CMD(msg=False)
    model.solve(solver)
    
    if model.status != 1:
        return {"error": "Нет допустимого решения. Уменьшите объёмы товаров или увеличьте вместимость зон."}
    
    # Собираем результаты
    allocation = [[0]*J for _ in range(I)]
    for i in range(I):
        for j in range(J):
            if allowed[i][j]:
                allocation[i][j] = x[i][j].varValue if x[i][j].varValue is not None else 0
    
    total_time = value(model.objective)
    
    # Заполненность зон
    zone_utilization = [0]*J
    for j in range(J):
        zone_utilization[j] = sum(allocation[i][j] for i in range(I))
    
    # Процент оптимизации (сравниваем с простым жадным размещением)
    # Жадный алгоритм: размещаем товары с наименьшим временем в свободные зоны
    greedy_time = greedy_allocation(demands, capacities, time_matrix, allowed)
    improvement = (greedy_time - total_time) / greedy_time * 100 if greedy_time > 0 else 0
    
    return {
        "status": "optimal",
        "allocation": allocation,
        "total_time": round(total_time, 2),
        "zone_utilization": [round(u, 2) for u in zone_utilization],
        "zone_capacities": capacities,
        "improvement_percent": round(improvement, 2),
        "greedy_time": round(greedy_time, 2)
    }

def greedy_allocation(demands, capacities, time_matrix, allowed):
    """Простое эвристическое размещение для сравнения"""
    I = len(demands)
    J = len(capacities)
    remaining_demand = demands[:]
    remaining_capacity = capacities[:]
    total_time = 0
    # сортируем товары по "скорости" - не точная имитация, но даст базу
    for i in range(I):
        for j in sorted(range(J), key=lambda j: time_matrix[i][j] if allowed[i][j] else 999):
            if allowed[i][j] and remaining_demand[i] > 0 and remaining_capacity[j] > 0:
                take = min(remaining_demand[i], remaining_capacity[j])
                total_time += take * time_matrix[i][j]
                remaining_demand[i] -= take
                remaining_capacity[j] -= take
    return total_time
