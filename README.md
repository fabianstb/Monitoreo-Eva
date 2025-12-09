# EXAMEN PRÁCTICO FINAL — MONITOREO Y OBSERVABILIDAD

**Autor:** Fabian Santibañez S.  
**Fecha:** 09/12/2025  
**Curso:** Monitoreo y Observabilidad  

---

##  Descripción
Implementar un entorno de observabilidad integral basado en Prometheus Cloud, Grafana Cloud y AWS CloudWatch,
demostrando el monitoreo de infraestructura, aplicación, métricas personalizadas y costos, junto con la documentación del proceso.

## 2. Herramientas Utilizadas

* **Prometheus Cloud:** Almacenamiento y consulta de series temporales.
* **Grafana Cloud:** Visualización unificada y alertas.
* **AWS CloudWatch:** Monitoreo nativo de servicios AWS.
* **Python:** Lenguaje utilizado para la instrumentación de métricas personalizadas `prometheus_client`.
* **Node Exporter:** Agente de recolección de métricas de sistema operativo.

---

##  Item I - Prometheus Cloud + Grafana Cloud para EC2
En esta sección se implementó la recolección de métricas de la instancia EC2 y los contenedores que ejecutan la aplicación. Se utilizó **Grafana Alloy** como agente colector para enviar los datos a **Grafana Cloud**.

### 1. Configuración del Agente Grafana Alloy
Se configuró el archivo `config.alloy` para realizar la captura de métricas del servidor Linux y de los contenedores Docker expuestos en el puerto 8080.

**Archivo:** `Item I/config.alloy`
```alloy
// Envío de métricas a Grafana Cloud
prometheus.remote_write "metrics_service" {
    endpoint {
        url = "https://prometheus-prod-40-prod-sa-east-1.grafana.net/api/prom/push"
        basic_auth {
            username = "2801377"
            password = sys.env("GCLOUD_RW_API_KEY")
        }
    }
}

// Recolección de Node Exporter (Sistema Operativo)
prometheus.exporter.unix "integrations_node_exporter" {
  disable_collectors = ["ipvs", "btrfs", "infiniband", "xfs", "zfs"]
  // ... (configuración de filesystems excluidos)
}

// Captura de métricas de contenedores (cAdvisor/Docker)
prometheus.scrape "extra_exporters" {
  targets = [{ __address__ = "localhost:8080" }]
  scrape_interval = "15s"
  forward_to = [prometheus.remote_write.metrics_service.receiver]
}

```
**2. Dashboard y Consultas PromQL**
Se diseñó un Dashboard en Grafana Cloud para visualizar el rendimiento de los contenedores. Las consultas utilizadas (Item I/queries.txt) son:

Muestra la velocidad de consumo de CPU del contenedor.
```
rate(container_cpu_usage_seconds_total{instance="localhost:8080"}[5m])
```
![Acción Reboot](Item%20I/Metrica%201%20-%20Item%20I.png)

Uso de Memoria.
```
container_memory_usage_bytes{instance="localhost:8080"}
```
![Acción Reboot](Item%20I/Metrica%202%20-%20Item%20I.png)

Muestra la tasa de bytes recibidos.
```
rate(container_network_receive_bytes_total{instance="localhost:8080"}[5m])
```
![Acción Reboot](Item%20I/Metrica%203%20-%20Item%20I.png)

**3. Alerta Visual Threshold .**

![Acción Reboot](Item%20I/Threshold%20-%20Item%20I.png)

---

##  <span style="color:blue">Item II - Métricas Personalizadas<span>

Para demostrar la capacidad de instrumentar aplicaciones y generar métricas de negocio personalizadas, se utilizó un simulador de gestión hospitalaria en Python (`Item II/Case-3-Mod.py`).

A diferencia del monitoreo de infraestructura (Item I), aquí se utilizó el modelo **Push**. El script genera datos y los envía a un **Prometheus Pushgateway**, desde donde Prometheus recoge las métricas.

**A. Distribución de Tiempos de Espera (Histogram):**
Permite visualizar no solo el promedio, sino la distribución de la demora en urgencias (percentiles).
```python
# Definición del Histograma con buckets personalizados
registry.hospital_er_wait_time_minutes_histogram = Histogram(
    "hospital_er_wait_time_minutes_histogram",
    "ER wait time minutes distribution",
    buckets=[5, 10, 20, 30, 45, 60, 120, float('inf')],
    registry=registry
)

# Simulación de datos
registry.hospital_er_wait_time_minutes_histogram.observe(random.uniform(5, 120))
```
**B. Inventario de Recursos (Gauge): Métrica volátil que puede subir o bajar, utilizada para medir suministros médicos.**
```
registry.hospital_med_supplies_remaining_gauge = Gauge(
    "hospital_med_supplies_remaining_gauge", 
    "Medical supplies remaining (units)", 
    ["supply_type"], 
    registry=registry
)
```
**Dashboard - Personalizado.png**

![Acción Reboot](Item%20II/Dashboard%20-%20Personalizado.png)

---

##  Item III - Monitoreo con AWS CloudWatch

### 1. Dashboard de Infraestructura
Se diseñó manualmente un panel de control en la consola de AWS para visualizar métricas críticas. Posteriormente, se exportó la definición del dashboard (`Item III/dashboard.json`) para fines de respaldo y versionamiento.

El dashboard incluye:
* **CPU Utilization:** Visualización tipo "Gauge" para lectura rápida de carga.
* **Network In/Out:** Gráfico de series de tiempo para correlacionar tráfico.
* **EBS Write Bytes:** Gráfico de barras para monitorear la intensidad de escritura en disco.

![Dashboard CloudWatch](Item%20III/Dashboard%20Metricas%20-%20CloudWatch.png)

### 2. Automatización y Alarmas
Se configuró una alarma llamada `AlarmaNetwork` para detectar anomalías de tráfico ej: posible ataque DDoS o error de aplicación.

* **Condición:** `NetworkPacketsIn > 40000` en un periodo de 5 minutos.
* **Acción de Notificación:** Envío de alerta al tópico SNS.
* **Acción de Remediación:** **Reinicio automático de la instancia EC2**. Esta configuración permite recuperar el servicio automáticamente sin intervención humana ante un bloqueo por saturación de red.

**Evidencia de Configuración:**
*Configuración del umbral y acción de reinicio:*
![Acción Reboot](Item%20III/Acción-2.png)

*Alarma creada exitosamente:*
![Alarma Estado](Item%20III/Alarma-5.png)

*Notificación por correo:*
![Alarma Notificación](Item%20III/Notificación-Correo.png)

---

##  Item IV - Observabilidad de Costos

Se implementó un sistema de alertas de facturación utilizando métricas nativas de **AWS CloudWatch Billing**.

### 1. Configuración de la Alerta
Se configuró una alarma proactiva sobre la métrica `EstimatedCharges`.

**Detalles de la configuración:**
* **Métrica:** `EstimatedCharges` (Namespace: AWS/Billing).
* **Condición:** Se activa si el costo estimado supera los **150 USD** en un periodo de 6 horas.
* **Acción:** Envío de notificación vía SNS.

### 2. Integración con la metodología FinOps
Esta implementación cubre el pilar de **"Informar"** y **"Operar"** de FinOps.

1.  **Visibilidad en Tiempo Real:** Permite al equipo de ingeniería ver el impacto económico de sus despliegues directamente en el mismo dashboard donde ven el rendimiento de CPU/Memoria.
2.  **Detección de Anomalías:** La alarma actúa como un Cortacircuitos. Si existe un error en los  servidores o un exceso de uso, la métrica de costo subirá rápidamente, disparando la alerta y permitiendo detener el problema en cuestión de horas, no semanas.
3.  **Cultura de Costos:** Al integrar métricas de dinero junto a métricas técnicas, se fomenta que el costo sea considerado un requisito no funcional más de la arquitectura.

**Evidencia de Configuración:**

*Vista previa de la métrica de Costo Estimado:*
![Alarma Costos](Item%20IV/Alarma-Costos.png)

*Configuración del umbral y acción de notificación:*
![Condiciones Alarma](Item%20IV/Condición-de-Alarma.png)
