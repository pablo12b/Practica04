import time
import random
import math
import threading
from queue import Queue
from datetime import datetime
from typing import List, Dict, Optional

# Importamos las clases base para mantener consistencia en los modelos y en el analizador pesado
from simulacion_secuencial import Medicion, AlertaAmbiental, AnalizadorDatos

class EstacionAmbientalThread(threading.Thread):
    def __init__(
        self,
        id_estacion: str,
        zona: str,
        ciclos: int,
        intervalo: float,
        controlador,
        queue: Optional[Queue] = None
    ):
        """
        Representa una estación de monitoreo que se ejecuta en su propio hilo.
        """
        super().__init__(name=id_estacion)
        self.id_estacion = id_estacion
        self.zona = zona
        self.ciclos = ciclos
        self.intervalo = intervalo  # Tiempo de espera en segundos entre ciclos
        self.controlador = controlador
        self.queue = queue
        
    def generar_mediciones(self) -> List[Medicion]:
        """Simula y retorna una lista de mediciones ambientales realistas para Cuenca."""
        ahora = datetime.now()
        
        # Identificar la zona para aplicar rangos coherentes
        id_upper = self.id_estacion.upper()
        
        if "CENTRO" in id_upper:
            # Centro Histórico: Más cálido (isla de calor), más ruido, alto CO2 y material particulado
            t = random.uniform(14.0, 25.0)
            h = random.uniform(50.0, 80.0)
            co2 = random.uniform(600.0, 1400.0)
            ruido = random.uniform(65.0, 95.0)
            pm25 = random.uniform(15.0, 45.0)
            pm10 = random.uniform(25.0, 75.0)
        elif "NORTE" in id_upper:
            # Norte (Zona Industrial): Temperaturas medias, ruido industrial alto, CO2 y alto material particulado
            t = random.uniform(11.0, 22.0)
            h = random.uniform(55.0, 85.0)
            co2 = random.uniform(500.0, 1100.0)
            ruido = random.uniform(60.0, 85.0)
            pm25 = random.uniform(18.0, 50.0)
            pm10 = random.uniform(30.0, 85.0)
        elif "SUR" in id_upper:
            # Sur (Residencial/Comercial): Valores moderados generales
            t = random.uniform(12.0, 23.0)
            h = random.uniform(50.0, 85.0)
            co2 = random.uniform(450.0, 950.0)
            ruido = random.uniform(50.0, 80.0)
            pm25 = random.uniform(10.0, 30.0)
            pm10 = random.uniform(20.0, 55.0)
        elif "ESTE" in id_upper or "ZONA 4" in id_upper:
            # Este (Periferia/Challuabamba/Río Tomebamba): Más frío, más húmedo, muy limpio, poco ruido
            t = random.uniform(9.0, 21.0)
            h = random.uniform(60.0, 95.0)
            co2 = random.uniform(400.0, 650.0)
            ruido = random.uniform(35.0, 60.0)
            pm25 = random.uniform(5.0, 20.0)
            pm10 = random.uniform(10.0, 35.0)
        else:
            # Rango por defecto para estaciones dinámicas adicionales (EST-5 en adelante)
            t = random.uniform(10.0, 23.0)
            h = random.uniform(50.0, 90.0)
            co2 = random.uniform(400.0, 1000.0)
            ruido = random.uniform(40.0, 85.0)
            pm25 = random.uniform(5.0, 35.0)
            pm10 = random.uniform(10.0, 60.0)
            
        mediciones = [
            Medicion(self.id_estacion, self.zona, "Temperatura", t, ahora),
            Medicion(self.id_estacion, self.zona, "Humedad", h, ahora),
            Medicion(self.id_estacion, self.zona, "CO2", co2, ahora),
            Medicion(self.id_estacion, self.zona, "Ruido", ruido, ahora),
            Medicion(self.id_estacion, self.zona, "PM2.5", pm25, ahora),
            Medicion(self.id_estacion, self.zona, "PM10", pm10, ahora),
        ]
        return mediciones

    def run(self):
        for ciclo in range(1, self.ciclos + 1):
            # Simular un pequeño retardo entre ciclos (útil para la visualización en tiempo real en la GUI)
            if self.intervalo > 0:
                time.sleep(self.intervalo)
                
            # 1. Generación de mediciones
            mediciones = self.generar_mediciones()
            
            # Enviar las mediciones individuales a la cola de la GUI si existe
            if self.queue:
                for med in mediciones:
                    self.queue.put(("MEDICION", med))
            
            # 2. MECANISMO DE SINCRONIZACIÓN 1: Lock
            # Usamos un Lock para evitar condiciones de carrera al escribir en la lista compartida de mediciones
            with self.controlador.lock:
                self.controlador.agregar_mediciones_ciclo(mediciones)
            
            # Evaluar alertas
            for med in mediciones:
                umbral = self.controlador.umbrales.get(med.variable, float('inf'))
                if med.valor > umbral:
                    # Riesgo ALTO si supera por más del 15% del umbral, de lo contrario MODERADO
                    nivel = "ALTO" if med.valor > umbral * 1.15 else "MODERADO"
                    alerta = AlertaAmbiental(
                        estacion_id=med.estacion_id,
                        variable=med.variable,
                        mensaje=f"{med.variable} de {med.valor:.2f} superó el umbral de {umbral}",
                        nivel_riesgo=nivel
                    )
                    
                    # Registrar alerta protegiendo el recurso compartido con Lock
                    with self.controlador.lock:
                        self.controlador.alertas.append(alerta)
                    
                    # Enviar la alerta a la cola de la GUI
                    if self.queue:
                        self.queue.put(("ALERTA", alerta))
            
            # 3. MECANISMO DE SINCRONIZACIÓN 2: Barrier
            # Las estaciones esperan a que todas completen el ciclo actual antes de pasar al siguiente.
            # Esto evita desfases temporales y permite procesar los datos de manera sincronizada.
            try:
                self.controlador.barrier.wait()
            except (threading.BrokenBarrierError, AssertionError):
                break


class ControladorMonitoreoHilos:
    def __init__(self, num_estaciones: int = 4, queue: Optional[Queue] = None):
        self.num_estaciones = num_estaciones
        self.analizador = AnalizadorDatos()
        self.queue = queue
        
        # Umbrales idénticos a los del secuencial
        self.umbrales = {
            "Temperatura": 35.0,
            "Humedad": 90.0,
            "CO2": 1000.0,
            "Ruido": 90.0
        }
        
        # Recursos compartidos entre hilos
        self.mediciones_ciclo_actual: List[Medicion] = []
        self.mediciones_historicas: List[Medicion] = []
        self.alertas: List[AlertaAmbiental] = []
        
        # Estructuras de sincronización
        self.lock = threading.Lock()
        self.barrier = None
        
        self.ciclo_actual = 1
        self.estaciones_threads: List[EstacionAmbientalThread] = []
        
        # Generación dinámica de nombres de estación y zonas
        self.estaciones_nombres = [f"EST-{i+1}" for i in range(num_estaciones)]
        self.zonas = [f"Zona {i+1}" for i in range(num_estaciones)]
        
        # Nombres legibles predeterminados si son 4 estaciones
        if num_estaciones == 4:
            self.estaciones_nombres = ["EST-CENTRO", "EST-SUR", "EST-NORTE", "EST-ESTE"]
            self.zonas = ["Centro", "Sur", "Norte", "Este"]

    def agregar_mediciones_ciclo(self, mediciones: List[Medicion]):
        """Agrega mediciones a la lista del ciclo actual (se ejecuta bajo Lock)."""
        self.mediciones_ciclo_actual.extend(mediciones)

    def procesar_ciclo_actual(self):
        """
        Acción ejecutada por el Barrier cuando todas las estaciones han completado su ciclo.
        Se ejecuta en el contexto de uno de los hilos de estación antes de liberarlos a todos.
        """
        with self.lock:
            mediciones = list(self.mediciones_ciclo_actual)
            self.mediciones_historicas.extend(mediciones)
            self.mediciones_ciclo_actual.clear()
            ciclo_procesado = self.ciclo_actual
            self.ciclo_actual += 1
            
        # Analizar mediciones simulando carga computacional pesada (GIL implicado)
        estadisticas = self.analizador.procesar(mediciones)
        
        # Notificar fin de ciclo a la GUI
        if self.queue:
            self.queue.put(("FIN_CICLO", {
                "ciclo": ciclo_procesado,
                "estadisticas": estadisticas
            }))
        else:
            # Consola
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Ciclo {ciclo_procesado} procesado con éxito.")
            for var, stats in estadisticas.items():
                print(f"  {var} -> Promedio: {stats['promedio']:.2f} | Min: {stats['min']:.2f} | Max: {stats['max']:.2f}")

    def ejecutar_hilos(self, ciclos: int = 10, intervalo: float = 0.0) -> float:
        """
        Inicia y coordina los hilos de las estaciones.
        """
        # Inicializar barrera
        self.barrier = threading.Barrier(self.num_estaciones, action=self.procesar_ciclo_actual)
        
        # Limpiar datos previos
        self.mediciones_ciclo_actual.clear()
        self.mediciones_historicas.clear()
        self.alertas.clear()
        self.ciclo_actual = 1
        
        if self.queue:
            self.queue.put(("INICIO", None))
        else:
            print(f"--- Iniciando Simulación con Hilos ({ciclos} ciclos, {self.num_estaciones} estaciones) ---")
            
        inicio_tiempo = time.perf_counter()
        
        # Crear y arrancar hilos
        self.estaciones_threads = []
        for i in range(self.num_estaciones):
            th = EstacionAmbientalThread(
                id_estacion=self.estaciones_nombres[i],
                zona=self.zonas[i],
                ciclos=ciclos,
                intervalo=intervalo,
                controlador=self,
                queue=self.queue
            )
            self.estaciones_threads.append(th)
            th.start()
            
        # Esperar a que todos terminen
        for th in self.estaciones_threads:
            th.join()
            
        fin_tiempo = time.perf_counter()
        tiempo_total = fin_tiempo - inicio_tiempo
        
        if self.queue:
            self.queue.put(("FIN", {
                "tiempo_total": tiempo_total,
                "mediciones_procesadas": len(self.mediciones_historicas),
                "total_alertas": len(self.alertas)
            }))
        else:
            print("\n" + "="*40)
            print("--- Resultados de la Simulación con Hilos ---")
            print("="*40)
            print(f"Tiempo Total de Ejecución : {tiempo_total:.4f} segundos")
            print(f"Mediciones Procesadas     : {len(self.mediciones_historicas)}")
            print(f"Total de Alertas Generadas: {len(self.alertas)}")
            print("="*40)
            if self.alertas:
                print("\nÚltimas 5 alertas generadas:")
                for alerta in self.alertas[-5:]:
                    print(f" [!] {alerta.estacion_id} - {alerta.variable}: {alerta.mensaje} (Riesgo: {alerta.nivel_riesgo})")
                    
        return tiempo_total

if __name__ == "__main__":
    # Prueba rápida standalone con hilos (4 estaciones, 10 ciclos)
    controlador = ControladorMonitoreoHilos(num_estaciones=4)
    controlador.ejecutar_hilos(ciclos=10, intervalo=0.05)
