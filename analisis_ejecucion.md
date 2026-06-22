# Análisis de Ejecución y Rendimiento Concurrente

Este documento detalla el análisis comparativo del rendimiento y la coherencia de datos del sistema urbano de monitoreo ambiental para la ciudad de Cuenca bajo tres esquemas de ejecución en Python.

Las pruebas fueron ejecutadas en igualdad de condiciones (sin retardo artificial entre ciclos, `intervalo=0.0`) con la configuración base de **4 estaciones** y **10 ciclos de simulación**.

---

## 1. Tabla Comparativa de Resultados

| Métrica | Versión Secuencial | Versión Hilos (`threading`) | Versión Procesos (`multiprocessing`) |
| :--- | :--- | :--- | :--- |
| **Tiempo de Ejecución** | **5.1178 segundos** | **5.1441 segundos** | **5.2278 segundos** |
| **Mediciones Procesadas** | 160 | 160 | 160 |
| **Alertas Generadas** | 59 (aleatorio) | 52 (aleatorio) | 48 (aleatorio) |
| **Coherencia de Datos** | Correcta ($160/160$) | Correcta ($160/160$) | Correcta ($160/160$) |

---

## 2. Coherencia de Inputs y Outputs

*   **Inputs (Entradas de Configuración):**
    *   **Estaciones:** $N=4$ (Centro, Sur, Norte y Este).
    *   **Ciclos:** $C=10$ ciclos de recolección de variables.
    *   **Variables por Estación:** 4 lecturas por ciclo (Temperatura, Humedad, CO₂ y Ruido).
    *   **Cálculo Teórico de Mediciones:** $4 \text{ estaciones} \times 4 \text{ variables} \times 10 \text{ ciclos} = 160$ mediciones individuales.

*   **Coherencia del Output (Salidas):**
    *   Las tres versiones procesaron exactamente **160 mediciones**, validando la integridad del flujo.
    *   En [simulacion_hilos.py](file:///Users/mkt/Developer/Uni/ComputacionParalela/Practica04/simulacion_hilos.py), el uso de `threading.Lock` previno condiciones de carrera en la memoria compartida.
    *   En [simulacion_procesos.py](file:///Users/mkt/Developer/Uni/ComputacionParalela/Practica04/simulacion_procesos.py), la cola `multiprocessing.Queue` transmitió todas las lecturas de los procesos aislados hacia el controlador principal sin pérdidas por concurrencia.

---

## 3. Análisis Crítico de Rendimiento y el GIL

### A. El impacto del GIL (Global Interpreter Lock) en Hilos
El análisis estadístico de variables ambientales invoca la función `_calculo_pesado_cpu` dentro de [AnalizadorDatos](file:///Users/mkt/Developer/Uni/ComputacionParalela/Practica04/simulacion_secuencial.py#L39) (en el archivo base [simulacion_secuencial.py](file:///Users/mkt/Developer/Uni/ComputacionParalela/Practica04/simulacion_secuencial.py)), la cual computa raíces cuadradas en un ciclo cerrado de 500,000 iteraciones para simular carga computacional.

Bajo la versión basada en hilos:
*   Múltiples hilos compiten por el procesador.
*   Sin embargo, el **GIL de Python** restringe la ejecución de código Python a un único hilo de manera simultánea en el mismo proceso.
*   Por tanto, los hilos de las estaciones ambientales se ven obligados a ejecutarse de forma secuencial en un solo núcleo. El tiempo resultante (5.1441 segundos) es ligeramente mayor al secuencial debido al costo administrativo y de conmutación de contexto de los hilos.

### B. Ejecución de Procesos con cuello de botella centralizado
Bajo la versión basada en procesos:
*   Los procesos hijos de las estaciones generan y evalúan los umbrales de alerta de forma realmente paralela en múltiples núcleos físicos de la CPU.
*   No obstante, una vez generadas, todas las lecturas se envían secuencialmente al proceso padre a través de una cola IPC (`multiprocessing.Queue`). El proceso padre es el único que procesa el análisis matemático pesado de cada ciclo.
*   Dado que el cálculo intensivo de CPU sigue ocurriendo secuencialmente en el proceso principal, no se observa una mejora del tiempo (5.2278 segundos), sumándole además la latencia de serialización y deserialización de objetos en la cola IPC.

---

## 4. Conclusiones para el Informe de Práctica
*   **Hilos:** Son e xcelentes para tareas limitadas por I/O (entrada/salida o retardos de red), pero no ofrecen ventajas en tareas pesadas de CPU en Python debido al GIL.
*   **Procesos:** Son la vía idónea para paralelismo real de CPU, pero para ver su beneficio de velocidad, **el procesamiento pesado debe ser distribuido y ejecutado de manera local dentro de cada proceso hijo**, en lugar de centralizarse en el proceso padre.
*   **Sincronización:** Los mecanismos de `Lock` y `Barrier` demostraron ser estables e indispensables para coordinar la concurrencia y mantener la coherencia matemática del sistema.
