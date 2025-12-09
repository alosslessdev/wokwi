"""
Configuración del sistema Smart Home IoT
Compatible con MicroPython en ESP32
"""

# ============================================================================
# CONFIGURACIÓN MQTT
# ============================================================================

# Broker MQTT público (puedes cambiarlo por tu propio broker)
MQTT_BROKER = "6231ad2c19cf4a8ebf1c527f4136a536.s1.eu.hivemq.cloud"  # Broker público gratuito
MQTT_PORT = 8883

# Client ID único (se genera automáticamente si usas el código de abajo)
# O puedes poner uno fijo como: MQTT_CLIENT_ID = "esp32_smarthome_001"
try:
    import ubinascii
    import machine
    # Genera un ID único basado en el MAC del ESP32
    _uid = ubinascii.hexlify(machine.unique_id()).decode('utf-8')[-8:]
    MQTT_CLIENT_ID = "esp32_{}".format(_uid)
except:
    # Fallback si falla la generación
    MQTT_CLIENT_ID = "esp32_default"

# Credenciales MQTT (dejar None si el broker no requiere autenticación)
MQTT_USERNAME = "asdfa"  # O tu usuario: "tu_usuario"
MQTT_PASSWORD = "Asdfasdf1" # O tu contraseña: "tu_password"
MQTT_USE_TLS = True

# Topics MQTT
MQTT_TOPIC_SENSORS = "smarthome/sensors"
MQTT_TOPIC_COMMANDS = "smarthome/commands"

print("🔑 MQTT Client ID: {}".format(MQTT_CLIENT_ID))

# ============================================================================
# CONFIGURACIÓN THINGSPEAK
# ============================================================================

THINGSPEAK_URL = "https://api.thingspeak.com/update"
THINGSPEAK_API_KEY = "YOUR_WRITE_API_KEY"  # Reemplaza con tu API Key real

# Para obtener tu API Key:
# 1. Crea una cuenta en https://thingspeak.com
# 2. Crea un nuevo Channel
# 3. Ve a API Keys y copia el "Write API Key"

# ============================================================================
# UMBRALES Y REGLAS DE NEGOCIO
# ============================================================================

THRESHOLDS = {
    # Temperatura
    "temperature_high": 28.0,      # °C - Activa ventilador
    "temperature_critical": 35.0,  # °C - Alerta crítica
    "temperature_low": 20.0,       # °C - Alerta de frío
    
    # Humedad
    "humidity_high": 70.0,         # % - Alerta de humedad alta
    "humidity_low": 30.0,          # % - Alerta de humedad baja
    
    # Luz
    "light_threshold": 300,        # lux - Enciende luz automática
}

# ============================================================================
# CONFIGURACIÓN DE BASE DE DATOS
# ============================================================================

DATABASE_FILE = "smarthome.db"

# ============================================================================
# CONFIGURACIÓN DE SENSORES (para ESP32)
# ============================================================================

# Pines GPIO del ESP32
PINS = {
    "DHT_SENSOR": 15,      # Pin para DHT22 (temperatura y humedad)
    "LDR_SENSOR": 34,      # Pin ADC para LDR (luz)
    "FAN_RELAY": 26,       # Pin para relé del ventilador
    "LIGHT_RELAY": 27,     # Pin para relé de la luz
    "LED_STATUS": 2,       # LED integrado del ESP32
}

# Tipo de sensor DHT (11 o 22)
DHT_TYPE = 22  # DHT22 (más preciso) o DHT11

# ============================================================================
# INTERVALOS DE TIEMPO (en segundos)
# ============================================================================

SENSOR_READ_INTERVAL = 5       # Leer sensores cada 5 segundos
MQTT_PUBLISH_INTERVAL = 10     # Publicar a MQTT cada 10 segundos
DATABASE_SAVE_INTERVAL = 30    # Guardar en BD cada 30 segundos
THINGSPEAK_INTERVAL = 20       # Enviar a ThingSpeak cada 20 segundos (mín 15s)

# ============================================================================
# CONFIGURACIÓN WIFI
# ============================================================================

# Para simuladores como Wokwi
WIFI_SSID = "Wokwi-GUEST"
WIFI_PASSWORD = ""

# Para ESP32 real, cambia estos valores:
# WIFI_SSID = "TuRedWiFi"
# WIFI_PASSWORD = "TuPasswordWiFi"

# ============================================================================
# CONFIGURACIÓN DE DEBUG
# ============================================================================

DEBUG = True  # Mostrar mensajes detallados
VERBOSE = False  # Mostrar mensajes muy detallados (solo para debugging)

# ============================================================================
# FUNCIONES AUXILIARES
# ============================================================================

def print_config():
    """Imprime la configuración actual"""
    print("\n" + "="*60)
    print("⚙️  CONFIGURACIÓN DEL SISTEMA")
    print("="*60)
    print("\n📡 MQTT:")
    print("   Broker: {}:{}".format(MQTT_BROKER, MQTT_PORT))
    print("   Client ID: {}".format(MQTT_CLIENT_ID))
    print("   Auth: {}".format("Sí" if MQTT_USERNAME else "No"))
    
    print("\n☁️  ThingSpeak:")
    print("   Configurado: {}".format("Sí" if THINGSPEAK_API_KEY != "YOUR_WRITE_API_KEY" else "No"))
    
    print("\n🌡️  Umbrales:")
    print("   Temp alta: {}°C".format(THRESHOLDS["temperature_high"]))
    print("   Temp crítica: {}°C".format(THRESHOLDS["temperature_critical"]))
    print("   Luz baja: {} lux".format(THRESHOLDS["light_threshold"]))
    
    print("\n⏱️  Intervalos:")
    print("   Lectura sensores: {}s".format(SENSOR_READ_INTERVAL))
    print("   Publicar MQTT: {}s".format(MQTT_PUBLISH_INTERVAL))
    print("   Guardar BD: {}s".format(DATABASE_SAVE_INTERVAL))
    print("   ThingSpeak: {}s".format(THINGSPEAK_INTERVAL))
    
    print("\n" + "="*60 + "\n")

# ============================================================================
# VALIDACIÓN DE CONFIGURACIÓN
# ============================================================================

def validate_config():
    """Valida que la configuración sea correcta"""
    errors = []
    warnings = []
    
    # Validar MQTT
    if not MQTT_BROKER:
        errors.append("MQTT_BROKER no está definido")
    if not MQTT_PORT or MQTT_PORT <= 0:
        errors.append("MQTT_PORT inválido")
    if not MQTT_CLIENT_ID:
        errors.append("MQTT_CLIENT_ID no está definido")
    
    # Validar ThingSpeak
    if THINGSPEAK_API_KEY == "YOUR_WRITE_API_KEY":
        warnings.append("ThingSpeak no configurado (usa la API Key por defecto)")
    
    if THINGSPEAK_INTERVAL < 15:
        errors.append("THINGSPEAK_INTERVAL debe ser >= 15 segundos")
    
    # Validar umbrales
    if THRESHOLDS["temperature_high"] >= THRESHOLDS["temperature_critical"]:
        errors.append("temperature_critical debe ser mayor que temperature_high")
    
    # Mostrar resultados
    if errors:
        print("\n❌ ERRORES EN CONFIGURACIÓN:")
        for error in errors:
            print("   - {}".format(error))
    
    if warnings:
        print("\n⚠️  ADVERTENCIAS:")
        for warning in warnings:
            print("   - {}".format(warning))
    
    if not errors and not warnings:
        print("\n✅ Configuración válida")
    
    return len(errors) == 0

# ============================================================================
# AUTO-EJECUCIÓN
# ============================================================================

if __name__ == "__main__":
    print_config()
    validate_config()
