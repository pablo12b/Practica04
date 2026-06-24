# Práctica 04 — Sistema Concurrente de Monitoreo Ambiental Urbano (Cuenca)

Simulación de un sistema urbano de monitoreo ambiental implementado con tres modelos
de ejecución en Python (**secuencial**, **hilos** y **procesos**) más una interfaz
gráfica en **PyQt6**. Permite comparar rendimiento, sincronización y el impacto del GIL.

## Variables simuladas por estación
Temperatura, Humedad, CO₂, Ruido, PM2.5 y PM10 (6 variables, con rangos realistas por zona).

## Arquitectura (POO)
- `Medicion` — dato individual (estación, zona, variable, valor, timestamp).
- `AlertaAmbiental` — alerta al superar un umbral (nivel MODERADO / ALTO).
- `EstacionAmbiental` / `EstacionAmbientalThread` / `EstacionAmbientalProcess` — generan mediciones.
- `AnalizadorDatos` — `procesar()` (cálculo pesado de CPU) y `agregar()` (agregación ligera).
- `ControladorMonitoreo*` — coordina ciclos, sincronización, estadísticas y alertas.

## Mecanismos de concurrencia
- **Hilos:** `threading.Lock` (protege la lista compartida de mediciones/alertas) + `threading.Barrier` (sincroniza el cierre de cada ciclo entre estaciones).
- **Procesos:** `multiprocessing.Queue` (IPC hijo→padre) + `multiprocessing.Barrier` (sincroniza ciclos entre procesos).

> Diseño clave: el cálculo pesado de CPU (`_calculo_pesado_cpu`) se ejecuta **distribuido**
> dentro de cada hilo/proceso sobre sus propias mediciones. Así, multiprocessing logra
> paralelismo real (vence al GIL) y threading evidencia el bloqueo del GIL.

## Requisitos
- Python 3.10+ (probado en 3.14)
- PyQt6 (solo para la GUI)

```bash
python3 -m venv .venv
source .venv/bin/activate        # fish: source .venv/bin/activate.fish
pip install PyQt6
```

## Ejecución

GUI (recomendado):
```bash
python3 gui.py
```

Cada versión por consola:
```bash
python3 simulacion_secuencial.py
python3 simulacion_hilos.py
python3 simulacion_procesos.py
```

Benchmark comparativo (3 repeticiones × tamaños 4/10, 8/20, 12/30):
```bash
python3 benchmark.py
```

## Archivos
| Archivo | Descripción |
| :--- | :--- |
| `simulacion_secuencial.py` | Versión base (línea de referencia). |
| `simulacion_hilos.py` | Versión con `threading` (Lock + Barrier). |
| `simulacion_procesos.py` | Versión con `multiprocessing` (Queue + Barrier). |
| `gui.py` | Interfaz gráfica PyQt6. |
| `benchmark.py` | Mediciones de rendimiento y speedup. |
| `analisis_ejecucion.md` | Informe: tabla comparativa y análisis. |
| `benchmark_resultados.txt` | Salida cruda del último benchmark. |
