"""
Módulo de gestión de sensores para Smart Home IoT
Maneja la lectura de DHT22 (temperatura/humedad) y LDR (luz)
"""

import time
import random
from datetime import datetime
import config

# Intentar importar librerías de hardware real
try:
    import board
    import adafruit_dht
    REAL_HARDWARE = True
except ImportError:
    REAL_HARDWARE = False
    print("⚠️ Modo simulación: librerías de hardware no disponibles")


class DHT22Sensor:
    """Sensor de temperatura y humedad DHT22"""
    
    def __init__(self, pin=None):
        self.pin = pin or config.GPIO_PINS["dht22_data"]
        self.temperature = None
        self.humidity = None
        
        if REAL_HARDWARE:
            try:
                # Configurar sensor real
                self.sensor = adafruit_dht.DHT22(getattr(board, f"D{self.pin}"))
                print(f"✅ DHT22 inicializado en pin {self.pin}")
            except Exception as e:
                print(f"❌ Error inicializando DHT22: {e}")
                self.sensor = None
        else:
            self.sensor = None
            print("📊 DHT22 en modo simulación")
    
    def read(self):
        """Lee temperatura y humedad del sensor"""
        try:
            if REAL_HARDWARE and self.sensor:
                # Leer sensor real
                self.temperature = self.sensor.temperature
                self.humidity = self.sensor.humidity
            else:
                # Simular lecturas realistas
                # Temperatura base con variación aleatoria
                base_temp = 25.0
                self.temperature = round(base_temp + random.uniform(-3, 8), 1)
                
                # Humedad base con variación
                base_humidity = 55.0
                self.humidity = round(base_humidity + random.uniform(-15, 20), 1)
            
            return {
                "temperature": self.temperature,
                "humidity": self.humidity,
                "timestamp": datetime.now().isoformat(),
                "status": "ok"
            }
        
        except RuntimeError as e:
            # Error común de lectura DHT22 (sensor ocupado)
            print(f"⚠️ Error leyendo DHT22: {e}")
            return {
                "temperature": self.temperature,  # Retornar última lectura
                "humidity": self.humidity,
                "timestamp": datetime.now().isoformat(),
                "status": "error_retry"
            }
        except Exception as e:
            print(f"❌ Error crítico DHT22: {e}")
            return None
    
    def get_temperature(self):
        """Obtiene solo la temperatura"""
        data = self.read()
        return data["temperature"] if data else None
    
    def get_humidity(self):
        """Obtiene solo la humedad"""
        data = self.read()
        return data["humidity"] if data else None


class LDRSensor:
    """Sensor de luz LDR (Light Dependent Resistor)"""
    
    def __init__(self, pin=None):
        self.pin = pin or config.GPIO_PINS["ldr_analog"]
        self.light_level = None
        self.last_reading = None
        
        if REAL_HARDWARE:
            try:
                # Configurar ADC para leer valor analógico
                # Esto varía según la plataforma (RPi necesita MCP3008, ESP32 tiene ADC integrado)
                print(f"✅ LDR inicializado en pin ADC {self.pin}")
            except Exception as e:
                print(f"❌ Error inicializando LDR: {e}")
        else:
            print("💡 LDR en modo simulación")
    
    def read_analog(self):
        """Lee valor analógico del LDR (0-1023 o 0-4095 según ADC)"""
        if REAL_HARDWARE:
            # Leer ADC real (implementar según hardware)
            # Para ESP32: valor = adc.read()
            # Para RPi + MCP3008: usar spidev
            return 0
        else:
            # Simular valor ADC (0-1023)
            # Valores bajos = oscuro, valores altos = brillante
            current_hour = datetime.now().hour
            
            # Simular ciclo día/noche
            if 6 <= current_hour <= 18:
                # Día: más luz
                base_value = random.randint(600, 1000)
            else:
                # Noche: poca luz
                base_value = random.randint(50, 300)
            
            return base_value
    
    def analog_to_lux(self, analog_value):
        """Convierte valor analógico a aproximación de lux"""
        # Conversión aproximada (calibrar según sensor real)
        # Asumiendo rango 0-1023 -> 0-1000 lux aproximadamente
        lux = (analog_value / 1023.0) * 1000
        return round(lux, 1)
    
    def read(self):
        """Lee nivel de luz en lux"""
        try:
            analog = self.read_analog()
            self.light_level = self.analog_to_lux(analog)
            self.last_reading = datetime.now()
            
            return {
                "light_level": self.light_level,
                "analog_value": analog,
                "timestamp": datetime.now().isoformat(),
                "status": "ok"
            }
        except Exception as e:
            print(f"❌ Error leyendo LDR: {e}")
            return None
    
    def get_light_level(self):
        """Obtiene solo el nivel de luz"""
        data = self.read()
        return data["light_level"] if data else None
    
    def is_dark(self, threshold=None):
        """Determina si está oscuro según umbral"""
        threshold = threshold or config.THRESHOLDS["light_threshold"]
        current_level = self.get_light_level()
        return current_level < threshold if current_level else False


class SensorManager:
    """Gestor centralizado de todos los sensores"""
    
    def __init__(self):
        self.dht22 = DHT22Sensor()
        self.ldr = LDRSensor()
        self.readings_count = 0
        self.last_read_time = None
        print("\n" + "="*50)
        print("📡 SENSOR MANAGER INICIALIZADO")
        print("="*50)
    
    def read_all(self):
        """Lee todos los sensores y retorna datos consolidados"""
        self.readings_count += 1
        self.last_read_time = datetime.now()
        
        # Leer cada sensor
        dht_data = self.dht22.read()
        ldr_data = self.ldr.read()
        
        # Consolidar datos
        readings = {
            "timestamp": datetime.now().isoformat(),
            "temperature": dht_data["temperature"] if dht_data else None,
            "humidity": dht_data["humidity"] if dht_data else None,
            "light_level": ldr_data["light_level"] if ldr_data else None,
            "readings_count": self.readings_count,
            "sensors_status": {
                "dht22": dht_data["status"] if dht_data else "error",
                "ldr": ldr_data["status"] if ldr_data else "error"
            }
        }
        
        return readings
    
    def check_thresholds(self, readings):
        """Verifica si las lecturas exceden umbrales configurados"""
        alerts = []
        
        temp = readings.get("temperature")
        humidity = readings.get("humidity")
        light = readings.get("light_level")
        
        # Verificar temperatura
        if temp:
            if temp > config.THRESHOLDS["temperature_critical"]:
                alerts.append({
                    "type": "temperature_critical",
                    "value": temp,
                    "message": config.MESSAGES["temp_critical"]
                })
            elif temp > config.THRESHOLDS["temperature_high"]:
                alerts.append({
                    "type": "temperature_high",
                    "value": temp,
                    "message": config.MESSAGES["temp_high"]
                })
            elif temp < config.THRESHOLDS["temperature_low"]:
                alerts.append({
                    "type": "temperature_low",
                    "value": temp,
                    "message": "⚠️ Temperatura baja detectada"
                })
        
        # Verificar humedad
        if humidity:
            if humidity > config.THRESHOLDS["humidity_critical"]:
                alerts.append({
                    "type": "humidity_critical",
                    "value": humidity,
                    "message": "💧 ALERTA: Humedad crítica"
                })
            elif humidity > config.THRESHOLDS["humidity_high"]:
                alerts.append({
                    "type": "humidity_high",
                    "value": humidity,
                    "message": config.MESSAGES["humidity_high"]
                })
        
        # Verificar luz
        if light is not None and light < config.THRESHOLDS["light_threshold"]:
            alerts.append({
                "type": "low_light",
                "value": light,
                "message": "🌙 Nivel de luz bajo"
            })
        
        return alerts
    
    def print_readings(self, readings):
        """Imprime lecturas de forma legible"""
        print("\n" + "-"*50)
        print(f"📊 LECTURAS #{readings['readings_count']}")
        print(f"🕐 Timestamp: {readings['timestamp']}")
        print(f"🌡️  Temperatura: {readings['temperature']}°C")
        print(f"💧 Humedad: {readings['humidity']}%")
        print(f"💡 Luz: {readings['light_level']} lux")
        print("-"*50)


# Función de prueba
def test_sensors():
    """Prueba todos los sensores"""
    print("\n🧪 INICIANDO PRUEBA DE SENSORES\n")
    
    manager = SensorManager()
    
    for i in range(5):
        print(f"\n--- Lectura {i+1} ---")
        readings = manager.read_all()
        manager.print_readings(readings)
        
        # Verificar umbrales
        alerts = manager.check_thresholds(readings)
        if alerts:
            print("\n⚠️ ALERTAS DETECTADAS:")
            for alert in alerts:
                print(f"  • {alert['message']} (Valor: {alert['value']})")
        
        time.sleep(2)


if __name__ == "__main__":
    test_sensors()