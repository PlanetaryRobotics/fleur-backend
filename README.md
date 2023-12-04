# FLEUR_Backend

## To Run:
### 1. Creating a .env File

To configure your Docker container with the required environment variables, create a `.env` file. This file will be used to set up the initial configuration for InfluxDB. Below are the environment variables that you can include in your `.env` file:

- `DOCKER_INFLUXDB_INIT_MODE`: Set this to `setup` to indicate that you want to initialize InfluxDB.

- `DOCKER_INFLUXDB_INIT_USERNAME`: Specify the admin username for InfluxDB to login to the UI.

- `DOCKER_INFLUXDB_INIT_PASSWORD`: Set the password for the admin user.

- `DOCKER_INFLUXDB_INIT_ORG`: Define the organization name.

- `DOCKER_INFLUXDB_INIT_BUCKET`: Specify the initial bucket for your InfluxDB setup.

- `DOCKER_INFLUXDB_INIT_ADMIN_TOKEN`: Set the admin token for InfluxDB. 

### 2. Spin up services

```
docker compose up
```

### 3. Run GDS IPC app

Run the mdap.py ipc app under ipc/ in this repository in the IrisBackend

## How to Use

### InfluxDB Management Portal

[Portal Link](http://localhost:8086/)

- username: `DOCKER_INFLUXDB_INIT_USERNAME`
- password: `DOCKER_INFLUXDB_INIT_PASSWORD`

### Grafana Dashboard

[Grafana Link](http://localhost:3000/)

- username: `admin`
- initial password: `admin`


## Data Model

The message structure has been defined while keeping the concept of Point in mind. Point is a data entry in influx db that contains a unique timestamp, measurement, fields, values, and tags. This structure allows easy constructing a point object from the raw telemetry data fetched from the DOWNLINK topic in GDS.

All points in a measurement MUST have the same set of fields and unique timestamps. Therefore, we cannot have the channel name as field_key because one module can have multiple channels. The issue that it brings here is that we cannot have more than one channel with the same timestamp.

```
message_structure = {
    "asset": "mission_name",
    "data": {
        "module_name_measurement": {
            "timestamp": {
                "field1": "channel_name",
                "field2": "value"
            }
        }
    }
}

example_message = {
    "asset": "iris",
    "data": {
        "WatchdogHeartbeatTvac": {
            "123445567": {
                "channel": "AdcTempKelvin",
                "value": 273.15
            }
        }
    }
}
