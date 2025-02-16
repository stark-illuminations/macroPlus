from xml.etree import ElementTree as ET


import value


def load_variables():
    """Load user variables from config file."""
    # Open and read the macro config file
    with open("config/variables.xml", "r") as variable_file:
        variable_tree = ET.parse(variable_file)

        # Parse the variables from the freshly-read file
        variable_root = variable_tree.getroot()
        variable_list = variable_root.findall("variable")

        return variable_list


def add_user_variable(variable_name, variable_value, user_variables, debug=False):
    """Add a new user variable with the given name and value"""
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
        user_variables.append(InternalVar(variable_name, value.parse_value(variable_value, debug=debug)))

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
                new_variable_value.text = str(value.parse_value(variable_value, debug=debug))

                variable_tree.write("config/variables.xml")

    return user_variables


def delete_user_variable(variable_name, user_variables, debug=False):
    """Delete the user variable with the given name."""
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

    return user_variables


def get_user_variable(variable_name, user_variables):
    """Get the value of the specified user variable, or return None if the variable does not exist."""
    for variable in user_variables:
        if variable.name == variable_name:
            return variable.var_value, user_variables

    # If the variable doesn't exist, return None
    return None, user_variables


def set_user_variable(variable_name, new_value, user_variables, debug=False):
    """Set a user variable to a new value"""
    for variable in user_variables:
        if variable.name == variable_name:
            variable.set_value(value.parse_value(new_value, debug=debug))

    with open("config/variables.xml", "r") as variable_file:
        variable_tree = ET.parse(variable_file)
        variable_root = variable_tree.getroot()
        variable_list = variable_root.findall("variable")

        for variable in variable_list:
            if variable.find("name").text == variable_name:
                variable.find("value").text = str(value.parse_value(new_value, debug=debug))

        variable_tree.write("config/variables.xml")

    return user_variables


def add_internal_variable(variable_name, variable_value, internal_variables, debug=False):
    """Add a new internal variable with the given name and value"""

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
        internal_variables.append(InternalVar(variable_name, value.parse_value(variable_value)))

    return internal_variables


def get_internal_variable(variable_name, internal_variables):
    """Get the value of the specified internal variable, or return None if the variable does not exist."""
    for variable in internal_variables:
        if variable.name == variable_name:
            return variable.var_value, internal_variables

    # If the variable doesn't exist, return None
    return None, internal_variables


def set_internal_variable(variable_name, internal_variables, new_value):
    """Set an internal variable to a new value"""
    for variable in internal_variables:
        if variable.name == variable_name:
            variable.set_value(value.parse_value(new_value))

    return internal_variables


def delete_internal_variable(variable_name, internal_variables, debug=False):
    """Delete the internal variable with the given name."""
    if debug:
        print("Deleting internal variable: %s" % variable_name)
        print("- Searching for internal variable.")

    for i in range(len(internal_variables)):
        if internal_variables[i].name == variable_name:
            if debug:
                print("-- Internal variable found! Deleting.")
            internal_variables.pop(i)

    return internal_variables


class InternalVar:
    """Holds a value for use by the user or a macro."""

    def __init__(self, name: str, value: str):
        self.name = name
        self.var_value = value

    def set_value(self, new_value):
        """Set the var_value to a new value, ensuring that it has been parsed."""
        self.var_value = value.parse_value(new_value)
