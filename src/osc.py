from pythonosc import udp_client

import value


def start_osc_client(network_config: list):
    """Start a new OSC server and client to connect to the console"""
    if type(network_config) == list:
        try:
            osc_client = udp_client.SimpleUDPClient(network_config[0], int(network_config[1]))
            osc_client.send_message("/eos/ping", "macroPlus")
            return osc_client
        except (ValueError, IndexError):
            print("Bad config")
            return "Invalid network config. Try again."
    else:
        print("Bad config")


def process_osc(osc_addr: str, osc_args=None, internal_variables=None, user_variables=None, dynamic_variables=None, arg_input=None, debug=False):
    """Process an OSC address and arguments, substituting in variables, then return them to be sent"""

    if debug:
        print("Processing OSC!")
        print("Initial OSC Address: %s" % osc_addr)
        print("Initial OSC arguments: ", osc_args)

    if osc_args is None:
        osc_args = []

    if type(osc_args) == str:
        osc_args = [osc_args]

    if internal_variables is None:
        internal_variables = []

    if user_variables is None:
        user_variables = []

    if dynamic_variables is None:
        dynamic_variables = []

    # Split the OSC address and look for variables
    split_osc_addr = osc_addr.split("/")
    if split_osc_addr[0] == "":
        # This is expected, and is evidence of a properly formed OSC address. Just cut it off.
        split_osc_addr = split_osc_addr[1:]

    if split_osc_addr[-1] == "":
        # User appended an extra slash to the end of the address, ignore it.
        split_osc_addr = split_osc_addr[:-1]

    if debug:
        print("Split OSC address: ", split_osc_addr)

    parsed_osc_addr = []
    for address_container in split_osc_addr:
        # Substitute in variables where appropriate
        parsed_container = str(value.parse_script_word(address_container, internal_variables, user_variables, dynamic_variables, arg_input=arg_input, debug=debug))
        if parsed_container is None:
            parsed_container = "None"
        parsed_osc_addr.append(parsed_container)

    # Rebuild the OSC address
    final_osc_addr = "/" + "/".join(parsed_osc_addr)

    # Process arguments, substituting in variable values where appropriate
    parsed_osc_args = []
    for argument in osc_args:
        parsed_arg = value.parse_script_word(argument, internal_variables, user_variables, dynamic_variables, arg_input=arg_input, debug=debug)
        if parsed_arg is None:
            parsed_arg = "None"
        parsed_osc_args.append(parsed_arg)
    if debug:
        print("Final OSC address: %s" % final_osc_addr)
        print("Final OSC arguments: ", parsed_osc_args)
        print("Sending OSC message!")

    return final_osc_addr, parsed_osc_args