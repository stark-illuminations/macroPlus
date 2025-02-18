from pythonosc import udp_client, osc_server
from pythonosc.dispatcher import Dispatcher
import osc, variables


def test_start_osc_client():
    "Test start_osc_client"

    assert isinstance(osc.start_osc_client(["127.0.0.1", 8000]), udp_client.SimpleUDPClient)
    assert isinstance(osc.start_osc_client(["127.0.0.1", "8000"]), udp_client.SimpleUDPClient)
    assert isinstance(osc.start_osc_client(["127.0.0.2", 8000]), udp_client.SimpleUDPClient)
    assert not isinstance(osc.start_osc_client(["127.0.0.1"]), udp_client.SimpleUDPClient)
    assert not isinstance(osc.start_osc_client("127.0.0.1"), udp_client.SimpleUDPClient)


def test_process_osc():
    "Test that process_osc formats OSC correctly."

    # Without variables
    assert osc.process_osc("/eos/ping", ["Test"]) == ("/eos/ping", ["Test"])
    assert osc.process_osc("eos/ping", ["Test"]) == ("/eos/ping", ["Test"])
    assert osc.process_osc("eos/ping/", ["Test"]) == ("/eos/ping", ["Test"])
    assert osc.process_osc("/eos/ping/", ["Test"]) == ("/eos/ping", ["Test"])
    assert osc.process_osc("/eos/ping", "Test") == ("/eos/ping", ["Test"])
    assert osc.process_osc("/eos/ping", ["Test", "Second Argument"]) == ("/eos/ping", ["Test", "Second Argument"])

    # With variables
    internal_variables = [variables.InternalVar("#internal_0#", "ping")]
    user_variables = [variables.InternalVar("*user_0*", "ping")]
    dynamic_variables = [variables.InternalVar("%cue%", "ping")]
    arg_input = ["ping"]

    # Internal variables
    assert (osc.process_osc("/eos/#internal_0#", "#internal_0#", internal_variables=internal_variables,
                           user_variables=user_variables, dynamic_variables=dynamic_variables, arg_input=arg_input)
            == ("/eos/ping", ["ping"]))
    assert (osc.process_osc("/eos/#internal_1#", "#internal_0#", internal_variables=internal_variables,
                           user_variables=user_variables, dynamic_variables=dynamic_variables, arg_input=arg_input) ==
            ("/eos/None", ["ping"]))

    assert (osc.process_osc("/eos/#internal_0#", "#internal_1#", internal_variables=internal_variables,
                            user_variables=user_variables, dynamic_variables=dynamic_variables, arg_input=arg_input) ==
            ("/eos/ping", ["None"]))

    assert (osc.process_osc("/eos/#internal_1#", "#internal_1#", internal_variables=internal_variables,
                            user_variables=user_variables, dynamic_variables=dynamic_variables, arg_input=arg_input) ==
            ("/eos/None", ["None"]))

    assert (osc.process_osc("/eos/#internal_1#", ["#internal_1#", "#internal_0#"], internal_variables=internal_variables,
                            user_variables=user_variables, dynamic_variables=dynamic_variables, arg_input=arg_input) ==
            ("/eos/None", ["None", "ping"]))


    # User variables
    assert (osc.process_osc("/eos/*user_0*", "*user_0*", internal_variables=internal_variables,
                            user_variables=user_variables, dynamic_variables=dynamic_variables, arg_input=arg_input)
            == ("/eos/ping", ["ping"]))
    assert (osc.process_osc("/eos/*user_1*", "*user_0*", internal_variables=internal_variables,
                            user_variables=user_variables, dynamic_variables=dynamic_variables, arg_input=arg_input) ==
            ("/eos/None", ["ping"]))

    assert (osc.process_osc("/eos/*user_0*", "*user_1*", internal_variables=internal_variables,
                            user_variables=user_variables, dynamic_variables=dynamic_variables, arg_input=arg_input) ==
            ("/eos/ping", ["None"]))

    assert (osc.process_osc("/eos/*user_1*", "*user_1*", internal_variables=internal_variables,
                            user_variables=user_variables, dynamic_variables=dynamic_variables, arg_input=arg_input) ==
            ("/eos/None", ["None"]))

    assert (osc.process_osc("/eos/*user_1*", ["*user_1*", "*user_0*"],
                            internal_variables=internal_variables,
                            user_variables=user_variables, dynamic_variables=dynamic_variables, arg_input=arg_input) ==
            ("/eos/None", ["None", "ping"]))


    # Dynamic variables
    assert (osc.process_osc("/eos/%cue%", "%cue%", internal_variables=internal_variables,
                            user_variables=user_variables, dynamic_variables=dynamic_variables, arg_input=arg_input)
            == ("/eos/ping", ["ping"]))
    assert (osc.process_osc("/eos/%random%", "%cue%", internal_variables=internal_variables,
                            user_variables=user_variables, dynamic_variables=dynamic_variables, arg_input=arg_input) ==
            ("/eos/None", ["ping"]))

    assert (osc.process_osc("/eos/%cue%", "%random%", internal_variables=internal_variables,
                            user_variables=user_variables, dynamic_variables=dynamic_variables, arg_input=arg_input) ==
            ("/eos/ping", ["None"]))

    assert (osc.process_osc("/eos/%random%", "%random%", internal_variables=internal_variables,
                            user_variables=user_variables, dynamic_variables=dynamic_variables, arg_input=arg_input) ==
            ("/eos/None", ["None"]))

    assert (osc.process_osc("/eos/%random%", ["%random%", "%cue%"],
                            internal_variables=internal_variables,
                            user_variables=user_variables, dynamic_variables=dynamic_variables, arg_input=arg_input) ==
            ("/eos/None", ["None", "ping"]))


    # Argument inputs
    assert (osc.process_osc("/eos/@0@", "@0@", internal_variables=internal_variables,
                            user_variables=user_variables, dynamic_variables=dynamic_variables, arg_input=arg_input)
            == ("/eos/ping", ["ping"]))
    assert (osc.process_osc("/eos/@1@", "@0@", internal_variables=internal_variables,
                            user_variables=user_variables, dynamic_variables=dynamic_variables, arg_input=arg_input) ==
            ("/eos/None", ["ping"]))

    assert (osc.process_osc("/eos/@0@", "@1@", internal_variables=internal_variables,
                            user_variables=user_variables, dynamic_variables=dynamic_variables, arg_input=arg_input) ==
            ("/eos/ping", ["None"]))

    assert (osc.process_osc("/eos/@1@", "@1@", internal_variables=internal_variables,
                            user_variables=user_variables, dynamic_variables=dynamic_variables, arg_input=arg_input) ==
            ("/eos/None", ["None"]))

    assert (osc.process_osc("/eos/@1@", ["@1@", "@0@"],
                            internal_variables=internal_variables,
                            user_variables=user_variables, dynamic_variables=dynamic_variables, arg_input=arg_input) ==
            ("/eos/None", ["None", "ping"]))
