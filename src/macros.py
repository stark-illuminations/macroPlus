import datetime
import math
import os
import re
import time
import uuid
from xml.etree import ElementTree as ET

import osc
import scripting
import variables
from pythonosc import udp_client
import eos_query

macro_cooldown_time = 1


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


def add_user_macro(name, trigger, action, uuid, arg_index, user_macros, path=""):
    """Add a new user macro to user_macros"""
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

    return user_macros


def delete_user_macro(macro_uuid, user_macros):
    """Delete a user macro from the XML config file, and remove its action file."""
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

    return user_macros


def add_internal_macro(name, trigger, action, uuid, internal_macros, arg_index=0):
    """Add a new user macro to internal_macros
    """
    internal_macros.append(Macro(name, trigger, action, uuid, arg_index))
    return internal_macros


def delete_internal_macro(macro_uuid, internal_macros):
    """Delete an internal macro from the list"""

    # Delete the macro from internal_macros
    for i in range(len(internal_macros)):
        if internal_macros[i].uuid == macro_uuid:
            internal_macros.pop(i)
            break

    return internal_macros


class Macro:
    """Holds macro trigger and action."""

    def __init__(self, name, trigger: str, action: list, uuid: str, requested_arg=0, arg_input="", last_fire_time=datetime.datetime.now()):
        self.name = name
        self.trigger = trigger
        self.action = action
        self.uuid = uuid
        self.requested_arg_index = int(requested_arg)
        self.input_from_arg = arg_input
        self.last_fire_time = last_fire_time

        print("New macro added!")
        print("- UUID: %s" % self.uuid)
        print("- Trigger: %s" % self.trigger)
        print("- Requested Arg: %s" % self.requested_arg_index)
        print("- Action: ", self.action)

    def run_action(self, osc_client, osc_addr: str, osc_arg: list, internal_macros: list, internal_variables, user_variables, dynamic_variables, has_eos_queries=False, arg_input=None, debug=False) -> tuple:
        """Loop through the action and handle all base steps before handing off to the interpreter."""
        if not has_eos_queries:
            if debug:
                print("STATUS: No Eos queries provided, searching action...")
            # Find all eos queries in the lines and then build their actions
            eos_queries = []
            for line in self.action:
                # Strip any newline characters or whitespace from the line
                line = line.strip(" \n\r")

                # Remove trailing colon, just in case
                line = line.strip(":")
                split_line = line.split(" ")
                for word in split_line:
                    if re.search("eos\(\S+\)", word) is not None:
                        # Eos query found, parse it and create an EosQuery object
                        word = word[5:-1]
                        if debug:
                            print("STATUS: Eos query found: %s" % word)

                        parse_query = eos_query.parse_eos_query(word)
                        if parse_query is not None:
                            new_eos_query = eos_query.EosQuery(parse_query["target_type"], parse_query["target"],
                                                               parse_query["attribute"], parse_query["frame_type"],
                                                               parse_query["frame_target"])
                            eos_queries.append(new_eos_query)
                        else:
                            # Query was improperly formatted, ignore it
                            print("Query was formatted wrong!")
                            eos_queries.append(None)

            if len(eos_queries) == 0:
                # No eos queries, return a run uuid action to run the macro's action
                if debug:
                    print("STATUS: Action searched, no Eos queries detected. Sending run action.")
                return ("run", self.uuid)

            if debug:
                print("STATUS: Action searched, Eos queries detected and parsed. "
                      "Building internal macros to resolve query.")

            print(eos_queries)

            # Build eos query actions
            last_osc = ""
            for i in range(len(eos_queries)):
                for j in range(len(eos_queries[i].final_queries)):
                    print(i, len(eos_queries), j, len(eos_queries[i].final_queries))
                    # Run through list and make an internal macro for each query
                    current_query_address = eos_queries[i].final_queries[j][0]
                    current_query_response_trigger = eos_queries[i].final_queries[j][1]
                    new_macro_name = "query_%s_%s" % (i, self.uuid)

                    new_macro_uuid = str(uuid.uuid4())
                    internal_variable_name = "internal_%i_%s" % (i, self.uuid)

                    if debug:
                        print("Current query address: %s" % current_query_address)
                    # TODO: Ignore the query if it is None (due to improper syntax)

                    if j == 0:
                        # First query
                        # Just sends the first query
                        if debug:
                            print("First query! Building send-only macro at UUID %s." % new_macro_uuid)

                        trigger = "None None"
                        action = ["osc %s" % current_query_address]
                        internal_macros.append(Macro(new_macro_name, trigger, action, new_macro_uuid))

                        first_macro_uuid = new_macro_uuid
                    elif j < len(eos_queries[i].final_queries):
                        # All macros that aren't first or last
                        # These macros receive and store the previous query response and then send the next query
                        if debug:
                            print("Middle query! Building send/receive macro at UUID %s." % new_macro_uuid)

                        trigger = "osc %s" % current_query_response_trigger[0]
                        action = ["newint #%s# = @%i@" % (internal_variable_name, current_query_response_trigger[1]),
                                  "osc %s" % current_query_address]
                        internal_macros.append(Macro(new_macro_name, trigger, action, new_macro_uuid,
                                                     requested_arg=current_query_response_trigger[1]))

                    if (j + 1) == len(eos_queries[i].final_queries) and (i + 1) < len(eos_queries):
                        # Final query of the sub-query, but not the last one overall
                        # Add final macro that just receives the final query response
                        if debug:
                            print("Final sub-query! Building receive-only macro at UUID %s." % new_macro_uuid)

                        trigger = "osc %s" % current_query_response_trigger[0]
                        action = ["newint #%s# = @%i@" % (internal_variable_name, current_query_response_trigger[1])]
                        internal_macros.append(Macro(new_macro_name, trigger, action, new_macro_uuid,
                                                     requested_arg=current_query_response_trigger[1]))

                    elif (j + 1) == len(eos_queries[i].final_queries) and (i + 1) == len(eos_queries):
                        # Real final query! Same sort of action as the last sub-query, but return a run command
                        if debug:
                            print("Final query! Building receive-only macro at UUID %s." % new_macro_uuid)

                        trigger = "osc %s" % current_query_response_trigger[0]
                        action = ["newint #%s# = @%i@" % (internal_variable_name, current_query_response_trigger[1])]
                        internal_macros.append(Macro(new_macro_name, trigger, action, new_macro_uuid,
                                                     requested_arg=current_query_response_trigger[1]))

                        # Done adding macros, send the osc message to start it all

                        return ("run", first_macro_uuid)
        else:
            if debug:
                print("STATUS: Eos queries provided, running action.")
            # Eos queries have been received, run the macro
            run_result, run_args = scripting.run_script(self.action, osc_client, osc_addr, osc_arg, internal_macros, internal_variables, user_variables, dynamic_variables, arg_input, debug=debug)

            return run_result, run_args
