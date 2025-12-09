"""
Módulo de gestión de base de datos SQLite
Almacena lecturas de sensores y eventos de actuadores
"""

import sqlite3
import os
from datetime import datetime, timedelta
import config


class DatabaseManager:
    """Gestor de base de datos SQLite"""
    
    def __init__(self, db_path=None):
        self.db_path = db_path or config.DATABASE_PATH
        self.connection = None
        self.ensure_directory()
        self.connect()
        print(f"💾 Base de datos: {self.db_path}")
    
    def ensure_directory(self):
        """Asegura que exista el directorio de la base de datos"""
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir)
            print(f"📁 Directorio creado: {db_dir}")
    
    def connect(self):
        """Establece conexión con la base de datos"""
        try:
            self.connection = sqlite3.connect(self.db_path)
            self.connection.row_factory = sqlite3.Row  # Acceso por nombre de columna
            print("✅ Conexión a BD establecida")
        except sqlite3.Error as e:
            print(f"❌ Error conectando a BD: {e}")
            raise
    
    def initialize(self):
        """Crea las tablas si no existen"""
        cursor = self.connection.cursor()
        
        # Tabla de lecturas de sensores
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sensor_readings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                temperature REAL,
                humidity REAL,
                light_level REAL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Tabla de eventos de actuadores
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS actuator_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                actuator_type TEXT NOT NULL,
                action TEXT NOT NULL,
                value TEXT,
                auto_triggered BOOLEAN DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Tabla de alertas
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                alert_type TEXT NOT NULL,
                message TEXT,
                value REAL,
                acknowledged BOOLEAN DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Índices para mejorar consultas
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_sensor_timestamp 
            ON sensor_readings(timestamp)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_actuator_timestamp 
            ON actuator_events(timestamp)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_alerts_timestamp 
            ON alerts(timestamp)
        """)
        
        self.connection.commit()
        print("✅ Tablas inicializadas")
    
    def save_sensor_reading(self, temperature, humidity, light_level):
        """Guarda una lectura de sensores"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                INSERT INTO sensor_readings (temperature, humidity, light_level)
                VALUES (?, ?, ?)
            """, (temperature, humidity, light_level))
            self.connection.commit()
            return cursor.lastrowid
        except sqlite3.Error as e:
            print(f"❌ Error guardando lectura: {e}")
            return None
    
    def save_actuator_event(self, actuator_type, action, value=None, auto_triggered=False):
        """Guarda un evento de actuador"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                INSERT INTO actuator_events (actuator_type, action, value, auto_triggered)
                VALUES (?, ?, ?, ?)
            """, (actuator_type, action, value, auto_triggered))
            self.connection.commit()
            return cursor.lastrowid
        except sqlite3.Error as e:
            print(f"❌ Error guardando evento: {e}")
            return None
    
    def save_alert(self, alert_type, message, value=None):
        """Guarda una alerta"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                INSERT INTO alerts (alert_type, message, value)
                VALUES (?, ?, ?)
            """, (alert_type, message, value))
            self.connection.commit()
            return cursor.lastrowid
        except sqlite3.Error as e:
            print(f"❌ Error guardando alerta: {e}")
            return None
    
    def get_last_readings(self, limit=10):
        """Obtiene las últimas N lecturas"""
        cursor = self.connection.cursor()
        cursor.execute("""
            SELECT * FROM sensor_readings
            ORDER BY timestamp DESC
            LIMIT ?
        """, (limit,))
        return cursor.fetchall()
    
    def get_last_24h_readings(self):
        """Obtiene lecturas de las últimas 24 horas"""
        cursor = self.connection.cursor()
        yesterday = datetime.now() - timedelta(hours=24)
        cursor.execute("""
            SELECT * FROM sensor_readings
            WHERE timestamp >= ?
            ORDER BY timestamp DESC
        """, (yesterday.isoformat(),))
        return cursor.fetchall()
    
    def get_hourly_averages(self, hours=24):
        """Calcula promedios por hora"""
        cursor = self.connection.cursor()
        start_time = datetime.now() - timedelta(hours=hours)
        cursor.execute("""
            SELECT 
                strftime('%Y-%m-%d %H:00:00', timestamp) as hour,
                AVG(temperature) as avg_temp,
                AVG(humidity) as avg_humidity,
                AVG(light_level) as avg_light,
                COUNT(*) as count
            FROM sensor_readings
            WHERE timestamp >= ?
            GROUP BY hour
            ORDER BY hour DESC
        """, (start_time.isoformat(),))
        return cursor.fetchall()
    
    def get_actuator_history(self, limit=50):
        """Obtiene historial de actuadores"""
        cursor = self.connection.cursor()
        cursor.execute("""
            SELECT * FROM actuator_events
            ORDER BY timestamp DESC
            LIMIT ?
        """, (limit,))
        return cursor.fetchall()
    
    def get_alerts(self, acknowledged=False, limit=20):
        """Obtiene alertas"""
        cursor = self.connection.cursor()
        cursor.execute("""
            SELECT * FROM alerts
            WHERE acknowledged = ?
            ORDER BY timestamp DESC
            LIMIT ?
        """, (acknowledged, limit))
        return cursor.fetchall()
    
    def acknowledge_alert(self, alert_id):
        """Marca una alerta como reconocida"""
        cursor = self.connection.cursor()
        cursor.execute("""
            UPDATE alerts
            SET acknowledged = 1
            WHERE id = ?
        """, (alert_id,))
        self.connection.commit()
    
    def get_statistics(self):
        """Obtiene estadísticas generales"""
        cursor = self.connection.cursor()
        
        # Últimas 24 horas
        cursor.execute("""
            SELECT 
                COUNT(*) as total_readings,
                AVG(temperature) as avg_temp,
                MIN(temperature) as min_temp,
                MAX(temperature) as max_temp,
                AVG(humidity) as avg_humidity,
                MIN(humidity) as min_humidity,
                MAX(humidity) as max_humidity,
                AVG(light_level) as avg_light
            FROM sensor_readings
            WHERE timestamp >= datetime('now', '-24 hours')
        """)
        
        stats = cursor.fetchone()
        
        return {
            "total_readings": stats["total_readings"],
            "temperature": {
                "avg": round(stats["avg_temp"], 1) if stats["avg_temp"] else None,
                "min": round(stats["min_temp"], 1) if stats["min_temp"] else None,
                "max": round(stats["max_temp"], 1) if stats["max_temp"] else None
            },
            "humidity": {
                "avg": round(stats["avg_humidity"], 1) if stats["avg_humidity"] else None,
                "min": round(stats["min_humidity"], 1) if stats["min_humidity"] else None,
                "max": round(stats["max_humidity"], 1) if stats["max_humidity"] else None
            },
            "light": {
                "avg": round(stats["avg_light"], 1) if stats["avg_light"] else None
            }
        }
    
    def cleanup_old_data(self, days=30):
        """Elimina datos antiguos (mantiene solo últimos N días)"""
        cursor = self.connection.cursor()
        cutoff_date = datetime.now() - timedelta(days=days)
        
        cursor.execute("""
            DELETE FROM sensor_readings
            WHERE timestamp < ?
        """, (cutoff_date.isoformat(),))
        
        cursor.execute("""
            DELETE FROM actuator_events
            WHERE timestamp < ?
        """, (cutoff_date.isoformat(),))
        
        deleted_readings = cursor.rowcount
        self.connection.commit()
        
        print(f"🧹 Limpieza: {deleted_readings} registros antiguos eliminados")
        return deleted_readings
    
    def export_to_csv(self, output_file="export.csv", days=7):
        """Exporta datos a CSV"""
        import csv
        
        cursor = self.connection.cursor()
        start_date = datetime.now() - timedelta(days=days)
        
        cursor.execute("""
            SELECT timestamp, temperature, humidity, light_level
            FROM sensor_readings
            WHERE timestamp >= ?
            ORDER BY timestamp
        """, (start_date.isoformat(),))
        
        rows = cursor.fetchall()
        
        with open(output_file, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['Timestamp', 'Temperature', 'Humidity', 'Light Level'])
            for row in rows:
                writer.writerow([row['timestamp'], row['temperature'], 
                               row['humidity'], row['light_level']])
        
        print(f"📊 Datos exportados a {output_file}")
        return output_file
    
    def close(self):
        """Cierra la conexión"""
        if self.connection:
            self.connection.close()
            print("🔌 Conexión a BD cerrada")


# Función de prueba
def test_database():
    """Prueba las funciones de la base de datos"""
    print("\n🧪 PROBANDO BASE DE DATOS\n")
    
    db = DatabaseManager("test_smart_home.db")
    db.initialize()
    
    # Insertar datos de prueba
    print("Insertando lecturas de prueba...")
    for i in range(5):
        db.save_sensor_reading(
            temperature=20 + i,
            humidity=50 + i,
            light_level=300 + i*10
        )
    
    # Insertar eventos de actuadores
    db.save_actuator_event("fan", "on", auto_triggered=True)
    db.save_actuator_event("light", "on", auto_triggered=False)
    
    # Insertar alerta
    db.save_alert("temperature_high", "Temperatura alta detectada", 30.5)
    
    # Consultar datos
    print("\n📊 Últimas 5 lecturas:")
    readings = db.get_last_readings(5)
    for reading in readings:
        print(f"  {reading['timestamp']}: {reading['temperature']}°C, "
              f"{reading['humidity']}%, {reading['light_level']} lux")
    
    # Estadísticas
    print("\n📈 Estadísticas:")
    stats = db.get_statistics()
    print(f"  Total lecturas: {stats['total_readings']}")
    print(f"  Temp promedio: {stats['temperature']['avg']}°C")
    print(f"  Humedad promedio: {stats['humidity']['avg']}%")
    
    db.close()
    print("\n✅ Prueba completada")


if __name__ == "__main__":
    test_database()