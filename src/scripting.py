import re
import time

import variables
import conditions
import value
import osc

def eval_expression(expression, uuid, internal_variables, user_variables, dynamic_variables,
                    eos_query_count=0, arg_input=None, debug=False):
    """Try to evaluate a script expression, and return the result"""
    if debug:
        print("Evaluating expression: ", expression)

    if len(expression) == 1:
        # One word expressions are just a wrapped value, evaluate and return
        if debug:
            print("Expression is one word long. Returning evaluated word.")

        collected_variables = {"internal_variables": internal_variables,
                               "user_variables": user_variables,
                               "dynamic_variables": dynamic_variables,
                               "eos_query_count": eos_query_count}

        expression_value = value.parse_script_word(expression[0], uuid, collected_variables,
                                                   arg_input=arg_input)

        if isinstance(expression_value, tuple):
            # Word was an eos query, set the eos_query_count
            if debug:
                print(f"Updating eos_query_count to {expression_value[1]}")
            eos_query_count = expression_value[1]
            expression_value = expression_value[0]

            return expression_value, eos_query_count

        return expression_value

    if len(expression) == 3:
        # Three word expressions can be addition or subtraction
        if debug:
            print("Expression is three words long.")

        # Set up collected_variables
        collected_variables = {"internal_variables": internal_variables,
                               "user_variables": user_variables,
                               "dynamic_variables": dynamic_variables,
                               "eos_query_count": eos_query_count}

        old_eos_query_count = eos_query_count

        if expression[1] == "+":
            if debug:
                print("Expression is attempting addition.")

            first_value = value.parse_script_word(expression[0], uuid, collected_variables,
                                                  arg_input=arg_input)

            if isinstance(first_value, tuple):
                # Word was an eos query, set the eos_query_count
                if debug:
                    print(f"Updating eos_query_count to {first_value[1]}")
                eos_query_count = first_value[1]
                collected_variables["eos_query_count"] = eos_query_count
                first_value = first_value[0]

            second_value = value.parse_script_word(expression[2], uuid, collected_variables,
                                                   arg_input=arg_input)

            if isinstance(first_value, tuple):
                # Word was an eos query, set the eos_query_count
                if debug:
                    print(f"Updating eos_query_count to {second_value[1]}")
                eos_query_count = second_value[1]
                second_value = second_value[0]

            try:
                if eos_query_count > old_eos_query_count:
                    return first_value + second_value, eos_query_count

                return first_value + second_value
            except TypeError:
                if debug:
                    print("Conventional addition impossible, returning concatenated strings.")

                if eos_query_count > old_eos_query_count:
                    return (str(first_value) + str(second_value)), eos_query_count

                return str(first_value) + str(second_value)

        elif expression[1] == "-":
            first_value = value.parse_script_word(expression[0], uuid, collected_variables,
                                                  arg_input=arg_input)
            if isinstance(first_value, tuple):
                # Word was an eos query, set the eos_query_count
                if debug:
                    print(f"Updating eos_query_count to {first_value[1]}")
                eos_query_count = first_value[1]
                collected_variables["eos_query_count"] = eos_query_count
                first_value = first_value[0]

            second_value = value.parse_script_word(expression[2], uuid, collected_variables,
                                                   arg_input=arg_input)

            if isinstance(first_value, tuple):
                # Word was an eos query, set the eos_query_count
                if debug:
                    print(f"Updating eos_query_count to {second_value[1]}")
                eos_query_count = second_value[1]
                second_value = second_value[0]

            if debug:
                print("Expression is attempting subtraction.")
            try:
                if eos_query_count > old_eos_query_count:
                    return first_value - second_value, eos_query_count

                return first_value - second_value
            except TypeError:
                if debug:
                    print("Subtraction failed, returning first word in expression.")
                if eos_query_count > old_eos_query_count:
                    return first_value, eos_query_count

                return first_value
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


def handle_endloop(loop_active, loop_start_line, loop_count, loop_limit, skip_to_endloop,
                   current_line, debug=False):
    """Handle an endloop opcode during line preprocessing."""
    if debug:
        print(f"- Endloop command found on line {current_line}. Processing!")

    # Set the loop_end_line for increased performance when the loop ends
    loop_end_line = current_line - 1

    # Handle cases where endloop was mistakenly placed on the first line
    loop_end_line = max(loop_end_line, 0)

    if debug:
        print(f"-- Set loop_end_line to {loop_end_line}")

    # Increment the loop counter
    if loop_active:
        loop_count += 1

        if debug:
            print(f"-- Loop is currently active. Incremented loop counter to {loop_count}")

        # If the loop count is greater than the loop limit, stop looping.
        # Otherwise, go to the top of the loop
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
                print(f"-- Loop count is below limit. Resetting current line to {loop_start_line}")
            current_line = loop_start_line
    else:
        # We've finished the loop, do nothing
        if debug:
            print("-- Loop finished naturally, passing.")

    return loop_active, loop_start_line, loop_end_line, loop_count, skip_to_endloop, current_line


def pre_process_script_line(line, uuid, internal_variables, user_variables, dynamic_variables,
                            eos_query_count=0, arg_input=None, debug=False):
    """Process a script line, handling quotes, expressions,
    and variable substitutions inside either."""
    # Strip any newline characters or whitespace from the line
    line = line.strip(" \n\r")

    # Remove trailing colons from all lines, in case the user included one
    line = line.strip(":")

    # Split the line into words
    raw_split_line = line.split(" ")

    # Separate any parentheses joined to a word as long as they aren't part of an Eos query
    parentheses_buffer = []
    for word in raw_split_line:
        if re.match("\(\S*\)", word):
            parentheses_buffer.append("(")
            parentheses_buffer.append(word[1:-1])
            parentheses_buffer.append(")")
        elif re.match("\(\S+", word):
            parentheses_buffer.append("(")
            parentheses_buffer.append(word[1:])
        elif re.match("\S+\)", word) and not re.match("eos\(\S*\)", word):
            parentheses_buffer.append(word[:-1])
            parentheses_buffer.append(")")
        else:
            parentheses_buffer.append(word)

    raw_split_line = parentheses_buffer
    if debug:
        print(f"After parentheses: {raw_split_line}")

    # Split arithmetic expressions formatted as a single word.
    # Also check that the word is not a UUID.
    arithmetic_buffer = []
    for word in raw_split_line:
        if re.match("\S+\+\S+", word):
            word = word.split("+")
            arithmetic_buffer.append(word[0])
            arithmetic_buffer.append("+")
            arithmetic_buffer.append(word[1])
        elif (re.match("\S+-\S+", word) and not re.match(
                    ".*[a-f0-9]{8}-?[a-f0-9]{4}-?4[a-f0-9]{3}-?[89ab][a-f0-9]{3}-?[a-f0-9]{12}#?",
                    word)):
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

    for word in raw_split_line:
        if debug:
            print(f"- Processing word: {word}")

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
                    # Word is the first word of a longer string.
                    # Set string variables and add word to string_buffer
                    string_active = True
                    word = word.strip("\"'")
                    string_buffer.append(word)
            else:
                # We're outside a string. Check if the word is the start of an expression
                if debug:
                    print("- No active string.")

                if re.match("\(", word):
                    # Word starts an expression.
                    # Increment active_expression_count and add a new list to expressions
                    if debug:
                        print("-- Word starts expression. Increment count.")
                    active_expression_count += 1
                    expressions.append([])

                elif active_expression_count > 0:
                    # Check if word ends an expression.
                    if debug:
                        print("-- Expression is already active.")
                    if re.match("\)", word):
                        # Word ends the innermost expression,
                        # reduce active_expression_count and evaluate the expression.
                        if debug:
                            print("--- Word ends innermost expression. Evaluating expression.")
                        active_expression_count -= 1
                        expression_result = eval_expression(expressions.pop(), uuid,
                                                            internal_variables, user_variables,
                                                            dynamic_variables, arg_input=arg_input,
                                                            eos_query_count=eos_query_count,
                                                            debug=debug)

                        if isinstance(expression_result, tuple):
                            if debug:
                                print(f"Updating eos_query_count to {expression_result[1]}")
                            eos_query_count = expression_result[1]
                            expression_result = expression_result[0]

                        if debug:
                            print(f"--- Innermost expression evaluated to "
                                  f"{str(expression_result)}.")

                        # Check if there is still at least one active expression
                        if active_expression_count > 0:
                            # This was a nested expression.
                            # Append the result to the innermost remaining expression.
                            if debug:
                                print("---- Still within a nested expression. "
                                      "Appending expression result to that.")
                            expressions[-1].append(expression_result)
                        else:
                            # No expressions remain to be evaluated. Append the result to split_line
                            if debug:
                                print(
                                    "---- Not within any remaining expressions. "
                                    "Appending expression result to split_line.")
                            split_line.append(expression_result)
                    else:
                        # Word is part of an ongoing expression.
                        # Append it to the innermost expression.
                        if debug:
                            print("--- Word is part of an ongoing expression. "
                                  "Appending word to innermost expression.")
                        expressions[-1].append(word)
                else:
                    # Word is not part of a string or an expression, add it to split_line
                    if debug:
                        print("-- Word is not part of any string or expression. "
                              "Appending to split_line.")
                    split_line.append(word)

            if debug:
                print("Word processed!")

    return split_line, eos_query_count


def run_script(script: list, osc_client, uuid, internal_macros: list, internal_variables,
               user_variables, dynamic_variables, arg_input, eos_query_count=0, debug=False):
    """Run a script, then return Done and internal macros."""
    # Set up variables which track the overall state of the action
    run_action = True
    current_line = 0

    # Set up variables that track loops
    loop_active = False
    loop_start_line = None
    loop_end_line = None
    loop_count = 0
    skip_to_endloop = False
    loop_limit = 99

    # Set up variables that track if statements
    if_active = False
    if_met = False
    if_cond_found = False

    # Run the action until run_action is set to False
    # when the next line would pass the end of the action.
    while run_action:
        line = script[current_line]

        # Pre-process every line, resolving expressions and strings
        split_line, eos_query_count = pre_process_script_line(line, uuid, internal_variables,
                                                              user_variables, dynamic_variables,
                                                              eos_query_count=eos_query_count,
                                                              arg_input=arg_input, debug=debug)

        if isinstance(split_line, tuple):
            # Eos query was included in an expression in the line
            if debug:
                print(f"Updating eos_query_count to {split_line[1]}")
            eos_query_count = split_line[1]
            split_line = split_line[0]

        # Get the opcode (first word) and the line statement (all other words)
        opcode = split_line[0]
        line_statement = split_line[1:]

        # Increment current_line and read that line from the action
        current_line += 1

        # Set up collected_variables
        collected_variables = {"internal_variables": internal_variables,
                               "user_variables": user_variables,
                               "dynamic_variables": dynamic_variables,
                               "eos_query_count": eos_query_count}
        if debug:
            print(f"STATUS: Current line: {current_line}, opcode: {opcode}, "
                  f"eos_query_count: {eos_query_count}")

        # If if_active is True and if_met is False, check if the opcode is else or endif.
        # If not, skip the match since we aren't running that line.
        if loop_active and skip_to_endloop:
            if debug:
                print("STATUS: Loop active but broken, skipping to endloop.")

            # Disregard all but endloop, since the loop has been broken
            if opcode == "endloop":
                if debug:
                    print(f"- Endloop found on line {current_line}! "
                          f"Deactivating loop and resetting loop variables.")

                loop_active = False
                loop_start_line = None
                loop_end_line = None
                loop_count = 0
                skip_to_endloop = False

        elif if_active and not if_met:
            # We're in an if statement, but the current line is not a valid part of it
            # Only respect elif, else and endif opcodes,
            # Which indicate that we should update the if statement's status
            if debug:
                print("STATUS: If statement active but unmet, searching for elif, else, or endif.")

            match opcode:
                case "elif":
                    # Check if the condition is met. If it is, set if_met and if_cond_found to True.
                    # Otherwise, pass.
                    condition_result = conditions.check_condition(line_statement, uuid,
                                                                  collected_variables,
                                                                  arg_input=arg_input, debug=debug)

                    if isinstance(condition_result, tuple):
                        # Condition contained eos_query, update eos_query_count
                        if debug:
                            print(f"Updating eos_query_count to {condition_result[1]}")

                        eos_query_count = condition_result[1]
                        condition_result = condition_result[0]

                    if not if_cond_found and condition_result:
                        # Condition was met
                        # Ensure the condition's contents are read in the upcoming lines
                        if debug:
                            print(
                                f"- Found valid elif on line {current_line}! "
                                f"Setting if_met and if_cond_found to True")
                        if_met = True
                        if_cond_found = True

                    else:
                        # Condition was not met
                        pass

                case "else":
                    # If we haven't found the condition yet, this is the catch all case.
                    if not if_cond_found:
                        if debug:
                            print(f"- Found valid else on line {current_line}! "
                                  f"Setting if_met and if_cond_found to True")

                        if_met = True
                        if_cond_found = True

                    else:
                        pass

                case "endif":
                    # If statement ends here
                    if debug:
                        print(f"- Found valid endif on line {current_line}! "
                              f"Deactivating if statement.")
                    if_active = False
                    if_met = False
                    if_cond_found = False

        elif (not if_active) or (if_active and if_met):
            # Default case when a line is going to be run
            # Either outside an if statement or in a met condition inside an if statement.
            if debug:
                if not if_active:
                    print("STATUS: Outside of if statement, running as usual.")
                else:
                    print("STATUS: If statement active, condition met. Running as usual.")

            # Switch case with all possible opcodes
            # Set appropriate variables and resolve action when one is found
            # Set up collected_variables
            collected_variables = {"internal_variables": internal_variables,
                                   "user_variables": user_variables,
                                   "dynamic_variables": dynamic_variables,
                                   "eos_query_count": eos_query_count}
            match opcode:
                case "osc":
                    # Send OSC to the given address, with the given arguments
                    # Syntax: osc /some/osc/address argument_1 argument_2 argument_3...
                    if debug:
                        print(f"- OSC command found on line {current_line}. Processing!")

                    osc_data = {"osc_addr": split_line[1],
                                "osc_args": split_line[2:]}
                    _cleaned_osc_addr, _cleaned_osc_args, eos_query_count = (
                        osc.process_osc(uuid, osc_data, collected_variables,
                                        arg_input=arg_input, debug=debug))

                    collected_variables["eos_query_count"] = eos_query_count

                    osc_client.send_message(_cleaned_osc_addr, _cleaned_osc_args)

                case "wait":
                    # Wait the listed amount of time in seconds
                    if debug:
                        print(f"- Wait command found on line {current_line}. Processing!")
                        print(f"-- Wait time: {line_statement[0]}")

                    try:
                        sleep_duration = value.parse_script_word(line_statement[0], uuid,
                                                                 collected_variables,
                                                                 arg_input=arg_input, debug=debug)

                        if isinstance(sleep_duration, tuple):
                            if debug:
                                print(f"Updating eos_query_count to {sleep_duration[1]}")
                            eos_query_count = sleep_duration[1]
                            sleep_duration = sleep_duration[0]

                        time.sleep(sleep_duration)
                    except TypeError:
                        # Invalid time
                        pass

                case "loop":
                    # Mark the current line as the start of a loop
                    # (Don't do the next line, Stark. Trust me.)
                    # Set loop_active to True and loop_start_line to the next line
                    # Syntax: loop
                    if debug:
                        print(f"- Loop command found on line {current_line}. Processing!")

                    if loop_active:
                        if debug:
                            print("-- A loop is already active. Ignoring loop command.")
                        # Only one loop at a time is allowed, do nothing

                    else:
                        if debug:
                            print("-- Starting new loop. Setting loop_active to True, "
                                  f"loop_start_line to {current_line}, and resetting loop_count.")
                        loop_active = True
                        loop_start_line = current_line
                        loop_end_line = None
                        loop_count = 0
                        skip_to_endloop = False

                case "endloop":
                    # Mark the previous line as the end of a loop
                    # Set loop_end_line to the previous line
                    # Syntax: endloop
                    (loop_active, loop_start_line, loop_end_line, loop_count, skip_to_endloop,
                     current_line) = (handle_endloop(loop_active, loop_start_line, loop_count,
                                                     loop_limit, skip_to_endloop, current_line,
                                                     debug=debug))

                case "new":
                    # Create a new user variable with the given name and value
                    # Syntax: new new_var_name = new_var_value
                    if debug:
                        print(f"- New command found at line {current_line}. Processing!")

                    variable_value = value.parse_script_word(line_statement[2], uuid,
                                                             collected_variables,
                                                             arg_input=arg_input, debug=debug)

                    if isinstance(variable_value, tuple):
                        if debug:
                            print(f"Updating eos_query_count to {variable_value[1]}")
                        eos_query_count = variable_value[1]
                        variable_value = variable_value[0]

                    user_variables = variables.add_user_variable(line_statement[0], variable_value,
                                                                 user_variables, debug=debug)
                case "newint":
                    # Create a new internal variable with the given name and value
                    # Syntax: new new_var_name = new_var_value
                    if debug:
                        print(f"- Newint command found at line {current_line}. Processing!")

                    variable_value = value.parse_script_word(line_statement[2], uuid,
                                                             collected_variables,
                                                             arg_input=arg_input, debug=debug)

                    if isinstance(variable_value, tuple):
                        if debug:
                            print(f"Updating eos_query_count to {variable_value[1]}")
                        eos_query_count = variable_value[1]
                        variable_value = variable_value[0]

                    internal_variables = variables.add_internal_variable(line_statement[0],
                                                                         variable_value,
                                                                         internal_variables,
                                                                         debug=debug)

                case "set":
                    # Set an existing user variable with the given name to a new value
                    # Syntax: set existing_var = new_value_or_var
                    if debug:
                        print(f"- Set command found at line {current_line}. Processing!")
                        print(f"- Variable name: {line_statement[0]}")

                    if re.match("\*\w+\*", line_statement[0]):
                        # User variable
                        if debug:
                            print("-- Variable is a user variable.")

                        try:
                            expression_result = eval_expression(line_statement[2:], uuid,
                                                                internal_variables, user_variables,
                                                                dynamic_variables,
                                                                arg_input=arg_input,
                                                                eos_query_count=eos_query_count,
                                                                debug=debug)

                            if isinstance(expression_result, tuple):
                                if debug:
                                    print(f"Updating eos_query_count to {expression_result[1]}")
                                eos_query_count = expression_result[1]
                                expression_result = expression_result[0]
                            user_variables = variables.set_user_variable(line_statement[0],
                                                                         expression_result,
                                                                         user_variables,
                                                                         debug=debug)
                        except IndexError:
                            if debug:
                                print("Improper syntax. Variable was not set.")

                    elif re.match("#\w+#", line_statement[0]):
                        # Internal variable
                        if debug:
                            print("-- Variable is an internal variable.")
                        try:
                            internal_variables = variables.set_internal_variable(
                                line_statement[0], internal_variables, eval_expression(
                                    line_statement[2:], uuid, internal_variables, user_variables,
                                    dynamic_variables, arg_input=arg_input,
                                    eos_query_count=eos_query_count, debug=debug))
                        except IndexError:
                            if debug:
                                print("Improper syntax. Variable was not set.")

                    else:
                        if debug:
                            print("-- Variable is not a user or internal variable. Passing")
                        # Not a user or internal variable, do nothing

                case "del":
                    # Delete an existing user variable with the given name
                    # Syntax: del existing_var
                    if debug:
                        print(f"- Del command found at line {current_line}. Processing!")
                        print(f"- Variable name: {line_statement[0]}")

                    if re.match("\*\w+\*", line_statement[0]):
                        # User variable
                        if debug:
                            print("-- Variable is a user variable.")
                        user_variables = variables.delete_user_variable(line_statement[0],
                                                                        user_variables, debug=True)

                    elif re.match("#\w+#", line_statement[0]):
                        # Internal variable
                        if debug:
                            print("-- Variable is an internal variable.")
                        internal_variables = variables.delete_internal_variable(line_statement[0],
                                                                                internal_variables,
                                                                                debug=True)

                    else:
                        # Not a user or internal variable, do nothing
                        if debug:
                            print("-- Variable is neither a user or internal variable. Passing.")

                case "if":
                    # Start an if statement
                    # which will only continue if the condition is met.
                    # Set if_active to true.
                    # If the condition is met, set if_met to True and if_cond_found to True
                    # If the condition is not met,
                    # set if_met to False and skip to either the next else or endif.
                    # Syntax: if [not] existing_var_or_value [operator] other_existing_var_or_value
                    if debug:
                        print(f"- If command found at line {current_line}. Processing!")
                    if not if_active:
                        if debug:
                            print("-- If statement is not active yet. Activating!")
                            print("-- Checking if condition is met...")

                        if_active = True
                        condition_result = conditions.check_condition(line_statement, uuid,
                                                           collected_variables,
                                                           arg_input=arg_input, debug=debug)

                        if isinstance(condition_result, tuple):
                            # Condition contained eos_query, update eos_query_count
                            if debug:
                                print(f"Updating eos_query_count to {condition_result[1]}")

                            eos_query_count = condition_result[1]
                            condition_result = condition_result[0]

                        if condition_result:
                            if debug:
                                print("-- Condition met! "
                                      "Setting if_met and if_cond_found to True.")

                            if_met = True
                            if_cond_found = True

                        else:
                            if debug:
                                print("-- Condition not met. "
                                      "Setting if_met and if_cond_found to False.")

                            if_met = False
                            if_cond_found = False

                    else:
                        if debug:
                            print("-- If statement already active. Passing.")
                        # Nested if statements are not allowed, pass

                case "elif":
                    # Add a case to an if statement
                    # which will only be triggered if previous conditions are not met.
                    # If the condition is met, set if_met to True and if_cond_found to True
                    # Syntax: Same as "if" opcode above.
                    # !!!!!! Start !!!!!!
                    # !!!!!! End !!!!!!
                    if debug:
                        print(f"- Elif statement found at line {current_line}! Processing.")

                    if if_active:
                        if debug:
                            print(
                                "-- If statement is active. "
                                "Checking if condition has already been found "
                                "and if condition is met.")

                        condition_result = conditions.check_condition(line_statement, uuid,
                                                           collected_variables,
                                                           arg_input=arg_input,
                                                           debug=debug)

                        if isinstance(condition_result, tuple):
                            # Condition contained eos_query, update eos_query_count
                            if debug:
                                print(f"Updating eos_query_count to {condition_result[1]}")

                            eos_query_count = condition_result[1]
                            condition_result = condition_result[0]

                        if not if_cond_found and condition_result:
                            if debug:
                                print(
                                    "-- Condition met/Condition not previously found! "
                                    "Setting if_met and if_cond_found to True.")

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

                case "else":
                    # Start an else statement if if_active is True and if_met is False.
                    # Set if_met to True and if_cond_found to True
                    # Set if_met to True so the next lines run.
                    # Syntax: else
                    if debug:
                        print(f"- Else statement found at line {current_line}! Processing.")

                    if if_active:
                        if debug:
                            print("-- If statement active. "
                                  "Checking if condition has already been met.")

                        if not if_cond_found:
                            if debug:
                                print(
                                    "-- Condition had not already been met! "
                                    "Setting if_met and if_cond_found to True.")

                            if_met = True
                            if_cond_found = True

                        else:
                            # We already found the condition, pass
                            if debug:
                                print("-- Condition has already been met. Passing.")

                    else:
                        # Invalid syntax, pass
                        if debug:
                            print("-- Invalid syntax (else statement "
                                  "outside of if statement). Passing.")

                case "endif":
                    # End an if/else statement. Set if_active and if_met to False.
                    # Syntax: endif
                    if debug:
                        print(
                            f"- Endif statement found at line {current_line}! "
                            f"Deactivating if statement and resetting if variables.")

                    if_active = False
                    if_met = False
                    if_cond_found = False

                case "break":
                    # Break a running loop and skip to the end of it.
                    # Set loop_active to False, then set skip_to_endloop to True
                    # Syntax: break
                    if debug:
                        print(f"- Break statement found at line {current_line}! Processing.")

                    if loop_active:
                        if debug:
                            print("-- Loop active. Setting loop_active to False.")

                        loop_active = False

                        if loop_end_line is not None:
                            if debug:
                                print(
                                    "-- Loop end line is known. Setting current_line "
                                    "to loop_end_line and resetting variables.")

                                current_line = loop_end_line
                                loop_start_line = None
                                loop_end_line = None
                                loop_count = 0
                                skip_to_endloop = False

                        else:
                            if debug:
                                print("-- Loop end line is unknown. "
                                      "Setting skip_to_endloop to True.")

                            skip_to_endloop = True

                case "wipeints":
                    # Delete all internal macros
                    internal_macros = []

                case "run":
                    if debug:
                        print(f"- Run statement found at line {current_line}! Running new macro.")
                        macro_uuid_to_run = line_statement[0]
                        return "run", macro_uuid_to_run, internal_macros

                case "pass":
                    if debug:
                        print(f"- Pass statement found at line {current_line}! Passing.")
                    # Do nothing.
                    # Syntax: pass

                case "comment":
                    if debug:
                        print(f"- Comment found at line {current_line}! Ignoring.")
                    # Do nothing with this line

                case _:
                    if debug:
                        print(f"- Unknown opcode {opcode} found at line {current_line}. Passing.")

        # Check if incrementing the line would go out of the action. If so, stop the action.
        if current_line + 1 > len(script):
            run_action = False

    if debug:
        print("Returning 'done'.")

    # Delete all relevant internal variables and macros
    return "done", "", internal_macros
