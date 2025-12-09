"""
Archivo de configuración para el sistema Smart Home IoT
Contiene todas las credenciales y parámetros del sistema
"""

# ===== CONFIGURACIÓN MQTT (HiveMQ Cloud) =====
MQTT_BROKER = "a696d90a2b6f41fe9008b1f1dcda2db5.s1.eu.hivemq.cloud"

# 🔥 CAMBIO 1: Puerto WebSockets con TLS
MQTT_PORT = 8884  

MQTT_USERNAME = "ivanwu"
MQTT_PASSWORD = "HiveCloud507"

# 🔥 CAMBIO 2: Activar TLS + WebSockets
MQTT_USE_TLS = True
MQTT_USE_WEBSOCKETS = True     # <<< NUEVO

# Topics MQTT
MQTT_TOPICS = {
    "temperature": "smarthome/sensors/temperature",
    "humidity": "smarthome/sensors/humidity",
    "light": "smarthome/sensors/light",
    "fan_status": "smarthome/actuators/fan",
    "light_status": "smarthome/actuators/light",
    "fan_command": "smarthome/actuators/fan/command",
    "light_command": "smarthome/actuators/light/command",
    "alerts": "smarthome/alerts",
    "system_status": "smarthome/system/status"
}

# ===== CONFIGURACIÓN THINGSPEAK =====
THINGSPEAK_API_KEY = "9CXKR5T6UUQPPB7T"
THINGSPEAK_CHANNEL_ID = "3193124"
THINGSPEAK_URL = "https://api.thingspeak.com/update"
THINGSPEAK_READ_KEY = "W0MWXRXAIITR5EK5"

# ===== CONFIGURACIÓN BASE DE DATOS =====
DATABASE_PATH = "database/smart_home.db"

# ===== CONFIGURACIÓN DE PINES GPIO (Raspberry Pi / ESP32) =====
GPIO_PINS = {
    "dht22_data": 4,
    "ldr_analog": 0,
    "led_red": 17,
    "led_green": 27,
    "led_blue": 22,
    "relay_fan": 23,
    "buzzer": 24,
    "oled_sda": 2,
    "oled_scl": 3
}

# ===== UMBRALES Y LÍMITES DE SENSORES =====
THRESHOLDS = {
    "temperature_high": 28.0,
    "temperature_low": 18.0,
    "humidity_high": 70.0,
    "humidity_low": 30.0,
    "light_threshold": 300,
    "temperature_critical": 35.0,
    "humidity_critical": 80.0
}

# ===== INTERVALOS DE TIEMPO (segundos) =====
TIMING = {
    "sensor_read_interval": 5,
    "mqtt_publish_interval": 10,
    "thingspeak_interval": 20,
    "database_save_interval": 30,
    "display_update_interval": 2
}

# ===== CONFIGURACIÓN DEL SISTEMA =====
SYSTEM_CONFIG = {
    "auto_mode": True,
    "alert_enabled": True,
    "debug_mode": False,
    "simulation_mode": True,
    "timezone": "America/Panama"
}

# ===== CONFIGURACIÓN DE ALERTAS =====
ALERTS = {
    "email_enabled": False,
    "buzzer_enabled": True,
    "mqtt_alerts": True
}

# ===== MENSAJES DEL SISTEMA =====
MESSAGES = {
    "system_start": "Sistema Smart Home iniciado",
    "system_stop": "Sistema Smart Home detenido",
    "temp_high": "⚠️ Temperatura alta detectada",
    "temp_critical": "🔥 ALERTA: Temperatura crítica",
    "humidity_high": "💧 Humedad alta detectada",
    "fan_auto_on": "Ventilador activado automáticamente",
    "fan_auto_off": "Ventilador desactivado automáticamente",
    "light_auto_on": "Luz activada automáticamente",
    "light_auto_off": "Luz desactivada automáticamente"
}

# ===== VALIDACIÓN DE CONFIGURACIÓN =====
def validate_config():
    """Valida que la configuración esté completa"""
    errors = []
    
    if MQTT_BROKER == "your-cluster.hivemq.cloud":
        errors.append("⚠️ Configurar MQTT_BROKER en config.py")
    
    if THINGSPEAK_API_KEY == "YOUR_WRITE_API_KEY":
        errors.append("⚠️ Configurar THINGSPEAK_API_KEY en config.py")
    
    if errors:
        print("\n" + "="*50)
        print("ERRORES DE CONFIGURACIÓN:")
        for error in errors:
            print(f"  {error}")
        print("="*50 + "\n")
        return False
    
    return True

if __name__ == "__main__":
    if validate_config():
        print("✅ Configuración válida")
    else:
        print("❌ Revisar configuración")
