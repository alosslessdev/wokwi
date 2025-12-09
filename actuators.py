"""
Módulo de gestión de actuadores para Smart Home IoT
Controla LED RGB, Relay (ventilador), Buzzer y Display OLED
"""

import time
from datetime import datetime
import config

# Intentar importar librerías de hardware real
try:
    import RPi.GPIO as GPIO
    REAL_GPIO = True
except ImportError:
    REAL_GPIO = False
    print("⚠️ GPIO en modo simulación")

try:
    from PIL import Image, ImageDraw, ImageFont
    import adafruit_ssd1306
    import board
    REAL_OLED = True
except ImportError:
    REAL_OLED = False
    print("⚠️ OLED en modo simulación")


class LEDController:
    """Controlador de LED RGB"""
    
    def __init__(self):
        self.pins = {
            "red": config.GPIO_PINS["led_red"],
            "green": config.GPIO_PINS["led_green"],
            "blue": config.GPIO_PINS["led_blue"]
        }
        self.current_state = {"red": False, "green": False, "blue": False}
        
        if REAL_GPIO:
            GPIO.setmode(GPIO.BCM)
            for color, pin in self.pins.items():
                GPIO.setup(pin, GPIO.OUT)
                GPIO.output(pin, GPIO.LOW)
        
        print(f"💡 LED RGB inicializado (R:{self.pins['red']}, G:{self.pins['green']}, B:{self.pins['blue']})")
    
    def set_color(self, red=False, green=False, blue=False):
        """Establece el color del LED"""
        self.current_state = {"red": red, "green": green, "blue": blue}
        
        if REAL_GPIO:
            GPIO.output(self.pins["red"], GPIO.HIGH if red else GPIO.LOW)
            GPIO.output(self.pins["green"], GPIO.HIGH if green else GPIO.LOW)
            GPIO.output(self.pins["blue"], GPIO.HIGH if blue else GPIO.LOW)
        
        color_name = self._get_color_name()
        print(f"💡 LED: {color_name}")
        return color_name
    
    def _get_color_name(self):
        """Obtiene el nombre del color actual"""
        r, g, b = self.current_state["red"], self.current_state["green"], self.current_state["blue"]
        
        if r and g and b:
            return "Blanco"
        elif r and g:
            return "Amarillo"
        elif r and b:
            return "Magenta"
        elif g and b:
            return "Cian"
        elif r:
            return "Rojo"
        elif g:
            return "Verde"
        elif b:
            return "Azul"
        else:
            return "Apagado"
    
    def off(self):
        """Apaga el LED"""
        return self.set_color(False, False, False)
    
    def white(self):
        """LED blanco (todos encendidos)"""
        return self.set_color(True, True, True)
    
    def red(self):
        """LED rojo (alerta/calor)"""
        return self.set_color(True, False, False)
    
    def green(self):
        """LED verde (OK/normal)"""
        return self.set_color(False, True, False)
    
    def blue(self):
        """LED azul (frío)"""
        return self.set_color(False, False, True)
    
    def yellow(self):
        """LED amarillo (advertencia)"""
        return self.set_color(True, True, False)


class RelayController:
    """Controlador de Relay para ventilador"""
    
    def __init__(self):
        self.pin = config.GPIO_PINS["relay_fan"]
        self.state = False
        
        if REAL_GPIO:
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(self.pin, GPIO.OUT)
            GPIO.output(self.pin, GPIO.LOW)
        
        print(f"🌀 Relay (Ventilador) inicializado en pin {self.pin}")
    
    def on(self):
        """Enciende el ventilador"""
        self.state = True
        if REAL_GPIO:
            GPIO.output(self.pin, GPIO.HIGH)
        print("🌀 Ventilador: ENCENDIDO")
        return True
    
    def off(self):
        """Apaga el ventilador"""
        self.state = False
        if REAL_GPIO:
            GPIO.output(self.pin, GPIO.LOW)
        print("🌀 Ventilador: APAGADO")
        return False
    
    def toggle(self):
        """Alterna el estado del ventilador"""
        if self.state:
            return self.off()
        else:
            return self.on()
    
    def get_state(self):
        """Obtiene el estado actual"""
        return self.state


class BuzzerController:
    """Controlador de Buzzer para alertas"""
    
    def __init__(self):
        self.pin = config.GPIO_PINS["buzzer"]
        
        if REAL_GPIO:
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(self.pin, GPIO.OUT)
            GPIO.output(self.pin, GPIO.LOW)
        
        print(f"🔔 Buzzer inicializado en pin {self.pin}")
    
    def beep(self, duration=0.1):
        """Emite un beep corto"""
        if REAL_GPIO:
            GPIO.output(self.pin, GPIO.HIGH)
            time.sleep(duration)
            GPIO.output(self.pin, GPIO.LOW)
        else:
            print(f"🔔 BEEP ({duration}s)")
    
    def alert(self, times=3, duration=0.2, interval=0.2):
        """Emite una secuencia de beeps de alerta"""
        print(f"🚨 ALERTA: {times} beeps")
        for i in range(times):
            self.beep(duration)
            if i < times - 1:
                time.sleep(interval)
    
    def alarm(self):
        """Alarma intensa"""
        self.alert(times=5, duration=0.3, interval=0.1)


class OLEDDisplay:
    """Controlador de Display OLED SSD1306"""
    
    def __init__(self):
        self.width = 128
        self.height = 64
        self.display = None
        
        if REAL_OLED:
            try:
                i2c = board.I2C()
                self.display = adafruit_ssd1306.SSD1306_I2C(self.width, self.height, i2c)
                self.display.fill(0)
                self.display.show()
                print("📺 Display OLED inicializado")
            except Exception as e:
                print(f"❌ Error inicializando OLED: {e}")
                self.display = None
        else:
            print("📺 OLED en modo simulación")
    
    def clear(self):
        """Limpia la pantalla"""
        if REAL_OLED and self.display:
            self.display.fill(0)
            self.display.show()
    
    def show_text(self, lines):
        """Muestra texto en el display"""
        if REAL_OLED and self.display:
            # Crear imagen
            image = Image.new("1", (self.width, self.height))
            draw = ImageDraw.Draw(image)
            
            # Dibujar líneas de texto
            y = 0
            for line in lines:
                draw.text((0, y), line, fill=255)
                y += 12
            
            # Mostrar en display
            self.display.image(image)
            self.display.show()
        else:
            # Simulación
            print("\n" + "="*40)
            print("📺 DISPLAY OLED:")
            for line in lines:
                print(f"  {line}")
            print("="*40)
    
    def show_sensor_data(self, temperature, humidity, light_level):
        """Muestra datos de sensores formateados"""
        lines = [
            "SMART HOME",
            f"Temp: {temperature:.1f}C" if temperature else "Temp: --",
            f"Hum:  {humidity:.1f}%" if humidity else "Hum: --",
            f"Luz:  {int(light_level)} lux" if light_level else "Luz: --",
            f"{datetime.now().strftime('%H:%M:%S')}"
        ]
        self.show_text(lines)
    
    def show_status(self, message):
        """Muestra un mensaje de estado"""
        lines = [
            "SMART HOME",
            "",
            message,
            "",
            datetime.now().strftime("%H:%M:%S")
        ]
        self.show_text(lines)


class ActuatorManager:
    """Gestor centralizado de todos los actuadores"""
    
    def __init__(self):
        self.led = LEDController()
        self.relay = RelayController()
        self.buzzer = BuzzerController()
        self.oled = OLEDDisplay()
        
        print("\n" + "="*50)
        print("🎛️  ACTUATOR MANAGER INICIALIZADO")
        print("="*50)
        
        # Prueba inicial
        self.oled.show_status("Sistema iniciado")
        self.led.green()
        time.sleep(0.5)
        self.led.off()
    
    def update_display(self, sensor_data):
        """Actualiza el display con datos de sensores"""
        self.oled.show_sensor_data(
            sensor_data.get("temperature"),
            sensor_data.get("humidity"),
            sensor_data.get("light_level")
        )
    
    def auto_control(self, sensor_data):
        """Control automático basado en sensores"""
        actions = []
        
        temp = sensor_data.get("temperature")
        light = sensor_data.get("light_level")
        
        # Control automático de ventilador por temperatura
        if temp and config.SYSTEM_CONFIG["auto_mode"]:
            if temp > config.THRESHOLDS["temperature_high"]:
                if not self.relay.state:
                    self.relay.on()
                    self.led.red()
                    actions.append("fan_on")
                    
                    if temp > config.THRESHOLDS["temperature_critical"]:
                        self.buzzer.alert()
            else:
                if self.relay.state:
                    self.relay.off()
                    self.led.green()
                    actions.append("fan_off")
        
        # Control automático de luz
        if light is not None and config.SYSTEM_CONFIG["auto_mode"]:
            if light < config.THRESHOLDS["light_threshold"]:
                self.led.white()
                actions.append("light_on")
            elif light > config.THRESHOLDS["light_threshold"] + 100:
                if not self.relay.state:  # Si no hay alerta de calor
                    self.led.off()
                    actions.append("light_off")
        
        return actions
    
    def manual_control(self, command):
        """Control manual mediante comandos"""
        action_result = None
        
        if command["actuator"] == "fan":
            if command["action"] == "on":
                self.relay.on()
                action_result = "fan_on"
            elif command["action"] == "off":
                self.relay.off()
                action_result = "fan_off"
            elif command["action"] == "toggle":
                self.relay.toggle()
                action_result = f"fan_{'on' if self.relay.state else 'off'}"
        
        elif command["actuator"] == "light":
            if command["action"] == "on":
                self.led.white()
                action_result = "light_on"
            elif command["action"] == "off":
                self.led.off()
                action_result = "light_off"
        
        elif command["actuator"] == "buzzer":
            if command["action"] == "beep":
                self.buzzer.beep()
                action_result = "buzzer_beep"
            elif command["action"] == "alert":
                self.buzzer.alert()
                action_result = "buzzer_alert"
        
        return action_result
    
    def get_status(self):
        """Obtiene estado de todos los actuadores"""
        return {
            "fan": self.relay.get_state(),
            "led": self.led._get_color_name(),
            "timestamp": datetime.now().isoformat()
        }
    
    def test_all(self):
        """Prueba todos los actuadores"""
        print("\n🧪 PROBANDO ACTUADORES\n")
        
        # Probar LED
        print("Probando LED...")
        for color in ["red", "green", "blue", "yellow", "white"]:
            getattr(self.led, color)()
            time.sleep(0.5)
        self.led.off()
        
        # Probar ventilador
        print("\nProbando ventilador...")
        self.relay.on()
        time.sleep(1)
        self.relay.off()
        
        # Probar buzzer
        print("\nProbando buzzer...")
        self.buzzer.beep()
        time.sleep(0.5)
        
        # Probar display
        print("\nProbando display...")
        self.oled.show_status("Test OK!")
        
        print("\n✅ Prueba completada\n")
    
    def cleanup(self):
        """Limpia recursos GPIO"""
        if REAL_GPIO:
            GPIO.cleanup()
        print("🧹 GPIO limpiado")


# Función de prueba
if __name__ == "__main__":
    manager = ActuatorManager()
    manager.test_all()
    manager.cleanup()