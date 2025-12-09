"""
Smart Home IoT System - Source Package
Módulos principales del sistema de automatización del hogar
"""

__version__ = "1.0.0"
__author__ = "Tu Nombre"
__email__ = "tu@email.com"

# Importar clases principales para acceso directo
from .sensors import SensorManager, DHT22Sensor, LDRSensor
from .actuators import ActuatorManager, LEDController, RelayController, BuzzerController, OLEDDisplay
from .database import DatabaseManager
from .mqtt_client import MQTTClient

__all__ = [
    'SensorManager',
    'DHT22Sensor',
    'LDRSensor',
    'ActuatorManager',
    'LEDController',
    'RelayController',
    'BuzzerController',
    'OLEDDisplay',
    'DatabaseManager',
    'MQTTClient'
]

print(f"📦 Smart Home IoT System v{__version__} - Módulos cargados")