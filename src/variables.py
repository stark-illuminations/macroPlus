import xml.etree.ElementTree
import time
import datetime

import value

last_variable_access_time = datetime.datetime.now()


def load_variables() -> list:
    """
    Load user variables from config file, then return the parsed list.
    """
    # Open and read the macro config file
    variables_loaded = False
    while not variables_loaded:
        try:
            with open("config/variables.xml", "r") as variable_file:
                variable_tree = xml.etree.ElementTree.parse(variable_file)

                # Parse the variables from the freshly-read file
                variable_root = variable_tree.getroot()
                variable_list = variable_root.findall("variable")
                variables_loaded = True
        except xml.etree.ElementTree.ParseError:
            print("XML error while loading variables, reattempting...")
            # I *think* this happens sometimes because the file
            # is being read while another function is working on it too
            # Just wait a fraction of a second and then try again
            time.sleep(.1)

    return variable_list


def add_user_variable(variable_name: str, variable_value: str, user_variables: list,
                      loaded_from_file: bool = False, debug:bool = False) -> list:
    """
    Add a new user variable with the given name and value

    :param str variable_name: The name to assign to the new variable
    :param str variable_value: The value to assign to the new variable. String preferred, but value
        will be parsed
    :param list user_variables: A list of current user variables
    :param bool loaded_from_file: Set to True if new variable was loaded from the file.
        Prevents re-writing XML
    :param bool debug: Whether to print debug messages

    """
    if debug:
        print("Adding user variable!")
        print(f"Raw variable name: {variable_name}")
        print(f"Raw variable value: {variable_value}")
    # Format name properly
    variable_name = variable_name.replace(" ", "_")
    variable_name = variable_name.replace("/", "_")
    variable_name = variable_name.lower()
    variable_name = variable_name.strip()
    variable_name = variable_name.strip("*")
    variable_name = "*%s*" % variable_name
    if debug:
        print(f"Processed variable name: {variable_name}")
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
        user_variables.append(InternalVar(variable_name, value.parse_value(
            variable_value, debug=debug)))

        if not loaded_from_file:
            with open("config/variables.xml", "r") as variable_file:
                variable_tree = xml.etree.ElementTree.parse(variable_file)
                variable_root = variable_tree.getroot()
                variable_list = variable_root.findall("variable")

                exists_in_config = False

                for variable in variable_list:
                    if variable.find("name").text == variable_name:
                        # Variable already exists in XML, we're probably pulling it from there.
                        exists_in_config = True

                if not exists_in_config:
                    new_variable = xml.etree.ElementTree.SubElement(variable_root, "variable")
                    new_variable_name = xml.etree.ElementTree.SubElement(new_variable, "name")
                    new_variable_name.text = variable_name
                    new_variable_value = xml.etree.ElementTree.SubElement(new_variable, "value")
                    new_variable_value.text = str(value.parse_value(variable_value, debug=debug))

                    variable_tree.write("config/variables.xml")

    return user_variables


def delete_user_variable(variable_name: str, user_variables: list, debug: bool = False) -> list:
    """
    Delete the user variable with the given name.

    :param str variable_name: The name of the user variable to delete
    :param list user_variables: A list of all current user variables
    :param bool debug: Whether to print debug messages
    """
    global last_variable_access_time

    if debug:
        print(f"Deleting user variable: {variable_name}")
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
        variable_tree = xml.etree.ElementTree.parse(variable_file)
        variable_root = variable_tree.getroot()
        variable_list = variable_root.findall("variable")

        for variable in variable_list:
            if variable.find("name").text == variable_name:
                if debug:
                    print("-- User variable found in XML! Deleting.")
                variable_root.remove(variable)
                break

        variable_tree.write("config/variables.xml")

    return user_variables


def get_user_variable(variable_name: str, user_variables: list) -> tuple:
    """
    Get the value of the specified user variable, or return None if the variable does not exist.

    :param str variable_name: The name of the user variable to search for
    :param list user_variables: A list of all current user_variables
    """
    for variable in user_variables:
        if variable.name == variable_name:
            return variable.var_value, user_variables

    # If the variable doesn't exist, return None
    return None, user_variables


def set_user_variable(variable_name: str, new_value: str, user_variables: list,
                      debug: bool = False) -> list:
    """
    Set a user variable to a new value

    :param str variable_name: The variable name to search for
    :param str new_value: The new value for the given variable. String preferred,
        but the value will be processed
    :param list user_variables: A list of all current user variables
    :param bool debug: Whether to print debug messages
    """
    for variable in user_variables:
        if variable.name == variable_name:
            variable.set_value(value.parse_value(new_value, debug=debug))

    with open("config/variables.xml", "r") as variable_file:
        variable_tree = xml.etree.ElementTree.parse(variable_file)
        variable_root = variable_tree.getroot()
        variable_list = variable_root.findall("variable")

        for variable in variable_list:
            if variable.find("name").text == variable_name:
                variable.find("value").text = str(value.parse_value(new_value, debug=debug))

        variable_tree.write("config/variables.xml")

    return user_variables


def add_internal_variable(variable_name: str, variable_value: str, internal_variables: list,
                          debug: bool = False) -> list:
    """
    Add a new internal variable with the given name and value.

    :param str variable_name: The name of the internal variable to add
    :param str variable_value: The value for the new variable
    :param list internal_variables: A list of all current internal variables
    :param bool debug: Whether to print debug messages
    """

    if debug:
        print("Adding internal variable!")
        print(f"Raw variable name: {variable_name}")
        print(f"Raw variable value: {variable_value}")
    # Format name properly
    variable_name = variable_name.replace(" ", "_")
    variable_name = variable_name.replace("/", "_")
    variable_name = variable_name.lower()
    variable_name = variable_name.strip()
    variable_name = variable_name.strip("#")
    variable_name = f"#{variable_name}#"
    if debug:
        print(f"Processed variable name: {variable_name}")

    # Check that variable is not a duplicate of an existing internal_variable
    add_variable = True
    for variable in internal_variables:
        if variable.name == variable_name:
            if debug:
                print("Duplicate found, overwriting.")
                variable.var_value = value.parse_value(variable_value)
            add_variable = False
            break

    if add_variable:
        # If the variable is not a duplicate, add it to the list.
        if debug:
            print("No duplicate found. Adding variable.")
        internal_variables.append(InternalVar(variable_name, value.parse_value(variable_value)))

    return internal_variables


def get_internal_variable(variable_name: str, internal_variables: list) -> tuple:
    """
    Get the value of the specified internal variable, or return None if the variable does not exist.

    :param str variable_name: The name of the variable to get the value of
    :param list internal_variables: A list containing all current internal variables
    """
    for variable in internal_variables:
        if variable.name == variable_name:
            return variable.var_value, internal_variables

    # If the variable doesn't exist, return None
    return None, internal_variables


def set_internal_variable(variable_name: str, internal_variables: list, new_value: str) -> list:
    """
    Set an internal variable to a new value.

    :param str variable_name: The name of the internal variable to set
    :param list internal_variables: A list containing all internal variables
    :param str new_value: The new value for the variable. String preferred,
        but value will be processed.
    """
    for variable in internal_variables:
        if variable.name == variable_name:
            variable.set_value(value.parse_value(new_value))

    return internal_variables


def delete_internal_variable(variable_name: str, internal_variables: list, debug: bool = False):
    """
    Delete the internal variable with the given name.

    :param str variable_name: The name of the internal variable to delete
    :param list internal_variables: A list of all current internal variables
    :param bool debug: Whether to print debug messages
    """
    if debug:
        print(f"Deleting internal variable: {variable_name}")
        print("- Searching for internal variable.")

    for i in range(len(internal_variables)):
        if internal_variables[i].name == variable_name:
            if debug:
                print("-- Internal variable found! Deleting.")
            internal_variables.pop(i)

    return internal_variables


class InternalVar:
    """Holds a value for use by the user or a macro."""

    def __init__(self, name: str, var_value: str):
        self.name = name
        self.var_value = var_value

    def set_value(self, new_value):
        """Set the var_value to a new value, ensuring that it has been parsed."""
        self.var_value = value.parse_value(new_value)
