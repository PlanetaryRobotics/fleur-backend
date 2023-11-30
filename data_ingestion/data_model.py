import time

payload = {
    "component": "temperature",     # component: measurement
    "fields": {
        "value": "273.15K",         # value: field
        "severity": "high"
    },
    "tags": {
        "module": "some_module",
        "channel": "some_channel",
        "event": "some_event",
    },
    "timestamp": time.localtime()
}

payloads = [payload]

message = {
    "asset": "telemetry",           # asset: bucket_name
    "data": payloads
}

