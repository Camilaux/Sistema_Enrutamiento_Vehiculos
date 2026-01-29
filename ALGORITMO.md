# Descripción Implementación Algoritmo

## Descripción general

El algoritmo resuelve un Vehicle Routing Problem con Ventanas de Tiempo y Capacidad (CVRPTW) priorizando el cumplimiento del mayor número posible de pedidos, especialmente aquellos de mayor prioridad.

El proceso completo funciona de la siguiente manera:

### 1. Lectura de datos

- Se cargan vehículos y pedidos desde el archivo Excel del escenario seleccionado.

- Se validan pedidos imposibles desde el inicio (peso mayor a la capacidad máxima de la flota).

### 2. Ordenamiento inicial de pedidos

Los pedidos se ordenan por prioridad descendente.

En caso de empate, se ordenan por hora de inicio de ventana ascendente.

### 3. Construcción de solución inicial (Greedy mejorado)

- Para cada pedido, se intenta insertar en todos los vehículos y en todas las posiciones posibles de sus rutas.

- Se simula la ruta para verificar:

    - Capacidad

    - Ventanas de tiempo

    - Jornada laboral máxima (8 horas)

- Se selecciona la inserción con menor incremento de costo según la función objetivo.

- Si el pedido no es factible en ningún vehículo, se marca como no asignado junto con la razón.

### 4. Mejora mediante Simulated Annealing (SA)

- La solución greedy se usa como punto de partida.

- Se aplican operadores de vecindad (swap, move, insert_unassigned).

- Se aceptan soluciones peores con una probabilidad controlada por la temperatura.

- El objetivo es mejorar cobertura y balance sin perder factibilidad.

### 5. Construcción de la salida

- Se generan métricas globales y por vehículo.

- Se reportan rutas, horarios estimados y pedidos no asignados con explicación.

## Pseudocódigo

```text
Entrada: Lista de Vehículos V, Lista de Pedidos P
Configuración: Temp_Inicial=1000, Cooling_Rate=0.995, Iteraciones=10000

1. Ordenar P por Prioridad (DESC) y Ventana Inicio (ASC)
2. Solución_Actual = GreedyConstructivo(V, P)
   - Para cada pedido p en P:
       - Probar inserción en cada posición de cada ruta de V
       - Elegir la posición con menor costo marginal
       - Si no cabe en ninguna, agregar a No_Asignados
       
3. Mejor_Solución = Solución_Actual
4. Temp = Temp_Inicial

5. Mientras i < Iteraciones:
    a. Generar Vecino (Nueva_Solución) aplicando un operador al azar:
       - SWAP_INTER: Intercambiar pedidos entre dos rutas.
       - MOVE_INTER: Mover un pedido de una ruta a otra.
       - SWAP_INTRA: Intercambiar orden dentro de una misma ruta.
       - INSERT_UNASSIGNED: Intentar insertar un pedido no asignado en un hueco factible.
       
    b. Calcular Delta = Costo(Nueva_Solución) - Costo(Solución_Actual)
    
    c. Si Delta < 0 (Mejora):
         Aceptar Nueva_Solución
    d. Si Delta > 0 (Empeora):
         Aceptar con probabilidad P = exp(-Delta / Temp)
         
    e. Si Costo(Nueva) < Costo(Mejor_Solución):
         Actualizar Mejor_Solución
         
    f. Temp = Temp * Cooling_Rate

6. Retornar Mejor_Solución
```

## Complejidad temporal

- **Greedy**: $O(N \cdot M \cdot K)$ donde N=Pedidos, M=Vehículos, K=Largo promedio ruta. Para cada pedido, revisamos todas las posiciones posibles.
- **Simulated Annealing**: $O(I \cdot K)$ donde I=Iteraciones. En cada iteración se recalcula el costo de las rutas afectadas (operación lineal respecto al largo de la ruta).
- **Global**: La complejidad está dominada por el número de iteraciones fijas, asegurando un tiempo de ejecución predecible $O(N \cdot M \cdot K + I \cdot K)$ que en conclusión sería $O(N)$

## Alternativas consideradas

1.  **Programación Lineal Entera (MIP)**:
    *   *Evaluación*: Ofrece el óptimo matemático exacto.
    *   *Motivo de descarte*: Computacionalmente inviable para respuesta en tiempo real en APIs, y difícil de modelar con restricciones no lineales complejas (ventanas suaves, prioridades cuadráticas).

2.  **Algoritmos Genéticos**:
    *   *Evaluación*: Buena exploración.
    *   *Motivo de descarte*: Mayor complejidad de implementación y ajuste de hiperparámetros (cruce, mutación, selección) comparado con la elegancia de un solo parámetro de temperatura en SA.

## Manejo de casos edge: 

### Pedidos con ventanas de tiempo conflictivas (Escenario 3)
El sistema detecta el conflicto durante la validación `check_time_window`. Si un pedido hace que el vehículo llegue tarde (ej. llegar a las 11:00 cuando la ventana cierra a las 10:00), la ruta se marca como inválida (costo infinito). El algoritmo intentará moverlo a otro vehículo. Si no cabe en ninguno, se mueve a la lista `pedidos_no_asignados`.

### Pedidos que exceden la capacidad de vehículos
Se implementó una verificación de dos niveles:
1.  **Individual**: Si `pedido.peso > max_capacidad_flota`, se descarta inmediatamente antes de iniciar.
2.  **Acumulada**: Durante la construcción de ruta, si sumar el pedido excede la capacidad remanente, se rechaza la inserción en ese vehículo específico.

### Priorización cuando hay conflictos
La función de costo utiliza pesos cuadráticos para la prioridad: `Costo = 600 * (prioridad^2)`.
Esto significa que dejar sin asignar un pedido de Prioridad 1 cuesta 600 puntos, pero uno de Prioridad 5 cuesta 15,000 puntos. El algoritmo siempre preferirá sacrificar distancia o tiempos de espera para acomodar un pedido de alta prioridad.