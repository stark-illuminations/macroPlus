"""
OSC server functionality for MacroPlus. Starts a UDP server listening for incoming OSC messages,
    then sends them to the Flask /osc route.

Functions:
- eos_out(): Convert OSC messages to JSON and send them to Flask.
- start_osc_server(): Starts a UDP OSC server and returns it.


"""

import json
import requests
from pythonosc import osc_server
from pythonosc.dispatcher import Dispatcher


def eos_out(addr: str, *args: any):
    """
    Handle Eos OSC messages and send them to Flask

    :param str addr: The OSC address to send to Flask
    :param args: Any arguments sent as part of the OSC message
    """
    flask_port = "5000"
    flask_url = f"http://127.0.0.1:{flask_port}/osc"

    # Format the message into appropriate JSON
    osc_json = {"address": addr, "args": json.dumps(args)}
    print(osc_json)

    requests.post(flask_url, json=osc_json, timeout=10)

    return (osc_json["address"], osc_json["args"])


def start_osc_server():
    """Start the OSC server to handle incoming OSC from the console."""
    dispatcher = Dispatcher()
    dispatcher.map("/eos/out/*", eos_out)

    server = osc_server.ThreadingOSCUDPServer(
        ("127.0.0.1", 5011), dispatcher)

    return server


if __name__ == "__main__":
    # Start the OSC server and keep it running
    osc_listener = start_osc_server()
    osc_listener.serve_forever()
