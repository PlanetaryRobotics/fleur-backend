from fastapi import FastAPI, HTTPException, Request
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
from pydantic import BaseModel

import uvicorn
import os

app = FastAPI()

influx_url = "http://mission_data:8086"
token = os.getenv('DOCKER_INFLUXDB_INIT_ADMIN_TOKEN')
org = os.getenv('DOCKER_INFLUXDB_INIT_ORG')
client = InfluxDBClient(url=influx_url, token=token)
write_api = client.write_api(write_options=SYNCHRONOUS)

class AlertRequest(BaseModel, extra='allow'):
    _check_id: str
    _check_name: str
    _level: str
    _measurement: str
    _message: str
    _notification_endpoint_id: str
    _notification_endpoint_name: str
    _notification_rule_id: str
    _notification_rule_name: str
    _source_measurement: str
    _source_timestamp: int
    _start: str
    _status_timestamp: int
    _stop: str
    _time: str
    _type: str
    _version: int

@app.post('/alert')
async def receive_alert(request: AlertRequest):
    try:
        data = request.dict()

        point = Point(data["_check_name"]) \
            .field(data["_notification_rule_name"], data["_message"]) \
            .time(data["_start"], WritePrecision.S) \
            .tag("measurement_name", data["_source_measurement"]) \
            .tag("value", data[data["_source_measurement"]])
        
        write_api.write("mission_alerts", org, point)
    except Exception as e:
        return {'Error': e}
    
    return 'OK'
        
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
