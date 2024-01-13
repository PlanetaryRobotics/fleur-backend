import json
import socket
from datetime import datetime
from typing import cast

import argparse

import IrisBackendv3 as IB3
import IrisBackendv3.ipc as ipc
from IrisBackendv3.codec.payload import TelemetryPayload, EventPayload
from IrisBackendv3.ipc.messages import DownlinkedPayloadsMessage
from IrisBackendv3.logs import VALID_LOG_LEVELS

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

parser = argparse.ArgumentParser(description=(
    'FLEUR-IRIS GDS — MDAP Connection for Data Ingest — CLI'
))

def get_opts(
    default_log_level: str = 'VERBOSE'
):
    parser.add_argument('-i', '--fleur-data-ip', type=str, default="0.0.0.0")
    parser.add_argument('-p', '--fleur-data-port', type=int, default=8070)

    def str_to_log_level(s):
        if isinstance(s, str) and s.upper() in VALID_LOG_LEVELS:
            return s.upper()
        else:
            raise argparse.ArgumentTypeError(
                f'Valid log level expected. Log levels are: {VALID_LOG_LEVELS}'
            )

    parser.add_argument('--log-level', type=str_to_log_level, default=default_log_level,
                        help=('Logging level to be used (i.e. how annoying the logging '
                              'printouts should be). Only logs with importance greater '
                              'than or equal to the specified logging level are '
                              f'displayed. Valid logging levels are: {VALID_LOG_LEVELS}'))

    return parser.parse_args()


def connect_to_telemetry_server(address: tuple) -> socket.socket:
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect(address)
    print("Connection with the telemetry server established successfully.")
    return client_socket


def test_telemetry(data_to_send, temperature, timestamp_dt: datetime | None = None):
    # Convert the temperature from Kelvin to Celsius.
    value = temperature - 273.15
    app.logger.notice(f"BATTERY TEMP IS: {value}ºC")

    if timestamp_dt is None:
        timestamp_dt = datetime.utcnow()

    timestamp = timestamp_dt.strftime("%Y-%m-%d %H:%M:%S")
    metrics = data_to_send["data"]
    metric_data = metrics.get("WatchdogHeartbeatTvac", {})
    timestamp_data = metric_data.get(timestamp, {})

    # Update or add the channel and value pair
    timestamp_data["AdcTempKelvin"] = value

    # Update the data_to_send dictionary
    metric_data[timestamp] = timestamp_data
    metrics["WatchdogHeartbeatTvac"] = metric_data


def telem_to_message(data_to_send, payloads):
    for telemetry in payloads[TelemetryPayload]:
        telemetry = cast(TelemetryPayload, telemetry)

        populate_data_to_send(telemetry.module.name, telemetry.channel.name,
                              telemetry.data, data_to_send,
                              timestamp_dt=telemetry.downlink_times.scet_est)

        # Testing against this particular module
        if telemetry.module.name == "WatchdogHeartbeatTvac" and telemetry.channel.name == "AdcTempKelvin":
            test_telemetry(data_to_send, telemetry.data,
                           timestamp_dt=telemetry.downlink_times.scet_est)

    return data_to_send


def events_to_message(data_to_send, payloads):
    for event in payloads[EventPayload]:
        event = cast(EventPayload, event)
        populate_data_to_send(
            event.module.name, event.event.name,
            event.formatted_string, data_to_send,
            timestamp_dt=event.downlink_times.scet_est)

    return data_to_send


def populate_data_to_send(metric, channel, value, data_to_send,
                          timestamp_dt: datetime | None = None):
    if timestamp_dt is None:
        # Get the current time with microsecond precision
        timestamp_dt = datetime.utcnow()

    # Convert datetime to string with a specific format
    timestamp = timestamp_dt.strftime("%Y-%m-%d %H:%M:%S")

    metrics = data_to_send["data"]

    metric_data = metrics.get(metric, {})
    timestamp_data = metric_data.get(timestamp, {})

    # Update or add the channel and value pair
    timestamp_data[channel] = value

    # Update the data_to_send dictionary
    metric_data[timestamp] = timestamp_data
    metrics[metric] = metric_data


def process_ipc_payload(ipc_payload):
    data_to_send = {
        "asset": "iris",
        "data": {}
    }
    try:
        msg = ipc.guard_msg(ipc_payload.message, DownlinkedPayloadsMessage)
        payloads = msg.content.payloads

        data_to_send = telem_to_message(data_to_send, payloads)
        data_to_send = events_to_message(data_to_send, payloads)

    except Exception as e:
        app.logger.error(
            f"Failed to decode IPC message `{ipc_payload.message}` "
            f"of `{ipc_payload=}` b/c: `{e}`."
        )
        return None

    return data_to_send


def send_data_to_backend(sock, data):
    # Display some statistics:
    # Count number of modules:
    modules = [*data['data'].keys()]
    n_modules = len(modules)
    # Count total number of telem points:
    n_telem_pts = sum(
        len([*entries_at_time_pt.keys()])
        for module in data['data'].values()
        for entries_at_time_pt in module.values()
    )
    # Count number of distinct telem channels:
    n_telem_channels = len(set(
        m_name + '_' + channel_name
        for m_name, module in data['data'].items()
        for entries_at_time_pt in module.values()
        for channel_name in entries_at_time_pt.keys()
    ))
    app.logger.info(
        f"Sending {n_telem_pts} entries "
        f"for {n_telem_channels} channels "
        f"across {n_modules} modules ({', '.join(modules)}) . . ."
    )

    # Transmit data:
    json_data = json.dumps(data)
    sock.send(json_data.encode('utf-8'))


def main(opts):
    app.setLogLevel(opts.log_level)
    server_address = (opts.fleur_data_ip, opts.fleur_data_port)
    client_socket = connect_to_telemetry_server(server_address)

    try:
        while True:
            ipc_payload = manager.read('sub')
            data_to_send = process_ipc_payload(ipc_payload)

            if data_to_send:
                send_data_to_backend(client_socket, data_to_send)

    except Exception as e:
        app.logger.critical(f"Exception Occurred: {e}")
        app.logger.critical('Closing...')
        client_socket.close()


if __name__ == "__main__":
    opts = get_opts()
    main(opts)
