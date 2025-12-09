"""
Cliente MQTT para MicroPython con soporte TLS
Compatible con HiveMQ Cloud (puerto 8883)
"""

import time
import json
import ssl

def safe_print(msg):
    """Impresión segura para MicroPython"""
    try:
        print(msg)
    except:
        pass

class MQTTClient:
    """Cliente MQTT con soporte para TLS y callbacks personalizados"""
    
    def __init__(self, on_command_callback=None):
        """
        Inicializa el cliente MQTT
        
        Args:
            on_command_callback: Función que se llama cuando llega un mensaje
        """
        try:
            import config
            
            self.broker = config.MQTT_BROKER
            self.port = config.MQTT_PORT
            self.client_id = config.MQTT_CLIENT_ID
            self.username = config.MQTT_USERNAME if hasattr(config, 'MQTT_USERNAME') else None
            self.password = config.MQTT_PASSWORD if hasattr(config, 'MQTT_PASSWORD') else None
            self.use_tls = getattr(config, 'MQTT_USE_TLS', False)
            
            self.client = None
            self.connected = False
            self.on_command_callback = on_command_callback
            
            safe_print("📱 Cliente MQTT inicializado")
            safe_print("   Broker: {}:{}".format(self.broker, self.port))
            safe_print("   TLS: {}".format("Sí" if self.use_tls else "No"))
            
        except Exception as e:
            safe_print("❌ Error inicializando MQTT: {}".format(str(e)))
            raise
    
    def _on_message(self, topic, msg):
        """Callback interno cuando llega un mensaje MQTT"""
        try:
            topic_str = topic.decode('utf-8')
            msg_str = msg.decode('utf-8')
            
            safe_print("\n📨 Mensaje MQTT recibido:")
            safe_print("   Topic: {}".format(topic_str))
            safe_print("   Data: {}".format(msg_str[:100]))
            
            try:
                data = json.loads(msg_str)
            except:
                safe_print("   ⚠️  No es JSON válido")
                data = {"raw": msg_str, "topic": topic_str}
            
            if self.on_command_callback:
                try:
                    self.on_command_callback(data)
                except Exception as e:
                    safe_print("   ❌ Error en callback: {}".format(str(e)))
            
        except Exception as e:
            safe_print("❌ Error procesando mensaje: {}".format(str(e)))
    
    def connect(self):
        """Conecta al broker MQTT con soporte para TLS"""
        try:
            from umqtt.simple import MQTTClient as UMQTTClient
            
            safe_print("\n🔌 Conectando a MQTT broker...")
            safe_print("   {}:{}".format(self.broker, self.port))
            
            # Configurar parámetros de conexión
            connect_params = {
                'client_id': self.client_id,
                'server': self.broker,
                'port': self.port,
                'keepalive': 60
            }
            
            # Agregar credenciales si existen
            if self.username and self.password:
                safe_print("   Con autenticación")
                connect_params['user'] = self.username
                connect_params['password'] = self.password
            
            # Configurar TLS si está habilitado
            if self.use_tls:
                safe_print("   Configurando TLS...")
                try:
                    # Crear contexto SSL
                    # CERT_NONE = No verifica el certificado del servidor
                    # Necesario para algunos brokers cloud
                    connect_params['ssl'] = ssl.CERT_NONE
                    safe_print("   TLS configurado (modo CERT_NONE)")
                except Exception as e:
                    safe_print("   ⚠️  Error configurando TLS: {}".format(str(e)))
                    safe_print("   Intentando sin TLS...")
                    self.use_tls = False
            
            # Crear cliente
            self.client = UMQTTClient(**connect_params)
            
            # Configurar callback
            self.client.set_callback(self._on_message)
            
            # Intentar conectar
            safe_print("   Conectando...")
            self.client.connect()
            self.connected = True
            
            safe_print("   ✅ Conectado exitosamente!\n")
            return True
            
        except ImportError:
            safe_print("❌ No se puede importar umqtt.simple")
            safe_print("   Instala con: upip.install('micropython-umqtt.simple')")
            return False
            
        except OSError as e:
            safe_print("❌ Error de conexión OSError: {}".format(str(e)))
            errno = e.args[0] if e.args else None
            
            if errno == 113:
                safe_print("   El broker no es alcanzable (EHOSTUNREACH)")
                safe_print("   Verifica:")
                safe_print("   - Red WiFi conectada")
                safe_print("   - Broker accesible desde tu red")
                safe_print("   - Puerto {} correcto".format(self.port))
            elif errno == 111:
                safe_print("   Conexión rechazada (ECONNREFUSED)")
                safe_print("   Verifica:")
                safe_print("   - Puerto correcto (8883 para TLS, 1883 sin TLS)")
                safe_print("   - Credenciales correctas")
            elif errno == -2:
                safe_print("   No se puede resolver el nombre (EAI_NONAME)")
                safe_print("   Verifica el MQTT_BROKER en config.py")
            
            self.connected = False
            return False
            
        except Exception as e:
            safe_print("❌ Error conectando: {}".format(str(e)))
            import sys
            sys.print_exception(e)
            self.connected = False
            return False
    
    def disconnect(self):
        """Desconecta del broker MQTT"""
        try:
            if self.client and self.connected:
                self.client.disconnect()
                self.connected = False
                safe_print("🔌 MQTT desconectado")
        except Exception as e:
            safe_print("Error desconectando: {}".format(str(e)))
    
    def publish(self, topic, message, qos=1):
        """Publica un mensaje en un topic"""
        try:
            if not self.connected:
                safe_print("⚠️  No conectado a MQTT")
                return False
            
            if isinstance(message, dict):
                message = json.dumps(message)
            
            if isinstance(topic, str):
                topic = topic.encode('utf-8')
            if isinstance(message, str):
                message = message.encode('utf-8')
            
            self.client.publish(topic, message, qos=qos)
            return True
            
        except Exception as e:
            safe_print("❌ Error publicando: {}".format(str(e)))
            return False
    
    def subscribe(self, topic):
        """Se suscribe a un topic"""
        try:
            if not self.connected:
                safe_print("⚠️  No conectado a MQTT")
                return False
            
            if isinstance(topic, str):
                topic = topic.encode('utf-8')
            
            self.client.subscribe(topic)
            safe_print("📡 Suscrito a: {}".format(topic.decode('utf-8')))
            return True
            
        except Exception as e:
            safe_print("❌ Error suscribiendo: {}".format(str(e)))
            return False
    
    def check_msg(self):
        """Verifica si hay mensajes nuevos (non-blocking)"""
        try:
            if self.connected and self.client:
                self.client.check_msg()
        except Exception as e:
            safe_print("Error en check_msg: {}".format(str(e)))
    
    def wait_msg(self):
        """Espera por mensajes (blocking)"""
        try:
            if self.connected and self.client:
                self.client.wait_msg()
        except Exception as e:
            safe_print("Error en wait_msg: {}".format(str(e)))


# Test
if __name__ == "__main__":
    def test_callback(data):
        print("📨 Callback: {}".format(data))
    
    mqtt = MQTTClient(on_command_callback=test_callback)
    
    if mqtt.connect():
        mqtt.subscribe("test/topic")
        
        try:
            while True:
                mqtt.check_msg()
                time.sleep(0.1)
        except KeyboardInterrupt:
            mqtt.disconnect()
    else:
        print("❌ No se pudo conectar")
