"""
Modelos de datos para el sistema de enrutamiento de vehículos.
"""
from pydantic import BaseModel
from typing import List, Optional


class Vehiculo(BaseModel):
    """Modelo de vehículo."""
    id: str
    capacidad_kg: float
    latitud_origen: float
    longitud_origen: float


class Pedido(BaseModel):
    """Modelo de pedido."""
    id: str
    latitud_destino: float
    longitud_destino: float
    peso_kg: float
    ventana_inicio: str  # Formato HH:MM
    ventana_fin: str  # Formato HH:MM
    prioridad: int  # 1-5, donde 5 es la más alta
