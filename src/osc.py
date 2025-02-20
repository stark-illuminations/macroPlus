"""OSC functions for MacroPlus

Includes the following functions:
- start_osc_client(): Takes a network configuration and returns a UDP client.
- process_osc(): Takes a string representing an OSC message, formats it, substitutes in variables,
    and returns it.
"""

from pythonosc import udp_client

import value


def start_osc_client(network_config: list, debug = False) -> (str or tuple):
    """
    Start a new OSC server and client to connect to the console.

    :param list network_config: The IP address and port to send OSC messages to
    :param bool debug: Whether to print debug messages
    """
    if isinstance(network_config, list):
        try:
            osc_client = udp_client.SimpleUDPClient(network_config[0], int(network_config[1]))
            osc_client.send_message("/eos/ping", "macroPlus")
            return osc_client
        except (ValueError, IndexError):
            if debug:
                print("Bad config")
            return "Invalid network config. Try again."
    else:
        if debug:
            print("Bad config")
        return "Invalid network config. Try again."


def process_osc_address(uuid: str, osc_addr: str, collected_variables: dict = None,
                        arg_input: dict = None, debug: bool = False):
    """
    Process an OSC address and return it with variables substituted in.

    :param str uuid: The UUID of the macro that is currently running.
    :param str osc_addr: The OSC address to process.
    :param dict collected_variables: The set of internal, dynamic, and user variables,
        plus eos_query_count
    :param dict arg_input: The argument input to the macro, if any
    :param bool debug: Whether to print debug messages
    """

    if collected_variables is None:
        collected_variables = {}

    try:
        internal_variables = collected_variables["internal_variables"]
    except KeyError:
        internal_variables = []

    try:
        user_variables = collected_variables["user_variables"]
    except KeyError:
        user_variables = []

    try:
        dynamic_variables = collected_variables["dynamic_variables"]
    except KeyError:
        dynamic_variables = None

    try:
        eos_query_count = collected_variables["eos_query_count"]
    except KeyError:
        eos_query_count = 0

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
        parsed_container = value.parse_script_word(address_container, uuid, collected_variables,
                                                   arg_input=arg_input, debug=debug)

        if isinstance(parsed_container, tuple):
            if debug:
                print("Updating eos_query_count to %i", parsed_container[1])
            eos_query_count = parsed_container[1]
            collected_variables["eos_query_count"] = eos_query_count
            parsed_container = parsed_container[0]

        if parsed_container is None:
            parsed_container = "None"

        parsed_osc_addr.append(str(parsed_container))

    # Rebuild the OSC address
    final_osc_addr = "/" + "/".join(parsed_osc_addr)

    return final_osc_addr, eos_query_count


def process_osc_args(uuid: str, osc_args: list, collected_variables: dict = None,
                arg_input: dict = None, debug: bool = True):
    """
    Process a list of OSC arguments and return it with variables substituted in.

    :param str uuid: The UUID of the macro that is currently running.
    :param list osc_args: The OSC arguments to process.
    :param dict collected_variables: The set of internal, dynamic, and user variables,
        plus eos_query_count
    :param dict arg_input: The argument input to the macro, if any
    :param bool debug: Whether to print debug messages
    """
    if isinstance(osc_args, str):
        osc_args = [osc_args]

    if collected_variables is None:
        collected_variables = {}

    try:
        _internal_variables = collected_variables["internal_variables"]
    except KeyError:
        _internal_variables = []
        collected_variables["internal_variables"] = []

    try:
        _user_variables = collected_variables["user_variables"]
    except KeyError:
        _user_variables = []
        collected_variables["user_variables"] = []

    try:
        _dynamic_variables = collected_variables["dynamic_variables"]
    except KeyError:
        _dynamic_variables = []
        collected_variables["dynamic_variables"] = []

    try:
        eos_query_count = collected_variables["eos_query_count"]
    except KeyError:
        eos_query_count = 0
        collected_variables["eos_query_count"] = 0

    # Process arguments, substituting in variable values where appropriate
    parsed_osc_args = []
    for argument in osc_args:
        parsed_arg = value.parse_script_word(argument, uuid, collected_variables,
                                             arg_input=arg_input, debug=debug)

        if isinstance(parsed_arg, tuple):
            if debug:
                print("Updating eos_query_count to %i", parsed_arg[1])
            eos_query_count = parsed_arg[1]
            collected_variables["eos_query_count"] = eos_query_count
            parsed_arg = parsed_arg[0]

        if parsed_arg is None:
            parsed_arg = "None"

        parsed_osc_args.append(parsed_arg)

    return parsed_osc_args, eos_query_count


def process_osc(uuid: str, osc_data: dict, collected_variables: dict = None,
                arg_input: dict = None, debug: bool = False) -> tuple:
    """
    Process an OSC address and arguments, substituting in collected_variables,
    then return them to be sent.
    :param str uuid: The UUID of the macro that is currently running.
    :param dict osc_data: The OSC message to process, with keys "osc_addr", "osc_args"
    :param dict collected_variables: The set of internal, dynamic, and user variables,
        plus eos_query_count
    :param dict arg_input: The argument input to the macro, if any
    :param bool debug: Whether to print debug messages
    """

    osc_addr = osc_data["osc_addr"]
    try:
        osc_args = osc_data["osc_args"]
    except KeyError:
        osc_args = []

    if collected_variables is None:
        collected_variables = {}

    try:
        _internal_variables = collected_variables["internal_variables"]
    except KeyError:
        collected_variables["internal_variables"] = []

    try:
        _user_variables = collected_variables["user_variables"]
    except KeyError:
        collected_variables["user_variables"] = []

    try:
        _dynamic_variables = collected_variables["dynamic_variables"]
    except KeyError:
        collected_variables["dynamic_variables"] = []

    try:
        eos_query_count = collected_variables["eos_query_count"]
    except KeyError:
        eos_query_count = 0
        collected_variables["eos_query_count"] = 0

    old_eos_query_count = eos_query_count

    if debug:
        print("Processing OSC!")
        print(f"Initial OSC Address: {osc_addr}")
        print("Initial OSC arguments: ", osc_args)

    if isinstance(osc_args, str):
        osc_args = [osc_args]

    final_osc_addr, eos_query_count = process_osc_address(uuid, osc_addr, collected_variables,
                                                          arg_input=arg_input, debug=debug)
    collected_variables["eos_query_count"] = eos_query_count
    parsed_osc_args, eos_query_count = process_osc_args(uuid, osc_args, collected_variables,
                                                        arg_input=arg_input, debug=debug)

    print("Parsed args: ", parsed_osc_args)
    if debug:
        print(f"Final OSC address: {final_osc_addr}")
        print("Final OSC arguments: ", parsed_osc_args)
        print("Sending OSC message!")

    return final_osc_addr, parsed_osc_args, eos_query_count
