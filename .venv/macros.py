import datetime
import math
import os
import re
import time
from xml.etree import ElementTree as ET

import osc
import scripting
import variables
from pythonosc import udp_client

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
    intermal_macros.append(Macro(name, trigger, action, uuid, arg_index))
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
        self.requested_arg_index = requested_arg
        self.input_from_arg = arg_input
        self.last_fire_time = last_fire_time

    def run_action(self, osc_client, osc_addr: str, osc_arg: list, internal_macros: list, internal_variables, user_variables, dynamic_variables, has_eos_queries=False, arg_input=None, debug=False) -> tuple:
        """Loop through the action and handle all base steps before handing off to the interpreter."""
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

                internal_macros = add_internal_macro(name, action, trigger, self.uuid, internal_macros)

                if i == len(eos_queries):
                    # Done adding macros, send the osc message to start it all
                    # TODO: make this send the first OSC message
                    return ("wait", "")
        else:
            if debug:
                print("STATUS: Eos queries provided, running action.")
            # Eos queries have been received, run the macro
            run_result, run_args = scripting.run_script(self.action, osc_client, osc_addr, osc_arg, internal_macros, internal_variables, user_variables, dynamic_variables, arg_input, debug=debug)

            return run_result, run_args
