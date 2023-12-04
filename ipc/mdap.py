import json
import socket
from datetime import datetime
from typing import cast

import IrisBackendv3 as IB3
import IrisBackendv3.ipc as ipc
from IrisBackendv3.codec.payload import TelemetryPayload, EventPayload
from IrisBackendv3.ipc.messages import DownlinkedPayloadsMessage

IB3.init_from_latest()

app = ipc.IpcAppHelper("FleurDLPayloadListener")
app.setLogLevel('VERBOSE')

manager = ipc.IpcAppManagerSync(socket_specs={
    'sub': ipc.SocketSpec(
        sock_type=ipc.SocketType.SUBSCRIBER,
        port=ipc.Port.TRANSCEIVER_SUB,
        topics=[ipc.Topic.DL_PAYLOADS]
    )
})


def connect_to_telemetry_server(address: tuple) -> socket.socket:
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect(address)
    print("Connection with the telemetry server established successfully.")
    return client_socket


def telem_to_message(data_to_send, payloads):
    for telemetry in payloads[TelemetryPayload]:
        telemetry = cast(TelemetryPayload, telemetry)

        populate_data_to_send(telemetry.module.name, telemetry.channel.name,
                              telemetry.data, data_to_send)

        # TODO: The if condition below is solely for local testing purposes. Remove it later.
        if telemetry.module.name == "WatchdogHeartbeatTvac":
            # Convert the temperature from Kelvin to Celsius.
            temperature = telemetry.data - 273.15
            app.logger.notice(f"BATTERY TEMP IS: {temperature}ºC")

            timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
            if "WatchdogHeartbeatTvac" in data_to_send:
                if "AdcTempKelvin" in data_to_send["WatchdogHeartbeatTvac"]["timestamp"]:
                    data_to_send["WatchdogHeartbeatTvac"][timestamp]["AdcTempKelvin"] = temperature
            else:
                data_to_send["data"]["WatchdogHeartbeatTvac"] = {
                    timestamp: {
                        "AdcTempKelvin": temperature
                    }
                }

    return data_to_send


def events_to_message(data_to_send, payloads):
    for event in payloads[EventPayload]:
        event = cast(EventPayload, event)
        populate_data_to_send(event.module.name, event.event.name, event.formatted_string, data_to_send)

    return data_to_send


def populate_data_to_send(key, channel, data, data_to_send):
    # Get the current time with microsecond precision
    current_time = datetime.utcnow()
    # Convert datetime to string with a specific format
    timestamp = current_time.strftime("%Y-%m-%d %H:%M:%S")

    if key in data_to_send["data"]:
        # module exists
        if timestamp in data_to_send["data"][key]:
            # timestamp exists, update or add the channel and value pair
            data_to_send["data"][key][timestamp][channel] = data
        else:
            # timestamp doesn't exist, add it
            data_to_send["data"][key][timestamp] = {
                channel: data
            }
    else:
        # module doesn't exist, create one
        data_to_send["data"][key] = {
            timestamp: {
                channel: data
            }
        }


def process_ipc_payload(ipc_payload):
    try:
        msg = ipc.guard_msg(ipc_payload.message, DownlinkedPayloadsMessage)
        payloads = msg.content.payloads
    except Exception as e:
        app.logger.error(
            f"Failed to decode IPC message `{msg}` "
            f"of `{ipc_payload=}` b/c: `{e}`."
        )
        return None

    data_to_send = {
        "asset": "iris",
        "data": {}
    }

    data_to_send = telem_to_message(data_to_send, payloads)
    data_to_send = events_to_message(data_to_send, payloads)

    return data_to_send


def send_data_to_backend(sock, data):
    json_data = json.dumps(data)
    sock.send(json_data.encode('utf-8'))


def main():
    server_address = ('127.0.0.1', 8070)
    client_socket = connect_to_telemetry_server(server_address)

    try:
        while True:
            ipc_payload = manager.read('sub')
            data_to_send = process_ipc_payload(ipc_payload)

            if data_to_send:
                print(data_to_send)
                send_data_to_backend(client_socket, data_to_send)

    except KeyboardInterrupt:
        print('Closing...')
        client_socket.close()


if __name__ == "__main__":
    main()
