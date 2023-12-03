from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
from datetime import datetime
from pydantic import BaseModel

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
        return self.client_socket.recv(8192)

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
        self.client = InfluxDBClient(url="http://mission_data:8086", token=self.token)
        self.write_api = self.client.write_api(write_options=SYNCHRONOUS)

    def send_points(self, points_by_bucket):
        for bucket in points_by_bucket:
            self.write_api.write(bucket, self.org, points_by_bucket[bucket])

    def to_points(self, message):

        bucket_name = message["asset"]
        data = message["data"]

        points_by_bucket = dict().setdefault(bucket_name, [])

        for module_name, dic in data:
            for timestamp, fields in dic.items():
                # Creating a Point object with module_name as measurement
                point = Point(module_name).time(timestamp, WritePrecision.S)
                # Adding channel name as field key and data as value to the point
                for channel, data in fields.items():
                    point.field(channel, data)

                points_by_bucket[bucket_name].append(point)

        return points_by_bucket

    def send_points_from_data(self, data):
        points_by_bucket = self.to_points(data)
        self.send_points(points_by_bucket)


class IngestionServer:
    def __init__(self):
        self.mission_db_client = MissionDB()
        self.client_conn = ClientConnection('0.0.0.0', 8070)

    def start_server(self):
        try:
            while True:
                # Receive telemetry data from the client
                telemetry_data = self.client_conn.get_next_json_request()

                # Data validation
                validated_telem_data = TelemetryData(**telemetry_data)

                #print validation result
                print(validated_telem_data.json())

                self.mission_db_client.send_points_from_data(validated_telem_data)

        except KeyboardInterrupt:
            print("Client terminated.")

        # Clean up
        client_socket.close()
        server_socket.close()


class TelemetryData(BaseModel):
    asset: str
    data: dict[]


if __name__ == '__main__':
    server = IngestionServer()
    server.start_server()
