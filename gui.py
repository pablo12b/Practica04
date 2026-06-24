import sys
import time
import random
import platform
import threading
import multiprocessing
from queue import Queue, Empty
from datetime import datetime
from typing import List, Dict, Optional

# Importamos PyQt6 para una interfaz nativa premium
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QGridLayout, QLabel, QProgressBar, QComboBox, QSlider, 
    QPushButton, QTabWidget, QListWidget, QListWidgetItem, QTableWidget, QTableWidgetItem,
    QHeaderView, QFrame, QScrollArea, QMessageBox
)
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QColor

# Importamos las simulaciones y modelos
from simulacion_secuencial import Medicion, AlertaAmbiental, AnalizadorDatos
from simulacion_hilos import ControladorMonitoreoHilos
from simulacion_procesos import ControladorMonitoreoProcesos

# Hojas de estilo CSS (QStyleSheet) 
STYLE_MAIN = """
QMainWindow {
    background-color: #f5f6f8;
}
QWidget#LeftPanel {
    background-color: #ffffff;
    border: 1px solid #d0d7de;
    border-radius: 8px;
}
QLabel {
    color: #333333;
}
QTabWidget::pane {
    border: 1px solid #d0d7de;
    background-color: #ffffff;
    border-radius: 8px;
}
QTabBar::tab {
    background-color: #e0e4e8;
    color: #495057;
    padding: 10px 18px;
    font-weight: bold;
    font-family: Helvetica;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    margin-right: 2px;
}
QTabBar::tab:selected {
    background-color: #1a73e8;
    color: #ffffff;
}
QTabBar::tab:hover:!selected {
    background-color: #e8f0fe;
    color: #1a73e8;
}
QComboBox {
    background-color: #ffffff;
    border: 1px solid #cccccc;
    border-radius: 4px;
    padding: 6px;
    color: #111111;
}
QSlider::groove:horizontal {
    height: 6px;
    background: #f1f3f4;
    border-radius: 3px;
}
QSlider::handle:horizontal {
    background: #1a73e8;
    width: 16px;
    height: 16px;
    margin-top: -5px;
    margin-bottom: -5px;
    border-radius: 8px;
}
"""

# Wrapper para la simulación secuencial compatible con la cola de la GUI
class ControladorMonitoreoSecuencialGUI:
    def __init__(self, num_estaciones: int, queue: Queue):
        self.num_estaciones = num_estaciones
        self.queue = queue
        self.analizador = AnalizadorDatos()
        self.umbrales = {
            "Temperatura": 24.0,
            "Humedad": 90.0,
            "CO2": 900.0,
            "Ruido": 80.0,
            "PM2.5": 25.0,
            "PM10": 50.0
        }
        self.alertas = []
        
        self.estaciones_nombres = [f"EST-{i+1}" for i in range(num_estaciones)]
        self.zonas = [f"Zona {i+1}" for i in range(num_estaciones)]
        if num_estaciones == 4:
            self.estaciones_nombres = ["EST-CENTRO", "EST-SUR", "EST-NORTE", "EST-ESTE"]
            self.zonas = ["Centro", "Sur", "Norte", "Este"]

    def generar_mediciones(self, id_estacion: str, zona: str) -> List[Medicion]:
        ahora = datetime.now()
        id_upper = id_estacion.upper()
        
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
            
        return [
            Medicion(id_estacion, zona, "Temperatura", t, ahora),
            Medicion(id_estacion, zona, "Humedad", h, ahora),
            Medicion(id_estacion, zona, "CO2", co2, ahora),
            Medicion(id_estacion, zona, "Ruido", ruido, ahora),
            Medicion(id_estacion, zona, "PM2.5", pm25, ahora),
            Medicion(id_estacion, zona, "PM10", pm10, ahora),
        ]

    def ejecutar(self, ciclos: int, intervalo: float):
        self.queue.put(("INICIO", None))
        inicio_tiempo = time.perf_counter()
        total_mediciones = 0

        for ciclo in range(1, ciclos + 1):
            if intervalo > 0:
                time.sleep(intervalo)

            mediciones_ciclo = []
            for i in range(self.num_estaciones):
                meds = self.generar_mediciones(self.estaciones_nombres[i], self.zonas[i])
                mediciones_ciclo.extend(meds)
                total_mediciones += len(meds)

                for med in meds:
                    self.queue.put(("MEDICION", med))

                for med in meds:
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
                        self.alertas.append(alerta)
                        self.queue.put(("ALERTA", alerta))

            estadisticas = self.analizador.procesar(mediciones_ciclo)
            self.queue.put(("FIN_CICLO", {
                "ciclo": ciclo,
                "estadisticas": estadisticas
            }))

        fin_tiempo = time.perf_counter()
        tiempo_total = fin_tiempo - inicio_tiempo

        self.queue.put(("FIN", {
            "tiempo_total": tiempo_total,
            "mediciones_procesadas": total_mediciones,
            "total_alertas": len(self.alertas)
        }))


# Widget visual para la Tarjeta de cada Estación (Tema Claro)
class TarjetaEstacionWidget(QWidget):
    def __init__(self, id_estacion: str, zona: str, parent=None):
        super().__init__(parent)
        self.id_estacion = id_estacion
        self.setObjectName("TarjetaEstacion")
        self.setStyleSheet("""
            QWidget#TarjetaEstacion {
                background-color: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(6)
        
        # Cabecera
        header = QHBoxLayout()
        self.lbl_title = QLabel(id_estacion, self)
        self.lbl_title.setStyleSheet("font-weight: bold; font-size: 12px; color: #1a73e8; border: 0px;")
        header.addWidget(self.lbl_title)
        
        self.lbl_status = QLabel("● Inactivo", self)
        self.lbl_status.setStyleSheet("font-weight: bold; font-size: 10px; color: #7f8c8d; border: 0px;")
        header.addWidget(self.lbl_status, alignment=Qt.AlignmentFlag.AlignRight)
        layout.addLayout(header)
        
        self.lbl_sub = QLabel(f"Zona: {zona}", self)
        self.lbl_sub.setStyleSheet("font-size: 10px; font-style: italic; color: #666666; border: 0px;")
        layout.addWidget(self.lbl_sub)
        
        # Divisor
        sep = QFrame(self)
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color: #eef2f5; border: 0px;")
        layout.addWidget(sep)
        
        # Variables y sus barras
        self.vars = ["Temperatura", "Humedad", "CO2", "Ruido", "PM2.5", "PM10"]
        self.lbl_valores = {}
        self.bars = {}
        self.anims = {}
        
        for var in self.vars:
            row = QHBoxLayout()
            lbl_name = QLabel(var, self)
            lbl_name.setStyleSheet("color: #4a4a4a; font-size: 11px; border: 0px;")
            row.addWidget(lbl_name)
            
            lbl_val = QLabel("--", self)
            lbl_val.setStyleSheet("font-weight: bold; color: #111111; font-size: 11px; border: 0px;")
            row.addWidget(lbl_val, alignment=Qt.AlignmentFlag.AlignRight)
            self.lbl_valores[var] = lbl_val
            layout.addLayout(row)
            
            # Subtítulos explicativos para PM2.5 y PM10 (Material Particulado)
            if var == "PM2.5":
                lbl_subt = QLabel("Partículas finas (hollín, metales)", self)
                lbl_subt.setStyleSheet("color: #888888; font-size: 8px; font-style: italic; border: 0px; margin-top: -4px; margin-bottom: 2px;")
                layout.addWidget(lbl_subt)
            elif var == "PM10":
                lbl_subt = QLabel("Polvo, polen y partículas gruesas", self)
                lbl_subt.setStyleSheet("color: #888888; font-size: 8px; font-style: italic; border: 0px; margin-top: -4px; margin-bottom: 2px;")
                layout.addWidget(lbl_subt)
            
            # Progress bar estilizado como indicador gráfico plano
            bar = QProgressBar(self)
            bar.setTextVisible(False)
            bar.setValue(0)
            bar.setFixedHeight(6)
            bar.setStyleSheet("""
                QProgressBar {
                    border: 0px;
                    background-color: #f1f3f4;
                    border-radius: 3px;
                }
                QProgressBar::chunk {
                    background-color: #1a73e8;
                    border-radius: 3px;
                }
            """)
            self.bars[var] = bar
            layout.addWidget(bar)

    def actualizar_status(self, activo: bool, finalizado: bool = False):
        if activo:
            self.lbl_status.setText("● Activo")
            self.lbl_status.setStyleSheet("font-weight: bold; font-size: 10px; color: #2e7d32; border: 0px;")
        elif finalizado:
            self.lbl_status.setText("● Listo")
            self.lbl_status.setStyleSheet("font-weight: bold; font-size: 10px; color: #1a73e8; border: 0px;")
        else:
            self.lbl_status.setText("● Inactivo")
            self.lbl_status.setStyleSheet("font-weight: bold; font-size: 10px; color: #7f8c8d; border: 0px;")

    def actualizar(self, variable: str, valor: float, umbral: float):
        lbl = self.lbl_valores.get(variable)
        bar = self.bars.get(variable)
        if not lbl or not bar:
            return
            
        unidades = {
            "Temperatura": " °C",
            "Humedad": " %",
            "CO2": " ppm",
            "Ruido": " dB",
            "PM2.5": " µg/m³",
            "PM10": " µg/m³"
        }
        lbl.setText(f"{valor:.1f}{unidades.get(variable, '')}")
        
        rangos = {
            "Temperatura": (0.0, 28.0), 
            "Humedad": (30.0, 100.0),
            "CO2": (400.0, 1500.0),
            "Ruido": (30.0, 100.0),
            "PM2.5": (0.0, 55.0),
            "PM10": (0.0, 100.0)
        }
        r_min, r_max = rangos.get(variable, (0.0, 100.0))
        pct = int(((valor - r_min) / (r_max - r_min)) * 100)
        pct = max(0, min(100, pct))
        
        # Animación suave del cambio de valor de la barra de progreso
        anim = self.anims.get(variable)
        if anim:
            anim.stop()
        else:
            anim = QPropertyAnimation(bar, b"value")
            anim.setDuration(400) 
            anim.setEasingCurve(QEasingCurve.Type.OutQuad) 
            self.anims[variable] = anim
            
        anim.setStartValue(bar.value())
        anim.setEndValue(pct)
        anim.start()
        
        if valor > umbral:
            lbl.setStyleSheet("font-weight: bold; color: #d32f2f; font-size: 11px; border: 0px;")
            bar.setStyleSheet("""
                QProgressBar { border: 0px; background-color: #f1f3f4; border-radius: 3px; }
                QProgressBar::chunk { background-color: #d32f2f; border-radius: 3px; }
            """)
        else:
            lbl.setStyleSheet("font-weight: bold; color: #2e7d32; font-size: 11px; border: 0px;")
            bar.setStyleSheet("""
                QProgressBar { border: 0px; background-color: #f1f3f4; border-radius: 3px; }
                QProgressBar::chunk { background-color: #2e7d32; border-radius: 3px; }
            """)


# Widget personalizado para la columna de Promedio en la tabla de Estadísticas
class CeldaEstadisticaPromedio(QWidget):
    def __init__(self, valor: float, variable: str, umbral: float, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 2, 10, 2)
        layout.setSpacing(10)
        
        unidades = {
            "Temperatura": " °C",
            "Humedad": " %",
            "CO2": " ppm",
            "Ruido": " dB",
            "PM2.5": " µg/m³",
            "PM10": " µg/m³"
        }
        
        lbl_val = QLabel(f"{valor:.1f}{unidades.get(variable, '')}", self)
        lbl_val.setStyleSheet("font-weight: bold; font-size: 11px; border: 0px;")
        layout.addWidget(lbl_val)
        
        # Micro barra de progreso indicadora
        bar = QProgressBar(self)
        bar.setTextVisible(False)
        bar.setFixedHeight(5)
        bar.setFixedWidth(80)
        
        rangos = {
            "Temperatura": (0.0, 28.0),
            "Humedad": (30.0, 100.0),
            "CO2": (400.0, 1500.0),
            "Ruido": (30.0, 100.0),
            "PM2.5": (0.0, 55.0),
            "PM10": (0.0, 100.0)
        }
        r_min, r_max = rangos.get(variable, (0.0, 100.0))
        pct = int(((valor - r_min) / (r_max - r_min)) * 100)
        pct = max(0, min(100, pct))
        bar.setValue(pct)
        
        if valor > umbral:
            lbl_val.setStyleSheet("font-weight: bold; color: #d32f2f; font-size: 11px; border: 0px;")
            bar.setStyleSheet("""
                QProgressBar { border: 0px; background-color: #f1f3f4; border-radius: 2px; }
                QProgressBar::chunk { background-color: #d32f2f; border-radius: 2px; }
            """)
        else:
            lbl_val.setStyleSheet("font-weight: bold; color: #2e7d32; font-size: 11px; border: 0px;")
            bar.setStyleSheet("""
                QProgressBar { border: 0px; background-color: #f1f3f4; border-radius: 2px; }
                QProgressBar::chunk { background-color: #2e7d32; border-radius: 2px; }
            """)
            
        layout.addWidget(bar, alignment=Qt.AlignmentFlag.AlignVCenter)
        layout.addStretch()


# Ventana Principal de la Aplicación en PyQt6 (con QTimer robusto e hilos estándar de Python)
class AplicacionMonitoreoWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sistema Concurrente de Monitoreo Ambiental Urbano - Cuenca")
        self.resize(1180, 760)
        self.setMinimumSize(1180, 760)
        self.setStyleSheet(STYLE_MAIN)
        
        self.simulacion_corriendo = False
        self.sim_thread = None
        self.queue = None
        self.controlador_activo = None
        self.historial_tiempos = {}
        self.umbrales = {
            "Temperatura": 24.0,
            "Humedad": 90.0,
            "CO2": 900.0,
            "Ruido": 80.0,
            "PM2.5": 25.0,
            "PM10": 50.0
        }
        
        # Configurar QTimer para leer de la cola de forma no bloqueante en el hilo de la GUI
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.check_queue)
        
        self.crear_diseno()
        
        # Animación de la barra de progreso global
        self.global_bar_anim = QPropertyAnimation(self.progress_bar, b"value")
        self.global_bar_anim.setDuration(300)
        self.global_bar_anim.setEasingCurve(QEasingCurve.Type.OutQuad)
        
    def crear_diseno(self):
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(12)
        
        # 1. Cabecera
        header = QFrame(self)
        header.setStyleSheet("background-color: #ffffff; border: 1px solid #dcdcdc; border-radius: 6px;")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 12, 20, 12)
        
        lbl_head = QLabel("SISTEMA CONCURRENTE DE MONITOREO AMBIENTAL", self)
        lbl_head.setStyleSheet("font-weight: bold; font-size: 14px; color: #1a73e8; border: 0px;")
        header_layout.addWidget(lbl_head)
        
        self.lbl_global_status = QLabel("●", self)
        self.lbl_global_status.setStyleSheet("font-size: 18px; color: #d32f2f; border: 0px;")
        header_layout.addWidget(self.lbl_global_status, alignment=Qt.AlignmentFlag.AlignRight)
        
        main_layout.addWidget(header)
        
        # Cuerpo
        body = QHBoxLayout()
        body.setSpacing(15)
        
        # 2. Panel de Control Izquierdo
        panel_izq = QWidget(self)
        panel_izq.setObjectName("LeftPanel")
        panel_izq.setFixedWidth(270)
        
        layout_izq = QVBoxLayout(panel_izq)
        layout_izq.setContentsMargins(20, 20, 20, 20)
        layout_izq.setSpacing(12)
        
        lbl_cfg_title = QLabel("CONFIGURACIÓN", self)
        lbl_cfg_title.setStyleSheet("font-weight: bold; font-size: 12px; color: #1a73e8; margin-bottom: 5px;")
        layout_izq.addWidget(lbl_cfg_title)
        
        # Modo
        layout_izq.addWidget(QLabel("Modo de Ejecución:", self))
        self.combo_modo = QComboBox(self)
        self.combo_modo.addItems(["Secuencial", "Hilos", "Procesos"])
        self.combo_modo.setCurrentText("Hilos")
        layout_izq.addWidget(self.combo_modo)
        
        # Estaciones
        self.lbl_estaciones_val = QLabel("Estaciones: 4", self)
        layout_izq.addWidget(self.lbl_estaciones_val)
        self.slider_estaciones = QSlider(Qt.Orientation.Horizontal, self)
        self.slider_estaciones.setRange(4, 12)
        self.slider_estaciones.setSingleStep(4)
        self.slider_estaciones.setPageStep(4)
        self.slider_estaciones.setValue(4)
        self.slider_estaciones.valueChanged.connect(self.on_estaciones_change)
        layout_izq.addWidget(self.slider_estaciones)
        
        # Ciclos
        self.lbl_ciclos_val = QLabel("Ciclos: 10", self)
        layout_izq.addWidget(self.lbl_ciclos_val)
        self.slider_ciclos = QSlider(Qt.Orientation.Horizontal, self)
        self.slider_ciclos.setRange(10, 50)
        self.slider_ciclos.setSingleStep(10)
        self.slider_ciclos.setValue(10)
        self.slider_ciclos.valueChanged.connect(lambda v: self.lbl_ciclos_val.setText(f"Ciclos: {v}"))
        layout_izq.addWidget(self.slider_ciclos)
        
        # Delay
        self.lbl_delay_val = QLabel("Retardo Ciclos: 0.15s", self)
        layout_izq.addWidget(self.lbl_delay_val)
        self.slider_delay = QSlider(Qt.Orientation.Horizontal, self)
        self.slider_delay.setRange(0, 100)
        self.slider_delay.setValue(15)
        self.slider_delay.valueChanged.connect(lambda v: self.lbl_delay_val.setText(f"Retardo Ciclos: {v/100:.2f}s"))
        layout_izq.addWidget(self.slider_delay)
        
        # Botones creados como tk.Button nativos para evitar el bloqueo del estilo de botón nativo en macOS
        self.btn_iniciar = QPushButton("INICIAR SIMULACIÓN", self)
        self.btn_iniciar.setObjectName("BtnIniciar")
        self.btn_iniciar.setFixedHeight(38)
        self.btn_iniciar.clicked.connect(self.iniciar_simulacion)
        layout_izq.addWidget(self.btn_iniciar)
        
        self.btn_detener = QPushButton("DETENER / ABORTAR", self)
        self.btn_detener.setObjectName("BtnDetener")
        self.btn_detener.setFixedHeight(38)
        self.btn_detener.setEnabled(False)
        self.btn_detener.clicked.connect(self.detener_simulacion)
        layout_izq.addWidget(self.btn_detener)
        
        # Barra de progreso
        layout_izq.addWidget(QLabel("Progreso de Ciclos:", self))
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #cccccc;
                border-radius: 4px;
                text-align: center;
                background-color: #f1f3f4;
            }
            QProgressBar::chunk {
                background-color: #1a73e8;
            }
        """)
        self.progress_bar.setValue(0)
        layout_izq.addWidget(self.progress_bar)

        # Información del entorno de ejecución
        lbl_env_title = QLabel("INFORMACIÓN DEL ENTORNO", self)
        lbl_env_title.setStyleSheet("font-weight: bold; font-size: 12px; color: #1a73e8; margin-top: 10px;")
        layout_izq.addWidget(lbl_env_title)

        gil_activo = sys._is_gil_enabled() if hasattr(sys, "_is_gil_enabled") else True
        info_entorno = (
            f"Python: {platform.python_version()} ({platform.python_implementation()})\n"
            f"SO: {platform.system()} {platform.release()}\n"
            f"Núcleos CPU: {multiprocessing.cpu_count()}\n"
            f"GIL: {'Activado' if gil_activo else 'Desactivado'}"
        )
        lbl_env = QLabel(info_entorno, self)
        lbl_env.setStyleSheet("font-size: 10px; color: #5f6368; border: 0px;")
        lbl_env.setWordWrap(True)
        layout_izq.addWidget(lbl_env)

        layout_izq.addStretch()
        
        body.addWidget(panel_izq)
        
        # 3. Tabbed Panel
        self.tabs = QTabWidget(self)
        
        # Tab 1
        self.tab_monitor = QWidget()
        self.setup_monitor_tab()
        self.tabs.addTab(self.tab_monitor, "ESTACIONES EN TIEMPO REAL")
        
        # Tab 2
        self.tab_stats = QWidget()
        self.setup_stats_tab()
        self.tabs.addTab(self.tab_stats, "ESTADÍSTICAS DEL CICLO")
        
        # Tab 3
        self.tab_alertas = QWidget()
        self.setup_alertas_tab()
        self.tabs.addTab(self.tab_alertas, "ALERTAS AMBIENTALES")
        
        # Tab 4
        self.tab_performance = QWidget()
        self.setup_performance_tab()
        self.tabs.addTab(self.tab_performance, "COMPARACIÓN & SPEEDUP")
        
        body.addWidget(self.tabs)
        
        main_layout.addLayout(body)
        
    def setup_monitor_tab(self):
        scroll = QScrollArea(self.tab_monitor)
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background-color: transparent; border: 0px;")
        
        scroll_widget = QWidget()
        scroll_widget.setStyleSheet("background-color: transparent;")
        
        self.grid_monitor = QGridLayout(scroll_widget)
        self.grid_monitor.setSpacing(15)
        self.grid_monitor.setContentsMargins(10, 10, 10, 10)
        
        scroll.setWidget(scroll_widget)
        
        layout = QVBoxLayout(self.tab_monitor)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(scroll)
        
    def setup_stats_tab(self):
        layout = QVBoxLayout(self.tab_stats)
        layout.setContentsMargins(20, 20, 20, 20)
        
        self.tbl_stats = QTableWidget(self)
        self.tbl_stats.setColumnCount(3)
        self.tbl_stats.setRowCount(6)
        self.tbl_stats.setHorizontalHeaderLabels(["Valor Promedio", "Valor Mínimo", "Valor Máximo"])
        self.tbl_stats.setVerticalHeaderLabels(["Temperatura", "Humedad", "CO2", "Ruido", "PM2.5", "PM10"])
        self.tbl_stats.setStyleSheet("background-color: #ffffff; color: #111111; gridline-color: #e2e8f0; font-family: Helvetica;")
        self.tbl_stats.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        header = self.tbl_stats.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tbl_stats.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        layout.addWidget(self.tbl_stats)
        
        self.lbl_ciclo_progreso = QLabel("Último Ciclo Procesado: Ninguno", self)
        self.lbl_ciclo_progreso.setStyleSheet("font-weight: bold; color: #1a73e8; font-size: 12px; margin-top: 10px;")
        layout.addWidget(self.lbl_ciclo_progreso, alignment=Qt.AlignmentFlag.AlignCenter)
        
    def setup_alertas_tab(self):
        layout = QVBoxLayout(self.tab_alertas)
        layout.setContentsMargins(20, 20, 20, 20)
        
        self.lst_alertas = QListWidget(self)
        self.lst_alertas.setStyleSheet("background-color: #ffffff; font-family: Courier New; font-weight: bold; border: 1px solid #d0d7de; border-radius: 6px; font-size: 11px;")
        layout.addWidget(self.lst_alertas)
        
    def setup_performance_tab(self):
        layout = QVBoxLayout(self.tab_performance)
        layout.setContentsMargins(20, 20, 20, 20)
        
        self.tbl_perf = QTableWidget(self)
        self.tbl_perf.setColumnCount(5)
        self.tbl_perf.setRowCount(9)
        self.tbl_perf.setHorizontalHeaderLabels(["Modo", "Estaciones", "Ciclos", "Tiempo (seg)", "Speedup vs Secuencial"])
        self.tbl_perf.verticalHeader().setVisible(False)
        self.tbl_perf.setStyleSheet("background-color: #ffffff; color: #333333; gridline-color: #e2e8f0;")
        self.tbl_perf.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        header = self.tbl_perf.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tbl_perf.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        for r in range(9):
            for c in range(5):
                self.tbl_perf.setItem(r, c, QTableWidgetItem("--"))
                
        layout.addWidget(self.tbl_perf)
        
        btn_limpiar = QPushButton("Limpiar Historial de Rendimiento", self)
        btn_limpiar.setStyleSheet("background-color: #ffebee; color: #d32f2f; font-weight: bold; padding: 10px; border-radius: 4px; border: 0px;")
        btn_limpiar.clicked.connect(self.limpiar_historial)
        layout.addWidget(btn_limpiar, alignment=Qt.AlignmentFlag.AlignCenter)

    def on_estaciones_change(self, value):
        if value < 6:
            value = 4
        elif value < 10:
            value = 8
        else:
            value = 12
            
        self.slider_estaciones.setValue(value)
        self.lbl_estaciones_val.setText(f"Estaciones: {value}")
        self.inicializar_tarjetas_estaciones(value)

    def inicializar_tarjetas_estaciones(self, num_estaciones: int):
        while self.grid_monitor.count():
            item = self.grid_monitor.takeAt(0)
            w = item.widget()
            if w is not None:
                w.deleteLater()
                
        self.tarjetas = {}
        
        nombres = [f"EST-{i+1}" for i in range(num_estaciones)]
        zonas = [f"Zona {i+1}" for i in range(num_estaciones)]
        if num_estaciones == 4:
            nombres = ["EST-CENTRO", "EST-SUR", "EST-NORTE", "EST-ESTE"]
            zonas = ["Centro", "Sur", "Norte", "Este"]
            
        cols = 4 if num_estaciones >= 4 else num_estaciones
        if num_estaciones == 12:
            cols = 4
            
        for idx in range(num_estaciones):
            r = idx // cols
            c = idx % cols
            
            tarjeta = TarjetaEstacionWidget(nombres[idx], zonas[idx], self)
            self.grid_monitor.addWidget(tarjeta, r, c)
            self.tarjetas[nombres[idx]] = tarjeta

    def iniciar_simulacion(self):
        if self.simulacion_corriendo:
            return
            
        modo = self.combo_modo.currentText()
        num_estaciones = self.slider_estaciones.value()
        ciclos = self.slider_ciclos.value()
        intervalo = self.slider_delay.value() / 100.0
        
        # Limpiar UI
        self.lst_alertas.clear()
        self.progress_bar.setRange(0, ciclos)
        self.progress_bar.setValue(0)
        self.lbl_ciclo_progreso.setText("Último Ciclo Procesado: Ninguno")
        
        for r in range(6):
            for c in range(3):
                self.tbl_stats.removeCellWidget(r, c)
                self.tbl_stats.setItem(r, c, QTableWidgetItem("--"))
                
        self.inicializar_tarjetas_estaciones(num_estaciones)
        for tarjeta in self.tarjetas.values():
            tarjeta.actualizar_status(activo=True)
            
        # Configurar cola e iniciar hilo estándar de Python (no QThread, evitando fallos Cocoa)
        self.queue = Queue()
        self.simulacion_corriendo = True
        self.btn_iniciar.setEnabled(False)
        self.btn_detener.setEnabled(True)
        self.lbl_global_status.setText("●")
        self.lbl_global_status.setStyleSheet("font-size: 18px; color: #2e7d32; border: 0px;")
        
        self.tiempo_inicio_sim = time.perf_counter()
        
        if modo == "Secuencial":
            self.controlador_activo = ControladorMonitoreoSecuencialGUI(num_estaciones, self.queue)
            self.sim_thread = threading.Thread(target=self.controlador_activo.ejecutar, args=(ciclos, intervalo))
        elif modo == "Hilos":
            self.controlador_activo = ControladorMonitoreoHilos(num_estaciones, self.queue)
            self.sim_thread = threading.Thread(target=self.controlador_activo.ejecutar_hilos, args=(ciclos, intervalo))
        elif modo == "Procesos":
            self.controlador_activo = ControladorMonitoreoProcesos(num_estaciones, self.queue)
            self.sim_thread = threading.Thread(target=self.controlador_activo.ejecutar_procesos, args=(ciclos, intervalo))
            
        self.sim_thread.daemon = True
        self.sim_thread.start()
        
        # Iniciar el QTimer para leer de la cola en el hilo principal
        self.timer.start(30)

    def detener_simulacion(self):
        if not self.simulacion_corriendo:
            return
            
        self.timer.stop()
        self.simulacion_corriendo = False
        
        if self.controlador_activo:
            if hasattr(self.controlador_activo, "barrier") and self.controlador_activo.barrier:
                try:
                    self.controlador_activo.barrier.reset()
                except Exception:
                    pass
            
        for tarjeta in self.tarjetas.values():
            tarjeta.actualizar_status(activo=False)
            
        self.finalizar_gui("Simulación Cancelada por el Usuario")

    def check_queue(self):
        if not self.simulacion_corriendo:
            return
            
        try:
            # Procesar todos los mensajes listos en la cola
            while True:
                msg_tipo, datos = self.queue.get_nowait()
                self.procesar_mensaje(msg_tipo, datos)
                self.queue.task_done()
        except Empty:
            pass

    def procesar_mensaje(self, msg_tipo: str, datos):
        if msg_tipo == "MEDICION":
            med = datos
            tarjeta = self.tarjetas.get(med.estacion_id)
            if tarjeta:
                tarjeta.actualizar(med.variable, med.valor, self.umbrales.get(med.variable, float('inf')))
                
        elif msg_tipo == "ALERTA":
            alerta = datos
            now_str = datetime.now().strftime('%H:%M:%S')
            alert_str = f"[{now_str}] ALERTA! {alerta.estacion_id} -> {alerta.mensaje} ({alerta.nivel_riesgo})"
            
            # Crear y colorear individualmente el ítem según el nivel de riesgo
            item = QListWidgetItem(alert_str)
            if alerta.nivel_riesgo == "MODERADO":
                item.setForeground(QColor("#d97706"))  # Naranja
            else:
                item.setForeground(QColor("#d32f2f"))  # Rojo
                
            self.lst_alertas.addItem(item)
            self.lst_alertas.scrollToBottom()
            
        elif msg_tipo == "FIN_CICLO":
            ciclo = datos["ciclo"]
            stats = datos["estadisticas"]
            self.lbl_ciclo_progreso.setText(f"Último Ciclo Procesado: {ciclo} / {self.slider_ciclos.value()}")
            self.global_bar_anim.stop()
            self.global_bar_anim.setStartValue(self.progress_bar.value())
            self.global_bar_anim.setEndValue(ciclo)
            self.global_bar_anim.start()
            
            variables = ["Temperatura", "Humedad", "CO2", "Ruido", "PM2.5", "PM10"]
            for row_idx, var in enumerate(variables):
                val_stats = stats.get(var, {})
                if val_stats:
                    self.tbl_stats.setItem(row_idx, 0, QTableWidgetItem(f"{val_stats.get('promedio', 0.0):.1f}"))
                    self.tbl_stats.setItem(row_idx, 1, QTableWidgetItem(f"{val_stats.get('min', 0.0):.1f}"))
                    self.tbl_stats.setItem(row_idx, 2, QTableWidgetItem(f"{val_stats.get('max', 0.0):.1f}"))
                    
        elif msg_tipo == "FIN":
            self.timer.stop()
            tiempo_total = datos["tiempo_total"]
            self.simulacion_corriendo = False
            
            for tarjeta in self.tarjetas.values():
                tarjeta.actualizar_status(activo=False, finalizado=True)
                
            self.registrar_tiempos_y_actualizar_tabla(tiempo_total)
            self.finalizar_gui(f"Completado con éxito en {tiempo_total:.4f} segundos.")

    def registrar_tiempos_y_actualizar_tabla(self, tiempo_total: float):
        modo = self.combo_modo.currentText()
        num_est = self.slider_estaciones.value()
        ciclos = self.slider_ciclos.value()
        
        clave = (num_est, ciclos)
        if clave not in self.historial_tiempos:
            self.historial_tiempos[clave] = {}
            
        self.historial_tiempos[clave][modo] = tiempo_total
        self.actualizar_tabla_performance()

    def actualizar_tabla_performance(self):
        for r in range(9):
            for c in range(5):
                self.tbl_perf.setItem(r, c, QTableWidgetItem("--"))
                
        row_idx = 0
        for (num_est, ciclos), modos_tiempos in sorted(self.historial_tiempos.items()):
            tiempo_sec = modos_tiempos.get("Secuencial")
            
            for modo, tiempo in sorted(modos_tiempos.items()):
                if row_idx >= 9:
                    break
                    
                self.tbl_perf.setItem(row_idx, 0, QTableWidgetItem(modo))
                self.tbl_perf.setItem(row_idx, 1, QTableWidgetItem(str(num_est)))
                self.tbl_perf.setItem(row_idx, 2, QTableWidgetItem(str(ciclos)))
                self.tbl_perf.setItem(row_idx, 3, QTableWidgetItem(f"{tiempo:.4f}"))
                
                if tiempo_sec and modo != "Secuencial":
                    speedup = tiempo_sec / tiempo
                    self.tbl_perf.setItem(row_idx, 4, QTableWidgetItem(f"{speedup:.2f}x"))
                elif modo == "Secuencial":
                    self.tbl_perf.setItem(row_idx, 4, QTableWidgetItem("1.00x (Ref)"))
                else:
                    self.tbl_perf.setItem(row_idx, 4, QTableWidgetItem("Falta Sec."))
                    
                row_idx += 1

    def limpiar_historial(self):
        self.historial_tiempos.clear()
        self.actualizar_tabla_performance()
        QMessageBox.information(self, "Limpieza", "Se ha borrado el historial de rendimiento.")

    def finalizar_gui(self, mensaje):
        self.btn_iniciar.setEnabled(True)
        self.btn_detener.setEnabled(False)
        self.lbl_global_status.setText("●")
        self.lbl_global_status.setStyleSheet("font-size: 18px; color: #d32f2f; border: 0px;")
        QMessageBox.information(self, "Simulación Finalizada", mensaje)


if __name__ == "__main__":
    import multiprocessing
    multiprocessing.freeze_support()
    
    app = QApplication(sys.argv)
    window = AplicacionMonitoreoWindow()
    window.show()
    sys.exit(app.exec())
