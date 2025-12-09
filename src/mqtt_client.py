"""
Módulo cliente MQTT para comunicación bidireccional
Publica datos de sensores y recibe comandos remotos
"""

import json
import ssl
from datetime import datetime
import paho.mqtt.client as mqtt
import config


class MQTTClient:
    """Cliente MQTT para Smart Home IoT"""
    
    def __init__(self, on_command_callback=None):
        self.client = mqtt.Client()
        self.connected = False
        self.on_command_callback = on_command_callback
        
        # Configurar callbacks
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message
        
        # Configurar credenciales
        if config.MQTT_USERNAME and config.MQTT_PASSWORD:
            self.client.username_pw_set(config.MQTT_USERNAME, config.MQTT_PASSWORD)
        
        # Configurar TLS si está habilitado
        if config.MQTT_USE_TLS:
            self.client.tls_set(cert_reqs=ssl.CERT_REQUIRED, tls_version=ssl.PROTOCOL_TLS)
        
        print(f"🌐 Cliente MQTT configurado: {config.MQTT_BROKER}:{config.MQTT_PORT}")
    
    def _on_connect(self, client, userdata, flags, rc):
        """Callback cuando se conecta al broker"""
        if rc == 0:
            self.connected = True
            print("✅ Conectado al broker MQTT")
            
            # Suscribirse a topics de comandos
            command_topics = [
                config.MQTT_TOPICS["fan_command"],
                config.MQTT_TOPICS["light_command"]
            ]
            
            for topic in command_topics:
                self.client.subscribe(topic)
                print(f"📬 Suscrito a: {topic}")
        else:
            self.connected = False
            error_messages = {
                1: "Versión de protocolo incorrecta",
                2: "ID de cliente inválido",
                3: "Servidor no disponible",
                4: "Usuario o contraseña incorrectos",
                5: "No autorizado"
            }
            print(f"❌ Error conectando: {error_messages.get(rc, f'Código {rc}')}")
    
    def _on_disconnect(self, client, userdata, rc):
        """Callback cuando se desconecta del broker"""
        self.connected = False
        if rc != 0:
            print(f"⚠️ Desconexión inesperada (código {rc})")
        else:
            print("🔌 Desconectado del broker MQTT")
    
    def _on_message(self, client, userdata, msg):
        """Callback cuando se recibe un mensaje"""
        try:
            topic = msg.topic
            payload = msg.payload.decode('utf-8')
            
            print(f"\n📩 Mensaje recibido en {topic}")
            print(f"   Payload: {payload}")
            
            # Parsear comando JSON
            try:
                command = json.loads(payload)
            except json.JSONDecodeError:
                # Si no es JSON, tratar como comando simple
                command = {"action": payload}
            
            # Procesar comando según el topic
            if topic == config.MQTT_TOPICS["fan_command"]:
                command["actuator"] = "fan"
            elif topic == config.MQTT_TOPICS["light_command"]:
                command["actuator"] = "light"
            
            # Ejecutar callback si está definido
            if self.on_command_callback:
                self.on_command_callback(command)
            
        except Exception as e:
            print(f"❌ Error procesando mensaje: {e}")
    
    def connect(self):
        """Conecta al broker MQTT"""
        try:
            print(f"🔄 Conectando a {config.MQTT_BROKER}...")
            self.client.connect(config.MQTT_BROKER, config.MQTT_PORT, keepalive=120)
            self.client.loop_start()  # Iniciar loop en thread separado
            return True
        except Exception as e:
            print(f"❌ Error conectando a MQTT: {e}")
            return False
    
    def disconnect(self):
        """Desconecta del broker"""
        self.client.loop_stop()
        self.client.disconnect()
    
    def publish_sensor_data(self, temperature, humidity, light_level):
        """Publica datos de sensores"""
        if not self.connected:
            print("⚠️ No conectado a MQTT, omitiendo publicación")
            return False
        
        try:
            # Publicar cada sensor en su topic
            self.client.publish(
                config.MQTT_TOPICS["temperature"],
                json.dumps({"value": temperature, "unit": "°C", 
                           "timestamp": datetime.now().isoformat()}),
                qos=1
            )
            
            self.client.publish(
                config.MQTT_TOPICS["humidity"],
                json.dumps({"value": humidity, "unit": "%",
                           "timestamp": datetime.now().isoformat()}),
                qos=1
            )
            
            self.client.publish(
                config.MQTT_TOPICS["light"],
                json.dumps({"value": light_level, "unit": "lux",
                           "timestamp": datetime.now().isoformat()}),
                qos=1
            )
            
            print(f"📤 Datos publicados: {temperature}°C, {humidity}%, {light_level} lux")
            return True
            
        except Exception as e:
            print(f"❌ Error publicando datos: {e}")
            return False
    
    def publish_actuator_status(self, actuator_type, state, value=None):
        """Publica estado de actuadores"""
        if not self.connected:
            return False
        
        try:
            topic = config.MQTT_TOPICS.get(f"{actuator_type}_status")
            if not topic:
                print(f"⚠️ Topic no encontrado para {actuator_type}")
                return False
            
            payload = {
                "state": state,
                "value": value,
                "timestamp": datetime.now().isoformat()
            }
            
            self.client.publish(topic, json.dumps(payload), qos=1)
            print(f"📤 Estado publicado: {actuator_type} = {state}")
            return True
            
        except Exception as e:
            print(f"❌ Error publicando estado: {e}")
            return False
    
    def publish_alert(self, alert_type, message, value=None):
        """Publica una alerta"""
        if not self.connected:
            return False
        
        try:
            payload = {
                "type": alert_type,
                "message": message,
                "value": value,
                "timestamp": datetime.now().isoformat()
            }
            
            self.client.publish(
                config.MQTT_TOPICS["alerts"],
                json.dumps(payload),
                qos=2  # QoS 2 para alertas (exactly once)
            )
            
            print(f"🚨 Alerta publicada: {message}")
            return True
            
        except Exception as e:
            print(f"❌ Error publicando alerta: {e}")
            return False
    
    def publish_system_status(self, status):
        """Publica estado general del sistema"""
        if not self.connected:
            return False
        
        try:
            payload = {
                "status": status,
                "timestamp": datetime.now().isoformat()
            }
            
            self.client.publish(
                config.MQTT_TOPICS["system_status"],
                json.dumps(payload),
                qos=1
            )
            
            return True
            
        except Exception as e:
            print(f"❌ Error publicando estado del sistema: {e}")
            return False


# Función de prueba
def test_mqtt():
    """Prueba el cliente MQTT"""
    print("\n🧪 PROBANDO CLIENTE MQTT\n")
    
    def handle_command(command):
        print(f"🎯 Comando recibido: {command}")
    
    # Crear cliente
    mqtt_client = MQTTClient(on_command_callback=handle_command)
    
    # Conectar
    if not mqtt_client.connect():
        print("❌ No se pudo conectar, verifica config.py")
        return
    
    # Esperar conexión
    import time
    time.sleep(2)
    
    if mqtt_client.connected:
        # Publicar datos de prueba
        mqtt_client.publish_sensor_data(25.5, 60.0, 450)
        time.sleep(1)
        
        mqtt_client.publish_actuator_status("fan", "on")
        time.sleep(1)
        
        mqtt_client.publish_alert("test", "Prueba de alerta", 123)
        
        # Mantener conexión para recibir mensajes
        print("\n⏳ Esperando comandos remotos (30s)...")
        print("   Publica un mensaje a los topics de comando para probar")
        time.sleep(30)
    
    # Desconectar
    mqtt_client.disconnect()
    print("\n✅ Prueba completada")


if __name__ == "__main__":
    test_mqtt()