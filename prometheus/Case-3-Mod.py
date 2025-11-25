#!/usr/bin/env python3
import time
import random
import argparse
from prometheus_client import CollectorRegistry, Gauge, Counter, Histogram, pushadd_to_gateway

def build_registry(registry):
    # --- MÉTRICAS ORIGINALES ---
    
    # 1. Capacidad e Instalaciones (Gauges)
    registry.hospital_beds_available_gauge = Gauge(
        "hospital_beds_available_gauge", "Beds available by ward", ["ward"], registry=registry
    )
    registry.hospital_waiting_room_patients_gauge = Gauge(
        "hospital_waiting_room_patients_gauge", "Patients waiting in ER", registry=registry
    )
    registry.hospital_icu_occupancy_percent_gauge = Gauge(
        "hospital_icu_occupancy_percent_gauge", "ICU occupancy percent", registry=registry
    )
    registry.hospital_ventilators_in_use_gauge = Gauge(
        "hospital_ventilators_in_use_gauge", "Ventilators in use", registry=registry
    )
    registry.hospital_isolation_rooms_available_gauge = Gauge(
        "hospital_isolation_rooms_available_gauge", "Isolation rooms available", registry=registry
    )
    registry.hospital_staff_on_duty_gauge = Gauge(
        "hospital_staff_on_duty_gauge", "Staff on duty count", registry=registry
    )

    # 2. Flujo de Pacientes (Counters & Histograms)
    registry.hospital_appointments_completed_total = Counter(
        "hospital_appointments_completed_total", "Appointments completed", ["clinic"], registry=registry
    )
    registry.hospital_admissions_total = Counter(
        "hospital_admissions_total", "Admissions total", registry=registry
    )
    registry.hospital_discharges_total = Counter(
        "hospital_discharges_total", "Discharges total", registry=registry
    )
    registry.hospital_icu_admissions_total = Counter(
        "hospital_icu_admissions_total", "ICU admissions total", registry=registry
    )
    registry.hospital_emergency_calls_total = Counter(
        "hospital_emergency_calls_total", "Emergency calls received", registry=registry
    )
    registry.hospital_er_wait_time_minutes_histogram = Histogram(
        "hospital_er_wait_time_minutes_histogram",
        "ER wait time minutes distribution",
        buckets=[5, 10, 20, 30, 45, 60, 120, float('inf')],
        registry=registry
    )

    # 3. Calidad y Seguridad (Counters & Histograms)
    registry.hospital_medication_errors_total = Counter(
        "hospital_medication_errors_total", "Medication errors", registry=registry
    )
    registry.hospital_patient_readmissions_total = Counter(
        "hospital_patient_readmissions_total", "Patient readmissions total (within 30 days)", registry=registry
    )
    registry.hospital_surgery_duration_minutes_histogram = Histogram(
        "hospital_surgery_duration_minutes_histogram", 
        "Surgery durations minutes distribution",
        buckets=[30, 60, 120, 240, 480, 600, float('inf')],
        registry=registry
    )
    registry.hospital_telemetry_errors_total = Counter(
        "hospital_telemetry_errors_total", "Telemetry/Monitoring errors", registry=registry
    )

    # 4. Logística y Recursos (Gauges)
    registry.hospital_med_supplies_remaining_gauge = Gauge(
        "hospital_med_supplies_remaining_gauge", "Medical supplies remaining (units)", ["supply_type"], registry=registry
    )
    registry.hospital_cleanliness_score_gauge = Gauge(
        "hospital_cleanliness_score_gauge", "Average daily cleanliness score", registry=registry
    )

    # --- NUEVAS MÉTRICAS ESTRATÉGICAS (Sección 5) ---
    
    # Métrica A: Tráfico de Ambulancias (Counter con labels)
    # Permite ver la tasa de llegada y si estamos rechazando pacientes (Diverted)
    registry.hospital_ambulance_traffic_total = Counter(
        "hospital_ambulance_traffic_total", 
        "Ambulance arrivals labeled by type and outcome", 
        ["type", "outcome"], # type: Trauma, Cardiac... outcome: Admitted, Diverted
        registry=registry
    )

    # Métrica B: Tiempos de Procesamiento de Laboratorio (Histogram)
    # Permite calcular percentiles de eficiencia diagnóstica
    registry.hospital_lab_processing_seconds = Histogram(
        "hospital_lab_processing_seconds",
        "Time taken to process lab samples",
        buckets=[300, 600, 1800, 3600, 7200, float('inf')], # 5min, 10min, 30min, 1h, 2h...
        registry=registry
    )

    # Métrica C: Costo Operativo Estimado (Counter)
    # Permite sumatorias financieras acumulativas
    registry.hospital_operating_cost_estimated_total = Counter(
        "hospital_operating_cost_estimated_total",
        "Estimated operating cost in USD",
        ["department"], # ICU, ER, Maintenance, Surgery
        registry=registry
    )

    return registry

def simulate_and_push(args):
    registry = CollectorRegistry()
    registry = build_registry(registry)

    wards = ["General A", "General B", "Pediatrics", "ICU", "Maternity"]
    clinics = ["Cardiology", "Neurology", "General Practice"]
    supplies = ["Masks", "Gloves", "Syringes"]
    
    # Listas para simulación de nuevas métricas
    amb_types = ["Trauma", "Cardiac", "Stroke", "General"]
    amb_outcomes = ["Admitted", "Admitted", "Admitted", "Diverted"] # 25% chance of diversion
    departments = ["ICU", "ER", "Surgery", "General Ward"]

    while True:
        # --- Simulación Existente ---
        for w in wards:
            capacity = random.randint(15, 50) if w != "ICU" else 20
            available = random.randint(0, int(capacity * random.uniform(0.1, 0.7)))
            registry.hospital_beds_available_gauge.labels(ward=w).set(available)
            if w == "ICU":
                occupancy_percent = 100 * (capacity - available) / capacity
                registry.hospital_icu_occupancy_percent_gauge.set(round(occupancy_percent, 2))

        registry.hospital_waiting_room_patients_gauge.set(random.randint(5, 50))
        registry.hospital_ventilators_in_use_gauge.set(random.randint(0, 30))
        registry.hospital_isolation_rooms_available_gauge.set(random.randint(0, 5))
        registry.hospital_staff_on_duty_gauge.set(random.randint(150, 400))
        
        registry.hospital_admissions_total.inc(random.randint(5, 20))
        registry.hospital_discharges_total.inc(random.randint(4, 18))
        registry.hospital_icu_admissions_total.inc(random.randint(0, 4))
        registry.hospital_emergency_calls_total.inc(random.randint(2, 10))
        
        for _ in range(random.randint(10, 30)):
            registry.hospital_er_wait_time_minutes_histogram.observe(random.uniform(5, 120))

        for c in clinics:
            registry.hospital_appointments_completed_total.labels(clinic=c).inc(random.randint(5, 30))

        if random.random() < 0.05:
            registry.hospital_medication_errors_total.inc()
        if random.random() < 0.03:
            registry.hospital_patient_readmissions_total.inc()
            
        registry.hospital_telemetry_errors_total.inc(random.randint(0, 5))
        
        for _ in range(random.randint(2, 8)):
            registry.hospital_surgery_duration_minutes_histogram.observe(random.uniform(30, 600))

        for s in supplies:
            registry.hospital_med_supplies_remaining_gauge.labels(supply_type=s).set(random.randint(100, 10000))

        registry.hospital_cleanliness_score_gauge.set(round(random.uniform(8.5, 9.9), 1))

        # --- SIMULACIÓN DE NUEVAS MÉTRICAS ESTRATÉGICAS ---

        # 1. Tráfico de Ambulancias
        # Simulamos entre 0 y 3 ambulancias llegando en este ciclo
        for _ in range(random.randint(0, 3)):
            t = random.choice(amb_types)
            # Si la ocupación de UCI es alta (>80%), más probabilidad de desvío (Diverted)
            if registry.hospital_icu_occupancy_percent_gauge._value.get() > 80:
                o = random.choice(["Admitted", "Diverted"])
            else:
                o = "Admitted"
            registry.hospital_ambulance_traffic_total.labels(type=t, outcome=o).inc()

        # 2. Eficiencia de Laboratorio
        # Simulamos el procesamiento de 5 a 15 muestras
        for _ in range(random.randint(5, 15)):
            # Tiempo aleatorio: a veces rápido (10 min), a veces lento (2 horas)
            processing_time = random.expovariate(1.0 / 1800) # Media de 30 mins (1800s)
            registry.hospital_lab_processing_seconds.observe(processing_time)

        # 3. Costo Operativo
        # Simulamos costos variables por departamento
        for dept in departments:
            # Costo base aleatorio + picos
            cost = random.randint(100, 5000) 
            registry.hospital_operating_cost_estimated_total.labels(department=dept).inc(cost)


        # --- Push al Pushgateway ---
        instance = args.instance or "hospital-sim-1"
        try:
            pushadd_to_gateway(
                args.pushgateway,
                job=args.job,
                registry=registry,
                grouping_key={"instance": instance}
            )
            print(f"Pushed metrics (incl. new strategic ones) to {args.pushgateway}...")
        except Exception as e:
            print(f"Error pushing to Pushgateway: {e}")

        time.sleep(args.interval)

def main():
    parser = argparse.ArgumentParser(description="Hospital metrics simulator (push to Pushgateway)")
    parser.add_argument("--pushgateway", default="http://localhost:9091", help="Pushgateway URL")
    parser.add_argument("--job", default="hospital_job", help="Pushgateway job name")
    parser.add_argument("--instance", default="hospital-sim-1", help="Instance label")
    parser.add_argument("--interval", type=int, default=5, help="Seconds between pushes")
    args = parser.parse_args()

    simulate_and_push(args)

if __name__ == "__main__":
    main()