import requests
import json
from pythonosc import osc_server
from pythonosc.dispatcher import Dispatcher

flask_port = "5000"
flask_url = "http://127.0.0.1:%s/osc" % flask_port


def eos_out(addr, *args):
    """Handle Eos OSC messages and send them to Flask"""
    global flask_url

    headers = {
        'Content-type': 'application/json',
        'Accept': 'application/json'
    }

    # Format the message into appropriate JSON
    osc_json = {"address": addr, "args": json.dumps(args)}

    requests.post(flask_url, json=osc_json)

    return (osc_json["address"], osc_json["args"])


def start_osc_server():
    """Start the OSC server to handle incoming OSC from the console."""
    dispatcher = Dispatcher()
    dispatcher.map("/eos/out/*", eos_out)

    server = osc_server.ThreadingOSCUDPServer(
        ("127.0.0.1", 5011), dispatcher)

    return server


if __name__ == "__main__":
    osc_listener = start_osc_server()
    osc_listener.serve_forever()