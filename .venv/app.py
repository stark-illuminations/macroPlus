import datetime
import json
import math
import time
import xml.etree.ElementTree as ET
import uuid
import os
import re

from flask import Flask, render_template, request
from pythonosc import udp_client

macro_cooldown_time = 1
internal_macros = []
user_macros = []
internal_variables = []
user_variables = []


def start_osc_client(network_config):
    """Start a new OSC server and client to connect to the console"""
    try:
        osc_client = udp_client.SimpleUDPClient(network_config[0], int(network_config[1]))
        osc_client.send_message("/eos/ping", "macroPlus")
        return osc_client
    except ValueError:
        print("Bad config")
        return "Invalid network config. Try again."


def load_macros(return_tree=False):
    """Load macros config from XML file"""
    # Open and read the macro config file
    with open("config/macros.xml", "r") as macro_file:
        macro_tree = ET.parse(macro_file)
        if return_tree:
            return macro_tree

    # Parse the macros from the freshly-read file
    macro_root = macro_tree.getroot()
    macro_list = macro_root.findall("macro")

    return macro_list


def parse_macros(macro_list):
    # Generate the information for the macro list on the page
    main_macro_list = []
    for macro in macro_list:
        # Open the macro's file and pull in the relevant trigger and action
        try:
            with open(macro.find("path").text, "r") as macro_file:
                macro_action = macro_file.read()
                for line in macro_action:
                    line = line.strip()
        except FileNotFoundError:
            macro_action = ""
        # Make a dictionary with the information about the macro
        macro_dict = {"uuid": macro.find("uuid").text,
                      "name": macro.find("name").text,
                      "trigger_type": macro.find("trigger_type").text,
                      "trigger": macro.find("trigger").text,
                      "arg_index": macro.find("arg_index").text,
                      "action": macro_action}
        # Make that dictionary the value of the macro's entry in the main list
        main_macro_list.append(macro_dict)

    return main_macro_list


def add_user_macro(name, trigger, action, uuid, arg_index, path=""):
    """Add a new user macro to user_macros"""
    global user_macros
    user_macros.append(Macro(name, trigger, action, uuid, arg_index))

    if path != "":
        # This is a brand new macro, add it to the XML tree and write to the file
        # Open and read the macro config file
        with open("config/macros.xml", "r") as macro_file:
            macro_tree = ET.parse(macro_file)

            macro_root = macro_tree.getroot()

            new_macro_element = ET.SubElement(macro_root, "macro")
            new_uuid = ET.SubElement(new_macro_element, "uuid")
            new_uuid.text = uuid
            new_name = ET.SubElement(new_macro_element, "name")
            new_name.text = name
            new_path = ET.SubElement(new_macro_element, "path")
            new_path.text = "config/macros/%s.txt" % uuid
            new_trigger_type = ET.SubElement(new_macro_element, "trigger_type")
            new_trigger_type.text = trigger.split(" ")[0].lower()
            new_trigger = ET.SubElement(new_macro_element, "trigger")
            new_trigger.text = "".join(trigger.split(" ")[1:])
            new_arg_index = ET.SubElement(new_macro_element, "arg_index")
            new_arg_index.text = arg_index

            # Write the macro config file
            macro_tree.write("config/macros.xml")

            # Write the macro's action file
            with open(path, "w+") as macro_action_file:
                macro_action_file.write("".join(action))


def delete_user_macro(macro_uuid):
    """Delete a user macro from the XML config file, and remove its action file."""
    global user_macros
    with open("config/macros.xml", "r") as macro_file:
        macro_tree = ET.parse(macro_file)
        macro_root = macro_tree.getroot()

    all_macros = macro_root.findall("macro")
    for macro in all_macros:
        if macro.find("uuid").text == macro_uuid:
            os.remove(macro.find("path").text)
            macro_root.remove(macro)

            break

    macro_tree.write("config/macros.xml")

    # Delete the macro from user_macros
    for i in range(len(user_macros)):
        if user_macros[i].uuid == macro_uuid:
            user_macros.pop(i)
            break


def add_internal_macro(name, trigger, action, uuid, arg_index=0):
    """Add a new user macro to internal_macros"""
    global internal_macros
    intermal_macros.append(Macro(name, trigger, action, uuid, arg_index))


def delete_internal_macro(macro_uuid):
    """Delete an internal macro from the list"""
    global internal_macros

    # Delete the macro from internal_macros
    for i in range(len(internal_macros)):
        if internal_macros[i].uuid == macro_uuid:
            internal_macros.pop(i)
            break


def load_variables():
    """Load user variables from config file."""
    # Open and read the macro config file
    with open("config/variables.xml", "r") as variable_file:
        variable_tree = ET.parse(variable_file)

        # Parse the variables from the freshly-read file
        variable_root = variable_tree.getroot()
        variable_list = variable_root.findall("variable")

        return variable_list


def add_user_variable(variable_name, variable_value, debug=False):
    """Add a new user variable with the given name and value"""
    global user_variables

    if debug:
        print("Adding user variable!")
        print("Raw variable name: %s" % variable_name)
        print("Raw variable value: %s" % variable_value)
    # Format name properly
    variable_name = variable_name.replace(" ", "_")
    variable_name = variable_name.replace("/", "_")
    variable_name = variable_name.lower()
    variable_name = variable_name.strip()
    variable_name = variable_name.strip("*")
    variable_name = "*%s*" % variable_name
    if debug:
        print("Processed variable name: %s" % variable_name)
        print("Checking for duplicate user variables.")

    # Check that variable is not a duplicate of an existing user_variable
    add_variable = True
    for variable in user_variables:
        if variable.name == variable_name:
            if debug:
                print("Duplicate found.")
            add_variable = False
            break

    if add_variable:
        # If the variable is not a duplicate, add it to the list and the XML config
        if debug:
            print("No duplicate found. Adding variable.")
        user_variables.append(InternalVar(variable_name, parse_value(variable_value, debug=debug)))

        with open("config/variables.xml", "r") as variable_file:
            variable_tree = ET.parse(variable_file)
            variable_root = variable_tree.getroot()
            variable_list = variable_root.findall("variable")

            exists_in_config = False

            for variable in variable_list:
                if variable.find("name").text == variable_name:
                    # Variable already exists in XML, we're probably pulling it from there.
                    exists_in_config = True

            if not exists_in_config:
                new_variable = ET.SubElement(variable_root, "variable")
                new_variable_name = ET.SubElement(new_variable, "name")
                new_variable_name.text = variable_name
                new_variable_value = ET.SubElement(new_variable, "value")
                new_variable_value.text = str(parse_value(variable_value, debug=debug))

                variable_tree.write("config/variables.xml")


def delete_user_variable(variable_name, debug=False):
    """Delete the user variable with the given name."""
    global user_variables
    if debug:
        print("Deleting user variable: %s" % variable_name)
        print("- Searching for user variable.")

    for i in range(len(user_variables)):
        if user_variables[i].name == variable_name:
            if debug:
                print("-- User variable found! Deleting.")
            user_variables.pop(i)
            break

    with open("config/variables.xml", "r") as variable_file:
        if debug:
            print("- Searching XML config for variable.")
        variable_tree = ET.parse(variable_file)
        variable_root = variable_tree.getroot()
        variable_list = variable_root.findall("variable")

        for variable in variable_list:
            if variable.find("name").text == variable_name:
                if debug:
                    print("-- User variable found in XML! Deleting.")
                variable_root.remove(variable)
                break

        variable_tree.write("config/variables.xml")


def get_user_variable(variable_name):
    """Get the value of the specified user variable, or return None if the variable does not exist."""
    global user_variables
    for variable in user_variables:
        if variable.name == variable_name:
            return variable.var_value

    # If the variable doesn't exist, return None
    return None


def set_user_variable(variable_name, new_value, debug=False):
    """Set a user variable to a new value"""
    global user_variables
    for variable in user_variables:
        if variable.name == variable_name:
            variable.set_value(parse_value(new_value, debug=debug))

    with open("config/variables.xml", "r") as variable_file:
        variable_tree = ET.parse(variable_file)
        variable_root = variable_tree.getroot()
        variable_list = variable_root.findall("variable")

        for variable in variable_list:
            if variable.find("name").text == variable_name:
                variable.find("value").text = str(parse_value(new_value, debug=debug))

        variable_tree.write("config/variables.xml")


def add_internal_variable(variable_name, variable_value, debug=False):
    """Add a new internal variable with the given name and value"""
    global internal_variables

    if debug:
        print("Adding internal variable!")
        print("Raw variable name: %s" % variable_name)
        print("Raw variable value: %s" % variable_value)
    # Format name properly
    variable_name = variable_name.replace(" ", "_")
    variable_name = variable_name.replace("/", "_")
    variable_name = variable_name.lower()
    variable_name = variable_name.strip()
    variable_name = variable_name.strip("#")
    variable_name = "#%s#" % variable_name
    if debug:
        print("Processed variable name: %s" % variable_name)
        print("Checking for duplicate internal variables.")

    # Check that variable is not a duplicate of an existing internal_variable
    add_variable = True
    for variable in internal_variables:
        if variable.name == variable_name:
            if debug:
                print("Duplicate found.")
            add_variable = False
            break

    if add_variable:
        # If the variable is not a duplicate, add it to the list.
        if debug:
            print("No duplicate found. Adding variable.")
        internal_variables.append(InternalVar(variable_name, parse_value(variable_value)))


def delete_internal_variable(variable_name, debug=False):
    """Delete the internal variable with the given name."""
    global internal_variables
    if debug:
        print("Deleting internal variable: %s" % variable_name)
        print("- Searching for internal variable.")

    for i in range(len(internal_variables)):
        if internal_variables[i].name == variable_name:
            if debug:
                print("-- Internal variable found! Deleting.")
            internal_variables.pop(i)


def get_internal_variable(variable_name):
    """Get the value of the specified internal variable, or return None if the variable does not exist."""
    global internal_variables
    for variable in internal_variables:
        if variable.name == variable_name:
            return variable.var_value

    # If the variable doesn't exist, return None
    return None


def set_internal_variable(variable_name, new_value):
    """Set an internal variable to a new value"""
    global internal_variables
    for variable in internal_variables:
        if variable.name == variable_name:
            variable.set_value(parse_value(new_value))


def parse_script_word(script_word, arg_input=None, debug=False):
    """Parse a non-opcode word in a macro action and return its value"""
    global internal_variables, user_variables, dynamic_variables
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


def check_condition(statement, arg_input=None):
    """Read a list of script words and attempt to interpret them as an expression, then return the result."""
    invert_condition = False

    if statement[0] == "not":
        # Invert the value, then remove "not" from the statement
        invert_condition = True
        statement = statement[1:]

    if len(statement) == 1:
        # If the script word represents a variable that exists, or is any raw value, return True
        result = parse_script_word(statement[0])
        print(result)
        if result is not None:
            initial_result = True
        else:
            initial_result = False

    elif len(statement) == 3:
        # Statement is assumed to be comparing two values, check for known operators. If operator is unknown, return False.
        match statement[1]:
            case "==":
                if str(parse_script_word(statement[0]), arg_input=arg_input) == str(parse_script_word(statement[2]), arg_input=arg_input):
                    initial_result = True
                else:
                    initial_result = False
            case "===":
                if parse_script_word(statement[0], arg_input=arg_input) == parse_script_word(statement[2], arg_input=arg_input):
                    initial_result = True
                else:
                    initial_result = False
            case ">":
                if parse_script_word(statement[0], arg_input=arg_input) > parse_script_word(statement[2], arg_input=arg_input):
                    initial_result = True
                else:
                    initial_result = False
            case ">=":
                if parse_script_word(statement[0], arg_input=arg_input) >= parse_script_word(statement[2], arg_input=arg_input):
                    initial_result = True
                else:
                    initial_result = False
            case "<":
                if parse_script_word(statement[0], arg_input=arg_input) < parse_script_word(statement[2], arg_input=arg_input):
                    initial_result = True
                else:
                    initial_result = False
            case "<=":
                if parse_script_word(statement[0], arg_input=arg_input) <= parse_script_word(statement[2], arg_input=arg_input):
                    initial_result = True
                else:
                    initial_result = False
            case "!=":
                if parse_script_word(statement[0], arg_input=arg_input) != parse_script_word(statement[2], arg_input=arg_input):
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


def eval_expression(expression, arg_input=None, debug=False):
    """Try to evaluate a script expression, and return the result"""
    if debug:
        print("Evaluating expression: ", expression)

    if len(expression) == 1:
        if debug:
            print("Expression is one word long. Returning evaluated word.")
        return parse_script_word(expression[0], arg_input=arg_input, debug=debug)

    elif len(expression) == 3:
        if debug:
            print("Expression is three words long.")
        if expression[1] == "+":
            if debug:
                print("Expression is attempting addition.")
            try:
                return parse_script_word(expression[0], arg_input=arg_input, debug=debug) + parse_script_word(expression[2], arg_input=arg_input, debug=debug)
            except TypeError:
                if debug:
                    print("Conventional addition impossible, returning concatenated strings.")
                return (str(parse_script_word(expression[0], arg_input=arg_input, debug=debug)) +
                        str(parse_script_word(expression[2], arg_input=arg_input, debug=debug)))
        elif expression[1] == "-":
            if debug:
                print("Expression is attempting subtraction.")
            try:
                return parse_script_word(expression[0], arg_input=arg_input, debug=debug) - parse_script_word(expression[2], arg_input=arg_input, debug=debug)
            except TypeError:
                if debug:
                    print("Subtraction failed, returning first word in expression.")
                return parse_script_word(expression[0], arg_input=arg_input, debug=debug)
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


def process_osc(osc_addr: str, osc_args: list, arg_input=None, debug=False):
    """Process an OSC address and arguments, substituting in variables, then send it."""
    global osc_client

    if debug:
        print("Processing OSC!")
        print("Initial OSC Address: %s" % osc_addr)
        print("Initial OSC arguments: ", osc_args)

    # Split the OSC address and look for variables
    split_osc_addr = osc_addr.split("/")
    if split_osc_addr[0] == "":
        # This is expected, and is evidence of a properly formed OSC address. Just cut it off.
        split_osc_addr = split_osc_addr[1:]

    if debug:
        print("Split OSC address: ", split_osc_addr)

    parsed_osc_addr = []
    for address_container in split_osc_addr:
        # Substitute in variables where appropriate
        parsed_osc_addr.append(parse_script_word(address_container, arg_input=arg_input, debug=debug))

    # Rebuild the OSC address
    final_osc_addr = "/" + "/".join(parsed_osc_addr)

    # Process arguments, substituting in variable values where appropriate
    parsed_osc_args = []
    for argument in osc_args:
        parsed_osc_args.append(parse_script_word(argument, arg_input=arg_input, debug=debug))

    if debug:
        print("Final OSC address: %s" % final_osc_addr)
        print("Final OSC arguments: ", parsed_osc_args)
        print("Sending OSC message!")

    osc_client.send_message(final_osc_addr, parsed_osc_args)


def handle_string_end(word, string_buffer, active_expression_count, expressions, split_line):
    """Handle the end of a string during script processing."""
    word = word.strip("\"'")
    string_buffer.append(word)

    # Re-assemble the string buffer into final_string, then reset string variables
    final_string = " ".join(string_buffer)
    string_buffer = []
    string_active = False

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
        elif re.match("\S*\)", word):
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
        elif re.match("\S+-\S+", word):
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
                        expression_result = eval_expression(expressions.pop(), arg_input=arg_input, debug=True)

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


def process_cue_number(raw_cue_number: list):
    """Process a user-written cue number string and return a list/cue formatted string."""
    if "/" in raw_cue_number[0]:
        raw_cue_number = raw_cue_number[0].split("/")

    print("Raw cue number: ", raw_cue_number)

    if len(raw_cue_number) == 1:
        # Assume this is a cue number only, and use list 1.
        list_num = 1
        # Attempt to float-ify it. If that's possible, it's a healthy cue number
        try:
            cue_num_float = float(raw_cue_number[0])
            cue_num = raw_cue_number[0]
        except ValueError:
            # Cue number isn't a number, use cue 0
            cue_num = "0"

    elif len(raw_cue_number) == 2:
        # Assume this is a list and cue with no separator.
        try:
            list_num_float = float(raw_cue_number[0])
            list_num = raw_cue_number[0]
        except ValueError:
            # List number isn't a number, use list 1
            list_num = "1"

        try:
            cue_num_float = float(raw_cue_number[0])
            cue_num = raw_cue_number[1]
        except ValueError:
            # Cue number isn't a number, use cue 0
            cue_num = "0"

    else:
        # Cue number is not in a known format, return 1/0
        list_num = "1"
        cue_num = "0"

    return "%s/%s" % (list_num, cue_num)


class ScriptInterpreter:
    """Handles all interpreting for macro actions."""

    def __init__(self):
        pass


class Macro:
    """Holds macro trigger and action."""

    def __init__(self, name, trigger: str, action: list, uuid: str, requested_arg=0, arg_input="", last_fire_time=datetime.datetime.now()):
        self.name = name
        self.trigger = trigger
        self.action = action
        self.uuid = uuid
        self.requested_arg_index = requested_arg
        self.input_from_arg = arg_input
        self.last_fire_time = last_fire_time

    def run_action(self, osc_addr: str, osc_arg: list, has_eos_queries=False, arg_input=None) -> tuple:
        """Loop through the action and handle all base steps before handing off to the interpreter."""
        global internal_macros
        debug = True
        if not has_eos_queries:
            if debug:
                print("STATUS: No Eos queries provided, searching action...")
            # Find all eos queries in the lines and then build their actions
            eos_queries = []
            for line in self.action:
                split_line = line.split(" ")
                for word in split_line:
                    if re.search("%eos.*%", word) is not None:
                        # Eos query found, add it to the list
                        if debug:
                            print("STATUS: Eos query found: %s" % word)
                        eos_queries.append(word)

            if len(eos_queries) == 0:
                # No eos queries, return a run uuid action to run the macro's action
                if debug:
                    print("STATUS: Action searched, no Eos queries detected. Sending run action.")
                return ("run", self.uuid)

            # Build eos query actions
            last_osc = ""
            for i in range(len(eos_queries)):
                # Run through list in reverse
                query = eos_queries[len(eos_queries) - i]
                # TODO: Create a way to determine the osc command for a given query, and the argument to read to set it.
                name = ""
                trigger = ""
                new_var_name = "eos_query_%i" % i
                osc_arg_num = ""

                if i == 0:
                    action = ["new %s %s" % (new_var_name, osc_arg_num), "run %s" % self.uuid]
                    last_osc = trigger
                else:
                    action = ["new %s %s" % (new_var_name, osc_arg_num), "osc %s" % last_osc]

                add_internal_macro(name, action, trigger, self.uuid)

                if i == len(eos_queries):
                    # Done adding macros, send the osc message to start it all
                    # TODO: make this send the first OSC message
                    return ("wait", "")
        else:
            if debug:
                print("STATUS: Eos queries provided, running action.")
            # Eos queries have been received, run the macro
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
                line = self.action[current_line]
                split_line = pre_process_script_line(line, arg_input=arg_input, debug=False)


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
                            if not if_cond_found and check_condition(line_statement, arg_input=arg_input):
                                if debug:
                                    print("- Found valid elif on line %i! Setting if_met and if_cond_found to True" % current_line)
                                if_met = True
                                if_cond_found = True
                                pass
                            else:
                                pass
                        case "else":
                            # If we haven't found the condition yet, we have now!
                            if not if_cond_found:
                                if debug:
                                    print("- Found valid else on line %i! Setting if_met and if_cond_found to True" % current_line)
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

                        # case "endloop":
                        #    # If we've reached the end of a loop without finding another case, loop it until we do,
                        #    # or until the limit is reached.
                        #    loop_active, loop_start_line, loop_end_line, loop_count, skip_to_endloop, current_line = (
                        #        handle_endloop(loop_active, loop_start_line, loop_count, loop_limit, skip_to_endloop, current_line, debug=False))"""

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
                            process_osc(split_line[1], split_line[2:], arg_input=arg_input, debug=True)
                            pass
                        case "wait":
                            # Wait the listed amount of time in seconds
                            if debug:
                                print("- Wait command found on line %i. Processing!" % current_line)
                                print("-- Wait time: %s" % line_statement[0])
                            try:
                                time.sleep(parse_script_word(line_statement[0], arg_input=arg_input))
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
                                handle_endloop(loop_active, loop_start_line, loop_count, loop_limit, skip_to_endloop, current_line, debug=debug))

                        case "new":
                            # Create a new user variable with the given name and value
                            # Syntax: new new_var_name = new_var_value
                            if debug:
                                print("- New command found at line %i. Processing!" % current_line)
                            add_user_variable(line_statement[0], parse_script_word(line_statement[2]), arg_input=arg_input, debug=True)
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
                                    set_user_variable(line_statement[0], eval_expression(line_statement[2:], arg_input=arg_input, debug=True))
                                except IndexError:
                                    if debug:
                                        print("Improper syntax. Variable was not set.")
                            elif re.match("#\w+#", line_statement[0]):
                                # Internal variable
                                if debug:
                                    print("-- Variable is an internal variable.")
                                try:
                                    set_internal_variable(line_statement[0], eval_expression(line_statement[2:], arg_input=arg_input, debug=True))
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
                                delete_user_variable(line_statement[0], debug=True)
                            elif re.match("#\w+#", line_statement[0]):
                                # Internal variable
                                if debug:
                                    print("-- Variable is an internal variable.")
                                delete_internal_variable(line_statement[0], debug=True)
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
                                if check_condition(line_statement, arg_input=arg_input):
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
                                    print("-- If statement is active. Checking if condition has already been found and if condition is met.")
                                if not if_cond_found and check_condition(line_statement, arg_input=arg_input):
                                    if debug:
                                        print("-- Condition met/Condition not previously found! Setting if_met and if_cond_found to True.")
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
                                        print("-- Condition had not already been met! Setting if_met and if_cond_found to True.")
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
                                print("- Endif statement found at line %i! Deactivating if statement and resetting if variables." % current_line)
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
                                        print("-- Loop end line is known. Setting current_line to loop_end_line and resetting variables.")
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
                print(len(self.action))
                if current_line + 1 > len(self.action):
                    run_action = False
            if debug:
                print("Returning 'done'.")
            return ("done", "")


class InternalVar:
    """Holds a value for use by the user or a macro."""

    def __init__(self, name: str, value: str):
        self.name = name
        self.var_value = value

    def set_value(self, new_value):
        """Set the var_value to a new value, ensuring that it has been parsed."""
        self.var_value = parse_value(new_value)


with open("config/network_settings.xml", "r") as file:
    try:
        network_tree = ET.parse(file)
        network_root = network_tree.getroot()
        console = network_root.find("console")
        console_ip = console.find("ip").text
        console_port = console.find("port").text
        console_network_config = [console_ip, console_port, ""]

    except IndexError:
        console_network_config = ["", "", ""]

osc_client = start_osc_client(console_network_config)

with open("config/macros.xml", "r") as file:
    macro_list = load_macros()

    # Make a macro object for each macro loaded
    for macro in macro_list:
        name = macro.find("name").text
        trigger = macro.find("trigger_type").text + " " + macro.find("trigger").text
        macro_uuid = macro.find("uuid").text
        arg_index = macro.find("arg_index").text
        with open(macro.find("path").text, "r") as action_file:
            action = action_file.readlines()

        # Append the new macro to user_macros
        add_user_macro(name, trigger, action, macro_uuid, arg_index)

with open("config/variables.xml", "r") as file:
    # Load user variables
    variable_list = load_variables()

    # Make a variable object for each variable loaded
    for variable in variable_list:
        add_user_variable(variable.find("name").text, variable.find("value").text)

# Initialize dynamic variables
dynamic_variables = {
    "%cue%": InternalVar("%cue%", ""),
    "%list%": InternalVar("%list%", ""),
    "%listcue%": InternalVar("%listcue%", ""),
    "%sel%": InternalVar("%sel%", ""),
    "%filename%": InternalVar("%filename%", ""),
    "%time%": InternalVar("%time%", ""),
    "%live%": InternalVar("%live%", ""),
    "%blind%": InternalVar("%blind%", ""),
    "%staging%": InternalVar("%staging%", "")
}

# Flask setup
app = Flask(__name__)

# Home page
@app.route("/", methods=["POST", "GET"])
def index():
    """Load existing macros and pass them to the page."""
    global macro_tree, user_macros, internal_macros

    macro_list = load_macros()

    if request.method == "GET":
        main_macro_list = parse_macros(macro_list)

    else:
        # Macro was updated, write to the file
        if ((request.form["submit_macro"] == "Update Macro") or (request.form["submit_macro"] == "Add Macro")
                or (request.form["submit_macro"] == "Duplicate Macro") or request.form["submit_macro"] == "Run Macro"):

            if request.form["submit_macro"] == "Duplicate Macro":
                # Give the new macro a new UUID
                macro_uuid_to_update = str(uuid.uuid4())
            else:
                macro_uuid_to_update = request.form["macro_uuid"]

            # Get macro variables from the form
            new_macro_name = request.form["macro_name"]
            new_macro_trigger_type = request.form["macro_trigger"].split(" ")[0].lower()
            new_macro_trigger = str().join(request.form["macro_trigger"].split(" ")[1:]).lower()
            try:
                new_macro_arg_index = str(int(request.form["macro_arg_index"]))
            except TypeError:
                new_macro_arg_index = 0
            new_macro_action = request.form["macro_action"].split("\n")

            # Set all loaded XML values to the new data
            all_macros = load_macros(return_tree=True)
            found_macro = False
            for macro in all_macros.getroot().findall("macro"):
                if macro.find("uuid").text == macro_uuid_to_update:
                    found_macro = True
                    macro.find("name").text = new_macro_name
                    macro.find("trigger_type").text = new_macro_trigger_type
                    macro.find("trigger").text = new_macro_trigger
                    macro.find("arg_index").text = new_macro_arg_index

                    all_macros.write("config/macros.xml")

                    with open(macro.find("path").text, "w+") as macro_file:
                        print(new_macro_action)
                        macro_file.write("".join(new_macro_action))

                    # Update the Macro object with the given UUID
                    for macro_object in user_macros:
                        if macro_object.uuid == macro.find("uuid").text:
                            macro_object.name = new_macro_name
                            macro_object.trigger_type = new_macro_trigger_type
                            macro_object.trigger = new_macro_trigger
                            macro_object.requested_arg_index = new_macro_arg_index
                            macro_object.action = new_macro_action
                            print(macro_object.action)
                            break

                    break

            if not found_macro:
                # Add the new macro to user_macros
                add_user_macro(new_macro_name, " ".join([new_macro_trigger_type, new_macro_trigger]),
                               new_macro_action, macro_uuid_to_update,
                               new_macro_arg_index, path="config/macros/%s.txt" % macro_uuid_to_update)

            if request.form["submit_macro"] == "Run Macro":
                # Manually run the macro's action
                for macro in user_macros:
                    if macro.uuid == request.form["macro_uuid"]:
                        print("Running macro!")
                        macro.run_action("", [""], has_eos_queries=True)


        elif request.form["submit_macro"] == "Delete Macro":
            # Find the macro with the matching UUID and delete it from the config completely
            delete_user_macro(request.form["macro_uuid"])

    macro_list = load_macros()
    main_macro_list = parse_macros(macro_list)

    return render_template("index.html", macro_list=main_macro_list, new_uuid=str(uuid.uuid4()))


@app.route("/network_config", methods=["POST", "GET"])
def network_config():
    global console_network_config, network_tree, osc_client
    if request.method == "POST":
        # Form submissions
        if request.form["submit"] == "Update Config":
            new_console_ip = request.form["console_ip"]
            new_console_port = request.form["console_port"]

            console_network_config = [new_console_ip, new_console_port, ""]

            # Attempt to start an OSC client with the provided config
            osc_client = start_osc_client(console_network_config)

            network_root = network_tree.getroot()
            console = network_root.find("console")
            console.find("ip").text = new_console_ip
            console.find("port").text = new_console_port
            network_tree.write("config/network_settings.xml")

            if isinstance(osc_client, str):
                # Error returned, display it to the user
                console_network_config[2] = osc_client
        elif request.form["submit"] == "Ping Console":
            if osc_client:
                # If the console is configured, ping it
                print("Pinging")
                process_osc("/eos/ping", ["macroPlus"])
        elif request.form["submit"] == "Send OSC":
            if osc_client:
                # If the console is configured, send the custom OSC
                process_osc(request.form["custom_osc_address"], request.form["custom_osc_arguments"].split())
        else:
            pass
        return render_template("network_config.html", console_network=console_network_config)

    else:
        # Basic loading
        return render_template("network_config.html", console_network=console_network_config)


@app.route("/osc", methods=["POST"])
def handle_osc():
    """Handle incoming OSC from the console. Comes in as JSON"""
    global console_network_config, internal_variables, user_variables, dynamic_variables
    json_osc = request.json
    json_osc["args"] = json.loads(json_osc["args"])

    if len(json_osc["args"]) == 0:
        # Not all OSC messages come with arguments, just give it an empty one
        json_osc["args"] = [""]

    if json_osc["address"] == "/eos/out/ping" and json_osc["args"][0] == "macroPlus":
        console_network_config[2] = "%s - Ping validated!" % str(datetime.datetime.now())
        return render_template("index.html", console_network_config=console_network_config)
    else:
        # Check incoming OSC against internal macros
        print("Received OSC address %s" % json_osc["address"])
        for internal_macro in internal_macros:
            # Internal macro triggers are always OSC commands, check the second word for the address.
            if internal_macro.trigger.split(" ")[1] == json_osc["address"]:
                # If the address matches, run the action.
                # Try to give it the requested argument if it exists
                try:
                    requested_arg = json_osc["args"][internal_macro.requested_arg_index]
                except IndexError:
                    requested_arg = ""
                run_result = internal_macro.run_action(json_osc["address"], json_osc["args"],
                                                       has_eos_queries=False, arg_input=requested_arg)

                print("Run result: ", run_result)

                # Check run_result to see what to do next
                if run_result[0] == "done" or run_result[0] == "wait":
                    # Do nothing
                    pass
                elif run_result[0] == "run":
                    # Run the action associated with the macro with the given uuid.
                    # Set has_eos_queries to True because run actions are expected to start the final run of a macro.
                    for macro in internal_macros:
                        if macro.uuid == run_result[1]:
                            _second_run_result = macro.run_action(json_osc["address"], json_osc["args"], has_eos_queries=True)

        for user_macro in user_macros:
            # Check if user macro relies on OSC for a trigger. If it does, see if it matches and run it if it does.
            if user_macro.trigger.split(" ")[0] == "osc":
                if user_macro.trigger.split(" ")[1] == json_osc["address"]:
                    # If the address matches, check that the macro's cooldown is over, then run the action.
                    print(("!!!!!!!!!!! ", (datetime.datetime.now() - user_macro.last_fire_time).total_seconds()))
                    if (datetime.datetime.now() - user_macro.last_fire_time).total_seconds() >= macro_cooldown_time:
                        run_result = user_macro.run_action(json_osc["address"], json_osc["args"],
                                                               has_eos_queries=False, arg_input=json_osc["args"])

                        print("Run result: ", run_result)

                        # Check run_result to see what to do next
                        if run_result[0] == "done" or run_result[0] == "wait":
                            # Do nothing
                            pass
                        elif run_result[0] == "run":
                            # Run the action associated with the macro with the given uuid.
                            # Set has_eos_queries to True because run actions are expected to start the final run of a macro.
                            print("Running second action!")
                            for macro in user_macros:
                                if macro.uuid == run_result[1]:
                                    _second_run_result = macro.run_action(json_osc["address"], json_osc["args"], has_eos_queries=True, arg_input=json_osc["args"])

                        user_macro.last_fire_time = datetime.datetime.now()

            elif user_macro.trigger.split(" ")[0] == "cue":
                # Handle macros which fire on a given cue
                cue_number = process_cue_number(user_macro.trigger.split(" ")[1:])
                print("/eos/out/event/cue/%s/fire" % user_macro.trigger.split(" ")[1], json_osc["address"])
                if "/eos/out/event/cue/%s/fire" % user_macro.trigger.split(" ")[1] == json_osc["address"]:
                    # Check that the macro_cooldown_time has elapsed since the macro was last fired.
                    if (datetime.datetime.now() - user_macro.last_fire_time).total_seconds() >= macro_cooldown_time:
                        # If the address matches, run the action.
                        run_result = user_macro.run_action(json_osc["address"], json_osc["args"],
                                                               has_eos_queries=False, arg_input=json_osc["args"])

                        # Check run_result to see what to do next
                        if run_result[0] == "done" or run_result[0] == "wait":
                            # Do nothing
                            pass
                        elif run_result[0] == "run":
                            # Run the action associated with the macro with the given uuid.
                            # Set has_eos_queries to True because run actions are expected to start the final run of a macro.
                            for macro in user_macros:
                                if macro.uuid == run_result[1]:
                                    _second_run_result = macro.run_action(json_osc["address"], json_osc["args"], has_eos_queries=True, arg_input=json_osc["args"])

                        user_macro.last_fire_time = datetime.datetime.now()

        # Check incoming OSC against dynamic variables
        if "/eos/out/active/cue/text" in json_osc["address"]:
            # Update the list, cue and listcue variables
            split_args = json_osc["args"][0].split(" ")
            dynamic_variables["%cue%"].set_value(split_args[0].split("/")[1])
            dynamic_variables["%list%"].set_value(split_args[0].split("/")[0])
            dynamic_variables["%listcue%"].set_value(split_args[0])

        elif "/eos/out/active/chan" in json_osc["address"]:
            # Update the sel variable
            dynamic_variables["%sel%"].set_value(json_osc["args"][0].split(" ")[0])

        elif "/eos/out/event/show/saved" in json_osc["address"]:
            # Update the filename variable
            dynamic_variables["%filename%"].set_value(json_osc["args"][0].split("/")[-1])

        elif "cmd" in json_osc["address"]:
            # Update the current console mode
            if "LIVE" in json_osc["args"][0]:
                dynamic_variables["%live%"].set_value("True")
                dynamic_variables["%blind%"].set_value("False")
                dynamic_variables["%staging%"].set_value("False")
            elif "BLIND" in json_osc["args"][0]:
                dynamic_variables["%live%"].set_value("False")
                dynamic_variables["%blind%"].set_value("True")
                dynamic_variables["%staging%"].set_value("False")

            if "Staging" in json_osc["args"][0]:
                dynamic_variables["%staging%"].set_value("True")
            else:
                dynamic_variables["%staging%"].set_value("False")

        dynamic_variables_list = []
        for item in dynamic_variables.items():
            dynamic_variables_list.append([item[0], getattr(item[1], "var_value")])

        return ("", 204)


@app.route("/variables", methods=["GET", "POST"])
def variables():
    global dynamic_variables
    if request.method == "GET":
        # Load the page, displaying variables
        dynamic_variables_list = []
        for item in dynamic_variables.items():
            dynamic_variables_list.append([item[0], getattr(item[1], "var_value")])

        return render_template("variables.html", user_variables=user_variables, dynamic_variables=dynamic_variables_list)

    elif request.method == "POST":
        # Variable is being updated
        if request.form["submit_variable"] == "Add":
            # Add only if it isn't a duplicate
            add_user_variable(request.form["variable_name"], request.form["variable_value"], debug=True)

        elif request.form["submit_variable"] == "Delete":
            # Delete the variable
            delete_user_variable(request.form["variable_name"], debug=True)

        else:
            # Set the variable to a new value
            set_user_variable(request.form["variable_name"], request.form["variable_value"], debug=True)

        dynamic_variables_list = []
        for item in dynamic_variables.items():
            dynamic_variables_list.append([item[0], getattr(item[1], "var_value")])

        return render_template("variables.html", user_variables=user_variables, dynamic_variables=dynamic_variables_list)


if __name__ == "__main__":
    app.run(debug=True)