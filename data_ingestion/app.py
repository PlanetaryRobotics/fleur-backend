from datetime import datetime

from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS

import os
import random
import time

token = os.getenv('DOCKER_INFLUXDB_INIT_ADMIN_TOKEN')
org = os.getenv('DOCKER_INFLUXDB_INIT_ORG')
bucket = os.getenv('DOCKER_INFLUXDB_INIT_BUCKET')

client = InfluxDBClient(url="http://mission_data:8086", token=token)
write_api = client.write_api(write_options=SYNCHRONOUS)

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
    generate_temperature_data()
