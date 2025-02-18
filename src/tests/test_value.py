import value
import variables

raw_values = {None, 0, -1, 1, 0.0, -1.0, 1.0, 0.1, -1.1, 1.1, True, False, "", "None", "0", "-1", "1", "0.0", "-1.0",
              "1.0", "0.1", "-1.1", "1.1", "True", "False", "Test", "Two words", "underscore_words"}


def test_parse_value():
    """Test parse_value with many possible values, and check that they are returned as the proper type."""

    assert value.parse_value(None) == None
    assert value.parse_value(0) == 0
    assert value.parse_value(-1) == -1
    assert value.parse_value(1) == 1
    assert value.parse_value(0.0) == 0
    assert value.parse_value(-1.0) == -1
    assert value.parse_value(1.0) == 1
    assert value.parse_value(0.1) == 0.1
    assert value.parse_value(-1.1) == -1.1
    assert value.parse_value(1.1) == 1.1
    assert value.parse_value(True) == True
    assert value.parse_value(False) == False
    assert value.parse_value("") == ""
    assert value.parse_value("None") == "None"
    assert value.parse_value("0") == 0
    assert value.parse_value("-1") == -1
    assert value.parse_value("1") == 1
    assert value.parse_value("0.0") == 0
    assert value.parse_value("-1.0") == -1
    assert value.parse_value("1.0") == 1
    assert value.parse_value("0.1") == 0.1
    assert value.parse_value("-1.1") == -1.1
    assert value.parse_value("1.1") == 1.1
    assert value.parse_value("True") == True
    assert value.parse_value("False") == False
    assert value.parse_value("Test") == "Test"
    assert value.parse_value("Two words") == "Two words"
    assert value.parse_value("underscore_words") == "underscore_words"


def test_parse_script_word():
    "Test parse_script_word."

    internal_variables = [variables.InternalVar("#internal_0#", "True")]
    user_variables = [variables.InternalVar("*user_0*", "True")]
    dynamic_variables = [variables.InternalVar("%cue%", "103")]
    arg_input=["Arg 0"]

    # Internal variables
    assert value.parse_script_word("#internal_0#", internal_variables, user_variables, dynamic_variables,
                                   arg_input=arg_input) == internal_variables[0].var_value
    assert value.parse_script_word("#Internal_0#", internal_variables, user_variables, dynamic_variables,
                                   arg_input=arg_input) == internal_variables[0].var_value
    assert value.parse_script_word("#internal_1#", internal_variables, user_variables, dynamic_variables,
                                   arg_input=arg_input) == None
    assert value.parse_script_word("#internal_0", internal_variables, user_variables, dynamic_variables,
                                   arg_input=arg_input) == "#internal_0"

    # User variables
    assert value.parse_script_word("*user_0*", internal_variables, user_variables, dynamic_variables,
                                   arg_input=arg_input) == user_variables[0].var_value
    assert value.parse_script_word("*User_0*", internal_variables, user_variables, dynamic_variables,
                                   arg_input=arg_input) == user_variables[0].var_value
    assert value.parse_script_word("*user_1*", internal_variables, user_variables, dynamic_variables,
                                   arg_input=arg_input) == None
    assert value.parse_script_word("*user_0", internal_variables, user_variables, dynamic_variables,
                                   arg_input=arg_input) == "*user_0"
    # Dynamic variables
    assert value.parse_script_word("%cue%", internal_variables, user_variables, dynamic_variables,
                                   arg_input=arg_input) == dynamic_variables[0].var_value
    assert value.parse_script_word("%Cue%", internal_variables, user_variables, dynamic_variables,
                                   arg_input=arg_input) == dynamic_variables[0].var_value
    assert value.parse_script_word("%random%", internal_variables, user_variables, dynamic_variables,
                                   arg_input=arg_input) == None
    assert value.parse_script_word("%cue", internal_variables, user_variables, dynamic_variables,
                                   arg_input=arg_input) == "%cue"

    # Argument inputs
    assert value.parse_script_word("@0@", internal_variables, user_variables, dynamic_variables,
                                   arg_input=arg_input) == arg_input[0]
    assert value.parse_script_word("@1@", internal_variables, user_variables, dynamic_variables,
                                   arg_input=arg_input) == None
    assert value.parse_script_word("@random@", internal_variables, user_variables, dynamic_variables,
                                   arg_input=arg_input) == None
    assert value.parse_script_word("@0", internal_variables, user_variables, dynamic_variables,
                                   arg_input=arg_input) == "@0"

    # Raw values
    assert value.parse_script_word("", internal_variables, user_variables, dynamic_variables, arg_input=arg_input) == ""
    assert value.parse_script_word("None", internal_variables, user_variables, dynamic_variables, arg_input=arg_input) == "None"
    assert value.parse_script_word("0", internal_variables, user_variables, dynamic_variables, arg_input=arg_input) == 0
    assert value.parse_script_word("-1", internal_variables, user_variables, dynamic_variables, arg_input=arg_input) == -1
    assert value.parse_script_word("1", internal_variables, user_variables, dynamic_variables, arg_input=arg_input) == 1
    assert value.parse_script_word("0.0", internal_variables, user_variables, dynamic_variables, arg_input=arg_input) == 0
    assert value.parse_script_word("-1.0", internal_variables, user_variables, dynamic_variables, arg_input=arg_input) == -1
    assert value.parse_script_word("1.0", internal_variables, user_variables, dynamic_variables, arg_input=arg_input) == 1
    assert value.parse_script_word("0.1", internal_variables, user_variables, dynamic_variables, arg_input=arg_input) == 0.1
    assert value.parse_script_word("-1.1", internal_variables, user_variables, dynamic_variables, arg_input=arg_input) == -1.1
    assert value.parse_script_word("1.1", internal_variables, user_variables, dynamic_variables, arg_input=arg_input) == 1.1
    assert value.parse_script_word("True", internal_variables, user_variables, dynamic_variables, arg_input=arg_input) == True
    assert value.parse_script_word("False", internal_variables, user_variables, dynamic_variables, arg_input=arg_input) == False
    assert value.parse_script_word("Test", internal_variables, user_variables, dynamic_variables, arg_input=arg_input) == "Test"
    assert value.parse_script_word("Two words", internal_variables, user_variables, dynamic_variables, arg_input=arg_input) == "Two words"
    assert value.parse_script_word("underscore_words", internal_variables, user_variables, dynamic_variables, arg_input=arg_input) == "underscore_words"
