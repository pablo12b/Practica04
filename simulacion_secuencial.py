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
        """Simula y retorna una lista de mediciones."""
        ahora = datetime.now()
        mediciones = [
            Medicion(self.id_estacion, self.zona, "Temperatura", random.uniform(15.0, 40.0), ahora),
            Medicion(self.id_estacion, self.zona, "Humedad", random.uniform(30.0, 100.0), ahora),
            Medicion(self.id_estacion, self.zona, "CO2", random.uniform(400.0, 2000.0), ahora),
            Medicion(self.id_estacion, self.zona, "Ruido", random.uniform(40.0, 120.0), ahora),
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
    def __init__(self):
        # Inicializa 4 estaciones (Centro, Sur, Norte, Este)
        self.estaciones = [
            EstacionAmbiental("EST-CENTRO", "Centro"),
            EstacionAmbiental("EST-SUR", "Sur"),
            EstacionAmbiental("EST-NORTE", "Norte"),
            EstacionAmbiental("EST-ESTE", "Este")
        ]
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
