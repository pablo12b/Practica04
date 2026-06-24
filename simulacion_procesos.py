import time
import random
import math
import multiprocessing
from queue import Empty
from datetime import datetime
from typing import List, Dict, Optional

# Importamos las clases base para mantener consistencia
from simulacion_secuencial import Medicion, AlertaAmbiental, AnalizadorDatos

class EstacionAmbientalProcess(multiprocessing.Process):
    def __init__(
        self,
        id_estacion: str,
        zona: str,
        ciclos: int,
        intervalo: float,
        queue: multiprocessing.Queue,
        barrier: multiprocessing.Barrier,
        umbrales: dict
    ):
        """
        Representa una estación de monitoreo que se ejecuta en su propio proceso.
        """
        super().__init__(name=id_estacion)
        self.id_estacion = id_estacion
        self.zona = zona
        self.ciclos = ciclos
        self.intervalo = intervalo
        self.queue = queue
        self.barrier = barrier
        self.umbrales = umbrales

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
        # Cada proceso tiene su propia instancia del analizador (memoria aislada)
        analizador = AnalizadorDatos()

        for ciclo in range(1, self.ciclos + 1):
            if self.intervalo > 0:
                time.sleep(self.intervalo)

            # 1. Generar mediciones
            mediciones = self.generar_mediciones()

            # 1.b CÁLCULO PESADO DISTRIBUIDO: cada proceso analiza SUS propias mediciones
            # en paralelo real sobre distintos núcleos (multiprocessing vence al GIL).
            analizador.procesar(mediciones)

            # Enviar las mediciones al proceso padre a través de la Queue (IPC)
            # Para evitar sobrecargar la IPC de mensajes individuales, podemos enviar la lista
            self.queue.put(("MEDICIONES_ESTACION", {
                "ciclo": ciclo,
                "estacion_id": self.id_estacion,
                "mediciones": mediciones
            }))

            # Evaluar alertas localmente y enviarlas si es necesario
            for med in mediciones:
                umbral = self.umbrales.get(med.variable, float('inf'))
                if med.valor > umbral:
                    # Riesgo ALTO si supera por más del 15% del umbral, de lo contrario MODERADO
                    nivel = "ALTO" if med.valor > umbral * 1.15 else "MODERADO"
                    alerta = AlertaAmbiental(
                        estacion_id=med.estacion_id,
                        variable=med.variable,
                        mensaje=f"{med.variable} de {med.valor:.2f} superó el umbral de {umbral}",
                        nivel_riesgo=nivel
                    )
                    self.queue.put(("ALERTA", alerta))

            # 2. MECANISMO DE SINCRONIZACIÓN: Barrier (Multiprocessing)
            # Esperar a que todas las estaciones completen el ciclo actual antes de pasar al siguiente.
            try:
                self.barrier.wait()
            except Exception:
                break


class ControladorMonitoreoProcesos:
    def __init__(self, num_estaciones: int = 4, gui_queue: Optional[any] = None):
        self.num_estaciones = num_estaciones
        self.analizador = AnalizadorDatos()
        self.gui_queue = gui_queue
        
        self.umbrales = {
            "Temperatura": 35.0,
            "Humedad": 90.0,
            "CO2": 1000.0,
            "Ruido": 90.0
        }
        
        self.mediciones_historicas: List[Medicion] = []
        self.alertas: List[AlertaAmbiental] = []
        
        self.estaciones_nombres = [f"EST-{i+1}" for i in range(num_estaciones)]
        self.zonas = [f"Zona {i+1}" for i in range(num_estaciones)]
        
        if num_estaciones == 4:
            self.estaciones_nombres = ["EST-CENTRO", "EST-SUR", "EST-NORTE", "EST-ESTE"]
            self.zonas = ["Centro", "Sur", "Norte", "Este"]

    def ejecutar_procesos(self, ciclos: int = 10, intervalo: float = 0.0) -> float:
        # Colas de comunicación y sincronización de multiprocessing
        ipc_queue = multiprocessing.Queue()
        barrier = multiprocessing.Barrier(self.num_estaciones)
        
        if self.gui_queue:
            self.gui_queue.put(("INICIO", None))
        else:
            print(f"--- Iniciando Simulación con Procesos ({ciclos} ciclos, {self.num_estaciones} estaciones) ---")
            
        inicio_tiempo = time.perf_counter()
        
        # Crear y arrancar procesos de estaciones
        procesos: List[EstacionAmbientalProcess] = []
        for i in range(self.num_estaciones):
            p = EstacionAmbientalProcess(
                id_estacion=self.estaciones_nombres[i],
                zona=self.zonas[i],
                ciclos=ciclos,
                intervalo=intervalo,
                queue=ipc_queue,
                barrier=barrier,
                umbrales=self.umbrales
            )
            procesos.append(p)
            p.start()
            
        # Hilo/Bucle de lectura del proceso padre para recolectar mediciones de la IPC
        # Esperamos recibir 'num_estaciones' listas de mediciones por cada uno de los ciclos
        mediciones_por_ciclo: Dict[int, List[Medicion]] = {c: [] for c in range(1, ciclos + 1)}
        estaciones_recibidas_ciclo: Dict[int, set] = {c: set() for c in range(1, ciclos + 1)}
        
        procesos_activos = len(procesos)
        
        while procesos_activos > 0 or not ipc_queue.empty():
            try:
                # Esperar mensajes de la cola IPC con un pequeño timeout
                msg_tipo, datos = ipc_queue.get(timeout=0.05)
                
                if msg_tipo == "MEDICIONES_ESTACION":
                    ciclo = datos["ciclo"]
                    estacion_id = datos["estacion_id"]
                    mediciones = datos["mediciones"]
                    
                    # Evitar duplicados y guardar
                    if estacion_id not in estaciones_recibidas_ciclo[ciclo]:
                        estaciones_recibidas_ciclo[ciclo].add(estacion_id)
                        mediciones_por_ciclo[ciclo].extend(mediciones)
                        self.mediciones_historicas.extend(mediciones)
                        
                        # Si tenemos GUI, notificar las mediciones en tiempo real
                        if self.gui_queue:
                            for med in mediciones:
                                self.gui_queue.put(("MEDICION", med))
                                
                    # Comprobar si el ciclo se completó (recibimos datos de todas las estaciones)
                    if len(estaciones_recibidas_ciclo[ciclo]) == self.num_estaciones:
                        # El cómputo pesado ya lo hizo cada proceso hijo; el padre solo
                        # agrega de forma ligera las estadísticas del ciclo (sin carga de CPU).
                        mediciones_ciclo = mediciones_por_ciclo[ciclo]
                        estadisticas = self.analizador.agregar(mediciones_ciclo)
                        
                        if self.gui_queue:
                            self.gui_queue.put(("FIN_CICLO", {
                                "ciclo": ciclo,
                                "estadisticas": estadisticas
                            }))
                        else:
                            print(f"Ciclo {ciclo} completado. Estadísticas:")
                            for var, stats in estadisticas.items():
                                print(f"  {var} -> Prom: {stats['promedio']:.2f} | Min: {stats['min']:.2f} | Max: {stats['max']:.2f}")
                                
                elif msg_tipo == "ALERTA":
                    self.alertas.append(datos)
                    if self.gui_queue:
                        self.gui_queue.put(("ALERTA", datos))
                        
            except Empty:
                # Comprobar si los procesos siguen vivos
                procesos_activos = sum(1 for p in procesos if p.is_alive())
                
        # Asegurar de vaciar cualquier dato restante
        for p in procesos:
            p.join()
            
        fin_tiempo = time.perf_counter()
        tiempo_total = fin_tiempo - inicio_tiempo
        
        if self.gui_queue:
            self.gui_queue.put(("FIN", {
                "tiempo_total": tiempo_total,
                "mediciones_procesadas": len(self.mediciones_historicas),
                "total_alertas": len(self.alertas)
            }))
        else:
            print("\n" + "="*40)
            print("--- Resultados de la Simulación con Procesos ---")
            print("="*40)
            print(f"Tiempo Total de Ejecución : {tiempo_total:.4f} segundos")
            print(f"Mediciones Procesadas     : {len(self.mediciones_historicas)}")
            print(f"Total de Alertas Generadas: {len(self.alertas)}")
            print("="*40)
            
        return tiempo_total

if __name__ == "__main__":
    # Prueba rápida standalone con procesos (4 estaciones, 10 ciclos)
    controlador = ControladorMonitoreoProcesos(num_estaciones=4)
    controlador.ejecutar_procesos(ciclos=10, intervalo=0.05)
