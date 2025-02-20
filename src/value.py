"""
Value processing functions for MacroPlus.

Functions:
- parse_value(): Parse a raw value and attempt to give it a non-string type
- parse_script_word(): Parse a word from a script, and substitute in variables as needed
- regex_osc_trigger(): Convert a string OSC trigger into a regex-friendly one,
    with wildcards and argument matching.
"""

import math
import re


def parse_value(script_word: str | int | float | bool, debug: bool = False):
    """Parse a raw value and return the result.

    :param script_word: The word to interpret
    :type script_word: str or int or float or bool
    :param bool debug: Whether to print debug messages
    """
    if debug:
        print("- Word appears to be a raw value. Attempting to interpret...")
    # Try to interpret this as a raw value
    if str(script_word).lower() == "true":
        if debug:
            print("-- Word is boolean True.")
        return True

    if str(script_word).lower() == "false":
        if debug:
            print("-- Word is boolean False.")
        return False

    if script_word is None:
        return None

    try:
        if math.isclose(float(script_word), round(float(script_word))):
            if debug:
                print("-- Word is likely an int, returning as int.")
            return int(float(script_word))

        if debug:
            print("-- Word is a float, returning as float.")
        script_word = float(script_word)
        return script_word
    except (ValueError, TypeError):
        if debug:
            print("-- Word is a string.")
        return script_word


def parse_script_word(script_word: str, uuid: str, collected_variables: dict,
                      arg_input: list = None, debug: bool = False):
    """
    Parse a non-opcode word in a macro action and return its value.

    Accepts any string, and checks if it is formatted as an internal variable, user variable,
    dynamic variable, argument input, Eos query, or if it it's just a raw value.

    :param str script_word: The string to be parsed
    :param str uuid: The UUID of the currently-running macro
    :param dict collected_variables: A dictionary containing internal variables,
        user variables, dynamic variables, and eos_query_count
    :param list arg_input: The current argument input, if provided
    :param bool debug: Whether to print debug messages
    """
    if debug:
        print(f"Processing script word: {script_word}")
        print("Argument input: ", arg_input)

    if collected_variables is None:
        collected_variables = {}

    try:
        internal_variables = collected_variables["internal_variables"]
    except KeyError:
        internal_variables = []
        collected_variables["internal_variables"] = []

    try:
        user_variables = collected_variables["user_variables"]
    except KeyError:
        user_variables = []
        collected_variables["user_variables"] = []

    try:
        dynamic_variables = collected_variables["dynamic_variables"]
    except KeyError:
        dynamic_variables = []
        collected_variables["dynamic_variables"] = []

    try:
        eos_query_count = collected_variables["eos_query_count"]
    except KeyError:
        eos_query_count = 0
        collected_variables["eos_query_count"] = 0

    try:
        if re.match("#[\w_-]+#", script_word):
            # Internal variable
            # Ensure that variable is lowercase
            script_word = script_word.lower()
            if debug:
                print("- Word appears to be an internal variable.")
            for variable in internal_variables:
                if variable.name == script_word:
                    # Return the internal variable's value
                    if debug:
                        print(f"-- Variable match found: {variable.name}. "
                              f"Returning value: {variable.var_value}")
                    return variable.var_value
            # If the variable wasn't found, return None
            if debug:
                print("-- No variable match found. Returning None.")
            return None
        if re.match("%\w+%", script_word):
            # Dynamic variable
            # Ensure that variable is lowercase
            script_word = script_word.lower()
            if debug:
                print("- Word appears to be a dynamic variable.")
            for variable in dynamic_variables:
                if variable.name == script_word:
                    # Return the dynamic variable's value
                    if debug:
                        print(f"-- Variable match found: {variable.name}. "
                              f"Returning value: {variable.var_value}")
                    return variable.var_value
            # If the variable wasn't found, return None
            if debug:
                print("-- No variable match found. Returning None.")
            return None
        if re.match("\*\w+\*", script_word):
            # User variable
            # Ensure that variable is lowercase
            script_word = script_word.lower()
            if debug:
                print("- Word appears to be a user variable.")
            for variable in user_variables:
                if variable.name == script_word:
                    # Return the user variable's value
                    if debug:
                        print(f"-- Variable match found: {variable.name}. "
                              f"Returning value: {str(variable.var_value)}")
                    return variable.var_value
            # If the variable wasn't found, return None
            if debug:
                print("-- No variable match found. Returning None.")
            return None
        if re.match("eos\([\w/+->]+\)", script_word):
            # Eos query, return the value at the right index and increment the eos query count
            if debug:
                print("- Word appears to be an Eos query.")

            # Find the variable name
            internal_variable_name = f"#internal_{eos_query_count}_{uuid}#"
            if debug:
                print(f"Searching for: {internal_variable_name}")

            for variable in internal_variables:
                if variable.name == internal_variable_name:
                    # Found the eos query!
                    # Increment the counter
                    eos_query_count += 1
                    return variable.var_value, eos_query_count
            # If the variable wasn't found, return None
            if debug:
                print("-- No eos query match found. Returning None.")

            # Always increment the counter
            eos_query_count += 1
            return None, eos_query_count
        if re.match("@\w+@", script_word):
            # Argument input
            # Ensure that argument is a valid index
            if debug:
                print("- Word appears to be an argument input. Attempting to substitute...")
            try:
                script_word = arg_input[int(script_word[1:-1])]
                return script_word
            except (ValueError, IndexError):
                if debug:
                    print("-- Argument index was not an integer or argument did not exist. "
                          "Returning None.")
                return None

        return parse_value(script_word, debug=debug)
    except TypeError:
        # Script_word is a raw value
        return parse_value(script_word, debug=debug)


def regex_osc_trigger(raw_trigger: str, debug: bool = False) -> tuple:
    """
    Make an OSC address pattern into a string which can be used to match incoming OSC.

    :param str raw_trigger: The trigger to make regex-friendly
    :param bool debug: Whether to print debug messages
    """

    # Split off any address patterns if they are given
    if debug:
        print("Making regex trigger")
    raw_trigger = raw_trigger.split("=")

    raw_trigger_address_pattern = raw_trigger[0]

    if len(raw_trigger) > 1:
        # Remove brackets from argument patterns, then split at commas
        raw_trigger_arg_patterns = raw_trigger[1][1:-1].split(",")

        parsed_arg_patterns = []
        for arg_pattern in raw_trigger_arg_patterns:
            # Strip leading and trailing spaces
            arg_pattern = arg_pattern.strip(" ")

            # Escape any forward slashes
            arg_pattern = arg_pattern.replace("/", "\/")

            # Any wildcard is a complete wildcard
            arg_pattern = arg_pattern.replace("*", ".*")

            parsed_arg_patterns.append(arg_pattern)

    else:
        parsed_arg_patterns = []

    # Escape forward slashes
    raw_trigger_address_pattern = raw_trigger_address_pattern.replace("/", "\/")

    # Treat all wildcards as internal, and able represent any single address container
    raw_trigger_address_pattern = raw_trigger_address_pattern.replace("*", "[^/]*")

    if raw_trigger_address_pattern[-1] == "*":
        # Terminal wildcard in address pattern can be any number of address containers
        raw_trigger_address_pattern = raw_trigger_address_pattern[0:-5] + ".*"

    return raw_trigger_address_pattern, parsed_arg_patterns
