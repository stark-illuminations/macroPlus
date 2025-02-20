from pythonosc import udp_client, osc_server
from pythonosc.dispatcher import Dispatcher
import osc
import variables
import uuid


def test_start_osc_client():
    """Test start_osc_client"""

    assert isinstance(osc.start_osc_client(["127.0.0.1", 8000]), udp_client.SimpleUDPClient)
    assert isinstance(osc.start_osc_client(["127.0.0.1", "8000"]), udp_client.SimpleUDPClient)
    assert isinstance(osc.start_osc_client(["127.0.0.2", 8000]), udp_client.SimpleUDPClient)
    assert not isinstance(osc.start_osc_client(["127.0.0.1"]), udp_client.SimpleUDPClient)
    assert not isinstance(osc.start_osc_client("127.0.0.1"), udp_client.SimpleUDPClient)


def test_process_osc():
    """Test that process_osc formats OSC correctly."""
    new_uuid = uuid.uuid4()
    # Without variables
    assert osc.process_osc(new_uuid, {"osc_addr": "/eos/ping", "osc_args": ["Test"]}) == ("/eos/ping", ["Test"])
    assert osc.process_osc(new_uuid, {"osc_addr": "eos/ping", "osc_args": ["Test"]}) == ("/eos/ping", ["Test"])
    assert osc.process_osc(new_uuid, {"osc_addr": "eos/ping/", "osc_args": ["Test"]}) == ("/eos/ping", ["Test"])
    assert osc.process_osc(new_uuid, {"osc_addr": "/eos/ping/", "osc_args": ["Test"]}) == ("/eos/ping", ["Test"])
    assert osc.process_osc(new_uuid, {"osc_addr": "/eos/ping", "osc_args": "Test"}) == ("/eos/ping", ["Test"])
    assert (osc.process_osc(new_uuid, {"osc_addr": "/eos/ping", "osc_args": ["Test", "Second Argument"]})
            == ("/eos/ping", ["Test", "Second Argument"]))

    # With variables
    internal_variables = [variables.InternalVar("#internal_0#", "ping")]
    user_variables = [variables.InternalVar("*user_0*", "ping")]
    dynamic_variables = [variables.InternalVar("%cue%", "ping")]
    test_variables = {"internal_variables": internal_variables, "user_variables": user_variables,
                      "dynamic_variables": dynamic_variables}
    arg_input = ["ping"]

    # Internal variables
    assert (osc.process_osc(new_uuid, {"osc_addr": "/eos/#internal_0#", "osc_args": "#internal_0#"},
                            test_variables, arg_input=arg_input) == ("/eos/ping", ["ping"]))
    assert (osc.process_osc(new_uuid, {"osc_addr": "/eos/#internal_1#", "osc_args": "#internal_0#"},
                            test_variables, arg_input=arg_input) == ("/eos/None", ["ping"]))
    assert (osc.process_osc(new_uuid, {"osc_addr": "/eos/#internal_0#", "osc_args": "#internal_1#"},
                            test_variables, arg_input=arg_input) == ("/eos/ping", ["None"]))
    assert (osc.process_osc(new_uuid, {"osc_addr": "/eos/#internal_1#", "osc_args": "#internal_1#"},
                            test_variables, arg_input=arg_input) == ("/eos/None", ["None"]))
    assert (osc.process_osc(new_uuid, {"osc_addr": "/eos/#internal_1#",
                                       "osc_args": ["#internal_1#", "#internal_0#"]},
                            test_variables, arg_input=arg_input) == ("/eos/None", ["None", "ping"]))

    # User variables
    assert (osc.process_osc(new_uuid, {"osc_addr": "/eos/*user_0*", "osc_args": "*user_0*"}, test_variables,
                            arg_input=arg_input) == ("/eos/ping", ["ping"]))
    assert (osc.process_osc(new_uuid, {"osc_addr": "/eos/*user_1*", "osc_args": "*user_0*"}, test_variables,
                            arg_input=arg_input) == ("/eos/None", ["ping"]))
    assert (osc.process_osc(new_uuid, {"osc_addr": "/eos/*user_0*", "osc_args": "*user_1*"}, test_variables,
                            arg_input=arg_input) == ("/eos/ping", ["None"]))
    assert (osc.process_osc(new_uuid, {"osc_addr": "/eos/*user_1*", "osc_args": "*user_1*"}, test_variables,
                            arg_input=arg_input) == ("/eos/None", ["None"]))
    assert (osc.process_osc(new_uuid, {"osc_addr": "/eos/*user_1*", "osc_args": ["*user_1*", "*user_0*"]},
                            test_variables, arg_input=arg_input) == ("/eos/None", ["None", "ping"]))

    # Dynamic variables
    assert (osc.process_osc(new_uuid, {"osc_addr": "/eos/%cue%", "osc_args": "%cue%"}, test_variables,
                            arg_input=arg_input) == ("/eos/ping", ["ping"]))
    assert (osc.process_osc(new_uuid, {"osc_addr": "/eos/%random%", "osc_args": "%cue%"}, test_variables,
                            arg_input=arg_input) == ("/eos/None", ["ping"]))
    assert (osc.process_osc(new_uuid, {"osc_addr": "/eos/%cue%", "osc_args": "%random%"}, test_variables,
                            arg_input=arg_input) == ("/eos/ping", ["None"]))
    assert (osc.process_osc(new_uuid, {"osc_addr": "/eos/%random%", "osc_args": "%random%"}, test_variables,
                            arg_input=arg_input) == ("/eos/None", ["None"]))
    assert (osc.process_osc(new_uuid, {"osc_addr": "/eos/%random%", "osc_args": ["%random%", "%cue%"]},
                            test_variables, arg_input=arg_input) == ("/eos/None", ["None", "ping"]))

    # Argument inputs
    assert (osc.process_osc(new_uuid, {"osc_addr": "/eos/@0@", "osc_args": "@0@"}, test_variables,
                            arg_input=arg_input) == ("/eos/ping", ["ping"]))
    assert (osc.process_osc(new_uuid, {"osc_addr": "/eos/@1@", "osc_args": "@0@"}, test_variables,
                            arg_input=arg_input) == ("/eos/None", ["ping"]))
    assert (osc.process_osc(new_uuid, {"osc_addr": "/eos/@0@", "osc_args": "@1@"}, test_variables,
                            arg_input=arg_input) == ("/eos/ping", ["None"]))
    assert (osc.process_osc(new_uuid, {"osc_addr": "/eos/@1@", "osc_args": "@1@"}, test_variables,
                            arg_input=arg_input) == ("/eos/None", ["None"]))
    assert (osc.process_osc(new_uuid, {"osc_addr": "/eos/@1@", "osc_args": ["@1@", "@0@"]},
                            test_variables, arg_input=arg_input) == ("/eos/None", ["None", "ping"]))
