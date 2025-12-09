-- Schema para la base de datos Smart Home IoT
-- SQLite Database

-- ========================================
-- TABLA: sensor_readings
-- Almacena todas las lecturas de sensores
-- ========================================
CREATE TABLE IF NOT EXISTS sensor_readings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    temperature REAL NOT NULL,
    humidity REAL NOT NULL,
    light_level REAL NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CHECK (temperature >= -50 AND temperature <= 100),
    CHECK (humidity >= 0 AND humidity <= 100),
    CHECK (light_level >= 0)
);

-- Índice para búsquedas por timestamp
CREATE INDEX IF NOT EXISTS idx_sensor_timestamp 
ON sensor_readings(timestamp);

-- Índice para búsquedas por temperatura
CREATE INDEX IF NOT EXISTS idx_sensor_temperature 
ON sensor_readings(temperature);

-- ========================================
-- TABLA: actuator_events
-- Registra todos los eventos de actuadores
-- ========================================
CREATE TABLE IF NOT EXISTS actuator_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    actuator_type TEXT NOT NULL,  -- 'fan', 'light', 'buzzer'
    action TEXT NOT NULL,          -- 'on', 'off', 'toggle', 'beep', etc.
    value TEXT,                    -- Valor adicional (opcional)
    auto_triggered BOOLEAN DEFAULT 0,  -- 0=manual, 1=automático
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CHECK (actuator_type IN ('fan', 'light', 'buzzer', 'led')),
    CHECK (auto_triggered IN (0, 1))
);

-- Índice para búsquedas por timestamp
CREATE INDEX IF NOT EXISTS idx_actuator_timestamp 
ON actuator_events(timestamp);

-- Índice para búsquedas por tipo de actuador
CREATE INDEX IF NOT EXISTS idx_actuator_type 
ON actuator_events(actuator_type);

-- ========================================
-- TABLA: alerts
-- Almacena alertas generadas por el sistema
-- ========================================
CREATE TABLE IF NOT EXISTS alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    alert_type TEXT NOT NULL,      -- 'temperature_high', 'humidity_critical', etc.
    message TEXT NOT NULL,
    value REAL,                    -- Valor que generó la alerta
    acknowledged BOOLEAN DEFAULT 0, -- 0=no reconocida, 1=reconocida
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CHECK (acknowledged IN (0, 1))
);

-- Índice para búsquedas por timestamp
CREATE INDEX IF NOT EXISTS idx_alerts_timestamp 
ON alerts(timestamp);

-- Índice para alertas no reconocidas
CREATE INDEX IF NOT EXISTS idx_alerts_acknowledged 
ON alerts(acknowledged);

-- ========================================
-- TABLA: system_logs (opcional)
-- Para registro de eventos del sistema
-- ========================================
CREATE TABLE IF NOT EXISTS system_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    log_level TEXT NOT NULL,       -- 'INFO', 'WARNING', 'ERROR', 'CRITICAL'
    component TEXT NOT NULL,        -- Componente que generó el log
    message TEXT NOT NULL,
    details TEXT,                  -- JSON con detalles adicionales
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CHECK (log_level IN ('INFO', 'WARNING', 'ERROR', 'CRITICAL'))
);

-- Índice para búsquedas por timestamp
CREATE INDEX IF NOT EXISTS idx_logs_timestamp 
ON system_logs(timestamp);

-- Índice para búsquedas por nivel
CREATE INDEX IF NOT EXISTS idx_logs_level 
ON system_logs(log_level);

-- ========================================
-- VISTAS ÚTILES
-- ========================================

-- Vista: Lecturas de las últimas 24 horas
CREATE VIEW IF NOT EXISTS v_last_24h_readings AS
SELECT 
    id,
    timestamp,
    temperature,
    humidity,
    light_level
FROM sensor_readings
WHERE timestamp >= datetime('now', '-24 hours')
ORDER BY timestamp DESC;

-- Vista: Promedios por hora (últimas 24h)
CREATE VIEW IF NOT EXISTS v_hourly_averages AS
SELECT 
    strftime('%Y-%m-%d %H:00:00', timestamp) as hour,
    COUNT(*) as reading_count,
    ROUND(AVG(temperature), 2) as avg_temperature,
    ROUND(MIN(temperature), 2) as min_temperature,
    ROUND(MAX(temperature), 2) as max_temperature,
    ROUND(AVG(humidity), 2) as avg_humidity,
    ROUND(AVG(light_level), 2) as avg_light
FROM sensor_readings
WHERE timestamp >= datetime('now', '-24 hours')
GROUP BY hour
ORDER BY hour DESC;

-- Vista: Eventos recientes de actuadores
CREATE VIEW IF NOT EXISTS v_recent_actuator_events AS
SELECT 
    id,
    timestamp,
    actuator_type,
    action,
    CASE WHEN auto_triggered = 1 THEN 'AUTO' ELSE 'MANUAL' END as trigger_mode
FROM actuator_events
ORDER BY timestamp DESC
LIMIT 100;

-- Vista: Alertas activas (no reconocidas)
CREATE VIEW IF NOT EXISTS v_active_alerts AS
SELECT 
    id,
    timestamp,
    alert_type,
    message,
    value
FROM alerts
WHERE acknowledged = 0
ORDER BY timestamp DESC;

-- ========================================
-- TRIGGERS
-- ========================================

-- Trigger: Limpiar lecturas antiguas automáticamente (>30 días)
CREATE TRIGGER IF NOT EXISTS cleanup_old_readings
AFTER INSERT ON sensor_readings
BEGIN
    DELETE FROM sensor_readings
    WHERE timestamp < datetime('now', '-30 days');
END;

-- Trigger: Limpiar eventos antiguos (>30 días)
CREATE TRIGGER IF NOT EXISTS cleanup_old_events
AFTER INSERT ON actuator_events
BEGIN
    DELETE FROM actuator_events
    WHERE timestamp < datetime('now', '-30 days');
END;

-- ========================================
-- DATOS INICIALES (opcional)
-- ========================================

-- Insertar log de inicialización
INSERT INTO system_logs (log_level, component, message)
VALUES ('INFO', 'DATABASE', 'Base de datos inicializada correctamente');

-- ========================================
-- COMENTARIOS Y DOCUMENTACIÓN
-- ========================================

/*
NOTAS DE USO:

1. SENSOR_READINGS:
   - Almacena lecturas cada 30 segundos por defecto
   - Retención: 30 días (limpieza automática vía trigger)
   - Campos: temperatura (°C), humedad (%), luz (lux)

2. ACTUATOR_EVENTS:
   - Registra cada acción de actuadores
   - auto_triggered indica si fue automático o manual
   - Útil para auditoría y análisis de comportamiento

3. ALERTS:
   - Almacena alertas de umbrales excedidos
   - acknowledged permite marcar alertas como vistas
   - Use UPDATE alerts SET acknowledged = 1 WHERE id = X

4. VISTAS:
   - v_last_24h_readings: Datos recientes
   - v_hourly_averages: Estadísticas agregadas
   - v_recent_actuator_events: Historial de acciones
   - v_active_alerts: Alertas pendientes

5. MANTENIMIENTO:
   - Los triggers limpian automáticamente datos >30 días
   - Para backup: sqlite3 smart_home.db ".dump" > backup.sql
   - Para restaurar: sqlite3 new_db.db < backup.sql

6. CONSULTAS ÚTILES:
   - Ver últimas 10 lecturas: SELECT * FROM v_last_24h_readings LIMIT 10;
   - Ver promedios: SELECT * FROM v_hourly_averages;
   - Ver alertas activas: SELECT * FROM v_active_alerts;
*/