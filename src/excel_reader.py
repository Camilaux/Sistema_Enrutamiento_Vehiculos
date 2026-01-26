"""
Módulo para leer y procesar el archivo Excel con los datos de vehículos y pedidos.
"""
import pandas as pd
from typing import List, Tuple
from src.models import Vehiculo, Pedido


def leer_vehiculos(filepath: str, sheet_name: str) -> List[Vehiculo]:
    """
    Lee los vehículos desde una hoja del Excel.
    
    Args:
        filepath: Ruta al archivo Excel
        sheet_name: Nombre de la hoja (ej: 'E1_Vehiculos')
    
    Returns:
        Lista de objetos Vehiculo
    """
    try:
        # Usar engine='openpyxl' explícitamente y cerrar el archivo después
        with pd.ExcelFile(filepath, engine='openpyxl') as xls:
            df = pd.read_excel(xls, sheet_name=sheet_name)
        
        # Validar que existan las columnas necesarias
        # Intentar diferentes variaciones de nombres de columnas
        columnas_posibles = [
            ['ID', 'Capacidad (kg)', 'Latitud Origen', 'Longitud Origen'],
            ['ID', 'Capacidad máxima (kg)', 'Latitud', 'Longitud']
        ]
        
        df_vehiculos = None
        columnas_encontradas = None
        for columnas in columnas_posibles:
            if all(col in df.columns for col in columnas):
                df_vehiculos = df[columnas].copy()
                columnas_encontradas = columnas
                break
        
        if df_vehiculos is None:
            raise ValueError(f"No se encontraron las columnas esperadas en {sheet_name}. Columnas disponibles: {df.columns.tolist()}")
        
        # Usar los nombres originales de las columnas del Excel
        col_id = columnas_encontradas[0]
        col_capacidad = columnas_encontradas[1]
        col_latitud = columnas_encontradas[2]
        col_longitud = columnas_encontradas[3]
        
        vehiculos = []
        for _, row in df_vehiculos.iterrows():
            # Limpiar valores NaN
            if pd.isna(row[col_id]) or pd.isna(row[col_capacidad]):
                continue
                
            vehiculo = Vehiculo(
                id=str(row[col_id]).strip(),
                capacidad_kg=float(row[col_capacidad]),
                latitud_origen=float(row[col_latitud]),
                longitud_origen=float(row[col_longitud])
            )
            vehiculos.append(vehiculo)
        
        return vehiculos
    
    except Exception as e:
        raise Exception(f"Error al leer vehículos de {sheet_name}: {str(e)}")


def leer_pedidos(filepath: str, sheet_name: str) -> List[Pedido]:
    """
    Lee los pedidos desde una hoja del Excel.
    
    Args:
        filepath: Ruta al archivo Excel
        sheet_name: Nombre de la hoja (ej: 'E1_Pedidos')
    
    Returns:
        Lista de objetos Pedido
    """
    try:
        # Usar engine='openpyxl' explícitamente y cerrar el archivo después
        with pd.ExcelFile(filepath, engine='openpyxl') as xls:
            df = pd.read_excel(xls, sheet_name=sheet_name)
        
        # Validar que existan las columnas necesarias
        # Intentar diferentes variaciones de nombres de columnas
        columnas_posibles = [
            ['ID', 'Latitud Destino', 'Longitud Destino', 'Peso (kg)', 'Ventana Inicio (HH:MM)', 'Ventana Fin (HH:MM)', 'Prioridad'],
            ['ID', 'Latitud', 'Longitud', 'Peso (kg)', 'Ventana inicio', 'Ventana fin', 'Prioridad']
        ]
        
        df_pedidos = None
        columnas_encontradas = None
        for columnas in columnas_posibles:
            if all(col in df.columns for col in columnas):
                df_pedidos = df[columnas].copy()
                columnas_encontradas = columnas
                break
        
        if df_pedidos is None:
            raise ValueError(f"No se encontraron las columnas esperadas en {sheet_name}. Columnas disponibles: {df.columns.tolist()}")
        
        # Usar los nombres originales de las columnas del Excel
        col_id = columnas_encontradas[0]
        col_latitud = columnas_encontradas[1]
        col_longitud = columnas_encontradas[2]
        col_peso = columnas_encontradas[3]
        col_inicio = columnas_encontradas[4]
        col_fin = columnas_encontradas[5]
        col_prioridad = columnas_encontradas[6]
        
        pedidos = []
        for _, row in df_pedidos.iterrows():
            # Limpiar valores NaN
            if pd.isna(row[col_id]):
                continue
            
            # Procesar ventana de tiempo - puede venir en formato "HH:MM - HH:MM" o separado
            inicio = str(row[col_inicio]).strip()
            fin = str(row[col_fin]).strip()
            
            # Si la ventana viene en una sola columna separada por "-"
            if '-' in inicio and fin == 'nan':
                partes = inicio.split('-')
                inicio = partes[0].strip()
                fin = partes[1].strip() if len(partes) > 1 else inicio
            
            pedido = Pedido(
                id=str(row[col_id]).strip(),
                latitud_destino=float(row[col_latitud]),
                longitud_destino=float(row[col_longitud]),
                peso_kg=float(row[col_peso]),
                ventana_inicio=inicio,
                ventana_fin=fin,
                prioridad=int(row[col_prioridad])
            )
            pedidos.append(pedido)
        
        return pedidos
    
    except Exception as e:
        raise Exception(f"Error al leer pedidos de {sheet_name}: {str(e)}")


def leer_escenario(filepath: str, escenario: str) -> Tuple[List[Vehiculo], List[Pedido]]:
    """
    Lee un escenario completo (vehículos y pedidos) del Excel.
    
    Args:
        filepath: Ruta al archivo Excel
        escenario: Nombre del escenario (E1, E2, E3)
    
    Returns:
        Tupla con (lista de vehículos, lista de pedidos)
    """
    sheet_vehiculos = f"{escenario}_Vehiculos"
    sheet_pedidos = f"{escenario}_Pedidos"
    
    vehiculos = leer_vehiculos(filepath, sheet_vehiculos)
    pedidos = leer_pedidos(filepath, sheet_pedidos)
    
    return vehiculos, pedidos


def listar_escenarios_disponibles(filepath: str) -> List[str]:
    """
    Lista los escenarios disponibles en el archivo Excel.
    
    Args:
        filepath: Ruta al archivo Excel
    
    Returns:
        Lista de nombres de escenarios (E1, E2, E3, etc.)
    """
    try:
        with pd.ExcelFile(filepath, engine='openpyxl') as xls:
            escenarios = []
            
            # Buscar hojas que sigan el patrón E*_Vehiculos
            for sheet_name in xls.sheet_names:
                if '_Vehiculos' in sheet_name:
                    escenario = sheet_name.replace('_Vehiculos', '')
                    # Verificar que también exista la hoja de pedidos
                    if f"{escenario}_Pedidos" in xls.sheet_names:
                        escenarios.append(escenario)
            
            return sorted(escenarios)
    
    except Exception as e:
        raise Exception(f"Error al listar escenarios: {str(e)}")
