from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
from datetime import datetime

import socket
import os
import time
import json


class ClientConnection:
    def __init__(self, url, port):
        # Define the server address and port
        self.server_address = (url, port)

        # Create a socket
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Bind the socket to the address and port
        self.server_socket.bind(self.server_address)

        # Listen for incoming connections
        self.server_socket.listen(1)

        print(f"Waiting for a connection on {self.server_address}")

        # Accept a connection
        self.wait_for_connection()

    def wait_for_connection(self):
        # Accept a connection when a client connects
        self.client_socket, self.client_address = self.server_socket.accept()
        print(f"Accepted connection from {self.client_address}")

    def get_next_request(self):
        return self.client_socket.recv(4096)

    def get_next_json_request(self):
        while True:
            client_request = self.get_next_request()
            if not client_request:
                self.client_socket.close()
                self.wait_for_connection()
                continue
            try:
                received_data = json.loads(client_request)
                return received_data
            except Exception as e:
                print("Error decoding client request")
                print(e, client_request)


class MissionDB:
    def __init__(self):
        self.token = os.getenv('DOCKER_INFLUXDB_INIT_ADMIN_TOKEN')
        self.org = os.getenv('DOCKER_INFLUXDB_INIT_ORG')
        self.bucket = os.getenv('DOCKER_INFLUXDB_INIT_BUCKET')
        self.client = InfluxDBClient(url="http://mission_data:8086", token=self.token)
        self.write_api = self.client.write_api(write_options=SYNCHRONOUS)

    def send_points(self, points):
        self.write_api.write(self.bucket, self.org, points)

    def to_points(self, data_dict):
        points = []
        for metric in data_dict:
            metric_name = metric.split("-")
            table, field = metric_name[0], metric_name[-1]
            point = Point(table) \
                .field(field, data_dict[metric]['value']) \
                .time(data_dict[metric]['timestamp'], WritePrecision.S)
            points.append(point)
        return points

    def send_points_from_data(self, data):
        points = self.to_points(data)
        self.send_points(points)


class IngestionServer:
    def __init__(self):
        self.mission_db_client = MissionDB()
        self.client_conn = ClientConnection('0.0.0.0', 8070)

    def start_server(self):
        try:
            while True:
                # Receive telemetry data from the client
                telemetry_data = self.client_conn.get_next_json_request()

                self.mission_db_client.send_points_from_data(telemetry_data)
        except KeyboardInterrupt:
            print("Client terminated.")

        # Clean up
        client_socket.close()
        server_socket.close()


if __name__ == '__main__':
    server = IngestionServer()
    server.start_server()
