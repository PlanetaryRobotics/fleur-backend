import prometheus_api_client
from flask import Flask, request

import time


# This will have the route to pushing data to FLEUR UI.

app = Flask(__name__)


@app.route('/alert', methods=['POST'])
def receive_alert():
    data = request.json  # Get the JSON data from the request
    print(data)  # Print the data to the terminal
    return 'OK'


def main():
    prometheus_url = "http://mission_data:9090"
    query = 'up'

    # Create a Prometheus API client
    prometheus_api = prometheus_api_client.PrometheusConnect(url=prometheus_url)

    # Query Prometheus for data
    result = prometheus_api.custom_query(query)

    print(f"Prometheus Query: {query}")
    for item in result:
        print(item['metric'], item['value'])


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)
