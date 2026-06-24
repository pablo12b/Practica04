# Análisis de Ejecución y Rendimiento Concurrente

Análisis comparativo del rendimiento y la coherencia de datos del sistema urbano de
monitoreo ambiental de Cuenca bajo tres esquemas de ejecución en Python.

**Condiciones de prueba:** sin retardo artificial entre ciclos (`intervalo=0.0`),
**3 repeticiones** por configuración, cálculo pesado de CPU **distribuido** en cada
hilo/proceso (cada estación analiza sus propias mediciones).

## Entorno de ejecución
| | |
| :--- | :--- |
| Python | 3.14.5 (CPython) |
| Sistema operativo | Linux 7.0.12-1-cachyos |
| Núcleos de CPU | 20 |
| GIL | Activado |

---

## 1. Tabla Comparativa de Resultados (tiempos promedio de 3 corridas)

| Configuración | Versión | Tiempo (s) | Mediciones | Med/s | Speedup |
| :--- | :--- | ---: | ---: | ---: | ---: |
| **4 est / 10 ciclos** | Secuencial | 4.8132 | 240 | 49.9 | 1.00× (base) |
| | Hilos | 5.0501 | 240 | 47.5 | **0.95×** |
| | Procesos | 1.4805 | 240 | 162.1 | **3.25×** |
| **8 est / 20 ciclos** | Secuencial | 21.0363 | 960 | 45.6 | 1.00× (base) |
| | Hilos | 25.4015 | 960 | 37.8 | **0.83×** |
| | Procesos | 5.4267 | 960 | 176.9 | **3.88×** |
| **12 est / 30 ciclos** | Secuencial | 53.7578 | 2160 | 40.2 | 1.00× (base) |
| | Hilos | 59.8278 | 2160 | 36.1 | **0.90×** |
| | Procesos | 8.7711 | 2160 | 246.3 | **6.13×** |

> Mediciones = N estaciones × 6 variables × ciclos. Las tres versiones procesaron
> **exactamente** la cantidad esperada en todas las corridas: coherencia de datos correcta.

---

## 2. Respuestas del Informe

### 1. ¿Qué versión fue más rápida?
La versión basada en **procesos** (`multiprocessing`) en todas las configuraciones, con
ventaja creciente al aumentar la carga (de 3.25× con 4 estaciones a 6.13× con 12). Aprovecha
los núcleos físicos para ejecutar el cálculo pesado de CPU en paralelo real.

### 2. ¿Hubo mejora respecto a la versión secuencial?
- **Procesos:** sí, mejora sustancial (hasta **6.13×** más rápido).
- **Hilos:** no; fueron incluso **más lentos** que la secuencial (0.83×–0.95×) por el costo
  de creación/conmutación de hilos sin ganancia de paralelismo de CPU.

### 3. Impacto del GIL en la versión con hilos
El cálculo `_calculo_pesado_cpu` (500 000 raíces cuadradas por medición) es CPU-bound. Aunque
cada estación corre en su propio hilo e intenta calcular en paralelo, el **GIL** sólo permite
ejecutar bytecode Python en un hilo a la vez dentro del proceso. Resultado: el cómputo se
serializa y, sumado al overhead de conmutación de contexto, los hilos rinden **por debajo**
de la versión secuencial. Es la demostración directa del impacto del GIL en tareas de CPU.

### 4. Mecanismos de sincronización/comunicación y justificación
| Versión | Mecanismos | Justificación |
| :--- | :--- | :--- |
| Hilos | `Lock` + `Barrier` | El `Lock` protege las listas compartidas de mediciones/alertas (evita condiciones de carrera). El `Barrier` alinea a todas las estaciones al final de cada ciclo para procesar estadísticas coherentes. |
| Procesos | `Queue` + `Barrier` | La `Queue` transporta mediciones y alertas de los procesos hijos (memoria aislada) al padre vía IPC. El `Barrier` sincroniza el avance de ciclo entre procesos. |

### 5. ¿Cuándo conviene hilos vs. procesos?
- **Hilos:** tareas limitadas por **I/O** (red, disco, esperas) donde el GIL se libera; bajo
  costo de memoria y comunicación por memoria compartida.
- **Procesos:** tareas limitadas por **CPU** (cálculo intensivo), donde el paralelismo real
  sobre múltiples núcleos compensa el costo de IPC y serialización. Es el caso de esta práctica.

### 6. Complejidad de implementación
- **Secuencial:** mínima.
- **Hilos:** media — exige proteger estado compartido con `Lock` y coordinar con `Barrier`.
- **Procesos:** mayor — los objetos deben ser serializables (pickle), no hay memoria compartida
  (se comunica por `Queue`) y hay que gestionar el ciclo de vida e IPC de los procesos.

---

## 3. Métricas de Aceleramiento (Speedup)
`S = T_secuencial / T_paralelo`

| Configuración | S_hilos | S_procesos |
| :--- | ---: | ---: |
| 4 est / 10 ciclos | 0.95× | 3.25× |
| 8 est / 20 ciclos | 0.83× | 3.88× |
| 12 est / 30 ciclos | 0.90× | 6.13× |

---

## 4. Conclusiones
- **Procesos** son la vía idónea para paralelismo real de CPU en Python; el speedup crece con
  la carga al distribuir el cómputo pesado dentro de cada proceso hijo.
- **Hilos** no aceleran tareas de CPU por el GIL; reservarlos para cargas de I/O.
- Los mecanismos `Lock`, `Barrier` y `Queue` mantuvieron la **coherencia total** de los datos
  (100% de mediciones esperadas) sin condiciones de carrera ni pérdidas por IPC.
