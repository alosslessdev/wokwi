"""
Backend Python - Smart Home IoT
Recibe datos del ESP32 vía MQTT, procesa lógica y envía a ThingSpeak
"""

import time
import json
import signal
import sys
from datetime import datetime
import requests
import config
from src.database import DatabaseManager
from src.mqtt_client import MQTTClient

class SmartHomeBackend:
    """Backend centralizado del sistema Smart Home"""
    
    def __init__(self):
        print("\n" + "="*60)
        print("🖥️  SMART HOME BACKEND SERVER")
        print("="*60)
        
        # Base de datos
        self.database = DatabaseManager()
        self.database.initialize()
        
        # Cliente MQTT (recibe de ESP32 y envía comandos)
        self.mqtt = MQTTClient(on_command_callback=self.handle_sensor_data)
        
        # Estado del sistema
        self.sensor_data = {
            "temperature": None,
            "humidity": None,
            "light_level": None,
            "timestamp": None
        }
        
        self.actuator_states = {
            "fan": False,
            "light": False
        }
        
        # Control de tiempos
        self.last_thingspeak = 0
        self.last_db_save = 0
        
        print("✅ Backend inicializado\n")
    
    def handle_sensor_data(self, message):
        """
        Procesa datos de sensores recibidos del ESP32 vía MQTT
        message = {"actuator": "sensor", "topic": "...", "data": {...}}
        """
        try:
            topic = message.get("topic", "")
            data = message.get("data", {})
            
            print(f"📥 Datos recibidos: {topic}")
            
            # Actualizar datos según el topic
            if "temperature" in topic:
                self.sensor_data["temperature"] = data.get("value")
                print(f"   🌡️  Temperatura: {data.get('value')}°C")
            
            elif "humidity" in topic:
                self.sensor_data["humidity"] = data.get("value")
                print(f"   💧 Humedad: {data.get('value')}%")
            
            elif "light" in topic:
                self.sensor_data["light_level"] = data.get("value")
                print(f"   💡 Luz: {data.get('value')} lux")
            
            self.sensor_data["timestamp"] = datetime.now().isoformat()
            
            # Procesar lógica de negocio
            self.process_business_logic()
            
        except Exception as e:
            print(f"❌ Error procesando datos: {e}")
    
    def process_business_logic(self):
        """Aplica lógica de negocio (control automático, alertas)"""
        temp = self.sensor_data.get("temperature")
        humidity = self.sensor_data.get("humidity")
        light = self.sensor_data.get("light_level")
        
        # Solo procesar si tenemos datos completos
        if temp is None or humidity is None or light is None:
            return
        
        # REGLA 1: Control automático de ventilador por temperatura
        if temp > config.THRESHOLDS["temperature_high"]:
            if not self.actuator_states["fan"]:
                print(f"🔥 Temperatura alta ({temp}°C) - Activando ventilador")
                self.send_command_to_esp32("fan", "on")
                self.actuator_states["fan"] = True
                
                # Guardar evento en BD
                self.database.save_actuator_event(
                    actuator_type="fan",
                    action="on",
                    auto_triggered=True
                )
                
                # Alerta crítica
                if temp > config.THRESHOLDS["temperature_critical"]:
                    self.database.save_alert(
                        alert_type="temperature_critical",
                        message=f"Temperatura crítica: {temp}°C",
                        value=temp
                    )
        else:
            if self.actuator_states["fan"]:
                print(f"✅ Temperatura normal ({temp}°C) - Desactivando ventilador")
                self.send_command_to_esp32("fan", "off")
                self.actuator_states["fan"] = False
                
                self.database.save_actuator_event(
                    actuator_type="fan",
                    action="off",
                    auto_triggered=True
                )
        
        # REGLA 2: Alertas de humedad
        if humidity > config.THRESHOLDS["humidity_high"]:
            print(f"⚠️ Humedad alta detectada: {humidity}%")
            self.database.save_alert(
                alert_type="humidity_high",
                message=f"Humedad alta: {humidity}%",
                value=humidity
            )
        
        # REGLA 3: Control automático de luz
        if light < config.THRESHOLDS["light_threshold"]:
            if not self.actuator_states["light"]:
                print(f"🌙 Poca luz ({light} lux) - Activando iluminación")
                self.send_command_to_esp32("light", "on")
                self.actuator_states["light"] = True
        else:
            if self.actuator_states["light"]:
                print(f"☀️ Luz suficiente ({light} lux) - Desactivando iluminación")
                self.send_command_to_esp32("light", "off")
                self.actuator_states["light"] = False
    
    def send_command_to_esp32(self, actuator, action):
        """Envía comando al ESP32 vía MQTT"""
        command = {
            "actuator": actuator,
            "action": action,
            "timestamp": datetime.now().isoformat()
        }
        
        topic = f"smarthome/commands/{actuator}"
        
        if self.mqtt.connected:
            self.mqtt.client.publish(
                topic,
                json.dumps(command),
                qos=1
            )
            print(f"📤 Comando enviado: {actuator} -> {action}")
        else:
            print(f"⚠️ No se puede enviar comando, MQTT desconectado")
    
    def save_to_database(self):
        """Guarda datos en SQLite"""
        if all([
            self.sensor_data.get("temperature"),
            self.sensor_data.get("humidity"),
            self.sensor_data.get("light_level")
        ]):
            self.database.save_sensor_reading(
                temperature=self.sensor_data["temperature"],
                humidity=self.sensor_data["humidity"],
                light_level=self.sensor_data["light_level"]
            )
            print("💾 Datos guardados en BD")
    
    def send_to_thingspeak(self):
        """Envía datos a ThingSpeak"""
        if config.THINGSPEAK_API_KEY == "YOUR_WRITE_API_KEY":
            return False
        
        try:
            url = config.THINGSPEAK_URL
            payload = {
                "api_key": config.THINGSPEAK_API_KEY,
                "field1": self.sensor_data.get("temperature"),
                "field2": self.sensor_data.get("humidity"),
                "field3": self.sensor_data.get("light_level"),
                "field4": 1 if self.actuator_states["fan"] else 0
            }
            
            response = requests.get(url, params=payload, timeout=10)
            
            if response.status_code == 200:
                print(f"☁️  ThingSpeak actualizado (entry {response.text})")
                return True
            else:
                print(f"⚠️ ThingSpeak error: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Error ThingSpeak: {e}")
            return False
    
    def run(self):
        """Ejecuta el backend"""
        print("🚀 Iniciando backend server...")
        
        # Conectar MQTT
        if not self.mqtt.connect():
            print("❌ No se pudo conectar a MQTT")
            return
        
        # Suscribirse a topics de sensores
        time.sleep(2)  # Esperar conexión
        
        print("\n📡 Escuchando datos del ESP32...\n")
        
        try:
            while True:
                current_time = time.time()
                
                # Guardar en BD cada 30 segundos
                if current_time - self.last_db_save >= 30:
                    self.save_to_database()
                    self.last_db_save = current_time
                
                # Enviar a ThingSpeak cada 20 segundos
                if current_time - self.last_thingspeak >= 20:
                    self.send_to_thingspeak()
                    self.last_thingspeak = current_time
                
                time.sleep(1)
                
        except KeyboardInterrupt:
            print("\n\n⏹️  Deteniendo backend...")
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Limpia recursos"""
        print("\n🧹 Limpiando recursos...")
        
        if self.mqtt.connected:
            self.mqtt.disconnect()
        
        self.database.close()
        
        # Estadísticas
        stats = self.database.get_statistics()
        print("\n📊 ESTADÍSTICAS:")
        print(f"   Total lecturas: {stats['total_readings']}")
        print(f"   Temp promedio: {stats['temperature']['avg']}°C")
        
        print("\n✅ Backend detenido\n")


# Modificar el MQTTClient para este flujo
def custom_on_message(client_instance):
    """Callback personalizado para mensajes MQTT"""
    def callback(client, userdata, msg):
        try:
            topic = msg.topic
            payload = msg.payload.decode('utf-8')
            
            # Parsear JSON
            try:
                data = json.loads(payload)
            except:
                data = {"raw": payload}
            
            # Llamar al callback con formato estructurado
            if client_instance.on_command_callback:
                client_instance.on_command_callback({
                    "topic": topic,
                    "data": data
                })
        except Exception as e:
            print(f"❌ Error en mensaje: {e}")
    
    return callback


def main():
    """Función principal"""
    # Registrar manejador de señales
    def signal_handler(sig, frame):
        print("\n\n⚠️ Señal de interrupción recibida")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    # Crear y ejecutar backend
    try:
        backend = SmartHomeBackend()
        
        # Configurar callback personalizado
        backend.mqtt.client.on_message = custom_on_message(backend.mqtt)
        
        # Suscribirse a todos los topics de sensores
        backend.mqtt.client.subscribe("smarthome/sensors/#")
        
        backend.run()
    except Exception as e:
        print(f"\n❌ Error fatal: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()