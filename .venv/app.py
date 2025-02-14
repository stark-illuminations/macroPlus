import datetime
import json
import time
import xml.etree.ElementTree as ET
import uuid
import os
import re

from flask import Flask, render_template, request
from pythonosc import udp_client

internal_macros = []
user_macros = []
internal_variables = []
user_variables = []


class ScriptInterpreter:
    """Handles all interpreting for macro actions."""

    def __init__(self):
        pass


class Macro:
    """Holds macro trigger and action."""

    def __init__(self, trigger: str, action: list, uuid: str, requested_arg=0, arg_input=""):
        self.trigger = trigger
        self.action = action
        self.uuid = uuid
        self.requested_arg_index = requested_arg
        self.input_from_arg = arg_input

    def run_action(self, osc_addr: str, osc_arg: list, has_eos_queries=False) -> tuple:
        """Loop through the action and handle all base steps before handing off to the interpreter."""
        global internal_macros
        if not has_eos_queries:
            # Find all eos queries in the lines and then build their actions
            eos_queries = []
            for line in self.action:
                split_line = line.split(" ")
                for word in split_line:
                    if re.search("%eos.*%", word) is not None:
                        # Eos query found, add it to the list
                        eos_queries.append(word)

            if len(eos_queries) == 0:
                # No eos queries, return a run uuid action to run the macro's action
                return ("run", self.uuid)

            # Build eos query actions
            last_osc = ""
            for i in range(len(eos_queries)):
                # Run through list in reverse
                query = eos_queries[len(eos_queries) - i]
                # TODO: Create a way to determine the osc command for a given query, and the argument to read to set it.
                trigger = ""
                new_var_name = "eos_query_%i" % i
                osc_arg_num = ""

                if i == 0:
                    action = ["new %s %s" % (new_var_name, osc_arg_num), "run %s" % self.uuid]
                    last_osc = trigger
                else:
                    action = ["new %s %s" % (new_var_name, osc_arg_num), "osc %s" % last_osc]

                new_internal_macro = Macro(trigger, action, self.uuid)
                internal_macros.append(new_internal_macro)

                if i == len(eos_queries):
                    # Done adding macros, send the osc message to start it all
                    # TODO: make this send the first OSC message
                    return ("wait", "")
        else:
            # Eos queries have been received, run the macro
            current_line = 0
            for line in self.action:
                split_line = line.split(" ")
                opcode = split_line[0]
                current_line = 0
                loop_active = False
                loop_start_line = None
                loop_end_line = None
                loop_count = 0
                if_active = False
                if_met = False
                if_cond_found = False
                # Increment current_line and read that line from the action
                # If if_active is True and if_met is False, check if the opcode is else or endif. If not, skip the match since we aren't running that line.
                # Switch case with all possible opcodes, set appropriate variables and call interpreter when one is found
                match opcode:
                    case "osc":
                        # Send OSC to the given address, with the given arguments
                        # Syntax: osc /some/osc/address [argument_1] [argument_2] [argument_3]...
                        pass
                    case "wait":
                        # Wait the listed amount of time in milliseconds
                        # Syntax: wait 500
                        pass
                    case "loop":
                        # Mark the current line as the start of a loop (Don't do the next line, Stark. Trust me.)
                        # Set loop_active to True and loop_start_line to the next line
                        # TODO: Handle cases where this is the last line of the file, and there isn't a loop
                        # Syntax: loop
                        pass
                    case "endloop":
                        # Mark the previous line as the end of a loop
                        # Set loop_end_line to the previous line
                        # TODO: Handle cases where this is the start of the file, and there isn't a loop
                        # Syntax: endloop
                        pass
                    case "new":
                        # Create a new user variable with the given name and value
                        # Syntax: new new_var_name = new_var_value
                        pass
                    case "set":
                        # Set an existing user variable with the given name to a new value
                        # Syntax 1: set existing_var = other_existing_var (get the value from the other variable)
                        # Syntax 2: set existing_var = new_value (set it to a new value)
                        # Syntax 3: set existing_var = existing_var_or_value + existing_var_or_value (add ints or floats, or concatenate strings. Does not affect bools)
                        # Syntax 4: set existing_var = existing_var_or_value - existing_var_or_value (subtract ints or floats. Does not affect strings or bools)
                        pass
                    case "del":
                        # Delete an existing user variable with the given name
                        # Syntax: del existing_var
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
                        pass
                    case "elif":
                        # Add a case to an if statement which will only be triggered if previous conditions are not met.
                        # If the condition is met, set if_met to True and if_cond_found to True
                        # Syntax: Same as "if" opcode above.
                        pass
                    case "else":
                        # Start an else statement if if_active is True and if_met is False. Set if_met to True and if_cond_found to True
                        # Set if_met to True so the next lines run.
                        # Syntax: else
                        pass
                    case "endif":
                        # End an if/else statement. Set if_active and if_met to False.
                        # Syntax: endif
                        pass
                    case "break":
                        # Break a running loop and skip to the end of it.
                        # Set loop_active to False, then set current_line to loop_end_line+1 to skip past the endloop line
                        # Syntax: break
                        pass
                    case "pass":
                        # Do nothing.
                        # Syntax: pass
                        pass
                    case "comment":
                        # Do nothing with this line
                        pass
                # Check if a loop is active. If it is, check if current_line is the same as loop_end_line.
                # If it is, set current_line to loop_start_line and increment loop_counter.
                # If loop_counter is greater than loop_limit, set loop_active to False, and reset loop line variables to 0
                # Stop the action if an error is encountered
                # Delete all eos query variables
            return ("done", "")


class InternalVar:
    """Holds a value for use by the user or a macro."""

    def __init__(self, name: str, value: str):
        self.name = name
        self.var_value = value

        # Check if the value can be an int, float, or bool, otherwise treat it as a string
        try:
            self.var_value = float(self.var_value)
        except (TypeError, ValueError):
            pass

        try:
            self.var_value = int(self.var_value)
        except (TypeError, ValueError):
            pass

        try:
            if self.var_value.lower() == "true" or self.var_value.lower() == "false":
                self.var_value = bool(self.value)
        except (TypeError, AttributeError):
            pass

    def set_value(self, new_value):
        self.var_value = new_value

        try:
            self.var_value = float(new_value)
        except (TypeError, ValueError):
            pass

        try:
            self.var_value = int(new_value)
        except (TypeError, ValueError):
            pass

        try:
            if new_value.lower() == "true":
                self.var_value = True
            elif new_value.lower() == "false":
                self.var_value = False
        except (TypeError, AttributeError):
            pass


osc_client = None

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

with open("config/macros.xml", "r") as file:
    macro_tree = ET.parse(file)

    # Make a macro object for each macro loaded
    # Parse the macros from the freshly-read file
    macro_root = macro_tree.getroot()
    macro_list = macro_root.findall("macro")

    for macro in macro_list:
        trigger = macro.find("trigger_type").text + " " + macro.find("trigger").text
        with open(macro.find("path").text, "r") as action_file:
            action = action_file.readlines()

        # Append the new macro to user_macros
        user_macros.append(Macro(trigger, action, macro.find("uuid").text))

with open("config/variables.xml", "r") as file:
    # Load user variables
    variable_tree = ET.parse(file)
    variable_root = variable_tree.getroot()
    variable_list = variable_root.findall("variable")

    # Make a variable object for each variable loaded
    for variable in variable_list:
        user_variables.append(InternalVar(variable.find("name").text, variable.find("value").text))

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

    # Re-open and read file when the page is reloaded
    with open("config/macros.xml", "r") as macro_file:
        macro_tree = ET.parse(macro_file)

    # Parse the macros from the freshly-read file
    macro_root = macro_tree.getroot()
    macro_list = macro_root.findall("macro")

    if request.method == "GET":
        main_macro_list = parse_macros(macro_list)

    else:
        # Macro was updated, write to the file
        if ((request.form["submit_macro"] == "Update Macro")
            or (request.form["submit_macro"] == "Add Macro")
                or (request.form["submit_macro"] == "Duplicate Macro")):

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
                new_macro_arg_index = int(request.form["macro_arg_index"])
            except TypeError:
                new_macro_arg_index = 0
            new_macro_action = request.form["macro_action"].split("\n")

            # Set all loaded XML values to the new data
            all_macros = macro_root.findall("macro")
            found_macro = False
            for macro in all_macros:
                if macro.find("uuid").text == macro_uuid_to_update:
                    found_macro = True
                    macro.find("name").text = new_macro_name
                    macro.find("trigger_type").text = new_macro_trigger_type
                    macro.find("trigger").text = new_macro_trigger
                    macro.find("arg_index").text = new_macro_arg_index

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
                # Macro is new, add a new entry to the tree and write a new config file to store the action.
                new_macro_element = ET.SubElement(macro_root, "macro")
                new_uuid = ET.SubElement(new_macro_element, "uuid")
                new_uuid.text = macro_uuid_to_update
                new_name = ET.SubElement(new_macro_element, "name")
                new_name.text = new_macro_name
                new_path = ET.SubElement(new_macro_element, "path")
                new_path.text = "config/macros/%s.txt" % macro_uuid_to_update
                new_trigger_type = ET.SubElement(new_macro_element, "trigger_type")
                new_trigger_type.text = new_macro_trigger_type
                new_trigger = ET.SubElement(new_macro_element, "trigger")
                new_trigger.text = new_macro_trigger
                new_arg_index = ET.SubElement(new_macro_element, "arg_index")
                new_arg_index.text = new_macro_arg_index

                with open(new_path.text, "w+") as macro_file:
                    macro_file.write("".join(new_macro_action))

                # Add the new macro to user_macros
                user_macros.append(Macro(new_macro_trigger, new_macro_action, macro_uuid_to_update, new_macro_arg_index))

            macro_tree.write("config/macros.xml")

            macro_list = macro_root.findall("macro")
            main_macro_list = parse_macros(macro_list)

        elif request.form["submit_macro"] == "Delete Macro":
            # Find the macro with the matching UUID and delete it from the config completely
            all_macros = macro_root.findall("macro")
            for macro in all_macros:
                if macro.find("uuid").text == request.form["macro_uuid"]:
                    os.remove(macro.find("path").text)
                    macro_root.remove(macro)

                    break

            macro_tree.write("config/macros.xml")

            # Delete the macro from user_macros
            for i in range(len(user_macros)):
                if user_macros[i].uuid == request.form["macro_uuid"]:
                    user_macros.pop(i)
                    break

            macro_list = macro_root.findall("macro")
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
                osc_client.send_message("/eos/ping", "macroPlus")
        elif request.form["submit"] == "Send OSC":
            if osc_client:
                # If the console is configured, send the custom OSC
                osc_client.send_message(request.form["custom_osc_address"], request.form["custom_osc_arguments"])
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
    if json_osc["address"] == "/eos/out/ping" and json_osc["args"][0] == "macroPlus":
        console_network_config[2] = "%s - Ping validated!" % str(datetime.datetime.now())
        return render_template("index.html", console_network_config=console_network_config)
    else:
        # Check incoming OSC against internal macros
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
                                                       has_eos_queries=False, input_from_arg=requested_arg)

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

        # Check incoming OSC against dynamic variables
        if "/eos/out/active/cue/text" in json_osc["address"]:
            # Update the list, cue and listcue variables
            print("Cue detected")
            split_args = json_osc["args"][0].split(" ")
            dynamic_variables["%cue%"].set_value(split_args[0].split("/")[1])
            dynamic_variables["%list%"].set_value(split_args[0].split("/")[0])
            dynamic_variables["%listcue%"].set_value(split_args[0])

        elif "/eos/out/active/chan" in json_osc["address"]:
            # Update the sel variable
            print("Sel detected")
            dynamic_variables["%sel%"].set_value(json_osc["args"][0].split(" ")[0])

        elif "/eos/out/event/show/saved" in json_osc["address"]:
            # Update the filename variable
            print("Filename detected")
            dynamic_variables["%filename%"].set_value(json_osc["args"][0].split("/")[-1])

        elif "cmd" in json_osc["address"]:
            print("Command detected")
            # Update the current console mode
            print(json_osc["args"][0])
            if "LIVE" in json_osc["args"][0]:
                print("LIVE!")
                dynamic_variables["%live%"].set_value("True")
                dynamic_variables["%blind%"].set_value("False")
                dynamic_variables["%staging%"].set_value("False")
            elif "BLIND" in json_osc["args"][0]:
                print("BLIND!")
                dynamic_variables["%live%"].set_value("False")
                dynamic_variables["%blind%"].set_value("True")
                dynamic_variables["%staging%"].set_value("False")

            if "Staging" in json_osc["args"][0]:
                print("STAGING!")
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
            add_variable = True
            for variable in user_variables:
                if variable.name == request.form["variable_name"]:
                    add_variable = False
                    break

            if add_variable:
                user_variables.append(InternalVar(request.form["variable_name"], request.form["variable_value"]))

                new_variable = ET.SubElement(variable_root, "variable")
                new_variable_name = ET.SubElement(new_variable, "name")
                new_variable_name.text = request.form["variable_name"]
                new_variable_value = ET.SubElement(new_variable, "value")
                new_variable_value.text = request.form["variable_value"]

                variable_tree.write("config/variables.xml")

        elif request.form["submit_variable"] == "Delete":
            # Delete the variable
            for i in range(len(user_variables)):
                if user_variables[i].name == request.form["variable_name"]:
                    user_variables.pop(i)

            variable_list = variable_root.findall("variable")
            for variable in variable_list:
                if variable.find("name").text == request.form["variable_name"]:
                    variable_root.remove(variable)
                    break

            variable_tree.write("config/variables.xml")
        else:
            for variable in user_variables:
                if variable.name == request.form["variable_name"]:
                    variable.set_value(request.form["variable_value"])

            variable_list = variable_root.findall("variable")
            for variable in variable_list:
                if variable.find("name").text == request.form["variable_name"]:
                    variable.find("value").text = request.form["variable_value"]

            variable_tree.write("config/variables.xml")

            dynamic_variables_list = []
            for item in dynamic_variables.items():
                dynamic_variables_list.append([item[0], getattr(item[1], "var_value")])

        return render_template("variables.html", user_variables=user_variables, dynamic_variables=dynamic_variables_list)


def start_osc_client(network_config):
    """Start a new OSC server and client to connect to the console"""
    try:
        osc_client = udp_client.SimpleUDPClient(network_config[0], int(network_config[1]))
        osc_client.send_message("/eos/ping", "macroPlus")
        return osc_client
    except ValueError:
        print("Bad config")
        return "Invalid network config. Try again."


def parse_macros(macro_list):
    # Generate the information for the macro list on the page
    main_macro_list = []
    for macro in macro_list:
        # Open the macro's file and pull in the relevant trigger and action
        try:
            with open(macro.find("path").text, "r") as macro_file:
                macro_action = macro_file.read()
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


if __name__ == "__main__":
    app.run(debug=True)