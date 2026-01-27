import math
from typing import List, Dict, Any

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

if __name__ == "__main__":
    # Ejemplo de uso
    lat1, lon1 = 19.4326, -99.1332
    lat2, lon2 = 19.55, -99.1  
    distancia = haversine_distance(lat1, lon1, lat2, lon2)
    print(f"La distancia es {distancia:.2f} km")