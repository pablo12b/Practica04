"""Benchmark comparativo de las tres versiones (secuencial, hilos, procesos).

Ejecuta cada versión 3 veces en los tamaños (4 est/10 ciclos), (8/20) y (12/30)
con intervalo=0.0 (sin retardo artificial) y reporta tiempos, mediciones/segundo
y speedup. Pensado para correr en consola: python3 benchmark.py
"""
import io
import os
import time
import statistics
import platform
import contextlib
import multiprocessing

from simulacion_secuencial import ControladorMonitoreo
from simulacion_hilos import ControladorMonitoreoHilos
from simulacion_procesos import ControladorMonitoreoProcesos

REPETICIONES = 3
TAMANOS = [(4, 10), (8, 20), (12, 30)]


def medir_secuencial(n, ciclos):
    c = ControladorMonitoreo(num_estaciones=n)
    t0 = time.perf_counter()
    c.ejecutar_secuencial(ciclos=ciclos)
    return time.perf_counter() - t0, len(c.estaciones) * 6 * ciclos


def medir_hilos(n, ciclos):
    c = ControladorMonitoreoHilos(num_estaciones=n)
    t = c.ejecutar_hilos(ciclos=ciclos, intervalo=0.0)
    return t, len(c.mediciones_historicas)


def medir_procesos(n, ciclos):
    c = ControladorMonitoreoProcesos(num_estaciones=n)
    t = c.ejecutar_procesos(ciclos=ciclos, intervalo=0.0)
    return t, len(c.mediciones_historicas)


def main():
    print("=" * 70)
    print("ENTORNO DE EJECUCIÓN")
    print("=" * 70)
    print(f"Python      : {platform.python_version()} ({platform.python_implementation()})")
    print(f"Sistema     : {platform.system()} {platform.release()}")
    print(f"Procesador  : {platform.processor() or 'N/D'}")
    print(f"Núcleos CPU : {multiprocessing.cpu_count()}")
    print(f"Repeticiones: {REPETICIONES} por configuración | intervalo=0.0\n")

    resultados = []  # (n, ciclos, version, t_prom, med, med_por_seg)

    for n, ciclos in TAMANOS:
        esperado = n * 6 * ciclos
        print("#" * 70)
        print(f"# CONFIGURACIÓN: {n} estaciones / {ciclos} ciclos  (esperadas {esperado} mediciones)")
        print("#" * 70)

        for nombre, fn in (("Secuencial", medir_secuencial),
                           ("Hilos", medir_hilos),
                           ("Procesos", medir_procesos)):
            tiempos, med_count = [], esperado
            for r in range(REPETICIONES):
                with contextlib.redirect_stdout(io.StringIO()):
                    t, med = fn(n, ciclos)
                tiempos.append(t)
                med_count = med
                ok = "OK" if med == esperado else f"!! {med}/{esperado}"
                print(f"  [{nombre:<10}] run {r+1}: {t:7.4f}s | mediciones={med} [{ok}]")
            t_prom = statistics.mean(tiempos)
            mps = med_count / t_prom if t_prom else 0
            resultados.append((n, ciclos, nombre, t_prom, med_count, mps))
            print(f"  -> {nombre} promedio: {t_prom:.4f}s | {mps:.1f} med/s\n")

    # Tabla resumen + speedup
    print("=" * 70)
    print("RESUMEN COMPARATIVO (tiempos promedio y speedup)")
    print("=" * 70)
    print(f"{'Config':<14}{'Versión':<12}{'T prom (s)':<12}{'Med/s':<10}{'Speedup':<10}")
    print("-" * 70)
    base = {}
    for n, ciclos, ver, t, med, mps in resultados:
        if ver == "Secuencial":
            base[(n, ciclos)] = t
    for n, ciclos, ver, t, med, mps in resultados:
        sp = base[(n, ciclos)] / t if t else 0
        cfg = f"{n}est/{ciclos}cic"
        sp_str = "1.00x (base)" if ver == "Secuencial" else f"{sp:.2f}x"
        print(f"{cfg:<14}{ver:<12}{t:<12.4f}{mps:<10.1f}{sp_str:<10}")
    print("=" * 70)


if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()
