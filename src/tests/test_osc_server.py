from pythonosc import osc_server
from osc_server import eos_out, start_osc_server


def test_eos_out():
    """Test that eos_out is formatting OSC messages properly before sending them to the app."""

    assert eos_out("/eos/out/ping", "macroPlus") == ("/eos/out/ping", '["macroPlus"]')
    assert eos_out("/eos/out/ping", "macroPlus", "second argument") == (
    "/eos/out/ping", '["macroPlus", "second argument"]')
    assert eos_out("/eos/out/ping", 0.1) == ("/eos/out/ping", '[0.1]')
    assert eos_out("/eos/out/ping", 1) == ("/eos/out/ping", '[1]')


def test_start_osc_server():
    """Test that start_osc_server returns a valid OSC server object"""
    assert isinstance(start_osc_server(), osc_server.ThreadingOSCUDPServer)
