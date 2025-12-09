# 🏠 Smart Home IoT - Sistema de Automatización del Hogar

## Descripción del Proyecto

Sistema IoT completo de automatización del hogar que monitorea temperatura, humedad e iluminación, controlando automáticamente ventilación e iluminación. Incluye almacenamiento en base de datos, visualización en la nube y control remoto bidireccional vía MQTT.

## 🎯 Características

### Sensores Implementados
- **DHT22**: Sensor de temperatura y humedad
- **LDR (Fotoresistor)**: Sensor de luz ambiental

### Actuadores Implementados
- **LED RGB**: Indicador de estado y luz automática
- **Relay + Ventilador**: Control de ventilación
- **Display OLED SSD1306**: Visualización local del estado
- **Buzzer**: Alertas sonoras

### Funcionalidades
- ✅ Monitoreo en tiempo real de temperatura, humedad y luz
- ✅ Control automático de ventilación (>28°C)
- ✅ Iluminación automática (nivel de luz < umbral)
- ✅ Almacenamiento de datos con timestamp en SQLite
- ✅ Integración con ThingSpeak para visualización
- ✅ Control remoto bidireccional vía MQTT (HiveMQ Cloud)
- ✅ Alertas por condiciones críticas
- ✅ Dashboard web en tiempo real

## 🏗️ Arquitectura del Sistema

```
[Sensores] → [ESP32/Raspberry Pi] → [MQTT Broker] → [ThingSpeak]
              ↓                           ↓
         [SQLite DB]              [Control Remoto]
              ↓
         [Consultas/Logs]
```

## 📦 Requisitos

### Hardware (Simulación Wokwi)
- ESP32 o Raspberry Pi Pico W
- Sensor DHT22
- Fotoresistor (LDR)
- Display OLED SSD1306 (128x64)
- LED RGB
- Relay Module
- Buzzer
- Resistencias (10kΩ, 220Ω)

### Software
```bash
pip install -r requirements.txt
```

## 🚀 Instalación

1. **Clonar el repositorio**
```bash
git clone https://github.com/tu-usuario/smart-home-iot.git
cd smart-home-iot
```

2. **Instalar dependencias**
```bash
pip install -r requirements.txt
```

3. **Configurar credenciales**
Editar `config.py` con tus credenciales:
- MQTT broker (HiveMQ)
- ThingSpeak API Key
- Umbrales de sensores

4. **Inicializar base de datos**
```bash
python -c "from src.database import DatabaseManager; db = DatabaseManager(); db.initialize()"
```

5. **Ejecutar el sistema**
```bash
python main.py
```

## 📊 Configuración de ThingSpeak

1. Crear cuenta en [ThingSpeak](https://thingspeak.com)
2. Crear un nuevo canal con 4 campos:
   - Field 1: Temperatura (°C)
   - Field 2: Humedad (%)
   - Field 3: Luz (lux)
   - Field 4: Estado Ventilador (0/1)
3. Copiar el Write API Key a `config.py`

## 🌐 Configuración MQTT (HiveMQ Cloud)

1. Crear cuenta gratuita en [HiveMQ Cloud](https://www.hivemq.com/mqtt-cloud-broker/)
2. Crear cluster gratuito
3. Configurar credenciales en `config.py`

### Topics MQTT:
- `smarthome/sensors/temperature` - Temperatura
- `smarthome/sensors/humidity` - Humedad
- `smarthome/sensors/light` - Nivel de luz
- `smarthome/actuators/fan` - Control ventilador (publish/subscribe)
- `smarthome/actuators/light` - Control luz (publish/subscribe)
- `smarthome/alerts` - Alertas del sistema

## 🗄️ Base de Datos

### Estructura SQLite

**Tabla: sensor_readings**
- id (INTEGER PRIMARY KEY)
- timestamp (DATETIME)
- temperature (REAL)
- humidity (REAL)
- light_level (REAL)

**Tabla: actuator_events**
- id (INTEGER PRIMARY KEY)
- timestamp (DATETIME)
- actuator_type (TEXT)
- action (TEXT)
- value (TEXT)

## 📱 Comandos Remotos (MQTT)

Enviar mensajes JSON a los topics de control:

```json
// Activar ventilador
Topic: smarthome/actuators/fan/command
Payload: {"state": "ON"}

// Controlar luz
Topic: smarthome/actuators/light/command
Payload: {"state": "ON", "brightness": 80}
```

## 🔍 Consultas de Datos

El sistema incluye queries predefinidas:

```python
# Últimas 24 horas de lecturas
python -c "from src.database import DatabaseManager; db = DatabaseManager(); print(db.get_last_24h_readings())"

# Promedios por hora
python -c "from src.database import DatabaseManager; db = DatabaseManager(); print(db.get_hourly_averages())"
```

## 🎨 Simulación en Wokwi

1. Ir a [Wokwi](https://wokwi.com)
2. Importar el archivo `wokwi/diagram.json`
3. Copiar el código adaptado para Wokwi
4. Iniciar simulación

## 📈 Monitoreo

- **Local**: Display OLED muestra estado en tiempo real
- **ThingSpeak**: Gráficos y dashboard web
- **MQTT**: Integración con apps móviles (MQTT Dash, IoT MQTT Panel)

## 🛠️ Mantenimiento

### Logs
Los eventos se registran en la base de datos y pueden consultarse:
```bash
sqlite3 database/smart_home.db "SELECT * FROM actuator_events ORDER BY timestamp DESC LIMIT 10;"
```

### Backup de Base de Datos
```bash
cp database/smart_home.db database/backup_$(date +%Y%m%d).db
```

## 🧪 Testing

```bash
# Probar sensores individualmente
python -c "from src.sensors import SensorManager; sm = SensorManager(); print(sm.read_all())"

# Probar actuadores
python -c "from src.actuators import ActuatorManager; am = ActuatorManager(); am.test_all()"
```

## 📝 Estructura del Código

```
src/
├── sensors.py       # Gestión de sensores DHT22 y LDR
├── actuators.py     # Control de LED, relay, buzzer, OLED
├── mqtt_client.py   # Cliente MQTT bidireccional
├── database.py      # Manejo de SQLite
└── cloud.py         # Integración con ThingSpeak
```

## 🎓 Documentación Adicional

Ver carpeta `docs/` para:
- Diagrama de arquitectura completo
- Flujo de datos del sistema
- Manual de configuración detallado
- Casos de uso

## 👥 Autor

[Tu Nombre] - Desarrollo de Software VIII

## 📄 Licencia

Este proyecto es para fines educativos - Universidad [Nombre]

## 🙏 Agradecimientos

- Profesor: [Nombre del profesor]
- Curso: Desarrollo de Software VIII
- Simulador: Wokwi
- Plataformas: ThingSpeak, HiveMQ