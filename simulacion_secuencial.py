import time
import random
import math
from datetime import datetime
from dataclasses import dataclass
from typing import List, Dict

@dataclass
class Medicion:
    estacion_id: str
    zona: str
    variable: str
    valor: float
    timestamp: datetime

@dataclass
class AlertaAmbiental:
    estacion_id: str
    variable: str
    mensaje: str
    nivel_riesgo: str

class EstacionAmbiental:
    def __init__(self, id_estacion: str, zona: str):
        self.id_estacion = id_estacion
        self.zona = zona

    def generar_mediciones(self) -> List[Medicion]:
        """Simula y retorna una lista de mediciones ambientales realistas para Cuenca.

        Usa los mismos rangos por zona que las versiones de hilos y procesos para que
        la línea base secuencial sea comparable (misma carga: 6 variables por estación).
        """
        ahora = datetime.now()
        id_upper = self.id_estacion.upper()

        if "CENTRO" in id_upper:
            t = random.uniform(14.0, 25.0)
            h = random.uniform(50.0, 80.0)
            co2 = random.uniform(600.0, 1400.0)
            ruido = random.uniform(65.0, 95.0)
            pm25 = random.uniform(15.0, 45.0)
            pm10 = random.uniform(25.0, 75.0)
        elif "NORTE" in id_upper:
            t = random.uniform(11.0, 22.0)
            h = random.uniform(55.0, 85.0)
            co2 = random.uniform(500.0, 1100.0)
            ruido = random.uniform(60.0, 85.0)
            pm25 = random.uniform(18.0, 50.0)
            pm10 = random.uniform(30.0, 85.0)
        elif "SUR" in id_upper:
            t = random.uniform(12.0, 23.0)
            h = random.uniform(50.0, 85.0)
            co2 = random.uniform(450.0, 950.0)
            ruido = random.uniform(50.0, 80.0)
            pm25 = random.uniform(10.0, 30.0)
            pm10 = random.uniform(20.0, 55.0)
        elif "ESTE" in id_upper or "ZONA 4" in id_upper:
            t = random.uniform(9.0, 21.0)
            h = random.uniform(60.0, 95.0)
            co2 = random.uniform(400.0, 650.0)
            ruido = random.uniform(35.0, 60.0)
            pm25 = random.uniform(5.0, 20.0)
            pm10 = random.uniform(10.0, 35.0)
        else:
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

class AnalizadorDatos:
    def _calculo_pesado_cpu(self):
        """Simula un cálculo pesado para evidenciar el impacto del GIL posteriormente."""
        resultado = 0.0
        # Bucle matemático pesado: suma de las raíces cuadradas de 1 a 500,000
        for i in range(1, 500001):
            resultado += math.sqrt(i)
        return resultado

    def agregar(self, mediciones: List[Medicion]) -> Dict[str, Dict[str, float]]:
        """Agregación ligera (promedio/min/max) SIN carga de CPU.

        La usa el padre (hilos/procesos) para combinar estadísticas ya calculadas por
        cada hilo/proceso, evitando recentralizar el cómputo pesado.
        """
        valores_por_variable: Dict[str, List[float]] = {}
        for med in mediciones:
            valores_por_variable.setdefault(med.variable, []).append(med.valor)
        return {
            variable: {
                "promedio": sum(valores) / len(valores),
                "min": min(valores),
                "max": max(valores),
            }
            for variable, valores in valores_por_variable.items()
        }

    def procesar(self, mediciones: List[Medicion]) -> Dict[str, Dict[str, float]]:
        """Calcula promedio, mínimo y máximo por variable, simulando carga de CPU."""
        estadisticas = {}
        valores_por_variable = {}
        
        for med in mediciones:
            # Requerimiento estricto: Ejecutar el cálculo pesado por cada medición
            self._calculo_pesado_cpu()
            
            if med.variable not in valores_por_variable:
                valores_por_variable[med.variable] = []
            valores_por_variable[med.variable].append(med.valor)
            
        for variable, valores in valores_por_variable.items():
            estadisticas[variable] = {
                "promedio": sum(valores) / len(valores),
                "min": min(valores),
                "max": max(valores)
            }
            
        return estadisticas

class ControladorMonitoreo:
    def __init__(self, num_estaciones: int = 4):
        self.num_estaciones = num_estaciones

        # Nombres y zonas dinámicos (coherentes con las versiones de hilos y procesos)
        nombres = [f"EST-{i+1}" for i in range(num_estaciones)]
        zonas = [f"Zona {i+1}" for i in range(num_estaciones)]
        if num_estaciones == 4:
            nombres = ["EST-CENTRO", "EST-SUR", "EST-NORTE", "EST-ESTE"]
            zonas = ["Centro", "Sur", "Norte", "Este"]

        self.estaciones = [EstacionAmbiental(n, z) for n, z in zip(nombres, zonas)]
        self.analizador = AnalizadorDatos()
        # Define umbrales estáticos
        self.umbrales = {
            "Temperatura": 35.0,
            "Humedad": 90.0,
            "CO2": 1000.0,
            "Ruido": 90.0
        }
        self.alertas: List[AlertaAmbiental] = []

    def ejecutar_secuencial(self, ciclos: int = 10):
        print(f"--- Iniciando Simulación Secuencial ({ciclos} ciclos) ---")
        # Inicia un temporizador
        inicio_tiempo = time.perf_counter()
        
        total_mediciones_procesadas = 0

        # Hace un bucle de N ciclos
        for ciclo in range(1, ciclos + 1):
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Iniciando ciclo {ciclo}/{ciclos}...")
            
            todas_mediciones_ciclo = []
            
            # Recolección de datos iterando sobre las estaciones
            for estacion in self.estaciones:
                mediciones = estacion.generar_mediciones()
                todas_mediciones_ciclo.extend(mediciones)
                total_mediciones_procesadas += len(mediciones)
                
                # Evalúa umbrales y guarda alertas
                for med in mediciones:
                    if med.valor > self.umbrales.get(med.variable, float('inf')):
                        alerta = AlertaAmbiental(
                            estacion_id=med.estacion_id,
                            variable=med.variable,
                            mensaje=f"{med.variable} de {med.valor:.2f} superó el umbral de {self.umbrales[med.variable]}",
                            nivel_riesgo="ALTO"
                        )
                        self.alertas.append(alerta)
            
            # Pasa todas las mediciones al AnalizadorDatos
            # Esto ejecutará la simulación de CPU de manera secuencial para cada dato
            _estadisticas_ciclo = self.analizador.procesar(todas_mediciones_ciclo)
            
        # Finaliza temporizador
        fin_tiempo = time.perf_counter()
        tiempo_total = fin_tiempo - inicio_tiempo
        
        # Al final, imprime las estadísticas
        print("\n" + "="*40)
        print("--- Resultados de la Simulación ---")
        print("="*40)
        print(f"Tiempo Total de Ejecución : {tiempo_total:.4f} segundos")
        print(f"Mediciones Procesadas     : {total_mediciones_procesadas}")
        print(f"Total de Alertas Generadas: {len(self.alertas)}")
        print("="*40)
        
        if self.alertas:
            print("\nÚltimas 5 alertas generadas:")
            for alerta in self.alertas[-5:]:
                print(f" [!] {alerta.estacion_id} - {alerta.variable}: {alerta.mensaje} (Riesgo: {alerta.nivel_riesgo})")


if __name__ == "__main__":
    controlador = ControladorMonitoreo()
    controlador.ejecutar_secuencial(ciclos=10)
