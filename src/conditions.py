import value

def check_soft_equality(check_values: list, uuid: str, collected_variables: dict, arg_input: list,
                        debug: bool = False) -> tuple:
    """
    Check for equality between two values' string representations.

    :param list check_values: A list containing the two values to compare
    :param str uuid: The UUID of the currently running macro
    :param dict collected_variables: A dict containing internal, user, and dynamic variables,
        as well as eos_query_count
    :param list arg_input: A list of current argument input, if any
    :param bool debug: Whether to print debug messages
    """
    # Soft equality operator.
    # If string representations of both values match, return True.
    try:
        eos_query_count = collected_variables["eos_query_count"]
    except KeyError:
        eos_query_count = 0

    first_value = value.parse_script_word(check_values[0], uuid, collected_variables,
                                          arg_input=arg_input)

    if isinstance(first_value, tuple):
        # Word was an eos query, set the eos_query_count
        if debug:
            print(f"Updating eos_query_count to {first_value[1]}")
        eos_query_count = first_value[1]
        collected_variables["eos_query_count"] = eos_query_count
        first_value = first_value[0]

    second_value = value.parse_script_word(check_values[1], uuid, collected_variables,
                                           arg_input=arg_input)

    if isinstance(second_value, tuple):
        # Word was an eos query, set the eos_query_count
        if debug:
            print(f"Updating eos_query_count to {second_value[1]}")
        eos_query_count = second_value[1]
        second_value = second_value[0]

    initial_result = bool(str(first_value) == str(second_value))

    return initial_result, eos_query_count


def check_hard_equality(check_values: list, uuid: str, collected_variables: dict, arg_input: list,
                        debug: bool = False) -> tuple:
    """
    Check for equality between two values. Both types and values must match.

    :param list check_values: A list containing the two values to compare
    :param str uuid: The UUID of the currently running macro
    :param dict collected_variables: A dict containing internal, user, and dynamic variables,
        as well as eos_query_count
    :param list arg_input: A list of current argument input, if any
    :param bool debug: Whether to print debug messages
    """
    # Hard equality operator.
    # Both values and types must match to return True
    try:
        eos_query_count = collected_variables["eos_query_count"]
    except KeyError:
        eos_query_count = 0

    first_value = value.parse_script_word(check_values[0], uuid, collected_variables,
                                          arg_input=arg_input)
    if isinstance(first_value, tuple):
        # Word was an eos query, set the eos_query_count
        if debug:
            print(f"Updating eos_query_count to {first_value[1]}")
        eos_query_count = first_value[1]
        collected_variables["eos_query_count"] = eos_query_count
        first_value = first_value[0]

    second_value = value.parse_script_word(check_values[1], uuid, collected_variables,
                                           arg_input=arg_input)
    if isinstance(first_value, tuple):
        # Word was an eos query, set the eos_query_count
        if debug:
            print(f"Updating eos_query_count to {second_value[1]}")
        eos_query_count = second_value[1]
        second_value = second_value[0]

    # Check that both value and type match
    initial_result = bool((first_value == second_value) and (type(first_value)
                                                             is type(second_value)))

    return initial_result, eos_query_count


def check_greater_than(check_values: list, uuid: str, collected_variables: dict, arg_input: list,
                        debug: bool = False) -> tuple:
    """
    Check that one value is greater than another.

    :param list check_values: A list containing the two values to compare
    :param str uuid: The UUID of the currently running macro
    :param dict collected_variables: A dict containing internal, user, and dynamic variables,
        as well as eos_query_count
    :param list arg_input: A list of current argument input, if any
    :param bool debug: Whether to print debug messages
    """
    try:
        eos_query_count = collected_variables["eos_query_count"]
    except KeyError:
        eos_query_count = 0
    # Simple 'greater than' operator
    first_value = value.parse_script_word(check_values[0], uuid, collected_variables,
                                          arg_input=arg_input)
    if isinstance(first_value, tuple):
        # Word was an eos query, set the eos_query_count
        if debug:
            print(f"Updating eos_query_count to {first_value[1]}")
        eos_query_count = first_value[1]
        collected_variables["eos_query_count"] = eos_query_count
        first_value = first_value[0]

    second_value = value.parse_script_word(check_values[1], uuid, collected_variables,
                                           arg_input=arg_input)
    if isinstance(first_value, tuple):
        # Word was an eos query, set the eos_query_count
        if debug:
            print(f"Updating eos_query_count to {second_value[1]}")
        eos_query_count = second_value[1]
        second_value = second_value[0]

    initial_result = bool(first_value > second_value)

    return initial_result, eos_query_count


def check_greater_than_equal(check_values: list, uuid: str, collected_variables: dict, arg_input: list,
                        debug: bool = False) -> tuple:
    """
    Check that one value is greater than or equal to another.

    :param list check_values: A list containing the two values to compare
    :param str uuid: The UUID of the currently running macro
    :param dict collected_variables: A dict containing internal, user, and dynamic variables,
        as well as eos_query_count
    :param list arg_input: A list of current argument input, if any
    :param bool debug: Whether to print debug messages
    """
    try:
        eos_query_count = collected_variables["eos_query_count"]
    except KeyError:
        eos_query_count = 0

    # Greater than or equal to operator.
    first_value = value.parse_script_word(check_values[0], uuid, collected_variables,
                                          arg_input=arg_input)
    if isinstance(first_value, tuple):
        # Word was an eos query, set the eos_query_count
        if debug:
            print(f"Updating eos_query_count to {first_value[1]}")
        eos_query_count = first_value[1]
        collected_variables["eos_query_count"] = eos_query_count
        first_value = first_value[0]

    second_value = value.parse_script_word(check_values[1], uuid, collected_variables,
                                           arg_input=arg_input)
    if isinstance(first_value, tuple):
        # Word was an eos query, set the eos_query_count
        if debug:
            print(f"Updating eos_query_count to {second_value[1]}")
        eos_query_count = second_value[1]
        second_value = second_value[0]

    initial_result = bool(first_value >= second_value)

    return initial_result, eos_query_count


def check_less_than(check_values: list, uuid: str, collected_variables: dict, arg_input: list,
                        debug: bool = False) -> tuple:
    """
    Check that one value is less than another.

    :param list check_values: A list containing the two values to compare
    :param str uuid: The UUID of the currently running macro
    :param dict collected_variables: A dict containing internal, user, and dynamic variables,
        as well as eos_query_count
    :param list arg_input: A list of current argument input, if any
    :param bool debug: Whether to print debug messages
    """
    try:
        eos_query_count = collected_variables["eos_query_count"]
    except KeyError:
        eos_query_count = 0
    # Simple 'less than' operator
    first_value = value.parse_script_word(check_values[0], uuid, collected_variables,
                                          arg_input=arg_input)
    if isinstance(first_value, tuple):
        # Word was an eos query, set the eos_query_count
        if debug:
            print(f"Updating eos_query_count to {first_value[1]}")
        eos_query_count = first_value[1]
        collected_variables["eos_query_count"] = eos_query_count
        first_value = first_value[0]

    second_value = value.parse_script_word(check_values[1], uuid, collected_variables,
                                           arg_input=arg_input)
    if isinstance(first_value, tuple):
        # Word was an eos query, set the eos_query_count
        if debug:
            print(f"Updating eos_query_count to {second_value[1]}")
        eos_query_count = second_value[1]
        second_value = second_value[0]

    initial_result = bool(first_value < second_value)

    return initial_result, eos_query_count


def check_less_than_equal(check_values: list, uuid: str, collected_variables: dict, arg_input: list,
                        debug: bool = False) -> tuple:
    """
    Check that one value is less than or equals another.

    :param list check_values: A list containing the two values to compare
    :param str uuid: The UUID of the currently running macro
    :param dict collected_variables: A dict containing internal, user, and dynamic variables,
        as well as eos_query_count
    :param list arg_input: A list of current argument input, if any
    :param bool debug: Whether to print debug messages
    """
    try:
        eos_query_count = collected_variables["eos_query_count"]
    except KeyError:
        eos_query_count = 0

    # Less than or equal to operator
    first_value = value.parse_script_word(check_values[0], uuid, collected_variables,
                                          arg_input=arg_input)
    if isinstance(first_value, tuple):
        # Word was an eos query, set the eos_query_count
        if debug:
            print(f"Updating eos_query_count to {first_value[1]}")
        eos_query_count = first_value[1]
        collected_variables["eos_query_count"] = eos_query_count
        first_value = first_value[0]

    second_value = value.parse_script_word(check_values[1], uuid, collected_variables,
                                           arg_input=arg_input)
    if isinstance(first_value, tuple):
        # Word was an eos query, set the eos_query_count
        if debug:
            print(f"Updating eos_query_count to {second_value[1]}")
        eos_query_count = second_value[1]
        second_value = second_value[0]

    initial_result = bool(first_value <= second_value)

    return initial_result, eos_query_count


def check_inequality(check_values: list, uuid: str, collected_variables: dict, arg_input: list,
                        debug: bool = False) -> tuple:
    """
    Check that one value is not equal to another.

    :param list check_values: A list containing the two values to compare
    :param str uuid: The UUID of the currently running macro
    :param dict collected_variables: A dict containing internal, user, and dynamic variables,
        as well as eos_query_count
    :param list arg_input: A list of current argument input, if any
    :param bool debug: Whether to print debug messages
    """
    try:
        eos_query_count = collected_variables["eos_query_count"]
    except KeyError:
        eos_query_count = 0

    # Inequality operator. Return True if the two values are at all different
    first_value = value.parse_script_word(check_values[0], uuid, collected_variables,
                                          arg_input=arg_input)
    if isinstance(first_value, tuple):
        # Word was an eos query, set the eos_query_count
        if debug:
            print(f"Updating eos_query_count to {first_value[1]}")
        eos_query_count = first_value[1]
        collected_variables["eos_query_count"] = eos_query_count
        first_value = first_value[0]

    second_value = value.parse_script_word(check_values[1], uuid, collected_variables,
                                           arg_input=arg_input)
    if isinstance(first_value, tuple):
        # Word was an eos query, set the eos_query_count
        if debug:
            print(f"Updating eos_query_count to {second_value[1]}")
        eos_query_count = second_value[1]
        second_value = second_value[0]

    initial_result = bool(first_value != second_value)

    return initial_result, eos_query_count


def check_condition(statement: list, uuid: str, collected_variables: dict, arg_input: list = None, debug: bool = False):
    """
    Read a list of script words and attempt to interpret them as an expression,
    then return the result.

    :param list statement: The statement to check the condition of
    :param str uuid: The UUID of the currently running macro
    :param dict collected_variables: A dictionary containing user, internal, and dynamic variables,
        plus eos_query_count
    :param list arg_input: The current input from arguments, if any
    :param bool debug: Whether to print debug messages
    """

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
        dynamic_variables = []

    try:
        eos_query_count = collected_variables["eos_query_count"]
    except KeyError:
        eos_query_count = 0
        collected_variables["eos_query_count"] = 0

    invert_condition = False

    if statement[0] == "not":
        # Invert the value at the end, and remove "not" from the statement
        invert_condition = True
        statement = statement[1:]

    if len(statement) == 1:
        # If the script word represents a variable that exists, or is any raw value, return True
        collected_variables = {"internal_variables": internal_variables,
                               "user_variables": user_variables,
                               "dynamic_variables": dynamic_variables,
                               "eos_query_count": eos_query_count}
        result = value.parse_script_word(statement[0], uuid, collected_variables,
                                         arg_input=arg_input)

        if isinstance(result, tuple):
            # Word was an eos query, set the eos_query_count
            if debug:
                print(f"Updating eos_query_count to {result[1]}")
            eos_query_count = result[1]
            result = result[0]

        # As long as parse_script_word found a value of some sort, return True
        initial_result = bool(result)

    elif len(statement) == 3:
        # Statement is assumed to be comparing two values, check for known operators.
        # If operator is unknown, return False.
        # Set up collected_variables for all cases
        collected_variables = {"internal_variables": internal_variables,
                               "user_variables": user_variables,
                               "dynamic_variables": dynamic_variables,
                               "eos_query_count": eos_query_count}
        match statement[1]:
            case "==":
                initial_result, eos_query_count = check_soft_equality([statement[0], statement[2]], uuid, collected_variables, arg_input=arg_input, debug=debug)
            case "===":
                initial_result, eos_query_count = check_hard_equality([statement[0], statement[2]],
                                                                      uuid, collected_variables,
                                                                      arg_input=arg_input,
                                                                      debug=debug)
            case ">":
                initial_result, eos_query_count = check_greater_than([statement[0], statement[2]],
                                                                     uuid, collected_variables,
                                                                     arg_input=arg_input,
                                                                     debug=debug)
            case ">=":
                initial_result, eos_query_count = check_greater_than_equal(
                    [statement[0], statement[2]], uuid, collected_variables, arg_input=arg_input,
                    debug=debug)
            case "<":
                initial_result, eos_query_count = check_less_than([statement[0], statement[2]],
                                                                  uuid, collected_variables,
                                                                  arg_input=arg_input, debug=debug)
            case "<=":
                initial_result, eos_query_count = check_less_than_equal(
                    [statement[0], statement[2]], uuid, collected_variables, arg_input=arg_input,
                    debug=debug)
            case "!=":
                initial_result, eos_query_count = check_inequality([statement[0], statement[2]],
                                                                   uuid, collected_variables,
                                                                   arg_input=arg_input, debug=debug)
            case _:
                # Operator is invalid, return False immediately
                if eos_query_count != 0:
                    return False, eos_query_count

                return False

    else:
        # No defined conditions are of length two or 4+, return False
        if eos_query_count != 0:
            return False, eos_query_count

        return False

    if invert_condition:
        # If the expression initially included a Not,
        # invert_condition was set to True. Return the opposite of the initial result.
        if eos_query_count != 0:
            return not initial_result, eos_query_count

        return not initial_result

    if eos_query_count != 0:
        return initial_result, eos_query_count

    return initial_result

