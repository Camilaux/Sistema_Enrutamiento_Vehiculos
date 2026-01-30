"""
API REST para el sistema de enrutamiento de vehículos.
"""
import sys
from pathlib import Path
import os
import shutil

# Configuración robusta del path
# Definir project_root de forma que funcione tanto con 'python main.py' como con 'uvicorn'
current_file = Path(__file__).resolve()
project_root = current_file.parent.parent
sys.path.insert(0, str(project_root))

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import tempfile
from datetime import datetime, timedelta

# Imports del proyecto
from src.excel_reader import leer_escenario, listar_escenarios_disponibles
from src.algoritmo import solve_vrp_simulated_annealing, haversine_distance, VELOCIDAD_PROMEDIO_KMH, HORA_INICIO

app = FastAPI(
    title="Sistema de Enrutamiento de Vehículos",
    description="API REST para optimizar rutas de entrega de vehículos",
    version="1.0.0"
)

# Montar archivos estáticos para el frontend
static_path = os.path.join(project_root, "src", "static")
os.makedirs(static_path, exist_ok=True) # Asegurar que existe
app.mount("/static", StaticFiles(directory=static_path), name="static")

@app.get("/")
async def root():
    """Endpoint raíz con información de la API."""
    return {
        "message": "Sistema de Enrutamiento de Vehículos API",
        "version": "1.0.0",
        "endpoints": {
            "POST /api/enrutar": "Procesa un archivo Excel y calcula rutas optimizadas",
            "GET /api/escenarios": "Lista los escenarios disponibles en un archivo Excel",
            "GET /health": "Health check",
            "GET /mapa": "Visualización gráfica de rutas"
        }
    }


@app.get("/mapa", response_class=FileResponse)
async def ver_mapa():
    """Retorna la interfaz gráfica para visualización."""
    return os.path.join(project_root, "src", "static", "index.html")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}


@app.post("/api/escenarios")
async def listar_escenarios(file: UploadFile = File(...)):
    """
    Lista los escenarios disponibles en el archivo Excel subido.
    
    Returns:
        Lista de escenarios disponibles (E1, E2, E3, etc.)
    """
    try:
        # Guardar archivo temporalmente
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_path = tmp_file.name
        
        try:
            escenarios = listar_escenarios_disponibles(tmp_path)
            return {"escenarios": escenarios}
        finally:
            # Limpiar archivo temporal
            os.unlink(tmp_path)
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error al procesar archivo: {str(e)}")


@app.post("/api/enrutar")
async def enrutar(
    file: UploadFile = File(...),
    escenario: Optional[str] = None
):
    """
    Procesa un archivo Excel y calcula rutas optimizadas para un escenario.
    
    Args:
        file: Archivo Excel con los datos
        
        escenario: Nombre del escenario a procesar (E1, E2, E3). 
                   Si no se especifica, se procesa el primer escenario disponible.
    
    Returns:
        Resultado del enrutamiento con rutas optimizadas
    """
    try:
        # Validar que sea un archivo Excel
        if not file.filename.endswith(('.xlsx', '.xls')):
            raise HTTPException(
                status_code=400, 
                detail="El archivo debe ser un Excel (.xlsx o .xls)"
            )
        
        # Guardar archivo temporalmente
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_path = tmp_file.name
        
        try:
            # Normalizar escenario a mayúsculas si existe (ej. e1 -> E1)
            if escenario:
                escenario = escenario.upper()

            # Si no se especifica escenario, listar y usar el primero
            if escenario is None:
                escenarios_disponibles = listar_escenarios_disponibles(tmp_path)
                if not escenarios_disponibles:
                    raise HTTPException(
                        status_code=400,
                        detail="No se encontraron escenarios en el archivo Excel"
                    )
                escenario = escenarios_disponibles[0]
            
            # Leer datos del escenario
            vehiculos, pedidos = leer_escenario(tmp_path, escenario)
            
            # Ejecutar algoritmo Simulated Annealing
            resultado_algo = solve_vrp_simulated_annealing(vehiculos, pedidos)
            
            rutas = resultado_algo["rutas"]
            no_asignados = resultado_algo["metricas"]["no_asignados_count"]
            pedidos_no_asignados = resultado_algo["no_asignados"]
            
            # Procesar rutas para calcular distancias y formatear respuesta
            vehiculos_response = []
            distancia_total_global = 0.0
            tiempo_total_global_horas = 0.0
            
            for v in vehiculos:
                pedidos_ruta = rutas.get(v.id, [])
                if not pedidos_ruta:
                    continue
                
                # Calcular recorrido de la ruta
                distancia_ruta = 0.0
                ruta_detallada = []
                pedidos_ids_asignados = []
                
                # Iniciar en el origen del vehículo
                lat_actual, lon_actual = v.latitud_origen, v.longitud_origen
                
                # Gestión de tiempo
                # Asumimos inicio a las 08:00 AM para la simulación
                tiempo_actual = datetime.strptime(HORA_INICIO, "%H:%M")
                tiempo_inicio = tiempo_actual
                
                carga_actual = 0.0
                orden_contador = 1
                
                for pedido in pedidos_ruta:
                    # Calcular distancia del tramo
                    dist_tramo = haversine_distance(lat_actual, lon_actual, pedido.latitud_destino, pedido.longitud_destino)
                    distancia_ruta += dist_tramo
                    
                    # Calcular tiempo de viaje
                    # t = d / v
                    horas_viaje = dist_tramo / VELOCIDAD_PROMEDIO_KMH
                    # Agregar tiempo de viaje
                    tiempo_actual += timedelta(hours=horas_viaje)
                    
                    # Manejo de Ventana Inicio ("esperar hasta que abra")
                    # Nota: check_time_window ya validó esto en el algoritmo, aquí solo recalculamos para mostrar
                    t_inicio_ventana = datetime.strptime(pedido.ventana_inicio, "%H:%M")
                    if tiempo_actual < t_inicio_ventana:
                        tiempo_actual = t_inicio_ventana
                    
                    # Formatear hora estimada
                    hora_entrega = tiempo_actual.strftime("%H:%M")
                    
                    # Actualizar posición y carga
                    lat_actual, lon_actual = pedido.latitud_destino, pedido.longitud_destino
                    carga_actual += pedido.peso_kg
                    
                    # Guardar información
                    pedidos_ids_asignados.append(pedido.id)
                    ruta_detallada.append({
                        "pedido": pedido.id,
                        "latitud": pedido.latitud_destino,
                        "longitud": pedido.longitud_destino,
                        "orden": orden_contador,
                        "hora_estimada_entrega": hora_entrega
                    })
                    orden_contador += 1
                    
                    # Asumir tiempo de servicio/descarga (ej. 10 mins)
                    tiempo_actual += timedelta(minutes=10)
                    
                distancia_total_global += distancia_ruta
                
                # Tiempo total del vehículo (fin - inicio) en horas
                duracion_total = (tiempo_actual - tiempo_inicio).total_seconds() / 3600.0
                tiempo_total_global_horas += duracion_total
                
                vehiculos_response.append({
                    "id": v.id,
                    "origen": {
                        "latitud": v.latitud_origen,
                        "longitud": v.longitud_origen
                    },
                    "pedidos_asignados": pedidos_ids_asignados,
                    "ruta": ruta_detallada,
                    "capacidad_utilizada_kg": carga_actual,
                    "capacidad_maxima_kg": v.capacidad_kg,
                    "distancia_total_km": round(distancia_ruta, 2),
                    "tiempo_total_horas": round(duracion_total, 2)
                })

            # Asignación de razones por pedidos no asignados
            no_asignados_fmt = []
            for item in pedidos_no_asignados:
                # item is dict {pedido: Pedido, razon: str}
                p_obj = item["pedido"]
                razon = item["razon"]
                no_asignados_fmt.append({
                    "id": p_obj.id,
                    "razon_no_asignacion": razon
                })

            
            # Resultado formato según requerimiento
            resultado = {
                "escenario": escenario,
                "metricas_generales": {
                    "total_pedidos": len(pedidos),
                    "pedidos_asignados": resultado_algo["metricas"]["asignados"],
                    "pedidos_no_asignados": no_asignados,
                    "distancia_total_km": round(distancia_total_global, 2),
                    "tiempo_total_horas": round(tiempo_total_global_horas, 2)
                },
                "vehiculos": vehiculos_response,
                "pedidos_no_asignados": no_asignados_fmt
            }
            
            return JSONResponse(content=resultado)
        
        finally:
            # Limpiar archivo temporal
            os.unlink(tmp_path)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al procesar el enrutamiento: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
