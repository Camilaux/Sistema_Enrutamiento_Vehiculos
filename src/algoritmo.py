import math
from typing import List, Dict, Any
from src.models import Vehiculo, Pedido

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

def solve_vrp_greedy(vehiculos: List[Vehiculo], pedidos: List[Pedido]) -> Dict[str, Any]:
    """
    Algoritmo Greedy Constructivo para asignar pedidos a vehículos.
    Criterios:
    1. Ordenar por Prioridad (desc) y Ventana de Inicio (asc).
    2. Asignar al vehículo disponible que minimice el incremento de distancia
       (Greedy espacial) y respete la capacidad.
    """
    # 1. Ordenar pedidos: Mayor prioridad, luego Ventana Inicio más temprana
    pedidos_ordenados = sorted(pedidos, key=lambda x: (-x.prioridad, x.ventana_inicio))
    
    # Estructuras de estado
    rutas = {v.id: [] for v in vehiculos}
    carga_vehiculos = {v.id: 0.0 for v in vehiculos}
    # Ubicación actual de cada vehículo (inicialmente su origen)
    ubicacion_vehiculos = {v.id: (v.latitud_origen, v.longitud_origen) for v in vehiculos}
    
    pedidos_no_asignados = []
    
    for pedido in pedidos_ordenados:
        best_vehiculo_id = None
        min_distance_increment = float('inf')
        
        for vehiculo in vehiculos:
            # Validar Capacidad
            current_load = carga_vehiculos[vehiculo.id]
            if current_load + pedido.peso_kg <= vehiculo.capacidad_kg:
                
                # Calcular costo: Distancia desde la última ubicación del vehículo
                last_lat, last_lon = ubicacion_vehiculos[vehiculo.id]
                dist = haversine_distance(last_lat, last_lon, pedido.latitud_destino, pedido.longitud_destino)
                
                # Elegir el que minimice la distancia adicional
                if dist < min_distance_increment:
                    min_distance_increment = dist
                    best_vehiculo_id = vehiculo.id
        
        if best_vehiculo_id:
            # Asignar al mejor vehículo encontrado
            rutas[best_vehiculo_id].append(pedido)
            carga_vehiculos[best_vehiculo_id] += pedido.peso_kg
            
            # Actualizar ubicación del vehículo al destino del pedido recién asignado
            ubicacion_vehiculos[best_vehiculo_id] = (pedido.latitud_destino, pedido.longitud_destino)
        else:
            pedidos_no_asignados.append(pedido)
            
    return {
        "rutas": rutas,
        "no_asignados": pedidos_no_asignados,
        "metricas": {
            "total_pedidos": len(pedidos),
            "asignados": len(pedidos) - len(pedidos_no_asignados),
            "no_asignados_count": len(pedidos_no_asignados)
        }
    }