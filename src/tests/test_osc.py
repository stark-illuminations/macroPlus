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


def test_process_osc_address():
    """Tests process_osc_address for correct formatting and variable insertion."""
    new_uuid = uuid.uuid4()
    # Without variables
    assert osc.process_osc_address(new_uuid, "/eos/ping", {}) == ("/eos/ping", 0)
    assert osc.process_osc_address(new_uuid, "eos/ping", {}) == ("/eos/ping", 0)
    assert osc.process_osc_address(new_uuid, "eos/ping/", {}) == ("/eos/ping", 0)
    assert osc.process_osc_address(new_uuid, "/eos/ping/", {}) == ("/eos/ping", 0)
    assert osc.process_osc_address(new_uuid, "/eos/ping", {}) == ("/eos/ping", 0)
    assert osc.process_osc_address(new_uuid, "/eos/ping", {}) == ("/eos/ping", 0)

    # With variables
    internal_variables = [variables.InternalVar(f"#internal_0_{new_uuid}#", "ping"),
                          variables.InternalVar(f"#internal_1_{new_uuid}#", "pong")]
    user_variables = [variables.InternalVar("*user_0*", "ping")]
    dynamic_variables = [variables.InternalVar("%cue%", "ping")]
    test_variables = {"internal_variables": internal_variables, "user_variables": user_variables,
                      "dynamic_variables": dynamic_variables, "eos_query_count": 0}
    arg_input = ["ping"]

    # Internal variables
    assert (osc.process_osc_address(new_uuid, f"/eos/#internal_0_{new_uuid}#", test_variables,
                                    arg_input=arg_input) == ("/eos/ping", 0))
    assert (osc.process_osc_address(new_uuid, "/eos/#internal_1#", test_variables,
                                    arg_input=arg_input) == ("/eos/None", 0))
    assert (osc.process_osc_address(new_uuid, f"/eos/#internal_0_{new_uuid}#", test_variables,
                                    arg_input=arg_input) == ("/eos/ping", 0))
    assert (osc.process_osc_address(new_uuid, "/eos/#internal_1#", test_variables,
                                    arg_input=arg_input) == ("/eos/None", 0))
    assert (osc.process_osc_address(new_uuid, "/eos/#internal_1#", test_variables,
                                    arg_input=arg_input) == ("/eos/None", 0))

    # User variables
    assert (osc.process_osc_address(new_uuid, "/eos/*user_0*", test_variables, arg_input=arg_input)
            == ("/eos/ping", 0))
    assert (osc.process_osc_address(new_uuid, "/eos/*user_1*", test_variables, arg_input=arg_input)
            == ("/eos/None", 0))
    assert (osc.process_osc_address(new_uuid, "/eos/*user_0*", test_variables, arg_input=arg_input)
            == ("/eos/ping", 0))
    assert (osc.process_osc_address(new_uuid, "/eos/*user_1*", test_variables, arg_input=arg_input)
            == ("/eos/None", 0))
    assert (osc.process_osc_address(new_uuid, "/eos/*user_1*", test_variables, arg_input=arg_input)
            == ("/eos/None", 0))

    # Dynamic variables
    assert (osc.process_osc_address(new_uuid, "/eos/%cue%", test_variables, arg_input=arg_input)
            == ("/eos/ping", 0))
    assert (osc.process_osc_address(new_uuid, "/eos/%random%", test_variables, arg_input=arg_input)
            == ("/eos/None", 0))
    assert (osc.process_osc_address(new_uuid, "/eos/%cue%", test_variables, arg_input=arg_input)
            == ("/eos/ping", 0))
    assert (osc.process_osc_address(new_uuid, "/eos/%random%", test_variables, arg_input=arg_input)
            == ("/eos/None", 0))
    assert (osc.process_osc_address(new_uuid, "/eos/%random%", test_variables, arg_input=arg_input)
            == ("/eos/None", 0))

    # Argument inputs
    assert (osc.process_osc_address(new_uuid, "/eos/@0@", test_variables, arg_input=arg_input)
            == ("/eos/ping", 0))
    assert (osc.process_osc_address(new_uuid, "/eos/@1@", test_variables, arg_input=arg_input)
            == ("/eos/None", 0))
    assert (osc.process_osc_address(new_uuid, "/eos/@0@", test_variables, arg_input=arg_input)
            == ("/eos/ping", 0))
    assert (osc.process_osc_address(new_uuid, "/eos/@1@", test_variables, arg_input=arg_input)
            == ("/eos/None", 0))
    assert (osc.process_osc_address(new_uuid, "/eos/@1@", test_variables, arg_input=arg_input)
            == ("/eos/None", 0))

    # Eos Queries and eos_query_count incrementing
    assert (osc.process_osc_address(new_uuid, "/eos/eos(test)/eos(test_2)", test_variables,
                                    arg_input=arg_input) == ("/eos/ping/pong", 2))
    assert (osc.process_osc_address(new_uuid, "/eos/eos(test)", test_variables,
                                    arg_input=arg_input) == ("/eos/ping", 1))
    test_variables["eos_query_count"] = 1
    assert (osc.process_osc_address(new_uuid, "/eos/eos(test_2)", test_variables,
                                    arg_input=arg_input) == ("/eos/pong", 2))
    test_variables["eos_query_count"] = 2
    assert (osc.process_osc_address(new_uuid, "/eos/eos(test_2)", test_variables,
                                    arg_input=arg_input) == ("/eos/None", 3))


def test_process_osc_args():
    """Test that process_osc_args fills and formats OSC arguments correctly."""
    new_uuid = uuid.uuid4()
    # Without variables
    assert (osc.process_osc_args(new_uuid, ["Test"]) == (["Test"], 0))
    assert (osc.process_osc_args(new_uuid, ["Test"]) == (["Test"], 0))
    assert (osc.process_osc_args(new_uuid, ["Test"]) == (["Test"], 0))
    assert (osc.process_osc_args(new_uuid, ["Test"]) == (["Test"], 0))
    assert (osc.process_osc_args(new_uuid, "Test") == (["Test"], 0))
    assert (osc.process_osc_args(new_uuid, ["Test", "Second Argument"]) ==
            (["Test", "Second Argument"], 0))

    # With variables
    internal_variables = [variables.InternalVar(f"#internal_0_{new_uuid}#", "ping"),
                          variables.InternalVar(f"#internal_1_{new_uuid}#", "pong")]
    user_variables = [variables.InternalVar("*user_0*", "ping")]
    dynamic_variables = [variables.InternalVar("%cue%", "ping")]
    test_variables = {"internal_variables": internal_variables, "user_variables": user_variables,
                      "dynamic_variables": dynamic_variables}
    arg_input = ["ping"]

    # Internal variables
    assert (osc.process_osc_args(new_uuid, f"#internal_0_{new_uuid}#", test_variables,
                                 arg_input=arg_input) == (["ping"], 0))
    assert (osc.process_osc_args(new_uuid, "#internal_1#", test_variables, arg_input=arg_input)
            == (["None"], 0))
    assert (osc.process_osc_args(new_uuid, "#internal_1#", test_variables, arg_input=arg_input)
            == (["None"], 0))
    assert (osc.process_osc_args(new_uuid, ["#internal_1#", f"#internal_0_{new_uuid}#"],
                                 test_variables, arg_input=arg_input) == (["None", "ping"], 0))

    # User variables
    assert (osc.process_osc_args(new_uuid, "*user_0*", test_variables, arg_input=arg_input)
            == (["ping"], 0))
    assert (osc.process_osc_args(new_uuid, "*user_0*", test_variables, arg_input=arg_input)
            == (["ping"], 0))
    assert (osc.process_osc_args(new_uuid, "*user_1*", test_variables, arg_input=arg_input)
            == (["None"], 0))
    assert (osc.process_osc_args(new_uuid, "*user_1*", test_variables, arg_input=arg_input)
            == (["None"], 0))
    assert (osc.process_osc_args(new_uuid, ["*user_1*", "*user_0*"], test_variables,
                                 arg_input=arg_input) == (["None", "ping"], 0))

    # Dynamic variables
    assert (osc.process_osc_args(new_uuid, "%cue%", test_variables, arg_input=arg_input)
            == (["ping"], 0))
    assert (osc.process_osc_args(new_uuid, "%cue%", test_variables, arg_input=arg_input)
            == (["ping"], 0))
    assert (osc.process_osc_args(new_uuid, "%random%", test_variables, arg_input=arg_input)
            == (["None"], 0))
    assert (osc.process_osc_args(new_uuid, "%random%", test_variables, arg_input=arg_input)
            == (["None"], 0))
    assert (osc.process_osc_args(new_uuid, ["%random%", "%cue%"], test_variables,
                                 arg_input=arg_input) == (["None", "ping"], 0))

    # Argument inputs
    assert (osc.process_osc_args(new_uuid, "@0@", test_variables, arg_input=arg_input)
            == (["ping"], 0))
    assert (osc.process_osc_args(new_uuid, "@0@", test_variables, arg_input=arg_input)
            == (["ping"], 0))
    assert (osc.process_osc_args(new_uuid, "@1@", test_variables, arg_input=arg_input)
            == (["None"], 0))
    assert (osc.process_osc_args(new_uuid, "@1@", test_variables, arg_input=arg_input)
            == (["None"], 0))
    assert (osc.process_osc_args(new_uuid, ["@1@", "@0@"], test_variables, arg_input=arg_input)
            == (["None", "ping"], 0))

    # Eos Queries and eos_query_count incrementing
    assert (osc.process_osc_args(new_uuid, ["eos(test)", "eos(test)"], test_variables,
                                 arg_input=arg_input) == (["ping", "pong"], 2))
    assert (osc.process_osc_args(new_uuid, ["eos(test)"], test_variables, arg_input=arg_input)
            == (["ping"], 1))
    test_variables["eos_query_count"] = 1
    assert (osc.process_osc_args(new_uuid, ["eos(test)"], test_variables, arg_input=arg_input)
            == (["pong"], 2))
    test_variables["eos_query_count"] = 2
    assert (osc.process_osc_args(new_uuid, ["eos(test)"], test_variables, arg_input=arg_input)
            == (["None"], 3))


def test_process_osc():
    """Test that process_osc formats OSC correctly."""
    new_uuid = uuid.uuid4()
    # Without variables
    assert (osc.process_osc(new_uuid, {"osc_addr": "/eos/ping", "osc_args": ["Test"]})
            == ("/eos/ping", ["Test"]))
    assert (osc.process_osc(new_uuid, {"osc_addr": "eos/ping", "osc_args": ["Test"]})
            == ("/eos/ping", ["Test"]))
    assert (osc.process_osc(new_uuid, {"osc_addr": "eos/ping/", "osc_args": ["Test"]})
            == ("/eos/ping", ["Test"]))
    assert (osc.process_osc(new_uuid, {"osc_addr": "/eos/ping/", "osc_args": ["Test"]})
            == ("/eos/ping", ["Test"]))
    assert (osc.process_osc(new_uuid, {"osc_addr": "/eos/ping", "osc_args": "Test"})
            == ("/eos/ping", ["Test"]))
    assert (osc.process_osc(new_uuid, {"osc_addr": "/eos/ping",
                                       "osc_args": ["Test", "Second Argument"]})
            == ("/eos/ping", ["Test", "Second Argument"]))

    # With variables
    internal_variables = [variables.InternalVar(f"#internal_0_{new_uuid}#", "ping"),
                          variables.InternalVar(f"#internal_1_{new_uuid}#", "pong")]
    user_variables = [variables.InternalVar("*user_0*", "ping")]
    dynamic_variables = [variables.InternalVar("%cue%", "ping")]
    test_variables = {"internal_variables": internal_variables, "user_variables": user_variables,
                      "dynamic_variables": dynamic_variables, "eos_query_count": 0}
    arg_input = ["ping"]

    # Internal variables
    assert (osc.process_osc(new_uuid, {"osc_addr": f"/eos/#internal_0_{new_uuid}#",
                                       "osc_args": f"#internal_0_{new_uuid}#"}, test_variables,
                            arg_input=arg_input) == ("/eos/ping", ["ping"]))
    assert (osc.process_osc(new_uuid, {"osc_addr": "/eos/#internal_1#",
                                       "osc_args": f"#internal_0_{new_uuid}#"}, test_variables,
                            arg_input=arg_input) == ("/eos/None", ["ping"]))
    assert (osc.process_osc(new_uuid, {"osc_addr": f"/eos/#internal_0_{new_uuid}#",
                                       "osc_args": "#internal_1#"}, test_variables,
                            arg_input=arg_input) == ("/eos/ping", ["None"]))
    assert (osc.process_osc(new_uuid, {"osc_addr": "/eos/#internal_1#",
                                       "osc_args": "#internal_1#"}, test_variables,
                            arg_input=arg_input) == ("/eos/None", ["None"]))
    assert (osc.process_osc(new_uuid, {"osc_addr": "/eos/#internal_1#",
                                       "osc_args": ["#internal_1#", f"#internal_0_{new_uuid}#"]},
                            test_variables, arg_input=arg_input) == ("/eos/None", ["None", "ping"]))

    # User variables
    assert (osc.process_osc(new_uuid, {"osc_addr": "/eos/*user_0*", "osc_args": "*user_0*"},
                            test_variables, arg_input=arg_input) == ("/eos/ping", ["ping"]))
    assert (osc.process_osc(new_uuid, {"osc_addr": "/eos/*user_1*", "osc_args": "*user_0*"},
                            test_variables, arg_input=arg_input) == ("/eos/None", ["ping"]))
    assert (osc.process_osc(new_uuid, {"osc_addr": "/eos/*user_0*", "osc_args": "*user_1*"},
                            test_variables, arg_input=arg_input) == ("/eos/ping", ["None"]))
    assert (osc.process_osc(new_uuid, {"osc_addr": "/eos/*user_1*", "osc_args": "*user_1*"},
                            test_variables, arg_input=arg_input) == ("/eos/None", ["None"]))
    assert (osc.process_osc(new_uuid, {"osc_addr": "/eos/*user_1*",
                                       "osc_args": ["*user_1*", "*user_0*"]}, test_variables,
                            arg_input=arg_input) == ("/eos/None", ["None", "ping"]))

    # Dynamic variables
    assert (osc.process_osc(new_uuid, {"osc_addr": "/eos/%cue%", "osc_args": "%cue%"},
                            test_variables, arg_input=arg_input) == ("/eos/ping", ["ping"]))
    assert (osc.process_osc(new_uuid, {"osc_addr": "/eos/%random%", "osc_args": "%cue%"},
                            test_variables, arg_input=arg_input) == ("/eos/None", ["ping"]))
    assert (osc.process_osc(new_uuid, {"osc_addr": "/eos/%cue%", "osc_args": "%random%"},
                            test_variables, arg_input=arg_input) == ("/eos/ping", ["None"]))
    assert (osc.process_osc(new_uuid, {"osc_addr": "/eos/%random%", "osc_args": "%random%"},
                            test_variables, arg_input=arg_input) == ("/eos/None", ["None"]))
    assert (osc.process_osc(new_uuid, {"osc_addr": "/eos/%random%",
                                       "osc_args": ["%random%", "%cue%"]}, test_variables,
                            arg_input=arg_input) == ("/eos/None", ["None", "ping"]))

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

    # Eos Queries and eos_query_count incrementing
    assert (osc.process_osc(new_uuid, {"osc_addr": "/eos/eos(test)", "osc_args": ["eos(test)"]},
                            test_variables, arg_input=arg_input) == ("/eos/ping", ["pong"], 2))
    test_variables["eos_query_count"] = 0
    assert (osc.process_osc(new_uuid, {"osc_addr": "/eos/eos(test)", "osc_args": []},
                            test_variables, arg_input=arg_input) == ("/eos/ping", [], 1))
    test_variables["eos_query_count"] = 1
    assert (osc.process_osc(new_uuid, {"osc_addr": "/eos/eos(test_1)", "osc_args": []},
                            test_variables, arg_input=arg_input) == ("/eos/pong", [], 2))
    test_variables["eos_query_count"] = 2
    assert (osc.process_osc(new_uuid, {"osc_addr": "/eos/eos(test_2)", "osc_args": []},
                            test_variables, arg_input=arg_input) == ("/eos/None", [], 3))
