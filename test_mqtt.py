import paho.mqtt.client as mqtt
import ssl

BROKER = "a696d90a2b6f41fe9008b1f1dcda2db5.s1.eu.hivemq.cloud"
PORT = 8884  # WebSockets + TLS

client = mqtt.Client(transport="websockets")

client.tls_set(cert_reqs=ssl.CERT_NONE)
client.tls_insecure_set(True)

client.username_pw_set("smarthome", "SmartHome123!")

def on_connect(client, userdata, flags, rc):
    print("🔥 Conectado! Código:", rc)

client.on_connect = on_connect

print("🔄 Conectando por WebSockets TLS...")

client.connect(BROKER, PORT, keepalive=60)

client.loop_forever()
