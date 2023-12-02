#!/bin/bash

# Start InfluxDB
exec influxd &

# Wait for InfluxDB to start (you might need to customize this part)
sleep 60s

# Setup initial InfluxDB user 
echo "Setting up influx..."
influx setup -b "$DOCKER_INFLUXDB_INIT_BUCKET" -o "$DOCKER_INFLUXDB_INIT_ORG" -u "$DOCKER_INFLUXDB_INIT_USERNAME" -p "$DOCKER_INFLUXDB_INIT_PASSWORD" -t "$DOCKER_INFLUXDB_INIT_ADMIN_TOKEN" -f

# Apply the InfluxDB templates
echo "Applying templates..."
influx apply -f /templates --force true

tail -f /dev/null