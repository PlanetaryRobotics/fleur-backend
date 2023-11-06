from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
from datetime import datetime

import socket
import os
import random
import time
import json

# Define the server address and port
server_address = ('0.0.0.0', 8070)

# Create a socket
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Bind the socket to the address and port
server_socket.bind(server_address)

# Listen for incoming connections
server_socket.listen(1)

print(f"Waiting for a connection on {server_address}")

# Accept a connection
client_socket, client_address = server_socket.accept()
print(f"Accepted connection from {client_address}")

token = os.getenv('DOCKER_INFLUXDB_INIT_ADMIN_TOKEN')
org = os.getenv('DOCKER_INFLUXDB_INIT_ORG')
bucket = os.getenv('DOCKER_INFLUXDB_INIT_BUCKET')

client = InfluxDBClient(url="http://mission_data:8086", token=token)
write_api = client.write_api(write_options=SYNCHRONOUS)

def start_server():
	try:
		while True:
			# Receive telemetry data from the client
			telemetry_data = client_socket.recv(1024)
			if not telemetry_data:
				print('Not Found')
				continue

			json_data = client_socket.recv(1024).decode('utf-8')
			received_data = json.loads(json_data)
			
			print(f"Received telemetry data: {received_data.keys()}")
			point = Point("temps")\
				.field("celsius", received_data['TempC'])\
				.time(datetime.utcnow(), WritePrecision.NS)

			print(received_data['TempC'])
			write_api.write(bucket, org, point)
	except KeyboardInterrupt:
		print("Client terminated.")

	# Clean up
	print('closing')
	client_socket.close()
	server_socket.close()

def generate_temperature_data():
	while True:
		temperature = random.uniform(0.0, 100.0)

		point = Point("temps")\
			.field("celsius", temperature)\
			.time(datetime.utcnow(), WritePrecision.NS)

		print(temperature)
		write_api.write(bucket, org, point)
		time.sleep(5)

if __name__ == '__main__':
	start_server()
    # generate_temperature_data()
