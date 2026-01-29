# Sistema Enrutamiento Vehiculos

Este proyecto implementa un sistema de enrutamiento de vehículos, en el cual con ayuda de un algoritmo se debe ayudar a una empresa a optimizar las rutas de entrega de sus vehículos. Se debe construir un sistema que calcule rutas eficientes teniendo en cuenta restricciones de capacidad, ventanas de tiempo y prioridades.

## Estimación de tiempo por cada item:

- Lectura del Excel e infrastructura - 5 horas
- Implementación del algoritmo base - 6 horas
- Optimizaciones y casos edge - 10 horas
- Documentación - 4 horas

## Tiempo real consumido por cada item:
- Lectura del Excel e infrastructura - 5 horas aproximadamente
- Implementación del algoritmo base - 4 horas aproximadamente (código) + 2 horas de estudio de la teoría
- Optimizaciones y casos edge - 7 horas aproximadamente (código) + 2 horas de estudio heurística SA y VRP
- Documentación - 

*Nota:* esta sección se completará progresivamente a medida que avance el desarrollo

## Instrucciones de Ejecución

### Prerrequisitos
- Python 3.10 o superior
- pip (gestor de paquetes de Python)

### Pasos para ejecutar

1. **Crear entorno virtual (opcional pero recomendado)**
   ```bash
   python -m venv venv
   ```

2. **Activar entorno virtual**
   - Windows (PowerShell):
     ```powershell
     .\venv\Scripts\Activate.ps1
     ```
   - Windows (CMD):
     ```cmd
     venv\Scripts\activate.bat
     ```
   - Linux/Mac:
     ```bash
     source venv/bin/activate
     ```

3. **Instalar dependencias**
   ```bash
   pip install -r requirements.txt
   ```

4. **Iniciar el servidor API**
   ```bash
   python main.py
   ```
   O usando uvicorn directamente:
   ```bash
   uvicorn main:app --reload
   ```

5. **Acceder a la API**
   - La API estará disponible en: `http://localhost:8000`
   - Documentación interactiva (Swagger): `http://localhost:8000/docs`
   - Documentación alternativa (ReDoc): `http://localhost:8000/redoc`

### Endpoints disponibles

- `GET /` - Información de la API
- `GET /health` - Health check
- `POST /api/escenarios` - Lista los escenarios disponibles en un archivo Excel
- `POST /api/enrutar` - Procesa un archivo Excel y calcula rutas optimizadas

### Ejemplo de uso con curl

**Listar escenarios:**
```bash
curl -X POST "http://localhost:8000/api/escenarios" -F "file=@data/datos_prueba_enrutamiento.xlsx"
```

**Procesar escenario E1:**
```bash
curl -X POST "http://localhost:8000/api/enrutar?escenario=E1" -F "file=@data/datos_prueba_enrutamiento.xlsx"
```

### Ejemplo de uso con Python requests

```python
import requests

# Listar escenarios
with open('data/datos_prueba_enrutamiento.xlsx', 'rb') as f:
    response = requests.post('http://localhost:8000/api/escenarios', files={'file': f})
    print(response.json())

# Procesar escenario E1
with open('data/datos_prueba_enrutamiento.xlsx', 'rb') as f:
    response = requests.post('http://localhost:8000/api/enrutar?escenario=E1', files={'file': f})
    print(response.json())
```

## Decisiones de Diseño

- ¿Qué algoritmo o approach usaste para el enrutamiento? ¿Por qué elegiste esa solución?
- ¿Cómo priorizas entre distancia, tiempo y prioridades de pedidos? Explica tu función objetivo 
- ¿Qué hace tu sistema cuando es imposible asignar todos los pedidos? (crítico para Escenario 3)
- ¿Cómo calculaste las distancias entre coordenadas geográficas?
- ¿Qué stack tecnológico elegiste y por qué? (justificación breve)

## Trade-offs Importantes

## Limitaciones Conocidas

- ¿Qué no hace tu solución?
- ¿Con cuántos vehículos/pedidos escala razonablemente?
- ¿Qué mejorarías con más tiempo?
