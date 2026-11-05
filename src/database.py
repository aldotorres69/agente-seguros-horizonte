"""
Capa de abstracción de datos para Seguros Horizonte S.A.
Permite ejecutar consultas SQL seguras en DuckDB (local) o intercambiarse por BigQuery en producción.
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import re
from pathlib import Path
import duckdb
from src.config import DATOS_DIR

class DatabaseProvider(ABC):
    """Interfaz base para proveedores de datos (DuckDB, BigQuery, Azure SQL)."""

    @abstractmethod
    def execute_query(self, sql: str, user_role: str, user_id: str) -> List[Dict[str, Any]]:
        """Ejecuta una consulta SQL respetando las reglas de rol y privacidad."""
        pass

class DuckDBProvider(DatabaseProvider):
    """
    Implementación de base de datos basada en DuckDB en memoria.
    Carga los archivos CSV de clientes, pólizas, siniestros y asesores.
    """

    FORBIDDEN_KEYWORDS = [
        "INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "TRUNCATE",
        "CREATE", "REPLACE", "GRANT", "REVOKE", "EXEC", "EXECUTE"
    ]

    def __init__(self, data_dir: Path = DATOS_DIR):
        self.data_dir = data_dir
        self.conn = duckdb.connect(":memory:")
        self._load_tables()

    def _load_tables(self):
        """Carga los CSVs en tablas DuckDB en memoria."""
        tables = {
            "clientes": self.data_dir / "clientes.csv",
            "polizas": self.data_dir / "polizas.csv",
            "siniestros": self.data_dir / "siniestros.csv",
            "asesores": self.data_dir / "asesores.csv"
        }
        for table_name, file_path in tables.items():
            if file_path.exists():
                escaped_path = str(file_path).replace("\\", "/")
                self.conn.execute(
                    f"CREATE TABLE {table_name} AS SELECT * FROM read_csv_auto('{escaped_path}')"
                )

    def _validate_safety(self, sql: str):
        """Verifica que la consulta sea estrictamente de solo lectura."""
        cleaned_sql = re.sub(r"--.*", "", sql) # Quitar comentarios simples
        cleaned_sql = re.sub(r"/\*.*?\*/", "", cleaned_sql, flags=re.DOTALL) # Quitar comentarios bloque
        tokens = re.findall(r"\b[A-Za-z_]+\b", cleaned_sql.upper())
        for token in tokens:
            if token in self.FORBIDDEN_KEYWORDS:
                raise PermissionError(
                    f"Operación no permitida: la consulta contiene la palabra clave restringida '{token}'. "
                    "El agente opera estrictamente en modo de solo lectura."
                )

    def _enforce_row_level_security(self, sql: str, user_role: str, user_id: str) -> str:
        """
        Garantiza que un cliente solo pueda consultar sus propios datos.
        Los asesores pueden realizar consultas agregadas o sobre cualquier cliente.
        """
        if user_role == "asesor":
            return sql

        # Regla para rol cliente:
        # Si la consulta accede a clientes, pólizas o siniestros sin filtrar por su ID,
        # se verifica que no consulte datos de otros clientes.
        # Detectar si se está intentando consultar explícitamente a otro cliente_id diferente al autenticado
        other_client_matches = re.findall(r"cliente_id\s*=\s*['\"](C\d+)['\"]", sql, re.IGNORECASE)
        for client_found in other_client_matches:
            if client_found.upper() != user_id.upper():
                raise PermissionError(
                    f"Violación de privacidad: el usuario {user_id} intentó consultar información del cliente {client_found}."
                )

        return sql

    def execute_query(self, sql: str, user_role: str, user_id: str) -> List[Dict[str, Any]]:
        """
        Ejecuta la consulta SQL con validaciones de seguridad y privacidad.
        """
        self._validate_safety(sql)
        safe_sql = self._enforce_row_level_security(sql, user_role, user_id)

        try:
            cursor = self.conn.execute(safe_sql)
            columns = [desc[0] for desc in cursor.description] if cursor.description else []
            rows = cursor.fetchall()
            results = []
            for row in rows:
                item = {}
                for col, val in zip(columns, row):
                    # Convertir fechas a string para serialización JSON
                    if hasattr(val, "isoformat"):
                        item[col] = val.isoformat()
                    else:
                        item[col] = val
                results.append(item)
            return results
        except Exception as e:
            if isinstance(e, PermissionError):
                raise
            return [{"error": f"Error al ejecutar SQL: {str(e)}"}]

    # Métodos directos seguros de ayuda para el agente:
    def get_client_info(self, client_id: str) -> Optional[Dict[str, Any]]:
        rows = self.execute_query(f"SELECT * FROM clientes WHERE cliente_id = '{client_id}'", "cliente", client_id)
        return rows[0] if rows and "error" not in rows[0] else None

    def get_client_policies(self, client_id: str) -> List[Dict[str, Any]]:
        return self.execute_query(f"SELECT * FROM polizas WHERE cliente_id = '{client_id}'", "cliente", client_id)

    def get_client_claims(self, client_id: str) -> List[Dict[str, Any]]:
        sql = f"""
        SELECT s.*, p.ramo, p.producto, p.estado as estado_poliza
        FROM siniestros s
        JOIN polizas p ON s.poliza_id = p.poliza_id
        WHERE p.cliente_id = '{client_id}'
        ORDER BY s.fecha_ocurrencia DESC
        """
        return self.execute_query(sql, "cliente", client_id)

    def get_claim_details(self, siniestro_id: str, user_role: str, user_id: str) -> Optional[Dict[str, Any]]:
        sql = f"""
        SELECT s.*, p.cliente_id, p.ramo, p.producto, p.deducible_soles, p.suma_asegurada_soles, p.estado as estado_poliza
        FROM siniestros s
        JOIN polizas p ON s.poliza_id = p.poliza_id
        WHERE s.siniestro_id = '{siniestro_id}'
        """
        rows = self.execute_query(sql, user_role, user_id)
        if not rows or "error" in rows[0]:
            return None
        claim = rows[0]
        # Validar pertenencia si es cliente
        if user_role == "cliente" and claim.get("cliente_id") != user_id:
            raise PermissionError(f"El siniestro {siniestro_id} no pertenece al cliente autenticado {user_id}.")
        return claim
