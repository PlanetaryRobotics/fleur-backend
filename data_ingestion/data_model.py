# All points in a measurement MUST have the same set of fields and unique timestamps.
# Therefore, we cannot have channel name as field_key because one module can have multiple
# channels. The issue that it brings here is that we cannot have more than one
# channel with the same timestamp.
message_structure = {
    "asset": "mission_name",
    "data": {
        "module_name_measurement": {
            "timestamp": {
                "channel_name": "value"
            }
        }
    }
}

example_message = {
    "asset": "iris",
    "data": {
        "WatchdogHeartbeatTvac": {
            "123445567": {
                "AdcTempKelvin": 273.15
            }
        }
    }
}
