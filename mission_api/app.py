from fastapi import FastAPI, HTTPException, Request
from influxdb_client import InfluxDBClient

import uvicorn
import os

app = FastAPI()

influx_url = "http://mission_data:8086"
token = os.getenv('DOCKER_INFLUXDB_INIT_ADMIN_TOKEN')
org = os.getenv('DOCKER_INFLUXDB_INIT_ORG')
client = InfluxDBClient(url=influx_url, token=token)

@app.post('/alert')
async def receive_alert(request: Request):
    data = await request.json()  # Get the JSON data from the request
    print(data)  # Print the data to the terminal
    return 'OK'
        
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
