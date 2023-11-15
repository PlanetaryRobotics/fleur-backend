import socket
import json
from typing import cast
import IrisBackendv3 as IB3
import IrisBackendv3.ipc as ipc
from IrisBackendv3.codec.payload import TelemetryPayload
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

    data_to_send = {}
    for telemetry in payloads[TelemetryPayload]:
        telemetry = cast(TelemetryPayload, telemetry)
        data_to_send[f"{telemetry.module.name}-{telemetry.channel.name}"] = {
            "value": telemetry.data,
            "timestamp": telemetry.timestamp
        }

        if (telemetry.module.name, telemetry.channel.name) == ('WatchdogHeartbeatTvac', 'AdcTempKelvin'):
            app.logger.notice(f"BATTERY TEMP IS: {telemetry.data - 273.15}ºC")
            data_to_send["TempC"] = {
                "value": telemetry.data - 273.15,
                "timestamp": telemetry.timestamp
            }

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
