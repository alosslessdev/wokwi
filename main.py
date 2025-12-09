"""
Backend Python - Smart Home IoT
Recibe datos del ESP32 vía MQTT, procesa lógica y envía a ThingSpeak
Compatible con MicroPython
"""

import time
import json
import network
import time
from mqtt_client import MQTTClient

def safe_print(msg):
    """Impresión segura para MicroPython"""
    try:
        print(msg)
    except:
        pass

class SmartHomeBackend:
    """Backend centralizado del sistema Smart Home"""
    
    def __init__(self, config, database, mqtt_client):
        safe_print("\n" + "="*60)
        safe_print("SMART HOME BACKEND SERVER")
        safe_print("="*60)
        
        self.config = config
        self.database = database
        self.mqtt = mqtt_client
        
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
        
        # Control de ejecución
        self.running = True
        
        safe_print("Backend inicializado\n")
    
    def handle_sensor_data(self, message):
        """
        Procesa datos de sensores recibidos del ESP32 vía MQTT
        message = {"actuator": "...", "action": "...", "value": ...}
        """
        try:
            actuator = message.get("actuator", "")
            
            # Si viene de un topic de sensores, procesarlo
            if "temperature" in str(actuator).lower():
                value = message.get("value")
                if value is not None:
                    self.sensor_data["temperature"] = value
                    safe_print("   Temperatura: {}C".format(value))
            
            elif "humidity" in str(actuator).lower():
                value = message.get("value")
                if value is not None:
                    self.sensor_data["humidity"] = value
                    safe_print("   Humedad: {}%".format(value))
            
            elif "light" in str(actuator).lower():
                value = message.get("value")
                if value is not None:
                    self.sensor_data["light_level"] = value
                    safe_print("   Luz: {} lux".format(value))
            
            self.sensor_data["timestamp"] = time.time()
            
            # Procesar lógica de negocio
            self.process_business_logic()
            
        except Exception as e:
            safe_print("Error procesando datos: {}".format(str(e)))
    
    def process_business_logic(self):
        """Aplica lógica de negocio (control automático, alertas)"""
        temp = self.sensor_data.get("temperature")
        humidity = self.sensor_data.get("humidity")
        light = self.sensor_data.get("light_level")
        
        # Solo procesar si tenemos datos completos
        if temp is None or humidity is None or light is None:
            return
        
        try:
            # REGLA 1: Control automático de ventilador por temperatura
            if temp > self.config.THRESHOLDS["temperature_high"]:
                if not self.actuator_states["fan"]:
                    safe_print("Temperatura alta ({}C) - Activando ventilador".format(temp))
                    self.send_command_to_esp32("fan", "on")
                    self.actuator_states["fan"] = True
                    
                    # Guardar evento en BD
                    try:
                        self.database.save_actuator_event(
                            actuator_type="fan",
                            action="on",
                            auto_triggered=True
                        )
                    except:
                        pass
                    
                    # Alerta crítica
                    if temp > self.config.THRESHOLDS["temperature_critical"]:
                        try:
                            self.database.save_alert(
                                alert_type="temperature_critical",
                                message="Temperatura critica: {}C".format(temp),
                                value=temp
                            )
                        except:
                            pass
            else:
                if self.actuator_states["fan"]:
                    safe_print("Temperatura normal ({}C) - Desactivando ventilador".format(temp))
                    self.send_command_to_esp32("fan", "off")
                    self.actuator_states["fan"] = False
                    
                    try:
                        self.database.save_actuator_event(
                            actuator_type="fan",
                            action="off",
                            auto_triggered=True
                        )
                    except:
                        pass
            
            # REGLA 2: Alertas de humedad
            if humidity > self.config.THRESHOLDS["humidity_high"]:
                safe_print("Humedad alta detectada: {}%".format(humidity))
                try:
                    self.database.save_alert(
                        alert_type="humidity_high",
                        message="Humedad alta: {}%".format(humidity),
                        value=humidity
                    )
                except:
                    pass
            
            # REGLA 3: Control automático de luz
            if light < self.config.THRESHOLDS["light_threshold"]:
                if not self.actuator_states["light"]:
                    safe_print("Poca luz ({} lux) - Activando iluminacion".format(light))
                    self.send_command_to_esp32("light", "on")
                    self.actuator_states["light"] = True
            else:
                if self.actuator_states["light"]:
                    safe_print("Luz suficiente ({} lux) - Desactivando iluminacion".format(light))
                    self.send_command_to_esp32("light", "off")
                    self.actuator_states["light"] = False
        except Exception as e:
            safe_print("Error en logica de negocio: {}".format(str(e)))
    
    def send_command_to_esp32(self, actuator, action):
        """Envía comando al ESP32 vía MQTT"""
        try:
            command = {
                "actuator": actuator,
                "action": action,
                "timestamp": time.time()
            }
            
            topic = "smarthome/commands/{}".format(actuator)
            
            if self.mqtt.connected:
                self.mqtt.client.publish(
                    topic.encode(),
                    json.dumps(command).encode(),
                    qos=1
                )
                safe_print("Comando enviado: {} -> {}".format(actuator, action))
            else:
                safe_print("No se puede enviar comando, MQTT desconectado")
        except Exception as e:
            safe_print("Error enviando comando: {}".format(str(e)))
    
    def save_to_database(self):
        """Guarda datos en SQLite"""
        try:
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
                safe_print("Datos guardados en BD")
        except Exception as e:
            safe_print("Error guardando en BD: {}".format(str(e)))
    
    def send_to_thingspeak(self):
        """Envía datos a ThingSpeak"""
        try:
            if self.config.THINGSPEAK_API_KEY == "YOUR_WRITE_API_KEY":
                return False
            
            # Intentar importar urequests
            try:
                import urequests as requests
            except:
                try:
                    import requests
                except:
                    safe_print("requests/urequests no disponible")
                    return False
            
            url = "{}?api_key={}&field1={}&field2={}&field3={}&field4={}".format(
                self.config.THINGSPEAK_URL,
                self.config.THINGSPEAK_API_KEY,
                self.sensor_data.get("temperature", 0),
                self.sensor_data.get("humidity", 0),
                self.sensor_data.get("light_level", 0),
                1 if self.actuator_states["fan"] else 0
            )
            
            response = requests.get(url)
            
            if response.status_code == 200:
                safe_print("ThingSpeak actualizado")
                response.close()
                return True
            else:
                safe_print("ThingSpeak error: {}".format(response.status_code))
                response.close()
                return False
        except Exception as e:
            safe_print("Error ThingSpeak: {}".format(str(e)))
            return False
    
    def run(self):
        """Ejecuta el backend"""
        safe_print("Iniciando backend server...")
        
        # Conectar MQTT
        if not self.mqtt.connect():
            safe_print("No se pudo conectar a MQTT")
            return
        
        # Esperar conexión
        time.sleep(2)
        
        safe_print("\nEscuchando datos del ESP32...\n")
        
        try:
            while self.running:
                current_time = time.time()
                
                # Verificar mensajes MQTT (importante para MicroPython)
                try:
                    self.mqtt.check_msg()
                except Exception as e:
                    safe_print("Error check_msg: {}".format(str(e)))
                
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
            safe_print("\n\nDeteniendo backend...")
            self.running = False
        except Exception as e:
            safe_print("\nError en bucle principal: {}".format(str(e)))
            self.running = False
        finally:
            self.cleanup()
    
    def stop(self):
        """Detiene el backend de forma controlada"""
        self.running = False
    
    def cleanup(self):
        """Limpia recursos"""
        safe_print("\nLimpiando recursos...")
        
        try:
            if self.mqtt.connected:
                self.mqtt.disconnect()
        except:
            pass
        
        try:
            self.database.close()
        except:
            pass
        
        # Estadísticas
        try:
            stats = self.database.get_statistics()
            safe_print("\nESTADISTICAS:")
            safe_print("   Total lecturas: {}".format(stats['total_readings']))
            safe_print("   Temp promedio: {}C".format(stats['temperature']['avg']))
        except:
            pass
        
        safe_print("\nBackend detenido\n")


def main():
    """Función principal"""
    print("Connecting to WiFi", end="")
    sta_if = network.WLAN(network.STA_IF)
    sta_if.active(True)
    sta_if.connect('Wokwi-GUEST', '')
    while not sta_if.isconnected():
        print(".", end="")
        time.sleep(0.1)
    print(" Connected!")
    try:
        # Importar módulos
        import config
        from database import DatabaseManager
        from mqtt_client import MQTTClient
        
        # Inicializar base de datos
        database = DatabaseManager()
        database.initialize()
        
        # Crear backend
        backend = SmartHomeBackend(config, database, None)
        
        # Crear cliente MQTT con callback
        mqtt_client = MQTTClient(on_command_callback=backend.handle_sensor_data)
        backend.mqtt = mqtt_client
        
        # Suscribirse a topics de sensores
        if mqtt_client.connect():
            time.sleep(1)
            try:
                mqtt_client.client.subscribe(b"smarthome/sensors/#")
                safe_print("Suscrito a sensores")
            except:
                pass
        
        backend.run()
        
    except KeyboardInterrupt:
        safe_print("\n\nInterrupcion detectada, cerrando...")
    except Exception as e:
        safe_print("\nError fatal: {}".format(str(e)))


if __name__ == "__main__":
    main()