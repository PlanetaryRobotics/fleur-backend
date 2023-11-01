from prometheus_client import start_http_server, Gauge
import random
import time

temperature_gauge = Gauge('temperature_celsius', 'Current temperature in Celsius')

def generate_temperature_data():
    while True:
        # Simulate temperature data (replace this with your own data source)
        temperature = random.uniform(20.0, 45.0)
        temperature_gauge.set(temperature)
        time.sleep(5)

if __name__ == '__main__':
    # Start an HTTP server to expose the metrics
    start_http_server(8070)
    print("Exporter is running on :8070/metrics")

    generate_temperature_data()
