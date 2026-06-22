# Práctica de Laboratorio 04: Desarrollo e implementación de aplicaciones de cómputo paralelo basado en procesos e hilos

## Objetivos
* Diseñar e implementar una aplicación concurrente que simule un sistema urbano de monitoreo ambiental.
* Aplicar paralelismo basado en procesos y paralelismo basado en hilos en Python.
* Analizar las diferencias de rendimiento, comunicación y sincronización entre threading y multiprocessing.
* Comprender el impacto del Global Interpreter Lock (GIL) en aplicaciones paralelas basadas en hilos.
* Utilizar mecanismos de sincronización y comunicación entre procesos e hilos.
* Incorporar una interfaz gráfica para visualizar el funcionamiento del sistema concurrente.

---

## Instrucciones: Sistema de monitoreo ambiental urbano

En esta práctica se desarrollará una simulación de un sistema urbano de monitoreo ambiental para la ciudad de Cuenca. El sistema estará compuesto por varias estaciones ambientales ubicadas en diferentes zonas de la ciudad.

Cada estación deberá generar datos simulados de variables ambientales:
* Temperatura
* Humedad
* Ruido
* CO₂
* PM2.5
* PM10

El sistema deberá recolectar, procesar y visualizar los datos utilizando dos modelos de programación concurrente en Python: threading y multiprocessing.

### Versiones a implementar

#### 1. Versión secuencial
* El sistema ejecuta la simulación sin hilos ni procesos.
* Las estaciones generan datos de forma secuencial.
* Sirve como línea base para comparar el rendimiento.

#### 2. Versión basada en hilos
* Cada estación se ejecuta como un threading.Thread.
* Deben compartir una estructura común de datos.
* **Mecanismos obligatorios (mínimo 2):** Lock, RLock, Condition, Semaphore, Barrier o Event.
* El controlador debe coordinar hilos, evitar condiciones de carrera y calcular estadísticas.

#### 3. Versión basada en procesos
* Cada estación (o grupo) se ejecuta como un multiprocessing.Process.
* **Mecanismos obligatorios (mínimo 2):** Queue, Pipe, Semaphore, Barrier, Event o Pool.
* El controlador se comunica con los procesos para recibir mediciones y enviar comandos.

---

## Requerimientos funcionales

### Arquitectura (Diseño orientado a objetos)
Se deben implementar como mínimo las siguientes clases:
* EstacionAmbiental: Genera mediciones simuladas.
* Medicion: Contiene estación, zona, variable, valor y tiempo.
* ControladorMonitoreo: Coordina ejecución, ciclos, estadísticas y alertas.
* AnalizadorDatos: Procesa valores (promedios, máximos, mínimos, alertas).
* AlertaAmbiental: Representa una alerta al superar umbrales.

### Datos y procesamiento
* **Simulación:** Al menos 4 estaciones, 3 tipos de mediciones, 10 ciclos mínimos.
* **Análisis:** Promedios, máximos, mínimos, alertas, zonas de riesgo, tiempos de ejecución y carga computacional.

### Interfaz gráfica (GUI)
Implementada con Tkinter, PyQt o similar. Debe mostrar:
* Estado de estaciones, última medición, alertas, estadísticas, tiempo de ejecución, modo de ejecución e información del entorno.

---

## Ejecución y pruebas
* Ejecutar las tres versiones (Secuencial, Hilos, Procesos) al menos 3 veces.
* Probar tamaños: (4 est/10 ciclos), (8 est/20 ciclos), (12 est/30 ciclos).
* Comparar: Tiempos, mediciones/segundo, uso de sincronización y problemas de concurrencia encontrados.

---

## Análisis comparativo (Informe)
El informe debe responder:
1. ¿Qué versión fue más rápida?
2. ¿Hubo mejora respecto a la versión secuencial?
3. Impacto del GIL en la versión con hilos.
4. Mecanismos de sincronización/comunicación utilizados y justificación.
5. ¿En qué tareas conviene hilos vs. procesos?
6. Complejidad de implementación.

### Métricas de rendimiento
* **Aceleramiento (Speedup):**
  * S_thread = T_secuencial / T_thread
  * S_process = T_secuencial / T_process

---

## Entregables (AVAC)
1. Enlace a GitHub.
2. Archivo README (Instalación y ejecución).
3. Capturas de pantalla de la GUI.
4. Tabla comparativa de resultados.
5. Informe técnico en PDF.