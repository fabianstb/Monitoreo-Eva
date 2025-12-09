# EXAMEN PRÁCTICO FINAL — MONITOREO Y OBSERVABILIDAD

**Autor:** Fabian Santibañez S.  
**Fecha:** 09/12/2025  
**Curso:** Monitoreo y Observabilidad  

---

## 📋 Descripción
Implementar un entorno de observabilidad integral basado en Prometheus Cloud, Grafana Cloud y AWS CloudWatch,
demostrando el monitoreo de infraestructura, aplicación, métricas personalizadas y costos, junto con la documentación del proceso.

## 2. Herramientas Utilizadas

* **Prometheus Cloud:** Almacenamiento y consulta de series temporales.
* **Grafana Cloud:** Visualización unificada y alertas.
* **AWS CloudWatch:** Monitoreo nativo de servicios AWS.
* **Python:** Lenguaje utilizado para la instrumentación de métricas personalizadas (`prometheus_client`).
* **Node Exporter:** Agente de recolección de métricas de sistema operativo.

---

## 🚀 Item I - Prometheus Cloud + Grafana Cloud para EC2
En esta sección se implementó la recolección de métricas de la instancia EC2 y los contenedores que ejecutan la aplicación. Se utilizó **Grafana Alloy** como agente colector para enviar los datos a **Grafana Cloud**.

### 1. Configuración del Agente (Grafana Alloy)
Se configuró el archivo `config.alloy` para realizar el *scraping* de métricas del sistema (Linux) y de los contenedores Docker expuestos en el puerto 8080.

**Archivo:** `Item I/config.alloy`
```alloy
// Envío de métricas a Grafana Cloud
prometheus.remote_write "metrics_service" {
    endpoint {
        url = "[https://prometheus-prod-40-prod-sa-east-1.grafana.net/api/prom/push](https://prometheus-prod-40-prod-sa-east-1.grafana.net/api/prom/push)"
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

// Scrape de métricas de contenedores (cAdvisor/Docker)
prometheus.scrape "extra_exporters" {
  targets = [{ __address__ = "localhost:8080" }]
  scrape_interval = "15s"
  forward_to = [prometheus.remote_write.metrics_service.receiver]
}

```
---

## 🚀 Item II - Métricas Personalizadas

---

## 🚀 Item III - Monitoreo con AWS CloudWatch

---

## 🚀 Item IV - Observabilidad de Costos


