"""
Script de ejecución automatizada de los 12 casos de prueba para Seguros Horizonte S.A.
Uso:
    python run_casos.py
"""
import sys
import os
import json
import time
from pathlib import Path

# Agregar directorio raíz al PYTHONPATH
sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.agent import InsuranceAgent
from src.config import CASOS_DIR, ROOT_DIR, LOGS_DIR

def run_all_cases():
    casos_file = CASOS_DIR / "casos_prueba.json"
    if not casos_file.exists():
        print(f"Error: No se encontró el archivo de casos en {casos_file}")
        return

    with open(casos_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    casos = data.get("casos", [])
    print("=" * 80)
    print("EJECUTANDO SUITE DE 12 CASOS DE PRUEBA - AGENTE DE SEGUROS HORIZONTE S.A.")
    print(f"Fecha de referencia: {data.get('fecha_referencia', '2026-10-15')}")
    print(f"Total casos a evaluar: {len(casos)}")
    print("=" * 80)

    agent = InsuranceAgent()
    resultados = []
    start_total = time.time()

    for idx, c in enumerate(casos, start=1):
        cid = c["id"]
        rol = c["rol"]
        uid = c["usuario_id"]
        msg = c["mensaje"]

        print(f"\n[{idx}/{len(casos)}] Procesando {cid} | Rol: {rol} | Usuario: {uid}")
        print(f"Consulta: \"{msg}\"")

        res = agent.process_query(mensaje=msg, rol=rol, usuario_id=uid, caso_id=cid)
        resultados.append(res)

        print(f"Herramientas usadas: {res['herramientas_usadas']}")
        print(f"Fuentes citadas: {res['fuentes_citadas']}")
        print(f"Tiempo: {res['duracion_ms']:.1f} ms")
        print("-" * 40)
        print("Respuesta del Agente:")
        print(res["respuesta"][:250] + ("..." if len(res["respuesta"]) > 250 else ""))

    total_time = time.time() - start_total
    print("\n" + "=" * 80)
    print(f"EJECUCIÓN COMPLETADA EN {total_time:.2f} SEGUNDOS")
    print("=" * 80)

    # 1. Guardar salida JSON estructurada
    out_json = ROOT_DIR / "salida_casos_prueba.json"
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump({
            "fecha_ejecucion": time.strftime("%Y-%m-%d %H:%M:%S"),
            "fecha_referencia": "2026-10-15",
            "total_casos": len(resultados),
            "duracion_total_segundos": round(total_time, 2),
            "casos": resultados
        }, f, ensure_ascii=False, indent=2)
    print(f"\nArchivo JSON de salida guardado en: {out_json}")

    # 2. Guardar reporte Markdown detallado
    out_md = ROOT_DIR / "salida_casos_prueba.md"
    with open(out_md, "w", encoding="utf-8") as f:
        f.write("# Salida de Ejecución de Casos de Prueba - Seguros Horizonte S.A.\n\n")
        f.write(f"- **Fecha de referencia de negocio:** 15 de octubre de 2026\n")
        f.write(f"- **Total de casos ejecutados:** {len(resultados)}\n")
        f.write(f"- **Tiempo total:** {total_time:.2f} segundos\n\n")
        f.write("## Resumen de Ejecución\n\n")
        f.write("| Caso | Rol | Usuario | Herramientas Usadas | Tiempo (ms) |\n")
        f.write("| :---: | :---: | :---: | :--- | :---: |\n")
        for r in resultados:
            tools_str = ", ".join(r["herramientas_usadas"]) if r["herramientas_usadas"] else "Ninguna"
            f.write(f"| {r['caso_id']} | {r['rol']} | {r['usuario_id']} | {tools_str} | {r['duracion_ms']:.1f} |\n")

        f.write("\n## Detalle por Caso\n\n")
        for r in resultados:
            f.write(f"### {r['caso_id']} ({r['rol']} - {r['usuario_id']})\n\n")
            f.write(f"**Consulta:** {r['mensaje']}\n\n")
            f.write(f"**Herramientas usadas:** {', '.join(r['herramientas_usadas'])}\n\n")
            f.write(f"**Fuentes citadas:** {', '.join(r['fuentes_citadas'])}\n\n")
            f.write("**Respuesta del agente:**\n\n")
            f.write(f"```text\n{r['respuesta']}\n```\n\n")
            f.write("---\n\n")

    print(f"Reporte Markdown de salida guardado en: {out_md}")

    # 3. Guardar muestra del log de interacciones (requerido por el entregable #5)
    recent_logs = agent.logger.get_recent_logs(limit=12)
    sample_log = ROOT_DIR / "muestra_log_interacciones.json"
    with open(sample_log, "w", encoding="utf-8") as f:
        json.dump(recent_logs, f, ensure_ascii=False, indent=2)
    print(f"Muestra de log de auditoría guardada en: {sample_log}")

if __name__ == "__main__":
    run_all_cases()
