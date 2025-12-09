-- Queries útiles para Smart Home IoT Database
-- Consultas predefinidas para análisis y reportes

-- ========================================
-- CONSULTAS BÁSICAS - LECTURAS DE SENSORES
-- ========================================

-- 1. Últimas 10 lecturas
SELECT 
    id,
    datetime(timestamp) as fecha_hora,
    ROUND(temperature, 1) as temperatura,
    ROUND(humidity, 1) as humedad,
    ROUND(light_level, 0) as luz
FROM sensor_readings
ORDER BY timestamp DESC
LIMIT 10;

-- 2. Lecturas de las últimas 24 horas
SELECT 
    datetime(timestamp) as fecha_hora,
    ROUND(temperature, 1) as temperatura,
    ROUND(humidity, 1) as humedad,
    ROUND(light_level, 0) as luz
FROM sensor_readings
WHERE timestamp >= datetime('now', '-24 hours')
ORDER BY timestamp DESC;

-- 3. Lecturas de hoy
SELECT 
    strftime('%H:%M', timestamp) as hora,
    ROUND(temperature, 1) as temperatura,
    ROUND(humidity, 1) as humedad,
    ROUND(light_level, 0) as luz
FROM sensor_readings
WHERE date(timestamp) = date('now')
ORDER BY timestamp DESC;

-- ========================================
-- ESTADÍSTICAS Y AGREGACIONES
-- ========================================

-- 4. Estadísticas generales (últimas 24h)
SELECT 
    COUNT(*) as total_lecturas,
    ROUND(AVG(temperature), 1) as temp_promedio,
    ROUND(MIN(temperature), 1) as temp_minima,
    ROUND(MAX(temperature), 1) as temp_maxima,
    ROUND(AVG(humidity), 1) as hum_promedio,
    ROUND(MIN(humidity), 1) as hum_minima,
    ROUND(MAX(humidity), 1) as hum_maxima,
    ROUND(AVG(light_level), 0) as luz_promedio
FROM sensor_readings
WHERE timestamp >= datetime('now', '-24 hours');

-- 5. Promedios por hora (últimas 24h)
SELECT 
    strftime('%Y-%m-%d %H:00', timestamp) as hora,
    COUNT(*) as lecturas,
    ROUND(AVG(temperature), 1) as temp_promedio,
    ROUND(AVG(humidity), 1) as hum_promedio,
    ROUND(AVG(light_level), 0) as luz_promedio
FROM sensor_readings
WHERE timestamp >= datetime('now', '-24 hours')
GROUP BY strftime('%Y-%m-%d %H', timestamp)
ORDER BY hora DESC;

-- 6. Promedios por día (última semana)
SELECT 
    date(timestamp) as fecha,
    COUNT(*) as lecturas,
    ROUND(AVG(temperature), 1) as temp_promedio,
    ROUND(AVG(humidity), 1) as hum_promedio,
    ROUND(AVG(light_level), 0) as luz_promedio
FROM sensor_readings
WHERE timestamp >= datetime('now', '-7 days')
GROUP BY date(timestamp)
ORDER BY fecha DESC;

-- 7. Temperaturas más altas (top 10)
SELECT 
    datetime(timestamp) as fecha_hora,
    ROUND(temperature, 1) as temperatura,
    ROUND(humidity, 1) as humedad
FROM sensor_readings
ORDER BY temperature DESC
LIMIT 10;

-- 8. Temperaturas más bajas (top 10)
SELECT 
    datetime(timestamp) as fecha_hora,
    ROUND(temperature, 1) as temperatura,
    ROUND(humidity, 1) as humedad
FROM sensor_readings
ORDER BY temperature ASC
LIMIT 10;

-- ========================================
-- CONSULTAS DE ACTUADORES
-- ========================================

-- 9. Historial de eventos de actuadores (últimos 50)
SELECT 
    datetime(timestamp) as fecha_hora,
    actuator_type as actuador,
    action as accion,
    CASE WHEN auto_triggered = 1 THEN 'Automático' ELSE 'Manual' END as tipo
FROM actuator_events
ORDER BY timestamp DESC
LIMIT 50;

-- 10. Conteo de activaciones del ventilador (últimas 24h)
SELECT 
    COUNT(*) as activaciones,
    SUM(CASE WHEN auto_triggered = 1 THEN 1 ELSE 0 END) as automaticas,
    SUM(CASE WHEN auto_triggered = 0 THEN 1 ELSE 0 END) as manuales
FROM actuator_events
WHERE actuator_type = 'fan' 
  AND action = 'on'
  AND timestamp >= datetime('now', '-24 hours');

-- 11. Eventos por actuador (últimas 24h)
SELECT 
    actuator_type as actuador,
    action as accion,
    COUNT(*) as cantidad
FROM actuator_events
WHERE timestamp >= datetime('now', '-24 hours')
GROUP BY actuator_type, action
ORDER BY cantidad DESC;

-- 12. Tiempo promedio entre activaciones del ventilador
SELECT 
    ROUND(AVG(tiempo_entre_activaciones), 2) as minutos_promedio
FROM (
    SELECT 
        (julianday(timestamp) - julianday(LAG(timestamp) OVER (ORDER BY timestamp))) * 24 * 60 as tiempo_entre_activaciones
    FROM actuator_events
    WHERE actuator_type = 'fan' AND action = 'on'
);

-- ========================================
-- CONSULTAS DE ALERTAS
-- ========================================

-- 13. Alertas activas (no reconocidas)
SELECT 
    id,
    datetime(timestamp) as fecha_hora,
    alert_type as tipo,
    message as mensaje,
    value as valor
FROM alerts
WHERE acknowledged = 0
ORDER BY timestamp DESC;

-- 14. Historial de alertas (últimas 50)
SELECT 
    datetime(timestamp) as fecha_hora,
    alert_type as tipo,
    message as mensaje,
    value as valor,
    CASE WHEN acknowledged = 1 THEN 'Sí' ELSE 'No' END as reconocida
FROM alerts
ORDER BY timestamp DESC
LIMIT 50;

-- 15. Conteo de alertas por tipo (últimas 24h)
SELECT 
    alert_type as tipo,
    COUNT(*) as cantidad,
    AVG(value) as valor_promedio
FROM alerts
WHERE timestamp >= datetime('now', '-24 hours')
GROUP BY alert_type
ORDER BY cantidad DESC;

-- 16. Alertas críticas (últimos 7 días)
SELECT 
    datetime(timestamp) as fecha_hora,
    alert_type as tipo,
    message as mensaje,
    value as valor
FROM alerts
WHERE alert_type LIKE '%critical%'
  AND timestamp >= datetime('now', '-7 days')
ORDER BY timestamp DESC;

-- ========================================
-- ANÁLISIS CORRELACIONAL
-- ========================================

-- 17. Correlación temperatura-ventilador (últimas 24h)
SELECT 
    sr.temperature as temperatura,
    CASE WHEN ae.id IS NOT NULL THEN 'ON' ELSE 'OFF' END as ventilador
FROM sensor_readings sr
LEFT JOIN actuator_events ae 
    ON ae.actuator_type = 'fan' 
    AND ae.action = 'on'
    AND ae.timestamp BETWEEN sr.timestamp AND datetime(sr.timestamp, '+5 minutes')
WHERE sr.timestamp >= datetime('now', '-24 hours')
ORDER BY sr.timestamp DESC
LIMIT 100;

-- 18. Condiciones cuando se activa el ventilador
SELECT 
    ROUND(AVG(sr.temperature), 1) as temp_promedio,
    ROUND(AVG(sr.humidity), 1) as hum_promedio,
    ROUND(AVG(sr.light_level), 0) as luz_promedio,
    COUNT(*) as veces_activado
FROM actuator_events ae
JOIN sensor_readings sr 
    ON sr.timestamp BETWEEN datetime(ae.timestamp, '-1 minute') AND ae.timestamp
WHERE ae.actuator_type = 'fan' 
  AND ae.action = 'on'
  AND ae.timestamp >= datetime('now', '-7 days');

-- ========================================
-- REPORTES Y EXPORTACIÓN
-- ========================================

-- 19. Reporte diario completo
SELECT 
    date('now') as fecha,
    COUNT(sr.id) as total_lecturas,
    ROUND(AVG(sr.temperature), 1) as temp_promedio,
    ROUND(MIN(sr.temperature), 1) as temp_min,
    ROUND(MAX(sr.temperature), 1) as temp_max,
    ROUND(AVG(sr.humidity), 1) as hum_promedio,
    COUNT(DISTINCT CASE WHEN ae.actuator_type = 'fan' THEN ae.id END) as eventos_ventilador,
    COUNT(a.id) as total_alertas
FROM sensor_readings sr
LEFT JOIN actuator_events ae ON date(ae.timestamp) = date('now')
LEFT JOIN alerts a ON date(a.timestamp) = date('now')
WHERE date(sr.timestamp) = date('now');

-- 20. Datos para exportar a CSV (últimos 7 días)
SELECT 
    datetime(timestamp) as fecha_hora,
    temperature as temperatura,
    humidity as humedad,
    light_level as nivel_luz
FROM sensor_readings
WHERE timestamp >= datetime('now', '-7 days')
ORDER BY timestamp;

-- ========================================
-- MANTENIMIENTO Y LIMPIEZA
-- ========================================

-- 21. Ver tamaño de las tablas
SELECT 
    'sensor_readings' as tabla,
    COUNT(*) as registros
FROM sensor_readings
UNION ALL
SELECT 
    'actuator_events',
    COUNT(*)
FROM actuator_events
UNION ALL
SELECT 
    'alerts',
    COUNT(*)
FROM alerts;

-- 22. Eliminar lecturas antiguas (>30 días)
DELETE FROM sensor_readings
WHERE timestamp < datetime('now', '-30 days');

-- 23. Eliminar eventos antiguos (>30 días)
DELETE FROM actuator_events
WHERE timestamp < datetime('now', '-30 days');

-- 24. Marcar todas las alertas como reconocidas
UPDATE alerts
SET acknowledged = 1
WHERE acknowledged = 0;

-- 25. Vacuear base de datos (liberar espacio)
VACUUM;

-- ========================================
-- ANÁLISIS AVANZADO
-- ========================================

-- 26. Patrones de temperatura por hora del día
SELECT 
    strftime('%H', timestamp) as hora_del_dia,
    COUNT(*) as lecturas,
    ROUND(AVG(temperature), 1) as temp_promedio,
    ROUND(AVG(humidity), 1) as hum_promedio
FROM sensor_readings
WHERE timestamp >= datetime('now', '-7 days')
GROUP BY hora_del_dia
ORDER BY hora_del_dia;

-- 27. Días con más alertas
SELECT 
    date(timestamp) as fecha,
    COUNT(*) as total_alertas,
    COUNT(CASE WHEN alert_type LIKE '%critical%' THEN 1 END) as alertas_criticas
FROM alerts
WHERE timestamp >= datetime('now', '-30 days')
GROUP BY fecha
ORDER BY total_alertas DESC
LIMIT 10;

-- 28. Eficiencia del sistema (uptime estimado)
SELECT 
    COUNT(DISTINCT date(timestamp)) as dias_activos,
    COUNT(*) as total_lecturas,
    ROUND(COUNT(*) * 1.0 / COUNT(DISTINCT date(timestamp)), 0) as lecturas_por_dia
FROM sensor_readings
WHERE timestamp >= datetime('now', '-30 days');

-- ========================================
-- CONSULTAS DE VERIFICACIÓN
-- ========================================

-- 29. Verificar integridad de datos
SELECT 
    'Lecturas nulas' as problema,
    COUNT(*) as cantidad
FROM sensor_readings
WHERE temperature IS NULL OR humidity IS NULL OR light_level IS NULL
UNION ALL
SELECT 
    'Temperaturas fuera de rango',
    COUNT(*)
FROM sensor_readings
WHERE temperature < -50 OR temperature > 100
UNION ALL
SELECT 
    'Humedad fuera de rango',
    COUNT(*)
FROM sensor_readings
WHERE humidity < 0 OR humidity > 100;

-- 30. Última actividad del sistema
SELECT 
    'Última lectura' as tipo,
    datetime(MAX(timestamp)) as fecha_hora
FROM sensor_readings
UNION ALL
SELECT 
    'Último evento actuador',
    datetime(MAX(timestamp))
FROM actuator_events
UNION ALL
SELECT 
    'Última alerta',
    datetime(MAX(timestamp))
FROM alerts;