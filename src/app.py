import datetime
import json
import math
import os
import re
import time
import uuid

import xml.etree.ElementTree as ET

import macros
import osc
import scripting
import variables
from flask import Flask, render_template, request
from pythonosc import udp_client

console_network_config = []
osc_client = None

user_macros = []
internal_macros = []

user_variables = []
internal_variables = []
dynamic_variables = [variables.InternalVar("%cue%", ""),
                     variables.InternalVar("%list%", ""),
                     variables.InternalVar("%listcue%", ""),
                     variables.InternalVar("%sel%", ""),
                     variables.InternalVar("%filename%", ""),
                     variables.InternalVar("%time%", ""),
                     variables.InternalVar("%live%", ""),
                     variables.InternalVar("%blind%", ""),
                     variables.InternalVar("%staging%", "")
                     ]

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


def initialize_config(console_network_config, osc_client, user_macros, user_variables):
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

    osc_client = osc.start_osc_client(console_network_config)

    with open("config/macros.xml", "r") as file:
        macro_list = macros.load_macros()

        # Make a macro object for each macro loaded
        for macro in macro_list:
            name = macro.find("name").text
            trigger = macro.find("trigger_type").text + " " + macro.find("trigger").text
            macro_uuid = macro.find("uuid").text
            arg_index = macro.find("arg_index").text
            try:
                with open(macro.find("path").text, "r") as action_file:
                    action = action_file.readlines()
            except FileNotFoundError:
                # Macro config file is out of date, macro action file does not exist.
                # TODO: Figure out how to remove this macro from the list/the XML config
                pass

            # Append the new macro to user_macros
            user_macros = macros.add_user_macro(name, trigger, action, macro_uuid, arg_index, user_macros, path=macro.find("path").text)

    with open("config/variables.xml", "r") as file:
        # Load user variables
        variable_list = variables.load_variables()

        # Make a variable object for each variable loaded
        for variable in variable_list:
            user_variables = variables.add_user_variable(variable.find("name").text, variable.find("value").text, user_variables, loaded_from_file=True)

    return console_network_config, osc_client, user_macros, user_variables


def run_macro(macro_uuid_to_run, osc_client, json_osc, user_macros, internal_macros, internal_variables, user_variables,
              dynamic_variables, requested_arg, has_eos_queries=False, mark_as_run=False, debug=False):
    """Run the given macro, and handle its run result appropriately"""
    print("Current mark as run: %s" % mark_as_run)
    run_result = ("wait", "")
    for macro in internal_macros:
        if macro.uuid == macro_uuid_to_run:
            macro.last_fire_time = datetime.datetime.now()
            run_result = macro.run_action(osc_client, json_osc["address"], json_osc["args"],
                                                  internal_macros, internal_variables, user_variables,
                                                  dynamic_variables, mark_as_run=True, arg_input=requested_arg, has_eos_queries=has_eos_queries,
                                                  debug=debug)

            print("Run result: ", run_result)
            internal_macros = run_result[2]
            break

    for macro in user_macros:
        if macro.uuid == macro_uuid_to_run:
            macro.last_fire_time = datetime.datetime.now()
            run_result = macro.run_action(osc_client, json_osc["address"], json_osc["args"],
                                                  internal_macros, internal_variables, user_variables,
                                                  dynamic_variables, mark_as_run=True, arg_input=requested_arg, has_eos_queries=has_eos_queries,
                                                  debug=debug)

            print("Run result: ", run_result)
            internal_macros = run_result[2]
            break

    # Check run_result to see what to do next
    if run_result[0] == "wait":
        # Do nothing
        pass
    elif run_result[0] == "done":
        # Delete all internal variables and macros
        # TODO: Add a reload from file feature for persistent internal objects
        pass

    elif run_result[0] == "run" and run_result[1] is not None:
        internal_macros = run_macro(run_result[1], osc_client, json_osc, user_macros, run_result[2], internal_variables, user_variables,
              dynamic_variables, requested_arg, has_eos_queries=True, mark_as_run=True, debug=debug)

        internal_macros = internal_macros
        print("Deleting macro %s" % macro_uuid_to_run)
        internal_macros = macros.delete_internal_macro(macro_uuid_to_run, internal_macros)
        print("Internal macros length: %i" % len(internal_macros))

    """print("Deleting macro %s" % macro_uuid_to_run)
    internal_macros = run_result[2]
    internal_macros = macros.delete_internal_macro(macro_uuid_to_run, internal_macros)
    print("Internal macros length: %i" % len(internal_macros))

    internal_macro_buffer = []
    for i in range(len(internal_macros)):
        print(internal_macros[i].has_been_run)
        if not internal_macros[i].has_been_run:
            internal_macro_buffer.append(internal_macros[i])
            # internal_macros.pop(i)
"""
    print("Deleting internal macros")
    print(len(internal_macros))

    return internal_macros


# Flask setup
app = Flask(__name__)

# Home page
@app.route("/", methods=["POST", "GET"])
def index():
    """Load existing macros and pass them to the page."""
    global osc_client, macro_tree, user_macros, internal_macros, internal_variables, user_variables, dynamic_variables

    macro_list = macros.load_macros()

    if request.method == "GET":
        main_macro_list = macros.parse_macros(macro_list)

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
            except ValueError:
                new_macro_arg_index = 0
            new_macro_action = request.form["macro_action"].split("\n")

            # Set all loaded XML values to the new data
            all_macros = macros.load_macros(return_tree=True)
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
                            macro_object.requested_arg_index = int(new_macro_arg_index)
                            macro_object.action = new_macro_action
                            print(macro_object.action)
                            break

                    break

            if not found_macro:
                # Add the new macro to user_macros
                user_macros = macros.add_user_macro(new_macro_name, " ".join([new_macro_trigger_type, new_macro_trigger]),
                               new_macro_action, macro_uuid_to_update,
                               new_macro_arg_index, user_macros, path="")

            if request.form["submit_macro"] == "Run Macro":
                # Manually run the macro's action
                for macro in user_macros:
                    if macro.uuid == request.form["macro_uuid"]:
                        print("Manually running macro: %s" % macro.uuid)
                        fake_json = {"address": "", "args": [""]}
                        fake_requested_arg = ""
                        internal_variables = []
                        internal_macros = run_macro(macro.uuid, osc_client, fake_json, user_macros, internal_macros, internal_variables, user_variables, dynamic_variables, fake_requested_arg, debug=True)


        elif request.form["submit_macro"] == "Delete Macro":
            # Find the macro with the matching UUID and delete it from the config completely
            user_macros = macros.delete_user_macro(request.form["macro_uuid"], user_macros)

    macro_list = macros.load_macros()
    main_macro_list = macros.parse_macros(macro_list)

    return render_template("index.html", macro_list=main_macro_list, new_uuid=str(uuid.uuid4()))


@app.route("/network_config", methods=["POST", "GET"])
def network_config():
    global console_network_config, network_tree, osc_client, internal_variables, user_variables, dynamic_variables
    if request.method == "POST":
        # Form submissions
        if request.form["submit"] == "Update Config":
            new_console_ip = request.form["console_ip"]
            new_console_port = request.form["console_port"]

            console_network_config = [new_console_ip, new_console_port, ""]

            # Attempt to start an OSC client with the provided config
            osc_client = osc.start_osc_client(console_network_config)

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
                osc_data = {"osc_addr": "/eos/ping", "osc_args": "macroPlus"}
                variables = {"internal_variables": internal_variables, "user_variables": user_variables, "dynamic_variables": dynamic_variables}
                _cleaned_osc= osc.process_osc("", osc_data, variables)

                if len(_cleaned_osc > 2):
                    eos_query_count = _cleaned_osc[2]

                _cleaned_osc_addr = _cleaned_osc[0]
                _cleaned_osc_args = _cleaned_osc[1]
                osc_client.send_message(_cleaned_osc_addr, _cleaned_osc_args)
        elif request.form["submit"] == "Send OSC":
            if osc_client:
                # If the console is configured, send the custom OSC
                osc_data = {"osc_addr": request.form["custom_osc_address"], "osc_args": request.form["custom_osc_arguments"].split()}
                variables = {"internal_variables": internal_variables, "user_variables": user_variables,
                             "dynamic_variables": dynamic_variables}
                _cleaned_osc = osc.process_osc("", osc_data, variables)

                if len(_cleaned_osc) > 2:
                    eos_query_count = _cleaned_osc[2]

                _cleaned_osc_addr = _cleaned_osc[0]
                _cleaned_osc_args = _cleaned_osc[1]
                osc_client.send_message(_cleaned_osc_addr, _cleaned_osc_args)
        else:
            pass
        return render_template("network_config.html", console_network=console_network_config)

    else:
        # Basic loading
        return render_template("network_config.html", console_network=console_network_config)


@app.route("/osc", methods=["POST"])
def handle_osc():
    """Handle incoming OSC from the console. Comes in as JSON"""
    global console_network_config, osc_client, user_macros, internal_macros, internal_variables, user_variables, dynamic_variables
    json_osc = request.json
    json_osc["args"] = json.loads(json_osc["args"])

    if json_osc["address"] == "/eos/out/ping" and json_osc["args"][0] == "macroPlus":
        console_network_config[2] = "%s - Ping validated!" % str(datetime.datetime.now())
        return render_template("index.html", console_network_config=console_network_config)
    else:
        # Check incoming OSC against internal macros
        print("Received OSC address %s" % json_osc["address"])
        for internal_macro in internal_macros:
            # Internal macro triggers are always OSC commands, check the second word for the address.
            # Check if the address matches the given address pattern and any specified arguments match the right argument pattern
            address_match = False
            args_match = True
            print("Addresses: ", internal_macro.trigger_address, json_osc["address"])
            if re.match(internal_macro.trigger_address, json_osc["address"]):
                address_match = True
                print("Address matched")

            # If any arguments do not match the pattern, or if a necessary argument doesn't exist, args do not match
            for i in range(len(internal_macro.trigger_args)):
                try:
                    if re.match(internal_macro.trigger_args[i], str(json_osc["args"][i])):
                        pass
                    else:
                        args_match = False
                        break
                except IndexError:
                    args_match = False

            cooldown_over = (datetime.datetime.now() - internal_macro.last_fire_time).total_seconds() >= macros.macro_cooldown_time

            if address_match and args_match and cooldown_over:
                # Address and args matched, run the action.
                # Try to give it the requested argument if it exists
                try:
                    requested_arg = json_osc["args"]
                    # requested_arg = json_osc["args"][internal_macro.requested_arg_index]
                except IndexError:
                    requested_arg = ""
                internal_macros = run_macro(internal_macro.uuid, osc_client, json_osc, user_macros, internal_macros, internal_variables, user_variables, dynamic_variables, requested_arg, debug=True)


        for user_macro in user_macros:
            # Check if user macro relies on OSC for a trigger. If it does, see if it matches and run it if it does.
            if user_macro.trigger_type == "osc":
                # Internal macro triggers are always OSC commands, check the second word for the address.
                # Check if the address matches the given address pattern and any specified arguments match the right argument pattern
                address_match = False
                args_match = True
                if re.match(user_macro.trigger_address, json_osc["address"]):
                    address_match = True

                # If any arguments do not match the pattern, or if a necessary argument doesn't exist, args do not match
                for i in range(len(user_macro.trigger_args)):
                    try:
                        if re.match(user_macro.trigger_args[i], json_osc["args"][i]):
                            pass
                        else:
                            args_match = False
                            break
                    except IndexError:
                        args_match = False

                cooldown_over = (datetime.datetime.now() - user_macro.last_fire_time).total_seconds() >= macros.macro_cooldown_time

                if address_match and args_match and cooldown_over:
                    # If the address matches, check that the macro's cooldown is over, then run the action.
                    try:
                        requested_arg = json_osc["args"]
                        # requested_arg = json_osc["args"][user_macro.requested_arg_index]
                    except IndexError:
                        requested_arg = 0

                    internal_variables = []
                    internal_macros = run_macro(user_macro.uuid, osc_client, json_osc, user_macros, internal_macros,
                              internal_variables, user_variables, dynamic_variables, requested_arg, debug=True)

            elif user_macro.trigger_type == "cue":
                # Handle macros which fire on a given cue
                if "/eos/out/event/cue/%s/fire" % user_macro.trigger_address == json_osc["address"]:
                    # Check that the macro_cooldown_time has elapsed since the macro was last fired.
                    if (datetime.datetime.now() - user_macro.last_fire_time).total_seconds() >= macros.macro_cooldown_time:
                        # If the address matches, run the action.
                        try:
                            requested_arg = json_osc["args"]
                            # requested_arg = json_osc["args"][user_macro.requested_arg_index]
                        except IndexError:
                            requested_arg = 0
                        internal_variables = []
                        internal_macros = run_macro(user_macro.uuid, osc_client, json_osc, user_macros, internal_macros,
                                  internal_variables, user_variables, dynamic_variables, requested_arg, debug=True)

        # Check incoming OSC against dynamic variables
        if "/eos/out/active/cue/text" in json_osc["address"]:
            # Update the list, cue and listcue variables
            split_args = json_osc["args"][0].split(" ")
            for dynamic_variable in dynamic_variables:
                if dynamic_variable.name == "%cue%":
                    dynamic_variable.set_value(split_args[0].split("/")[1])
                    break
                elif dynamic_variable.name == "%list%":
                    dynamic_variable.set_value(split_args[0].split("/")[0])
                    break
                elif dynamic_variable.name == "%listcue%":
                    dynamic_variable.set_value(split_args[0])
                    break

        elif "/eos/out/active/chan" in json_osc["address"]:
            # Update the sel variable
            for dynamic_variable in dynamic_variables:
                if dynamic_variable.name == "%sel%":
                    dynamic_variable.set_value(json_osc["args"][0].split(" ")[0])
                    break

        elif "/eos/out/event/show/saved" in json_osc["address"]:
            # Update the filename variable
            for dynamic_variable in dynamic_variables:
                if dynamic_variable.name == "%filename%":
                    dynamic_variable.set_value(json_osc["args"][0].split("/")[-1])
                    break

        elif "cmd" in json_osc["address"]:
            # Update the current console mode
            if "LIVE" in json_osc["args"][0]:
                for dynamic_variable in dynamic_variables:
                    if dynamic_variable.name == "%live%":
                        dynamic_variable.set_value("True")
                        break
                    elif dynamic_variable.name == "%blind%":
                        dynamic_variable.set_value("False")
                        break
            elif "BLIND" in json_osc["args"][0]:
                for dynamic_variable in dynamic_variables:
                    if dynamic_variable.name == "%live%":
                        dynamic_variable.set_value("False")
                        break
                    elif dynamic_variable.name == "%blind%":
                        dynamic_variable.set_value("True")
                        break

            if "Staging" in json_osc["args"][0]:
                for dynamic_variable in dynamic_variables:
                    if dynamic_variable.name == "%staging%":
                        dynamic_variable.set_value("True")
                        break
            else:
                for dynamic_variable in dynamic_variables:
                    if dynamic_variable.name == "%staging%":
                        dynamic_variable.set_value("False")
                        break

        return ("", 204)


@app.route("/variable_console", methods=["GET", "POST"])
def variable_console():
    global user_variables, dynamic_variables
    if request.method == "GET":
        # Load the page, displaying variables

        return render_template("variable_console.html", user_variables=user_variables, dynamic_variables=dynamic_variables, internal_variables=internal_variables)

    elif request.method == "POST":
        # Variable is being updated
        if request.form["submit_variable"] == "Add":
            # Add only if it isn't a duplicate
            user_variables = variables.add_user_variable(request.form["variable_name"], request.form["variable_value"], user_variables, debug=True)

        elif request.form["submit_variable"] == "Delete":
            # Delete the variable
            user_variables = variables.delete_user_variable(request.form["variable_name"], user_variables, debug=True)

        else:
            # Set the variable to a new value
            user_variables = variables.set_user_variable(request.form["variable_name"], request.form["variable_value"], user_variables, debug=True)

        return render_template("variable_console.html", user_variables=user_variables, dynamic_variables=dynamic_variables)


# Initialize the config on startup
console_network_config, osc_client, user_macros, user_variables = initialize_config(console_network_config, osc_client, user_macros, user_variables)

if __name__ == "__main__":
    app.run(debug=True)
