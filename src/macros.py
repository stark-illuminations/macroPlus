import datetime
import os
import re
import time
import uuid
import xml.etree.ElementTree
from xml.etree import ElementTree as ET

import scripting
import value
import eos_query

macro_cooldown_time = 1

last_macro_access_time = datetime.datetime.now()
macro_write_interval = 30


def load_macros(return_tree: bool = False):
    """
    Load macros config from XML file

    :param bool return_tree: Whether to return the macro tree. If set to False, returns nothing
    """
    # Open and read the macro config file
    macros_loaded = False
    while not macros_loaded:
        try:
            with open("config/macros.xml", "r") as macro_file:
                macro_tree = ET.parse(macro_file)
                macros_loaded = True

        except xml.etree.ElementTree.ParseError:
            print("XML error while loading macros, reattempting...")
            # I *think* this happens sometimes because the file is being read
            # while another function is working on it too.
            # Just wait a fraction of a second and then try again
            time.sleep(.1)

        if return_tree:
            return macro_tree

    # Parse the macros from the freshly-read file
    macro_root = macro_tree.getroot()
    macro_list = macro_root.findall("macro")

    return macro_list


def parse_macros(macro_list) -> list:
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
    global last_macro_access_time, macro_write_interval
    trigger_type = trigger.split(" ")[0]
    if trigger_type == "osc":
        trigger_address, trigger_args = value.regex_osc_trigger(trigger.split(" ")[1])
    else:
        trigger_address = trigger.split(" ")[1]
        trigger_args = []
    user_macros.append(Macro(name, trigger_type, trigger_address, trigger_args, action, uuid,
                             arg_index))

    if (path == "" and (datetime.datetime.now() - last_macro_access_time).total_seconds()
            > macro_write_interval):
        # This is a brand-new macro, add it to the XML tree and write to the file
        # Open and read the macro config file
        last_macro_access_time = datetime.datetime.now()
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
            with open(new_path.text, "w+") as macro_action_file:
                macro_action_file.write("".join(action))

    return user_macros


def delete_user_macro(macro_uuid, user_macros):
    """Delete a user macro from the XML config file, and remove its action file."""
    global last_macro_access_time, macro_write_interval
    if (datetime.datetime.now() - last_macro_access_time).total_seconds() > macro_write_interval:
        last_macro_access_time = datetime.datetime.now()
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


def add_internal_macro(name: str, trigger: tuple, action: str,
                       uuid: str, internal_macros: list, arg_index: int = 0) -> list:
    """
    Add a new user macro to internal_macros

    :param str name: The user-friendly name for the new macro
    :param tuple trigger: A tuple containing the trigger type in index 0, and the trigger value in index 1
    :param str action: A string containing the action script, separated by \n newlines
    :param str uuid: A UUID4 for the new macro
    :param internal_macros: A list of all current internal macros
    :param int arg_index: The argument index to get on firing (currently unused)
    """
    trigger_type = trigger[0]

    if trigger_type == "osc":
        # regex-ify trigger[1], yielding an address pattern and possible argument patterns
        trigger_address, trigger_args = value.regex_osc_trigger(trigger[1])
    else:
        # No arguments are allowed with non-OSC triggers
        trigger_address = trigger[1][0]
        trigger_args = []

    # Append the new macro to internal_macros
    internal_macros.append(Macro(name, trigger_type, trigger_address, trigger_args, action, uuid,
                                 arg_index))
    return internal_macros


def delete_internal_macro(macro_uuid: str, internal_macros: list) -> list:
    """
    Delete an internal macro from the list, then return remaining internal macros

    :param str macro_uuid: The UUID of the macro to delete
    :param list internal_macros: A list containing all current internal macros
    """
    # Delete the macro from internal_macros
    for i in range(len(internal_macros)):
        if internal_macros[i].uuid == macro_uuid:
            internal_macros.pop(i)
            break

    return internal_macros


class Macro:
    """Holds macro trigger and action."""

    def __init__(self, name, trigger_type: str, trigger_address: str, trigger_args: list,
                 action: list, uuid: str, requested_arg=0, arg_input="",
                 last_fire_time=datetime.datetime.now(), mark_as_run=False):
        self.name = name
        self.trigger_type = trigger_type
        self.trigger_address = trigger_address
        self.trigger_args = trigger_args
        self.action = action
        self.uuid = uuid
        self.requested_arg_index = int(requested_arg)
        self.input_from_arg = arg_input
        self.last_fire_time = last_fire_time
        self.has_been_run = mark_as_run

        print("New macro added!")
        print(f"- UUID: {self.uuid}")
        print("- Trigger Type: ", self.trigger_type)
        print("- Trigger Address: ", self.trigger_address)
        print("- Trigger Args: ", self.trigger_args)
        print(f"- Requested Arg: {self.requested_arg_index}")
        print("- Action: ", self.action)

    def run_action(self, osc_client, internal_macros: list, internal_variables, user_variables,
                   dynamic_variables, has_eos_queries=False, arg_input=None, mark_as_run=False,
                   debug=False) -> tuple:
        """Loop through the action and handle all base steps."""
        self.has_been_run = mark_as_run
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
                            print(f"STATUS: Eos query found: {word}")

                        parse_query = eos_query.parse_eos_query(word)
                        if parse_query is not None:
                            new_eos_query = eos_query.EosQuery(parse_query["target_type"],
                                                               parse_query["target"],
                                                               parse_query["attribute"],
                                                               parse_query["frame_type"],
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
                return ("run", self.uuid, internal_macros)

            if debug:
                print("STATUS: Action searched, Eos queries detected and parsed. "
                      "Building internal macros to resolve query.")

            # Build eos query actions
            # Set first_macro_uuid to None
            first_macro_uuid = None

            # Set next_macro_uuid to None. If internally set, it will override the next UUID
            # to be given (allows linking macros between sub-queries).
            next_macro_uuid = None

            for i in range(len(eos_queries)):
                for j in range(len(eos_queries[i].final_queries)):
                    # Run through list and make an internal macro for each query
                    current_query_address = eos_queries[i].final_queries[j][0]
                    current_query_response_trigger = eos_queries[i].final_queries[j][1]
                    new_macro_name = f"query_{i}_{self.uuid}"

                    internal_variable_name = f"internal_{i}_{self.uuid}"
                    print(f"Writing new variable: {internal_variable_name}")

                    if debug:
                        print(f"Current query address: {current_query_address}")
                    # TODO: Ignore the query if it is None (due to improper syntax)

                    if i == 0 and j == 0:
                        # First query
                        # Sends the first query and sets the first macro to be run
                        new_macro_uuid = str(uuid.uuid4())

                        if debug:
                            print(f"First query! Building send-only macro at UUID {new_macro_uuid} "
                                  f"and setting first macro.")

                        trigger = ("none", ["none"])
                        action = [f"osc {current_query_address}"]
                        internal_macros = add_internal_macro(new_macro_name, trigger, action,
                                                             new_macro_uuid, internal_macros)

                        first_macro_uuid = new_macro_uuid
                    elif j == 0:
                        # First sub-query
                        # Just sends the first query
                        if next_macro_uuid is None:
                            new_macro_uuid = str(uuid.uuid4())
                        else:
                            new_macro_uuid = next_macro_uuid
                            next_macro_uuid = None
                        if debug:
                            print(f"First subquery! Building send-only macro at UUID {new_macro_uuid}.")

                        trigger = ("none", ["none"])
                        action = [f"osc {current_query_address}"]
                        internal_macros = add_internal_macro(new_macro_name, trigger, action,
                                                             new_macro_uuid, internal_macros)
                    elif j < len(eos_queries[i].final_queries):
                        # All macros that aren't first or last
                        # These macros receive and store the previous query response
                        # and then send the next query
                        if next_macro_uuid is None:
                            new_macro_uuid = str(uuid.uuid4())
                        else:
                            new_macro_uuid = next_macro_uuid
                            next_macro_uuid = None
                        if debug:
                            print(f"Middle query! Building send/receive macro at"
                                  f" UUID {new_macro_uuid}.")

                        trigger = ("osc", eos_queries[i].final_queries[j - 1][1])
                        action = [f"newint #{internal_variable_name}# ="
                                  f" @{current_query_response_trigger[1]}@",
                                  f"osc {current_query_address}"]
                        internal_macros = add_internal_macro(new_macro_name, trigger, action,
                                                             new_macro_uuid, internal_macros,
                                                             arg_index=current_query_response_trigger[1])

                    if (j + 1) == len(eos_queries[i].final_queries) and (i + 1) < len(eos_queries):
                        # Final query of the sub-query, but not the last one overall
                        # Add final macro that just receives the final query response
                        new_macro_uuid = str(uuid.uuid4())

                        # Set next_macro_uuid to a new UUID so that the next macro build
                        # will use a predictable one so this macro can link to it.
                        next_macro_uuid = str(uuid.uuid4())
                        if debug:
                            print(f"Final sub-query! Building receive-and-run macro at"
                                  f" UUID {new_macro_uuid}.")

                        trigger = ("osc", current_query_response_trigger[0])
                        action = [f"newint #{internal_variable_name}# ="
                                  f" @{current_query_response_trigger[1]}@",
                                  f"run {next_macro_uuid}"]
                        internal_macros = add_internal_macro(new_macro_name, trigger, action,
                                                             new_macro_uuid, internal_macros,
                                                             arg_index=current_query_response_trigger[1])

                    elif (j + 1) == len(eos_queries[i].final_queries) and (i + 1) == len(eos_queries):
                        # Real final query! Same sort of action as the last sub-query,
                        # plus a line to delete all internal macros, and then run the original macro
                        new_macro_uuid = str(uuid.uuid4())
                        if debug:
                            print(f"Final query! Building receive-only macro at "
                                  f"UUID {new_macro_uuid}.")

                            print(current_query_response_trigger)
                        trigger = ("osc", current_query_response_trigger[0])
                        action = [f"newint #{internal_variable_name}# = "
                                  f"@{current_query_response_trigger[1]}@",
                                  "wipeints",
                                  "run %s" % self.uuid]
                        add_internal_macro(new_macro_name, trigger, action, new_macro_uuid,
                                           internal_macros,
                                           arg_index=current_query_response_trigger[1])

                        # Done adding macros, send the osc message to start it all

            return "run", first_macro_uuid, internal_macros
        else:
            if debug:
                print("STATUS: Eos queries provided, running action.")
            # Eos queries have been received, run the macro
            run_result, run_args, internal_macros = scripting.run_script(self.action, osc_client,
                                                                         self.uuid, internal_macros,
                                                                         internal_variables,
                                                                         user_variables,
                                                                         dynamic_variables,
                                                                         arg_input, debug=debug)

            # If instructed to, mark self as run
            return run_result, run_args, internal_macros
