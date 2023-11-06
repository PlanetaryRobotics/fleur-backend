import socket
import json
from typing import cast

import IrisBackendv3 as IB3
import IrisBackendv3.ipc as ipc
from IrisBackendv3.codec.payload import TelemetryPayload
from IrisBackendv3.ipc.messages import DownlinkedPayloadsMessage

# Define the server address and port (must match the values used in telemetry server)
server_address = ('127.0.0.1', 8070)

# Create a socket
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Connect to the server
client_socket.connect(server_address)
print("Connection with the server established successfully.")


IB3.init_from_latest()

app = ipc.IpcAppHelper("FleurDLPayloadListener")
manager = ipc.IpcAppManagerSync(socket_specs={
    'sub': ipc.SocketSpec(
        sock_type=ipc.SocketType.SUBSCRIBER,
        port=ipc.Port.TRANSCEIVER_SUB,
        topics=[ipc.Topic.DL_PAYLOADS]
    )
})

if __name__ == "__main__":
    app.setLogLevel('VERBOSE')

    telemetryCounter = dict()
    eventCounter = dict()

    # while True:
    for _ in range(500):  # read 50 packets worth of data then stop
        ipc_payload = manager.read('sub')
        try:
            msg = ipc.guard_msg(ipc_payload.message,
                                DownlinkedPayloadsMessage)
            payloads = msg.content.payloads
        except Exception as e:
            app.logger.error(
                f"Failed to decode IPC message `{msg}` "
                f"of `{ipc_payload=}` b/c: `{e}`."
            )

        # Print out all Telemetry we received:
        data_to_send = dict()
        for telemetry in payloads[TelemetryPayload]:
            telemetry = cast(TelemetryPayload, telemetry)
            data_to_send[f"{telemetry.module.name}-{telemetry.channel.name}"] = telemetry.data

            # Fish out a special telemetry channel we care about:
            if (telemetry.module.name, telemetry.channel.name) == ('WatchdogHeartbeatTvac', 'AdcTempKelvin'):
                app.logger.notice(f"BATTERY TEMP IS: {telemetry.data - 273.15}ºC")
                data_to_send["TempC"] = telemetry.data - 273.15

            else:
                app.logger.verbose(f"GOT: {telemetry}")

        json_data = json.dumps(data_to_send)
        # Send the telemetry data to FLEUR backend server.
        client_socket.send(json_data.encode('utf-8'))

            

# Clean up
print('closing')
client_socket.close()
