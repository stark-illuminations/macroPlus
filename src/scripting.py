import math
import re

import value
import variables
import value
import osc


def check_condition(statement: list, internal_variables, user_variables, dynamic_variables, arg_input=None):
    """Read a list of script words and attempt to interpret them as an expression, then return the result.
    """
    invert_condition = False

    if statement[0] == "not":
        # Invert the value, then remove "not" from the statement
        invert_condition = True
        statement = statement[1:]

    if len(statement) == 1:
        # If the script word represents a variable that exists, or is any raw value, return True
        result = value.parse_script_word(statement[0], internal_variables, user_variables, dynamic_variables)
        print(result)
        if result is not None:
            initial_result = True
        else:
            initial_result = False

    elif len(statement) == 3:
        # Statement is assumed to be comparing two values, check for known operators. If operator is unknown, return False.
        match statement[1]:
            case "==":
                if str(value.parse_script_word(statement[0], internal_variables, user_variables, dynamic_variables, arg_input=arg_input)) == str(value.parse_script_word(statement[2], internal_variables, user_variables, dynamic_variables, arg_input=arg_input)):
                    initial_result = True
                else:
                    initial_result = False
            case "===":
                if (((value.parse_script_word(statement[0], internal_variables, user_variables, dynamic_variables,
                                           arg_input=arg_input) ==
                        value.parse_script_word(statement[2], internal_variables, user_variables, dynamic_variables,
                                                arg_input=arg_input))) and
                        (type(value.parse_script_word(statement[0], internal_variables, user_variables,
                                                      dynamic_variables, arg_input=arg_input)) is
                         type(value.parse_script_word(statement[2], internal_variables, user_variables,
                                                      dynamic_variables, arg_input=arg_input)))):
                    initial_result = True
                else:
                    initial_result = False
            case ">":
                if value.parse_script_word(statement[0], internal_variables, user_variables, dynamic_variables, arg_input=arg_input) > value.parse_script_word(statement[2], internal_variables, user_variables, dynamic_variables, arg_input=arg_input):
                    initial_result = True
                else:
                    initial_result = False
            case ">=":
                if value.parse_script_word(statement[0], internal_variables, user_variables, dynamic_variables, arg_input=arg_input) >= value.parse_script_word(statement[2], internal_variables, user_variables, dynamic_variables, arg_input=arg_input):
                    initial_result = True
                else:
                    initial_result = False
            case "<":
                if value.parse_script_word(statement[0], internal_variables, user_variables, dynamic_variables, arg_input=arg_input) < value.parse_script_word(statement[2], internal_variables, user_variables, dynamic_variables, arg_input=arg_input):
                    initial_result = True
                else:
                    initial_result = False
            case "<=":
                if value.parse_script_word(statement[0], internal_variables, user_variables, dynamic_variables, arg_input=arg_input) <= value.parse_script_word(statement[2], internal_variables, user_variables, dynamic_variables, arg_input=arg_input):
                    initial_result = True
                else:
                    initial_result = False
            case "!=":
                if value.parse_script_word(statement[0], internal_variables, user_variables, dynamic_variables, arg_input=arg_input) != value.parse_script_word(statement[2], internal_variables, user_variables, dynamic_variables, arg_input=arg_input):
                    initial_result = True
                else:
                    initial_result = False
            case _:
                # Operator is invalid, return False immediately
                return False

    else:
        # No defined conditions are of length two or 4+, return False
        return False

    if invert_condition:
        return not initial_result
    else:
        return initial_result


def eval_expression(expression, internal_variables, user_variables, dynamic_variables, arg_input=None, debug=False):
    """Try to evaluate a script expression, and return the result"""
    if debug:
        print("Evaluating expression: ", expression)

    if len(expression) == 1:
        if debug:
            print("Expression is one word long. Returning evaluated word.")
        return value.parse_script_word(expression[0], internal_variables, user_variables, dynamic_variables, arg_input=arg_input, debug=debug)

    elif len(expression) == 3:
        if debug:
            print("Expression is three words long.")
        if expression[1] == "+":
            if debug:
                print("Expression is attempting addition.")
            try:
                return value.parse_script_word(expression[0], internal_variables, user_variables, dynamic_variables, arg_input=arg_input, debug=debug) + value.parse_script_word(expression[2], internal_variables, user_variables, dynamic_variables, arg_input=arg_input, debug=debug)
            except TypeError:
                if debug:
                    print("Conventional addition impossible, returning concatenated strings.")
                return (str(value.parse_script_word(expression[0], internal_variables, user_variables, dynamic_variables, arg_input=arg_input, debug=debug)) +
                        str(value.parse_script_word(expression[2], internal_variables, user_variables, dynamic_variables, arg_input=arg_input, debug=debug)))
        elif expression[1] == "-":
            if debug:
                print("Expression is attempting subtraction.")
            try:
                return value.parse_script_word(expression[0], internal_variables, user_variables, dynamic_variables, arg_input=arg_input, debug=debug) - value.parse_script_word(expression[2], internal_variables, user_variables, dynamic_variables, arg_input=arg_input, debug=debug)
            except TypeError:
                if debug:
                    print("Subtraction failed, returning first word in expression.")
                return value.parse_script_word(expression[0], internal_variables, user_variables, dynamic_variables, arg_input=arg_input, debug=debug)
        else:
            # Invalid operator, return None
            if debug:
                print("Operator was invalid. Returning None.")
            return None
    else:
        # Improper syntax, return None
        if debug:
            print("Improper syntax. Returning None.")
        return None


def handle_string_end(word, string_buffer, active_expression_count, expressions, split_line):
    """Handle the end of a string during script processing."""
    word = word.strip("\"'")
    string_buffer.append(word)
    print(string_buffer)

    # Re-assemble the string buffer into final_string, then reset string variables
    final_string = " ".join(string_buffer)
    string_buffer = []

    # Check if any expressions are active
    if active_expression_count > 0:
        # If an expression is active, add the final_string to the innermost expression.
        expressions[-1].append(final_string)
    else:
        # Otherwise, put the string on split_line
        split_line.append(final_string)

    return string_buffer, expressions, split_line


def handle_endloop(loop_active, loop_start_line, loop_count, loop_limit, skip_to_endloop, current_line, debug=False):
    if debug:
        print("- Endloop command found on line %i. Processing!" % current_line)

    loop_end_line = current_line - 1

    if debug:
        print("-- Set loop_end_line to %i" % loop_end_line)
    # Increment the loop counter
    if loop_active:
        loop_count += 1

        if debug:
            print("-- Loop is currently active. Incremented loop counter to %i" % loop_count)

        # If the loop count is greater than the loop limit, stop looping. Otherwise, go to the top of the loop
        if loop_count > loop_limit:
            if debug:
                print("-- Loop limit exceeded! Deactivating loop and resetting variables.")
            loop_active = False
            loop_start_line = None
            loop_end_line = None
            loop_count = 0
            skip_to_endloop = False
        else:
            if debug:
                print("-- Loop count is below limit. Resetting current line to %i" % loop_start_line)
            current_line = loop_start_line
    else:
        # We've finished the loop, do nothing
        if debug:
            print("-- Loop finished naturally, passing.")
        pass

    return loop_active, loop_start_line, loop_end_line, loop_count, skip_to_endloop, current_line


def pre_process_script_line(line, arg_input=None, debug=False):
    """Process a script line, handling quotes, expressions, and variable substitutions."""
    # Strip any newline characters or whitespace from the line
    line = line.strip(" \n\r")

    # Remove trailing colon, just in case
    line = line.strip(":")
    raw_split_line = line.split(" ")


    # Separate any parentheses joined to a word
    parentheses_buffer = []
    for word in raw_split_line:
        if re.match("\(\S*\)", word):
            parentheses_buffer.append("(")
            parentheses_buffer.append(word[1:-1])
            parentheses_buffer.append(")")
        elif re.match("\(\S*", word):
            parentheses_buffer.append("(")
            parentheses_buffer.append(word[1:])
        elif re.match("\S*\)", word) and not re.match("eos\(\S*\)", word):
            parentheses_buffer.append(word[:-1])
            parentheses_buffer.append(")")
        else:
            parentheses_buffer.append(word)

    raw_split_line = parentheses_buffer

    arithmetic_buffer = []
    for word in raw_split_line:
        if re.match("\S+\+\S+", word):
            word = word.split("+")
            arithmetic_buffer.append(word[0])
            arithmetic_buffer.append("+")
            arithmetic_buffer.append(word[1])
        elif re.match("\S+-\S+", word) and not re.match("#internal_\d+_[a-f0-9]{8}-?[a-f0-9]{4}-?4[a-f0-9]{3}-?[89ab][a-f0-9]{3}-?[a-f0-9]{12}#", word):
            word = word.split("-")
            arithmetic_buffer.append(word[0])
            arithmetic_buffer.append("-")
            arithmetic_buffer.append(word[1])
        else:
            arithmetic_buffer.append(word)

    raw_split_line = arithmetic_buffer

    # Check for strings in single quotes, and for expressions in parentheses
    active_expression_count = 0
    expressions = []
    string_active = False
    string_buffer = []
    split_line = []

    if debug:
        print("--- Processing next line. ---")

    # For each word:
    for word in raw_split_line:
        if debug:
            print("- Processing word: %s" % word)
        # Check if a string is active. If one is, expressions are ignored.
        if string_active:
            if debug:
                print("- String is active.")
            if re.match("\S*\"", word) or re.match("\S*'", word):
                # Word ends string, handle string ending
                if debug:
                    print("-- Word ends string. Processing.")
                string_buffer, expressions, split_line = handle_string_end(
                    word, string_buffer, active_expression_count, expressions, split_line)

                string_active = False

            else:
                # String is continuing, add the word to string_buffer
                if debug:
                    print("-- Word does not end string. Adding to string buffer.")
                string_buffer.append(word)
        else:
            # String is not active, check if the word starts a string
            if debug:
                print("- String is not active.")
            if re.match("\"\S*", word) or re.match("'\S*", word):
                # Word starts a string. Set string_active to True and add it to the string buffer.
                if debug:
                    print("-- Word starts string.")
                if re.match("\w*\"", word[1:]) or re.match("\w*'", word[1:]):
                    # This is a one word string. Handle the ending of the string:
                    if debug:
                        print("-- ...and ends it too. Processing.")
                    string_buffer, expressions, split_line = handle_string_end(
                        word, string_buffer, active_expression_count, expressions, split_line)

                    string_active = False
                else:
                    if debug:
                        print("-- ...but does not end it. Adding it to string buffer.")
                    # Word is the first word of a longer string. Set string variables and add word to string_buffer
                    string_active = True
                    word = word.strip("\"'")
                    string_buffer.append(word)
            else:
                # We're outside of a string. Check if the word is the start of an expression
                if debug:
                    print("- No active string.")
                if re.match("\(", word):
                    # Word starts an expression. Increment active_expression_count and add a new list to expressions
                    if debug:
                        print("-- Word starts expression. Increment count.")
                    active_expression_count += 1
                    expressions.append([])
                elif active_expression_count > 0:
                    # Check if word ends an expression.
                    if debug:
                        print("-- Expression is already active.")
                    if re.match("\)", word):
                        # Word ends the innermost expression, reduce active_expression_count and evaluate the expression.
                        if debug:
                            print("--- Word ends innermost expression. Evaluating expression.")
                        active_expression_count -= 1
                        expression_result = eval_expression(expressions.pop(), internal_variables, user_variables, dynamic_variables, arg_input=arg_input, debug=True)

                        if debug:
                            print("--- Innermost expression evaluated to %s." % str(expression_result))

                        # Check if there is still at least one active expression
                        if active_expression_count > 0:
                            # This was a nested expression. Append the result to the innermost remaining expression.
                            if debug:
                                print("---- Still within a nested expression. Appending expression result to that.")
                            expressions[-1].append(expression_result)
                        else:
                            # No expressions remain to be evaluated. Append the result to split_line
                            if debug:
                                print(
                                    "---- Not within any remaining expressions. Appending expression result to split_line.")
                            split_line.append(expression_result)
                    else:
                        # Word is part of an ongoing expression. Append it to the innermost expression.
                        if debug:
                            print("--- Word is part of an ongoing expression. Appending word to innermost expression.")
                        expressions[-1].append(word)
                else:
                    # Word is not part of a string or an expression, add it to split_line
                    if debug:
                        print("-- Word is not part of any string or expression. Appending to split_line.")
                    split_line.append(word)

            if debug:
                print("Word processed!")
                print("String active: ", string_active)
                print("String buffer: ", string_buffer)
                print("Active expression count: %i" % active_expression_count)
                print("Expressions: ", expressions)

    return split_line


def run_script(script: list, osc_client, osc_addr: str, osc_arg: list, internal_macros: list, internal_variables, user_variables, dynamic_variables, arg_input, debug=False ):
    """Run a script, then return Done."""
    run_action = True
    current_line = 0
    loop_active = False
    loop_start_line = None
    loop_end_line = None
    loop_count = 0
    skip_to_endloop = False
    loop_limit = 99
    if_active = False
    if_met = False
    if_cond_found = False

    while run_action:
        line = script[current_line]
        split_line = pre_process_script_line(line, arg_input=arg_input, debug=debug)

        # Get the opcode and the line statement
        opcode = split_line[0]
        line_statement = split_line[1:]

        # Increment current_line and read that line from the action
        current_line += 1
        if debug:
            print("STATUS: Current line: %i, opcode: %s" % (current_line, opcode))

        # If if_active is True and if_met is False, check if the opcode is else or endif. If not, skip the match since we aren't running that line.
        if loop_active and skip_to_endloop:
            if debug:
                print("STATUS: Loop active but broken, skipping to endloop.")
            # Disregard all but endloop
            if opcode == "endloop":
                if debug:
                    print("- Endloop found on line %i! Deactivating loop and resetting loop variables." % current_line)
                loop_active = False
                loop_start_line = None
                loop_end_line = None
                loop_count = 0
                skip_to_endloop = False
        elif if_active and not if_met:
            if debug:
                print("STATUS: If statement active but unmet, searching for elif, else, or endif.")
            # We're in an if statement, but the current line is not a valid part of it
            # Only respect elif, else and endif opcodes
            match opcode:
                case "elif":
                    # Check if the condition is met. If it is, set if_met and if_cond_found to True. Otherwise, pass.
                    if not if_cond_found and check_condition(line_statement, internal_variables, user_variables,
                                                             dynamic_variables, arg_input=arg_input):
                        if debug:
                            print(
                                "- Found valid elif on line %i! Setting if_met and if_cond_found to True" % current_line)
                        if_met = True
                        if_cond_found = True
                        pass
                    else:
                        pass
                case "else":
                    # If we haven't found the condition yet, we have now!
                    if not if_cond_found:
                        if debug:
                            print(
                                "- Found valid else on line %i! Setting if_met and if_cond_found to True" % current_line)
                        if_met = True
                        if_cond_found = True
                        pass
                    else:
                        pass
                case "endif":
                    if debug:
                        print("- Found valid endif on line %i! Deactivating if statement." % current_line)
                    if_active = False
                    if_met = False
                    if_cond_found = False

        elif (if_active and if_met) or (not if_active):
            if debug:
                if not if_active:
                    print("STATUS: Outside of if statement, running as usual.")
                else:
                    print("STATUS: If statement active, condition met. Running as usual.")
            # Switch case with all possible opcodes, set appropriate variables and call interpreter when one is found
            match opcode:
                case "osc":
                    # Send OSC to the given address, with the given arguments
                    # Syntax: osc /some/osc/address [argument_1] [argument_2] [argument_3]...
                    if debug:
                        print("- OSC command found on line %i. Processing!" % current_line)
                    _cleaned_osc_addr, _cleaned_osc_args = osc.process_osc(split_line[1], split_line[2:],
                                                                           internal_variables=internal_variables,
                                                                           user_variables=user_variables,
                                                                           dynamic_variables=dynamic_variables,
                                                                           arg_input=arg_input,
                                                                           debug=True)
                    osc_client.send_message(_cleaned_osc_addr, _cleaned_osc_args)
                    pass
                case "wait":
                    # Wait the listed amount of time in seconds
                    if debug:
                        print("- Wait command found on line %i. Processing!" % current_line)
                        print("-- Wait time: %s" % line_statement[0])
                    try:
                        time.sleep(value.parse_script_word(line_statement[0], internal_variables, user_variables,
                                                               dynamic_variables, arg_input=arg_input))
                    except TypeError:
                        # Invalid time
                        pass
                case "loop":
                    # Mark the current line as the start of a loop (Don't do the next line, Stark. Trust me.)
                    # Set loop_active to True and loop_start_line to the next line
                    # TODO: Handle cases where this is the last line of the file, and there isn't a loop
                    # Syntax: loop
                    if debug:
                        print("- Loop command found on line %i. Processing!" % current_line)
                    if loop_active:
                        if debug:
                            print("-- A loop is already active. Ignoring loop command.")
                        # Only one loop at a time is allowed, do nothing
                        pass
                    else:
                        if debug:
                            print("-- Starting new loop. Setting loop_active to True, "
                                  "loop_start_line to %i, and resetting loop_count." % current_line)
                        loop_active = True
                        loop_start_line = current_line
                        loop_end_line = None
                        loop_count = 0
                        skip_to_endloop = False
                case "endloop":
                    # Mark the previous line as the end of a loop
                    # Set loop_end_line to the previous line
                    # TODO: Handle cases where this is the start of the file, and there isn't a loop
                    # Syntax: endloop
                    loop_active, loop_start_line, loop_end_line, loop_count, skip_to_endloop, current_line = (
                        handle_endloop(loop_active, loop_start_line, loop_count, loop_limit, skip_to_endloop,
                                                 current_line, debug=debug))

                case "new":
                    # Create a new user variable with the given name and value
                    # Syntax: new new_var_name = new_var_value
                    if debug:
                        print("- New command found at line %i. Processing!" % current_line)
                    user_variables = variables.add_user_variable(line_statement[0],
                                                value.parse_script_word(line_statement[2], internal_variables,
                                                                            user_variables, dynamic_variables,
                                                                            arg_input=arg_input, debug=debug),
                                                user_variables, debug=debug)
                case "newint":
                    # Create a new internal variable with the given name and value
                    # Syntax: new new_var_name = new_var_value
                    if debug:
                        print("- Newint command found at line %i. Processing!" % current_line)
                    internal_variables = variables.add_internal_variable(line_statement[0],
                                                                         value.parse_script_word(line_statement[2],
                                                                                                 internal_variables,
                                                                                                 user_variables,
                                                                                                 dynamic_variables,
                                                                                                 arg_input=arg_input,
                                                                                                 debug=debug),
                                                                         internal_variables, debug=debug)
                case "set":
                    # Set an existing user variable with the given name to a new value
                    # Syntax 1: set existing_var = other_existing_var (get the value from the other variable)
                    # Syntax 2: set existing_var = new_value (set it to a new value)
                    # Syntax 3: set existing_var = existing_var_or_value + existing_var_or_value (add ints or floats, or concatenate strings. Does not affect bools)
                    # Syntax 4: set existing_var = existing_var_or_value - existing_var_or_value (subtract ints or floats. Does not affect strings or bools)
                    if debug:
                        print("- Set command found at line %i. Processing!" % current_line)
                        print("- Variable name: %s" % line_statement[0])
                    if re.match("\*\w+\*", line_statement[0]):
                        # User variable
                        if debug:
                            print("-- Variable is a user variable.")
                        try:
                            user_variables = variables.set_user_variable(line_statement[0], eval_expression(line_statement[2:],
                                                                                                     internal_variables,
                                                                                                     user_variables,
                                                                                                     dynamic_variables,
                                                                                                     arg_input=arg_input,
                                                                                                     debug=debug),
                                                        user_variables, debug=debug)
                        except IndexError:
                            if debug:
                                print("Improper syntax. Variable was not set.")
                    elif re.match("#\w+#", line_statement[0]):
                        # Internal variable
                        if debug:
                            print("-- Variable is an internal variable.")
                        try:
                            internal_variables = variables.set_internal_variable(line_statement[0],
                                                            eval_expression(line_statement[2:],
                                                                                      internal_variables,
                                                                                      user_variables, dynamic_variables,
                                                                                      arg_input=arg_input, debug=True))
                        except IndexError:
                            if debug:
                                print("Improper syntax. Variable was not set.")
                    else:
                        if debug:
                            print("-- Variable is not a user or internal variable. Passing")
                        # Not a user or internal variable, do nothing
                        pass
                case "del":
                    # Delete an existing user variable with the given name
                    # Syntax: del existing_var
                    if debug:
                        print("- Del command found at line %i. Processing!" % current_line)
                        print("- Variable name: %s" % line_statement[0])
                    if re.match("\*\w+\*", line_statement[0]):
                        # User variable
                        if debug:
                            print("-- Variable is a user variable.")
                        user_variables = variables.delete_user_variable(line_statement[0], debug=True)
                    elif re.match("#\w+#", line_statement[0]):
                        # Internal variable
                        if debug:
                            print("-- Variable is an internal variable.")
                        internal_variables = variables.delete_internal_variable(line_statement[0], debug=True)
                    else:
                        # Not a user or internal variable, do nothing
                        if debug:
                            print("-- Variable is neither a user or internal variable. Passing.")
                        pass
                case "if":
                    # Start an if statement which will only continue if the condition is met. Set if_active to true.
                    # If the condition is met, set if_met to True and if_cond_found to True
                    # If the condition is not met, set if_met to False and skip to either the next else or endif.
                    # Syntax 1: if existing_var_or_value = other_existing_var_or_value
                    # Syntax 2: if existing_var_or_value > other_existing_var_or_value
                    # Syntax 3: if existing_var_or_value < other_existing_var_or_value
                    # Syntax 4: if existing_var_or_value >= other_existing_var_or_value
                    # Syntax 5: if existing_var_or_value <= other_existing_var_or_value
                    # Syntax 6: if existing_var_or_value != other_existing_var_or_value
                    # Syntax 7: if existing_var (check if variable exists)
                    if debug:
                        print("- If command found at line %i. Processing!" % current_line)
                    if not if_active:
                        if debug:
                            print("-- If statement is not active yet. Activating!")
                            print("-- Checking if condition is met...")
                        if_active = True
                        if check_condition(line_statement, internal_variables, user_variables,
                                                     dynamic_variables, arg_input=arg_input):
                            if debug:
                                print("-- Condition met! Setting if_met and if_cond_found to True.")
                            if_met = True
                            if_cond_found = True
                        else:
                            if debug:
                                print("-- Condition not met. Setting if_met and if_cond_found to False.")
                            if_met = False
                            if_cond_found = False
                    else:
                        if debug:
                            print("-- If statement already active. Passing.")
                        # Nested if statements are not allowed, pass
                        pass

                    # Check if the condition has been met, then set if_met and if_cond_found appropriately
                case "elif":
                    # Add a case to an if statement which will only be triggered if previous conditions are not met.
                    # If the condition is met, set if_met to True and if_cond_found to True
                    # Syntax: Same as "if" opcode above.
                    if debug:
                        print("- Elif statement found at line %i! Processing." % current_line)
                    if if_active:
                        if debug:
                            print(
                                "-- If statement is active. Checking if condition has already been found and if condition is met.")
                        if not if_cond_found and check_condition(line_statement, internal_variables,
                                                                           user_variables, dynamic_variables,
                                                                           arg_input=arg_input):
                            if debug:
                                print(
                                    "-- Condition met/Condition not previously found! Setting if_met and if_cond_found to True.")
                            if_met = True
                            if_cond_found = True
                        else:
                            # We've finished the elif statement, reset if_met
                            if debug:
                                print("-- Condition not met. Setting if_met to False.")
                            if_met = False
                    else:
                        # Invalid syntax, ignore it
                        if debug:
                            print("-- Invalid syntax (elif outside of if statement. Passing.")
                        pass
                    pass
                case "else":
                    # Start an else statement if if_active is True and if_met is False. Set if_met to True and if_cond_found to True
                    # Set if_met to True so the next lines run.
                    # Syntax: else
                    if debug:
                        print("- Else statement found at line %i! Processing." % current_line)
                    if if_active:
                        if debug:
                            print("-- If statement active. Checking if condition has already been met.")
                        if not if_cond_found:
                            if debug:
                                print(
                                    "-- Condition had not already been met! Setting if_met and if_cond_found to True.")
                            if_met = True
                            if_cond_found = True
                        else:
                            # We already found the condition, pass
                            if debug:
                                print("-- Condition has already been met. Passing.")
                            pass
                    else:
                        # Invalid syntax, pass
                        if debug:
                            print("-- Invalid syntax (else statement outside of if statement). Passing.")
                        pass
                case "endif":
                    # End an if/else statement. Set if_active and if_met to False.
                    # Syntax: endif
                    if debug:
                        print(
                            "- Endif statement found at line %i! Deactivating if statement and resetting if variables." % current_line)
                    if_active = False
                    if_met = False
                    if_cond_found = False
                case "break":
                    # Break a running loop and skip to the end of it.
                    # Set loop_active to False, then set skip_to_endloop to True
                    # Syntax: break
                    if debug:
                        print("- Break statement found at line %i! Processing." % current_line)
                    if loop_active:
                        if debug:
                            print("-- Loop active. Setting loop_active to False.")
                        loop_active = False
                        if loop_end_line is not None:
                            if debug:
                                print(
                                    "-- Loop end line is known. Setting current_line to loop_end_line and resetting variables.")
                                current_line = loop_end_line
                                loop_start_line = None
                                loop_end_line = None
                                loop_count = 0
                                skip_to_endloop = False
                        else:
                            if debug:
                                print("-- Loop end line is unknown. Setting skip_to_endloop to True.")
                            skip_to_endloop = True
                case "pass":
                    if debug:
                        print("- Pass statement found at line %i! Passing." % current_line)
                    # Do nothing.
                    # Syntax: pass
                    pass
                case "comment":
                    if debug:
                        print("- Comment found at line %i! Ignoring." % current_line)
                    # Do nothing with this line
                    pass
                case _:
                    if debug:
                        print("- Unknown opcode %s found at line %i. Passing." % (opcode, current_line))
        # Delete all eos query variables

        # Check if incrementing the line would go out of the action. If so, stop the action.
        print(current_line)
        print(len(script))
        if current_line + 1 > len(script):
            run_action = False
    if debug:
        print("Returning 'done'.")
    return ("done", "")
