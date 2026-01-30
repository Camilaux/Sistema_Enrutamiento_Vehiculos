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
- Documentación - 2 horas aproximadamente
- Bonus - 8 horas aproximadamente

*Nota:* esta sección se completará progresivamente a medida que avance el desarrollo

## Instrucciones de Ejecución

### Prerrequisitos
- Python 3.10 o superior
- pip (gestor de paquetes de Python)

### Pasos para ejecutar

1. **Crear entorno virtual (opcional pero recomendado)**
   ```bash
   python -m venv .venv
   ```

2. **Activar entorno virtual**
   - Windows (PowerShell):
     ```powershell
     .\.venv\Scripts\Activate.ps1
     ```
   - Windows (CMD):
     ```cmd
     .venv\Scripts\activate.bat
     ```
   - Linux/Mac:
     ```bash
     source .venv/bin/activate
     ```

3. **Instalar dependencias**
   ```bash
   pip install -r requirements.txt
   ```

4. **Iniciar el servidor API**
   ```bash
   python src/main.py
   ```

5. **Acceder a la API**
   - La API estará disponible en: `http://localhost:8000`
   - Documentación interactiva (Swagger): `http://localhost:8000/docs`
   - Visualización mapa: `http://localhost:8000/mapa`

### Endpoints disponibles

- `GET /` - Información de la API
- `GET /health` - Health check
- `POST /api/escenarios` - Lista los escenarios disponibles en un archivo Excel
- `POST /api/enrutar` - Procesa un archivo Excel y calcula rutas optimizadas

## Decisiones de Diseño

### ¿Qué algoritmo o approach usaste para el enrutamiento? ¿Por qué elegiste esa solución?

Se implementó un enfoque híbrido de dos fases:
1.  **Construcción Greedy Inteligente**: Genera una solución inicial factible evaluando la inserción óptima de cada pedido priorizado en todas las posiciones posibles.

2.  **Optimización via Simulated Annealing**: Refina la solución inicial permitiendo movimientos estocásticos (swaps, movimientos, inserciones) para escapar de mínimos locales.

Se eligió esta combinación porque el problema VRP con ventanas de tiempo y múltiples restricciones (CVRPTW) es NP-Hard. El greedy provee una base sólida rápida, y el Simulated Annealing permite optimizar costos globales complejos (como el balance de carga y rescate de no asignados) que un greedy puro no puede ver.

### ¿Cómo priorizas entre distancia, tiempo y prioridades de pedidos? Explica tu función objetivo 

El algoritmo utiliza una función objetivo con penalizaciones (penalty-based objective function), ampliamente usada en problemas de enrutamiento con múltiples restricciones.

El objetivo no es minimizar únicamente la distancia, sino reflejar de forma explícita las prioridades del negocio:

- Cumplir la mayor cantidad posible de pedidos

- Priorizar pedidos críticos (alta prioridad)

- Respetar restricciones duras (capacidad, ventanas, jornada)

- Minimizar costos operativos solo cuando lo anterior ya se cumple

La función objetivo global se define como:

$$
C_{global} = \sum_{vehiculos} C_{ruta}(r_v) + \sum_{p \in N} (w_{un} \cdot prio(p)^2)
$$

$$
\text{Costo total} = \sum \text{Costo ruta} + \sum \text{Penalización no asignados}
$$
Donde $N$ representan los pedidos no asignados.

##### Costo de una ruta

Para cada vehículo, el costo se calcula como:

$$
\text{Costo ruta} = w_{dist} \cdot \text{distancia total} + w_{wait} \cdot \text{tiempo espera} + w_{waste} \cdot (\text{desperdicio capacidad})^2
C_{ruta}(r) = w_D \cdot D(r) + w_{wait} \cdot T_{wait}(r) + w_{late} \cdot L(r) + w_{ot} \cdot OT(r) + w_{cap} \cdot U(r)^2
$$

Donde:

- $D(r)$: Distancia total recorrida ($w_D$)
- $T_{wait}(r)$: Tiempo de espera acumulado ($w_{wait}$)
- $L(r)$: Violaciones de ventana de tiempo ($w_{late}$)
- $OT(r)$: Exceso de jornada laboral ($w_{ot}$)
- $U(r)$: Uso de capacidad al cuadrado ($w_{cap}$) para balanceo

- tiempo_espera: tiempo acumulado esperando la apertura de ventanas de tiempo

- desperdicio_capacidad: 

$$
\text{desperdicio capacidad} = \frac{\text{capacidad vehículo} - \text{carga asignada}}{\text{capacidad vehículo}}
$$

Este término penaliza el uso ineficiente de vehículos grandes para pedidos que podrían ser atendidos por vehículos más pequeños, favoreciendo un mejor capacity matching.

Las siguientes restricciones se tratan como hard constraints (costo infinito si se violan):

- Exceder la capacidad máxima del vehículo

- Llegar fuera de la ventana de tiempo

- Exceder la jornada laboral máxima (8 horas)
En la implementación, $L(r)$ y $OT(r)$ actúan como restrictiones duras (Hard Constraints), resultando en un costo infinito si se violan.

##### Penalización por pedidos no asignados

Cada pedido no asignado genera una penalización cuadrática:
$$
\text{Penalización no asignado} = w_{unassigned} \cdot \text{prioridad}^2
\text{Penalización} = w_{un} \cdot prio(p)^2
$$

Esto garantiza que perder un pedido de alta prioridad sea costoso.

### ¿Qué hace tu sistema cuando es imposible asignar todos los pedidos? (crítico para Escenario 3)

El sistema está diseñado para ser resiliente:
1.  Identifica restricciones "duras" (ej. un pedido de 2000kg en una flota de 1000kg) y los marca inmediatamente con la razón precisa.
2.  El algoritmo de Simulated Annealing tiene un movimiento específico (`insert_unassigned`) que intenta activamente reinsertar pedidos excluidos si encuentra huecos factibles.
3.  Si finalmente no es posible asignar un pedido (por conflicto de ventanas irreconciliable o falta de capacidad), se retorna en una lista explícita `pedidos_no_asignados` junto con la razón técnica.

### ¿Cómo calculaste las distancias entre coordenadas geográficas?

Se utilizó la **Fórmula de Haversine**, que calcula la distancia del círculo máximo entre dos puntos de una esfera (la Tierra), considerando la latitud y longitud. Esto ofrece una precisión adecuada para logística urbana sin requerir servicios externos de mapeo.

### ¿Qué stack tecnológico elegiste y por qué? (justificación breve)

*   **Python**: Lenguaje estándar en ciencia de datos e investigación operativa.
*   **FastAPI**: Framework moderno y rápido para construir APIs, con validación de datos automática (Pydantic) y documentación interactiva.
*   **Simulated Annealing**: Implementación pura en Python para mantener el control total sobre la función objetivo y las restricciones personalizadas.

## Trade-offs Importantes

- Se optó por Simulated Annealing en lugar de un Algoritmo Genético debido a su menor complejidad de implementación y menor costo computacional. SA permite partir de una solución greedy factible y mejorarla progresivamente mediante operadores locales, lo que resulta más adecuado para ejecución en una API REST.

Si bien los algoritmos genéticos ofrecen mayor exploración global del espacio de soluciones, requieren poblaciones, operadores de cruce y mutación, así como mayor tiempo de cómputo y ajuste de hiperparámetros. El trade-off asumido fue sacrificar parte de esa exploración global a cambio de mayor estabilidad, explicabilidad y control del tiempo de ejecución.

- **Hard Constraints**: La jornada de 8h es estricta. Esto puede dejar pedidos sin entregar que solo requerían 10 minutos extra, privilegiando el cumplimiento legal sobre la entregas marginales.

## Limitaciones Conocidas

- No se modelan recargas múltiples por vehículo

- No se optimiza el retorno al depósito

- La solución no garantiza optimalidad global

- Escala razonablemente hasta decenas de vehículos y cientos de pedidos

- Se asume velocidad constante (30km/h), ignorando tráfico en tiempo real.

## Posibles mejoras

- Multi-depot VRP

- Ajuste dinámico de pesos

- Paralelización del Simulated Annealing

- Integración con motores de optimización externos
