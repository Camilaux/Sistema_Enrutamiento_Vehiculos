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
        errors = []
        for index, row in df_vehiculos.iterrows():
            row_num = index + 2  # Header es row 1
            
            # Limpiar valores NaN
            if pd.isna(row[col_id]):
                errors.append(f"Fila {row_num}: ID de vehículo vacío")
                continue
                
            vid = str(row[col_id]).strip()
            
            try:
                cap = float(row[col_capacidad])
                if cap <= 0:
                    errors.append(f"Fila {row_num} (Vehículo {vid}): La capacidad debe ser mayor a 0")
                    continue
                    
                lat = float(row[col_latitud])
                lon = float(row[col_longitud])
                
                # Validación básica de coordenadas
                if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
                    errors.append(f"Fila {row_num} (Vehículo {vid}): Coordenadas inválidas")
                    continue

                vehiculo = Vehiculo(
                    id=vid,
                    capacidad_kg=cap,
                    latitud_origen=lat,
                    longitud_origen=lon
                )
                vehiculos.append(vehiculo)
            except ValueError:
                errors.append(f"Fila {row_num} (Vehículo {vid}): Datos numéricos inválidos (capacidad o coordenadas)")
        
        if errors:
            raise ValueError("Errores en datos de vehículos:\n" + "\n".join(errors[:10]))
            
        return vehiculos
    
    except ValueError as ve:
        raise ve
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
        errors = []
        import re
        time_pattern = re.compile(r'^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$')

        for index, row in df_pedidos.iterrows():
            row_num = index + 2
            
            # Limpiar valores NaN en ID
            if pd.isna(row[col_id]):
                continue # Skip empty rows silently or log warning? Skipping empty IDs usually safe
            
            pid = str(row[col_id]).strip()
            
            try:
                # Validar coordenadas
                lat = float(row[col_latitud])
                lon = float(row[col_longitud])
                if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
                    errors.append(f"Fila {row_num} (Pedido {pid}): Coordenadas inválidas")
                    continue
                
                # Validar peso
                peso = float(row[col_peso])
                if peso <= 0:
                    errors.append(f"Fila {row_num} (Pedido {pid}): Peso debe ser mayor a 0")
                    continue
                
                # Validar prioridad
                prioridad = int(row[col_prioridad])
                if not (1 <= prioridad <= 5):
                     errors.append(f"Fila {row_num} (Pedido {pid}): Prioridad debe estar entre 1 y 5")
                     continue

                # Procesar ventana de tiempo - puede venir en formato "HH:MM - HH:MM" o separado
                inicio = str(row[col_inicio]).strip()
                fin = str(row[col_fin]).strip()
                
                # Si la ventana viene en una sola columna separada por "-"
                if '-' in inicio and (fin == 'nan' or fin == ''):
                    partes = inicio.split('-')
                    inicio = partes[0].strip()
                    fin = partes[1].strip() if len(partes) > 1 else inicio

                # Validar formato HH:MM
                if not time_pattern.match(inicio):
                     errors.append(f"Fila {row_num} (Pedido {pid}): Hora inicio '{inicio}' formato inválido (HH:MM)")
                     continue
                if not time_pattern.match(fin):
                     errors.append(f"Fila {row_num} (Pedido {pid}): Hora fin '{fin}' formato inválido (HH:MM)")
                     continue
                
                # Validar lógica temporal
                h_inicio = int(inicio.split(':')[0]) * 60 + int(inicio.split(':')[1])
                h_fin = int(fin.split(':')[0]) * 60 + int(fin.split(':')[1])
                if h_inicio > h_fin:
                    errors.append(f"Fila {row_num} (Pedido {pid}): La ventana de inicio no puede ser posterior al fin")
                    continue
                
                pedido = Pedido(
                    id=pid,
                    latitud_destino=lat,
                    longitud_destino=lon,
                    peso_kg=peso,
                    ventana_inicio=inicio,
                    ventana_fin=fin,
                    prioridad=prioridad
                )
                pedidos.append(pedido)
            
            except ValueError:
                errors.append(f"Fila {row_num} (Pedido {pid}): Datos numéricos inválidos")
                continue
        
        if errors:
            # Mostrar solo hasta 10 errores para no saturar
            raise ValueError("Errores en datos de pedidos:\n" + "\n".join(errors[:10]))
        
        return pedidos
    
    except ValueError as ve:
        raise ve
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
