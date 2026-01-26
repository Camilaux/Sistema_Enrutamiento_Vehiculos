"""
API REST para el sistema de enrutamiento de vehículos.
"""
import sys
from pathlib import Path

# Agregar el directorio raíz al path para permitir imports relativos
if __name__ == "__main__":
    project_root = Path(__file__).parent.parent
    sys.path.insert(0, str(project_root))

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from typing import Optional
import tempfile
import os

# Usar imports absolutos (funciona cuando el directorio raíz está en sys.path)
from src.excel_reader import leer_escenario, listar_escenarios_disponibles

app = FastAPI(
    title="Sistema de Enrutamiento de Vehículos",
    description="API REST para optimizar rutas de entrega de vehículos",
    version="1.0.0"
)


@app.get("/")
async def root():
    """Endpoint raíz con información de la API."""
    return {
        "message": "Sistema de Enrutamiento de Vehículos API",
        "version": "1.0.0",
        "endpoints": {
            "POST /api/enrutar": "Procesa un archivo Excel y calcula rutas optimizadas",
            "GET /api/escenarios": "Lista los escenarios disponibles en un archivo Excel",
            "GET /health": "Health check"
        }
    }


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
            
            # Aquí se implementará el algoritmo de enrutamiento
            
            # Placeholder para el resultado
            resultado = {
                "escenario": escenario,
                "metricas_generales": {
                    "total_pedidos": len(pedidos),
                    "pedidos_asignados": 0,
                    "pedidos_no_asignados": len(pedidos),
                    "distancia_total_km": 0.0,
                    "tiempo_total_horas": 0.0 
                },
                "vehiculos": [],
                "pedidos_no_asignados": []
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
