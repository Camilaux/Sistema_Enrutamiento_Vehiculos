import math
import random
import copy
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple
from src.models import Vehiculo, Pedido

# Configuraciones Globales
VELOCIDAD_PROMEDIO_KMH = 30.0
TIEMPO_SERVICIO_MINUTOS = 10
HORA_INICIO = "08:00"
MAX_JORNADA_HORAS = 8.0  # Límite máximo de horas laborables por vehículo

# Pesos para la Función Objetivo
W_UNASSIGNED = 600.0  # Penalización por pedido no asignado
W_LATE = 200.0        # Penalización por llegar tarde
W_OT = 500.0          # Penalización por exceder jornada
W_CAP = 20.0          # Penalización por uso de capacidad (balance)
W_WAIT = 0.5          # Penalización por tiempo de espera
W_DIST = 1.0          # Penalización por distancia (km)

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calcula la distancia del círculo máximo entre dos puntos 
    en la tierra (especificados en grados decimales) usando la fórmula de Haversine.
    
    Args:
        lat1: Latitud del primer punto en grados.
        lon1: Longitud del primer punto en grados.
        lat2: Latitud del segundo punto en grados.
        lon2: Longitud del segundo punto en grados.
        
    Returns:
        Distancia en kilómetros.
    """
    # Radio de la Tierra en kilómetros
    R = 6371.0
    
    # Convertir grados a radianes
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    lambda1 = math.radians(lon1)
    lambda2 = math.radians(lon2)
    
    # Fórmula de Haversine
    a = math.sin((phi2-phi1) / 2)**2 + \
        math.cos(phi1) * math.cos(phi2) * \
        math.sin((lambda2 - lambda1) / 2)**2
        
    c = 2 * math.asin(math.sqrt(a))
    
    distance = R * c
    return distance

def calculate_route_metrics(vehicle: Vehiculo, route: List[Pedido]) -> Dict[str, Any]:
    """
    Calcula métricas detalladas de una ruta para la función de costo.
    Retorna distacia, tiempos, carga, violaciones, etc.
    """
    metrics = {
        "distance_km": 0.0,
        "wait_minutes": 0.0,
        "load_kg": 0.0,
        "overtime_hours": 0.0,
        "lateness_count": 0,
        "is_feasible": True,
        "rejection_reason": ""
    }
    
    current_time = datetime.strptime(HORA_INICIO, "%H:%M")
    inicio_jornada = current_time
    lat_curr, lon_curr = vehicle.latitud_origen, vehicle.longitud_origen
    current_load = 0.0
    
    # Validar capacidad global primero
    total_weight = sum(p.peso_kg for p in route)
    metrics["load_kg"] = total_weight
    if total_weight > vehicle.capacidad_kg:
        metrics["is_feasible"] = False
        metrics["rejection_reason"] = f"Capacidad excedida ({total_weight} > {vehicle.capacidad_kg})"
        return metrics # Retorno temprano si es hard constraint
    
    for pedido in route:
        # Distancia y Viaje
        dist = haversine_distance(lat_curr, lon_curr, pedido.latitud_destino, pedido.longitud_destino)
        metrics["distance_km"] += dist
        hours_trip = dist / VELOCIDAD_PROMEDIO_KMH
        current_time += timedelta(hours=hours_trip)
        
        # Ventanas de Tiempo
        t_inicio = datetime.strptime(pedido.ventana_inicio, "%H:%M")
        t_fin = datetime.strptime(pedido.ventana_fin, "%H:%M")
        
        # Espera
        if current_time < t_inicio:
            wait_td = t_inicio - current_time
            metrics["wait_minutes"] += wait_td.total_seconds() / 60.0
            current_time = t_inicio
            
        # Tardanza (Lateness)
        if current_time > t_fin:
            metrics["lateness_count"] += 1
            metrics["is_feasible"] = False
            metrics["rejection_reason"] = f"Llegada tardía a {pedido.id}"
            return metrics
            
        # Servicio
        current_time += timedelta(minutes=TIEMPO_SERVICIO_MINUTOS)
        
        # Actualizar posición
        lat_curr, lon_curr = pedido.latitud_destino, pedido.longitud_destino
        
    # Validar Jornada
    total_hours = (current_time - inicio_jornada).total_seconds() / 3600.0
    if total_hours > MAX_JORNADA_HORAS:
        metrics["overtime_hours"] = total_hours - MAX_JORNADA_HORAS
        metrics["is_feasible"] = False
        metrics["rejection_reason"] = f"Excede jornada máxima ({round(total_hours, 2)}h)"
        return metrics
        
    return metrics

def calculate_global_cost(vehiculos_dict: Dict[str, Vehiculo], routes: Dict[str, List[Pedido]], unassigned: List[Any]) -> float:
    """
    Calcula el costo global (Función Objetivo).
    C_global = Sum(C_ruta) + Sum(C_unassigned)
    """
    total_cost = 0.0
    
    # 1. Costo por Ruta
    for vid, route in routes.items():
        veh = vehiculos_dict[vid]
        m = calculate_route_metrics(veh, route)
        
        # Penalización infinita por rutas inviables (validación estricta)
        if not m["is_feasible"]:
            return float('inf')
            
        # Componentes del costo de ruta
        # C_ruta = wD*D + wWait*Wait + wCap*U^2 ...
        
        # Capacidad al cuadrado (ratio)
        load_ratio = m["load_kg"] / veh.capacidad_kg if veh.capacidad_kg > 0 else 0
        cap_cost = W_CAP * (load_ratio ** 2)
        
        route_cost = (
            W_DIST * m["distance_km"] +
            W_WAIT * (m["wait_minutes"] / 60.0) + # convertir a horas para consistencia
            cap_cost
        )
        # Nota: Lateness y OT son hard constraints aquí, así que sus costos son 0 o Infinito (manejado arriba).
        # Si quisieramos soft constraints, sumaríamos W_LATE * count + W_OT * hours
        
        total_cost += route_cost

    # 2. Costo por No Asignados
    for item in unassigned:
        # Manejar tanto objetos Pedido puros como dicts {pedido, razon}
        p = item["pedido"] if isinstance(item, dict) else item
        
        # Penalización cuadrática por prioridad: w_un * prio^2
        # Asumiendo prioridad numerica alta es mas importante (e.g. 1 a 5)
        # Si priority 5 es mas importante:
        prio_cost = W_UNASSIGNED * (p.prioridad ** 2)
        total_cost += prio_cost
        
    return total_cost

def calculate_route_cost(vehicle: Vehiculo, route: List[Pedido]) -> float:
    """Calcula el costo de una sola ruta (wrapper legacy para compatibilidad parcial)."""
    # Esta funcion se usa internamente en SA para delta calculo rapido si solo cambia una ruta,
    # pero la funcion objetivo requiere contexto global o recalculo preciso.
  
    m = calculate_route_metrics(vehicle, route)
    if not m["is_feasible"]:
        return float('inf')
    
    load_ratio = m["load_kg"] / vehicle.capacidad_kg if vehicle.capacidad_kg > 0 else 0
    
    cost = (
        W_DIST * m["distance_km"] +
        W_WAIT * (m["wait_minutes"] / 60.0) +
        W_CAP * (load_ratio ** 2)
    )
    return cost

def solve_vrp_greedy(vehiculos: List[Vehiculo], pedidos: List[Pedido]) -> Dict[str, Any]:
    """
    Algoritmo Greedy Constructivo Mejorado.
    Evalúa inserción en TODAS las posiciones posibles para encontrar el mejor lugar.
    """
    # 1. Ordenar por Prioridad (desc) y Ventana
    pedidos_ordenados = sorted(pedidos, key=lambda x: (-x.prioridad, x.ventana_inicio))
    
    rutas = {v.id: [] for v in vehiculos}
    pedidos_no_asignados = [] 
    
    # Mapeo id -> objeto
    veh_dict = {v.id: v for v in vehiculos}

    for pedido in pedidos_ordenados:
        best_cost_increase = float('inf')
        best_insertion = None # (veh_id, index)
        rejection_reasons = []
        
        # Verificar peso maximo absoluto
        max_cap = max(v.capacidad_kg for v in vehiculos)
        if pedido.peso_kg > max_cap:
            pedidos_no_asignados.append({
                "pedido": pedido,
                "razon": f"Peso excesivo ({pedido.peso_kg} > max flota {max_cap})"
            })
            continue

        # Probar inserción en cada vehículo y cada posición
        candidate_found = False
        
        for v in vehiculos:
            current_route = rutas[v.id]
            
            # Calcular costo base de la ruta actual
            base_cost = calculate_route_cost(v, current_route)
            if base_cost == float('inf'): # Should not happen if logic is sound
                base_cost = 0 
            
            # Probar posiciones 0..N
            for i in range(len(current_route) + 1):
                # Simular ruta
                temp_route = current_route[:i] + [pedido] + current_route[i:]
                
                # Calcular nuevo costo
                # calculate_route_cost retorna Inf si no es factible (hard constraint check interno)
                new_cost = calculate_route_cost(v, temp_route)
                
                if new_cost != float('inf'):
                    delta = new_cost - base_cost
                    if delta < best_cost_increase:
                        best_cost_increase = delta
                        best_insertion = (v.id, i)
                        candidate_found = True
                else:
                    # Solo para debug/razones
                    m = calculate_route_metrics(v, temp_route)
                    rejection_reasons.append(f"{v.id}: {m['rejection_reason']}")

        # Aplicar mejor inserción
        if candidate_found and best_insertion:
            vid, idx = best_insertion
            rutas[vid].insert(idx, pedido)
        else:
            reason = "; ".join(list(set(rejection_reasons))) if rejection_reasons else "No factible en ninguna ruta"
            pedidos_no_asignados.append({
                "pedido": pedido,
                "razon": reason
            })
            
    return {
        "rutas": rutas,
        "no_asignados": pedidos_no_asignados,
        "metricas": {
            "total_pedidos": len(pedidos),
            "asignados": len(pedidos) - len(pedidos_no_asignados),
            "no_asignados_count": len(pedidos_no_asignados)
        }
    }


def solve_vrp_simulated_annealing(vehiculos: List[Vehiculo], pedidos: List[Pedido], 
                                  initial_temp=1000, cooling_rate=0.995, max_iterations=10000) -> Dict[str, Any]:
    """
    Optimiza las rutas usando Simulated Annealing con función objetivo avanzada.
    Incluye movimientos para insertar pedidos no asignados.
    """
    # 1. Solución Inicial (Greedy)
    greedy_sol = solve_vrp_greedy(vehiculos, pedidos)
    current_routes = greedy_sol["rutas"]
    no_asignados = greedy_sol["no_asignados"] # Lista de dicts {pedido, razon}
    
    # Mapeo rápido de objeto vehiculo
    vehiculos_dict = {v.id: v for v in vehiculos}
    
    current_cost = calculate_global_cost(vehiculos_dict, current_routes, no_asignados)
    best_routes = copy.deepcopy(current_routes)
    best_no_asignados = copy.deepcopy(no_asignados)
    best_cost = current_cost
    
    temp = initial_temp
    
    for i in range(max_iterations):
        # Copiar estado
        new_routes = copy.deepcopy(current_routes)
        new_no_asignados = copy.deepcopy(no_asignados)
        
        # Seleccionar movimiento
        # Aumentamos probabilidad de "insert_unassigned" si hay unassigned
        options = ['swap_inter', 'move_inter', 'swap_intra']
        if new_no_asignados:
            options.append('insert_unassigned')
            options.append('insert_unassigned') # Doble chance
            
        move_type = random.choice(options)
        
        v_ids = list(new_routes.keys())
        v1_id = random.choice(v_ids)
        route1 = new_routes[v1_id]
        
        moved = False
        
        if move_type == 'insert_unassigned' and new_no_asignados:
            # Intentar insertar un pedido no asignado (priorizando alta prioridad)
            # Ordenar temporamente para el intento (o random weighted)
            # Simplemente tomamos uno random para SA (exploracion) o uno de alta prioridad
            
            # Estrategia híbrida: Random pero sesgado a alta prioridad?
            # Simple: Random choice
            idx_un = random.randint(0, len(new_no_asignados)-1)
            item_un = new_no_asignados[idx_un]
            p_un = item_un["pedido"]
            
            # Intentar insertar en la mejor posición de un vehículo random o el mejor?
            # SA prefiere cambios pequeños, probemos insertar en UN vehiculo random en SU mejor posicion
            v_target_id = random.choice(v_ids)
            r_target = new_routes[v_target_id]
            veh_target = vehiculos_dict[v_target_id]
            
            best_pos = -1
            min_local_cost = float('inf')
            
            # Probar todas las posiciones en este vehiculo
            for pos in range(len(r_target)+1):
                temp_r = r_target[:pos] + [p_un] + r_target[pos:]
                # Verificar factibilidad rápida (metrics)
                cost = calculate_route_cost(veh_target, temp_r) # Usamos calculate_route_cost wrapper que usa metricas nuevas
                if cost != float('inf'):
                    if cost < min_local_cost:
                        min_local_cost = cost
                        best_pos = pos
            
            if best_pos != -1:
                # Realizar inserción
                r_target.insert(best_pos, p_un)
                new_no_asignados.pop(idx_un)
                moved = True

        elif move_type == 'swap_inter' and len(v_ids) > 1:
            # Intercambiar pedido entre dos vehiculos distintos
            v2_id = random.choice([v for v in v_ids if v != v1_id])
            route2 = new_routes[v2_id]
            
            if route1 and route2:
                idx1 = random.randint(0, len(route1)-1)
                idx2 = random.randint(0, len(route2)-1)
                
                # Swap
                p1, p2 = route1[idx1], route2[idx2]
                route1[idx1] = p2
                route2[idx2] = p1
                
                # Check Hard Constraints
                # calculate_route_cost retorna inf si check falla
                c1 = calculate_route_cost(vehiculos_dict[v1_id], route1)
                c2 = calculate_route_cost(vehiculos_dict[v2_id], route2)
                
                if c1 != float('inf') and c2 != float('inf'):
                    moved = True

        elif move_type == 'move_inter' and len(v_ids) > 1:
            # Mover un pedido de v1 a v2
            v2_id = random.choice([v for v in v_ids if v != v1_id])
            route2 = new_routes[v2_id]
            
            if route1:
                idx1 = random.randint(0, len(route1)-1)
                p_move = route1.pop(idx1)
                
                # Insertar en posición aleatoria
                insert_idx = random.randint(0, len(route2))
                route2.insert(insert_idx, p_move)
                
                c1 = calculate_route_cost(vehiculos_dict[v1_id], route1)
                c2 = calculate_route_cost(vehiculos_dict[v2_id], route2)
                
                if c1 != float('inf') and c2 != float('inf'):
                    moved = True

        elif move_type == 'swap_intra':
            # Intercambiar orden dentro de la misma ruta
            if len(route1) > 1:
                idx1, idx2 = random.sample(range(len(route1)), 2)
                route1[idx1], route1[idx2] = route1[idx2], route1[idx1]
                
                c1 = calculate_route_cost(vehiculos_dict[v1_id], route1)
                if c1 != float('inf'):
                    moved = True
        
        # Evaluar Solución
        if moved:
            new_cost = calculate_global_cost(vehiculos_dict, new_routes, new_no_asignados)
            delta = new_cost - current_cost
            
            # Aceptar si mejora O si cumple criterio de metropolis
            # Nota: Si new_cost es inf (no feasible), delta es inf, no entra.
            if delta < 0 or random.random() < math.exp(-delta / temp):
                current_routes = new_routes
                no_asignados = new_no_asignados
                current_cost = new_cost
                
                if current_cost < best_cost:
                    best_routes = copy.deepcopy(current_routes)
                    best_no_asignados = copy.deepcopy(no_asignados)
                    best_cost = current_cost
        
        # Enfriar
        temp *= cooling_rate
        
    return {
        "rutas": best_routes,
        "no_asignados": best_no_asignados, 
        "metricas": {
            "total_pedidos": len(pedidos),
            "asignados": len(pedidos) - len(best_no_asignados),
            "no_asignados_count": len(best_no_asignados)
        }
    }