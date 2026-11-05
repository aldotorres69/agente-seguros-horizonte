"""
Interfaz de Línea de Comandos (CLI) Interactiva para el Agente de Seguros Horizonte S.A.
Uso:
    python app_cli.py
"""
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT_DIR))

from src.agent import InsuranceAgent
from src.config import REFERENCE_DATE

def main():
    agent = InsuranceAgent()
    print("=" * 70)
    print("  SEGUROS HORIZONTE S.A. - ASISTENTE VIRTUAL (MODO TERMINAL)")
    print(f"  Fecha de referencia del sistema: {REFERENCE_DATE}")
    print("=" * 70)

    print("\nSelecciona tu perfil de sesión inicial:")
    print("1. Cliente C001 (María Elena Torres)")
    print("2. Cliente C002 (Jorge Luis Ramos)")
    print("3. Asesor ASE01 (Carlos Benavides)")
    print("4. Ingresar otro ID manualmente")

    opc = input("Opción [1-4] (default 1): ").strip()
    if opc == "2":
        rol, uid = "cliente", "C002"
    elif opc == "3":
        rol, uid = "asesor", "ASE01"
    elif opc == "4":
        rol = input("Rol (cliente/asesor): ").strip().lower() or "cliente"
        uid = input("Usuario ID (ej: C003): ").strip() or "C001"
    else:
        rol, uid = "cliente", "C001"

    print(f"\n[+] Sesión autenticada iniciada como: {rol.upper()} ({uid})")
    print("[+] Escribe tu consulta o 'salir' para terminar. Escribe 'cambiar' para cambiar de usuario.\n")

    while True:
        try:
            msg = input(f"[{uid}] > ").strip()
            if not msg:
                continue
            if msg.lower() in ["salir", "exit", "quit"]:
                print("Cerrando sesión. ¡Hasta luego!")
                break
            if msg.lower() == "cambiar":
                rol = input("Nuevo rol (cliente/asesor): ").strip().lower() or "cliente"
                uid = input("Nuevo usuario ID: ").strip() or "C001"
                print(f"[+] Cambiado a: {rol.upper()} ({uid})")
                continue

            res = agent.process_query(mensaje=msg, rol=rol, usuario_id=uid)
            print("\n" + "-" * 60)
            print("RESPUESTA:")
            print(res["respuesta"])
            print("-" * 60)
            print(f"Herramientas: {res['herramientas_usadas']} | Tiempo: {res['duracion_ms']:.1f} ms")
            print("=" * 60 + "\n")

        except (KeyboardInterrupt, EOFError):
            print("\nSesión finalizada.")
            break

if __name__ == "__main__":
    main()
