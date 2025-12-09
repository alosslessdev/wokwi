"""
Cliente de base de datos para MicroPython
Este archivo va en tu ESP32/ESP8266
Se conecta al API REST para guardar datos en MySQL
"""

import urequests as requests
import ujson as json
from time import time


# CONFIGURACIÓN - Cambia esto con la URL de tu servidor API
API_ENDPOINT = "http://137.184.120.179:5000/api"
# Cambiar a tu servidor:
# - Desarrollo local: "http://192.168.1.100:5000/api"
# - Producción: "https://tu-dominio.com/api"


class DatabaseManager:
    """Gestor de base de datos MySQL mediante API REST"""
    
    def __init__(self, api_endpoint=None):
        """
        Inicializa el gestor de base de datos
        api_endpoint: URL del API REST (ej: "http://192.168.1.100:5000/api")
        """
        self.api_endpoint = api_endpoint or API_ENDPOINT
        
        if not self.api_endpoint or self.api_endpoint == "http://192.168.1.100:5000/api":
            print("⚠️  ADVERTENCIA: Debes configurar API_ENDPOINT con tu servidor")
            print("    Edita la variable API_ENDPOINT en este archivo")
        
        print("💾 Base de datos API: {}".format(self.api_endpoint))


    
    def _make_request(self, endpoint, method='GET', data=None, params=None):
        """Hace una petición HTTP al API"""
        if not self.api_endpoint:
            print("❌ Error: API endpoint no configurado")
            return None
        
        url = "{}/{}".format(self.api_endpoint, endpoint)
        
        # Agregar parámetros de query si existen
        if params:
            query_parts = []
            for key, value in params.items():
                query_parts.append("{}={}".format(key, value))
            if query_parts:
                url = "{}?{}".format(url, "&".join(query_parts))
        
        # DEBUG: Mostrar detalles de la petición
        print("🔍 [DEBUG] {} {}".format(method, url))
        if data:
            print("🔍 [DEBUG] Datos: {}".format(json.dumps(data)))
        
        headers = {'Content-Type': 'application/json'}
        response = None
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers)
            
            print("🔍 [DEBUG] Status: {}".format(response.status_code))
            
            if response.status_code >= 200 and response.status_code < 300:
                result = response.json()
                print("🔍 [DEBUG] Respuesta OK")
                return result
            else:
                print("❌ Error HTTP {}: {}".format(
                    response.status_code,
                    response.text[:100]  # Primeros 100 caracteres
                ))
                return None
                
        except Exception as e:
            print("❌ Error en petición: {}".format(e))
            return None
        finally:
            if response:
                response.close()
    
    def health_check(self):
        """Verifica la conexión con el servidor"""
        print("📡 Verificando salud del servidor...")
        result = self._make_request('health')
        if result and result.get('status') == 'healthy':
            print("✅ Servidor API conectado")
            return True
        else:
            print("❌ Servidor API no disponible")
            return False
    
    def initialize(self):
        """Crea las tablas si no existen (llamada al API)"""
        print("🔧 Inicializando tablas en base de datos...")
        result = self._make_request('initialize', method='POST')
        if result and result.get('status') == 'success':
            print("✅ Tablas inicializadas")
            return True
        return False
    
    def save_sensor_reading(self, temperature, humidity, light_level):
        """Guarda una lectura de sensores"""
        print("💾 Guardando lectura: T={:.1f}°C, H={:.1f}%, L={}".format(
            temperature, humidity, light_level))
        data = {
            'temperature': temperature,
            'humidity': humidity,
            'light_level': light_level,
            'timestamp': int(time())
        }
        result = self._make_request('sensor_readings', method='POST', data=data)
        if result and result.get('status') == 'success':
            return result.get('id')
        return None
    
    def save_actuator_event(self, actuator_type, action, value=None, auto_triggered=False):
        """Guarda un evento de actuador"""
        print("🔧 Guardando evento: {} -> {} (auto={})".format(
            actuator_type, action, auto_triggered))
        data = {
            'actuator_type': actuator_type,
            'action': action,
            'value': value,
            'auto_triggered': auto_triggered,
            'timestamp': int(time())
        }
        result = self._make_request('actuator_events', method='POST', data=data)
        if result and result.get('status') == 'success':
            return result.get('id')
        return None
    
    def save_alert(self, alert_type, message, value=None):
        """Guarda una alerta"""
        print("⚠️  Guardando alerta: {} - {}".format(alert_type, message))
        data = {
            'alert_type': alert_type,
            'message': message,
            'value': value,
            'timestamp': int(time())
        }
        result = self._make_request('alerts', method='POST', data=data)
        if result and result.get('status') == 'success':
            return result.get('id')
        return None
    
    def get_last_readings(self, limit=10):
        """Obtiene las últimas N lecturas"""
        print("📊 Consultando últimas {} lecturas...".format(limit))
        result = self._make_request('sensor_readings', params={'limit': limit})
        if result and result.get('status') == 'success':
            return result.get('data', [])
        return []
    
    def get_last_24h_readings(self):
        """Obtiene lecturas de las últimas 24 horas"""
        print("📊 Consultando lecturas de últimas 24 horas...")
        result = self._make_request('sensor_readings/24h')
        if result and result.get('status') == 'success':
            return result.get('data', [])
        return []
    
    def get_actuator_history(self, limit=50):
        """Obtiene historial de actuadores"""
        print("📜 Consultando historial de actuadores (limit={})...".format(limit))
        result = self._make_request('actuator_events', params={'limit': limit})
        if result and result.get('status') == 'success':
            return result.get('data', [])
        return []
    
    def get_alerts(self, acknowledged=False, limit=20):
        """Obtiene alertas"""
        print("🔔 Consultando alertas (acknowledged={}, limit={})...".format(
            acknowledged, limit))
        ack = 1 if acknowledged else 0
        result = self._make_request('alerts', params={'acknowledged': ack, 'limit': limit})
        if result and result.get('status') == 'success':
            return result.get('data', [])
        return []
    
    def get_statistics(self):
        """Obtiene estadísticas generales"""
        print("📈 Consultando estadísticas...")
        result = self._make_request('statistics')
        if result and result.get('status') == 'success':
            return result.get('data', {})
        return {}
    
    def cleanup_old_data(self, days=30):
        """Elimina datos antiguos (mantiene solo últimos N días)"""
        print("🧹 Limpiando datos antiguos (>{} días)...".format(days))
        result = self._make_request('cleanup', method='DELETE', params={'days': days})
        if result and result.get('status') == 'success':
            deleted = result.get('deleted', 0)
            print("🧹 Limpieza: {} registros eliminados".format(deleted))
            return deleted
        return 0
    
    def close(self):
        """Cierra la conexión (no necesario para API REST)"""
        print("🔌 Sesión cerrada")


# Función de prueba
def test_database():

    """Prueba las funciones de la base de datos"""
    print("\n🧪 PROBANDO BASE DE DATOS\n")
    
    # IMPORTANTE: Cambia esto con la URL de tu servidor
    db = DatabaseManager("http://137.184.120.179:5000/api")
    
    # Verificar conexión
    print("🔍 Verificando conexión...")
    if not db.health_check():
        print("❌ No se puede conectar al servidor API")
        print("    Asegúrate de:")
        print("    1. El servidor API está corriendo")
        print("    2. La URL es correcta")
        print("    3. El ESP32 puede acceder a la red")
        return
    
    # Inicializar tablas
    print("\n🔧 Inicializando tablas...")
    db.initialize()
    
    # Insertar datos de prueba
    print("\n📝 Insertando lecturas de prueba...")
    for i in range(3):
        reading_id = db.save_sensor_reading(
            temperature=20.0 + i,
            humidity=50.0 + i,
            light_level=300 + i*10
        )
        if reading_id:
            print("  ✅ Lectura #{} guardada".format(reading_id))
        else:
            print("  ❌ Error al guardar lectura #{}".format(i))
    
    # Eventos de actuadores
    print("\n🔧 Guardando eventos de actuadores...")
    fan_id = db.save_actuator_event("fan", "on", auto_triggered=True)
    light_id = db.save_actuator_event("light", "on", auto_triggered=False)
    if fan_id and light_id:
        print("  ✅ Eventos guardados")
    
    # Alerta
    print("\n⚠️  Guardando alerta...")
    alert_id = db.save_alert("temperature_high", "Temperatura alta detectada", 30.5)
    if alert_id:
        print("  ✅ Alerta #{} guardada".format(alert_id))
    
    # Consultar datos
    print("\n📊 Consultando últimas 5 lecturas:")
    readings = db.get_last_readings(5)
    if readings:
        for reading in readings:
            print("  ID {}: {:.1f}°C, {:.1f}%, {} lux - timestamp: {}".format(
                reading.get('id', 'N/A'),
                reading.get('temperature', 0),
                reading.get('humidity', 0),
                reading.get('light_level', 0),
                reading.get('timestamp', 0)
            ))
    else:
        print("  No hay lecturas disponibles")
    
    # Consultar lecturas de 24h
    print("\n📊 Consultando lecturas de últimas 24 horas:")
    readings_24h = db.get_last_24h_readings()
    print("  Total de lecturas en 24h: {}".format(len(readings_24h)))
    
    # Historial de actuadores
    print("\n🔧 Consultando historial de actuadores:")
    actuator_events = db.get_actuator_history(5)
    if actuator_events:
        for event in actuator_events:
            print("  {} - {} ({})".format(
                event.get('actuator_type', 'N/A'),
                event.get('action', 'N/A'),
                'auto' if event.get('auto_triggered', False) else 'manual'
            ))
    
    # Consultar alertas
    print("\n⚠️  Consultando alertas no reconocidas:")
    alerts = db.get_alerts(acknowledged=False, limit=5)
    if alerts:
        for alert in alerts:
            print("  {} - {} (valor: {})".format(
                alert.get('alert_type', 'N/A'),
                alert.get('message', 'N/A'),
                alert.get('value', 'N/A')
            ))
    else:
        print("  No hay alertas pendientes")
    
    # Estadísticas
    print("\n📈 Estadísticas generales:")
    stats = db.get_statistics()
    if stats:
        print("  Total lecturas: {}".format(stats.get('total_readings', 0)))
        temp = stats.get('temperature', {})
        if temp:
            print("  Temperatura - Min: {:.1f}°C, Max: {:.1f}°C, Avg: {:.1f}°C".format(
                temp.get('min', 0),
                temp.get('max', 0),
                temp.get('avg', 0)
            ))
        hum = stats.get('humidity', {})
        if hum:
            print("  Humedad - Min: {:.1f}%, Max: {:.1f}%, Avg: {:.1f}%".format(
                hum.get('min', 0),
                hum.get('max', 0),
                hum.get('avg', 0)
            ))
    
    db.close()
    print("\n✅ Prueba completada")


if __name__ == "__main__":
    test_database()
