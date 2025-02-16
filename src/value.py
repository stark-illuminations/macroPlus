import math
import re


def parse_value(script_word, debug=False):
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


def parse_script_word(script_word, internal_variables, user_variables, dynamic_variables, arg_input=None, debug=False):
    """Parse a non-opcode word in a macro action and return its value"""
    # Possible patterns: #internal_variable#, *user_variable*, %dynamic_variable%, @arg_input_value@
    # Anything else is a value
    if debug:
        print("Processing script word: %s" % script_word)

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
                        print("-- Variable match found: %s. Returning value: %s" % (variable.name, str(variable.var_value)))
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
                        print("-- Variable match found: %s. Returning value: %s" % (variable.name, str(variable.var_value)))
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
                        print("-- Variable match found: %s. Returning value: %s" % (variable.name, str(variable.var_value)))
                    return variable.var_value
            # If the variable wasn't found, return None
            if debug:
                print("-- No variable match found. Returning None.")
            return None
        elif re.match("@\w+@", script_word):
            # Argument input
            # Ensure that argument is a valid index
            if debug:
                print("- Word appears to be an argument input. Attempting to substitute...")
            try:
                script_word = int(script_word[1:-1])
            except ValueError:
                if debug:
                    print("-- Argument index was not an integer. Returning None.")
                    return None

            try:
                return arg_input[script_word]
            except IndexError:
                if debug:
                    print("-- Argument index was out of range. Returning None.")
                return None
        else:
            return parse_value(script_word, debug=debug)
    except TypeError:
        # Script_word is a raw value
        return parse_value(script_word, debug=debug)
