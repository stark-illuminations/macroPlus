import math
import re


def parse_value(script_word: str | int | float | bool, debug=False):
    """Parse a raw value and return the result."""
    if debug:
        print("- Word appears to be a raw value. Attempting to interpret...")
    # Try to interpret this as a raw value
    if str(script_word).lower() == "true":
        if debug:
            print("-- Word is boolean True.")
        return True
    elif str(script_word).lower() == "false":
        if debug:
            print("-- Word is boolean False.")
        return False
    elif script_word is None:
        return None
    else:
        try:
            if math.isclose(float(script_word), round(float(script_word))):
                if debug:
                    print("-- Word is likely an int, returning as int.")
                return int(float(script_word))
            else:
                if debug:
                    print("-- Word is a float, returning as float.")
                script_word = float(script_word)
                return script_word
        except (ValueError, TypeError):
            if debug:
                print("-- Word is a string.")
            return script_word


def parse_script_word(script_word, uuid, internal_variables, user_variables, dynamic_variables, arg_input=None, eos_query_count=0, debug=False):
    """Parse a non-opcode word in a macro action and return its value"""
    # Possible patterns: #internal_variable#, *user_variable*, %dynamic_variable%, @arg_input_value@
    # Anything else is a value
    if debug:
        print("Processing script word: %s" % script_word)
        print("Argument input: ", arg_input)

    try:
        if re.match("#\w+#", script_word):
            # Internal variable
            # Ensure that variable is lowercase
            script_word = script_word.lower()
            if debug:
                print("- Word appears to be an internal variable.")
            for variable in internal_variables:
                if variable.name == script_word:
                    # Return the internal variable's value
                    if debug:
                        print("-- Variable match found: %s. Returning value: %s" % (
                        variable.name, str(variable.var_value)))
                    return variable.var_value
            # If the variable wasn't found, return None
            if debug:
                print("-- No variable match found. Returning None.")
            return None
        elif re.match("%\w+%", script_word):
            # Dynamic variable
            # Ensure that variable is lowercase
            script_word = script_word.lower()
            if debug:
                print("- Word appears to be a dynamic variable.")
            for variable in dynamic_variables:
                if variable.name == script_word:
                    # Return the dynamic variable's value
                    if debug:
                        print("-- Variable match found: %s. Returning value: %s" % (
                        variable.name, str(variable.var_value)))
                    return variable.var_value
            # If the variable wasn't found, return None
            if debug:
                print("-- No variable match found. Returning None.")
            return None
        elif re.match("\*\w+\*", script_word):
            # User variable
            # Ensure that variable is lowercase
            script_word = script_word.lower()
            if debug:
                print("- Word appears to be a user variable.")
            for variable in user_variables:
                if variable.name == script_word:
                    # Return the user variable's value
                    if debug:
                        print("-- Variable match found: %s. Returning value: %s" % (
                        variable.name, str(variable.var_value)))
                    return variable.var_value
            # If the variable wasn't found, return None
            if debug:
                print("-- No variable match found. Returning None.")
            return None
        elif re.match("eos\([\w/+->]+\)", script_word):
            # Eos query, return the value at the right index and increment the eos query count
            if debug:
                print("- Word appears to be an Eos query.")

            # Find the variable name
            internal_variable_name = "#internal_%i_%s#" % (eos_query_count, uuid)
            print("Searching for: %s" % internal_variable_name)
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
        elif re.match("@\w+@", script_word):
            # Argument input
            # Ensure that argument is a valid index
            if debug:
                print("- Word appears to be an argument input. Attempting to substitute...")
                print(arg_input[int(script_word[1:-1])])
            try:
                script_word = arg_input[int(script_word[1:-1])]
                return script_word
            except (ValueError, IndexError):
                if debug:
                    print("-- Argument index was not an integer or argument did not exist. Returning None.")
                return None
        else:
            return parse_value(script_word, debug=debug)
    except TypeError:
        # Script_word is a raw value
        return parse_value(script_word, debug=debug)


def regex_osc_trigger(raw_trigger: str):
    # Make an OSC address pattern into a string which can be used to match incoming OSC

    # Split off any address patterns if they are given
    raw_trigger = raw_trigger.split("=")

    print("raw trigger: %s" % raw_trigger)
    raw_trigger_address_pattern = raw_trigger[0]
    print("raw trigger address pattern: %s" % raw_trigger_address_pattern)

    if len(raw_trigger) > 1:
        # Remove brackets from argument patterns, then split at commas
        raw_trigger_arg_patterns = raw_trigger[1][1:-1].split(",")

        for arg_pattern in raw_trigger_arg_patterns:
            # Escape any forward slashes
            arg_pattern = arg_pattern.replace("/", "\/")

            # Any wildcard is a complete wildcard
            arg_pattern = arg_pattern.replace("*", "[^/]*")

    else:
        raw_trigger_arg_patterns = []

    if raw_trigger_address_pattern[-1] == "*":
        # Terminal wildcard in address pattern can be any number of address containers
        print("Terminal wildcard")
        raw_trigger_address_pattern = raw_trigger_address_pattern[0:-1] + ".*"

    # Escape forward slashes
    raw_trigger_address_pattern = raw_trigger_address_pattern.replace("/", "\/")

    # Remaining wildcards are internal, and can represent any single address container
    raw_trigger_address_pattern = raw_trigger_address_pattern.replace("*", "[^/]*")

    print("Final address pattern: %s" % raw_trigger_address_pattern)
    return raw_trigger_address_pattern, raw_trigger_arg_patterns
