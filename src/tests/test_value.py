import value
import variables
import uuid

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

    new_uuid = uuid.uuid4()

    internal_variables = [variables.InternalVar(f"#internal_0_{new_uuid}#", "True"),
                          variables.InternalVar(f"#internal_1_{new_uuid}#", "False")]
    user_variables = [variables.InternalVar("*user_0*", "True")]
    dynamic_variables = [variables.InternalVar("%cue%", "103")]
    test_variables = {"internal_variables": internal_variables, "user_variables": user_variables,
                      "dynamic_variables": dynamic_variables, "eos_query_count": 0}
    arg_input = ["Arg 0"]

    # Internal variables
    assert value.parse_script_word(f"#internal_0_{new_uuid}#", new_uuid, test_variables,
                                   arg_input=arg_input) == internal_variables[0].var_value
    assert value.parse_script_word(f"#internal_0_{new_uuid}#", new_uuid, test_variables,
                                   arg_input=arg_input) == internal_variables[0].var_value
    assert value.parse_script_word("#internal_1#", new_uuid, test_variables,
                                   arg_input=arg_input) == None
    assert value.parse_script_word(f"#internal_0_{new_uuid}", new_uuid, test_variables,
                                   arg_input=arg_input) == f"#internal_0_{new_uuid}"

    # User variables
    assert value.parse_script_word("*user_0*", new_uuid, test_variables,
                                   arg_input=arg_input) == user_variables[0].var_value
    assert value.parse_script_word("*User_0*", new_uuid, test_variables,
                                   arg_input=arg_input) == user_variables[0].var_value
    assert value.parse_script_word("*user_1*", new_uuid, test_variables,
                                   arg_input=arg_input) == None
    assert value.parse_script_word("*user_0", new_uuid, test_variables,
                                   arg_input=arg_input) == "*user_0"
    # Dynamic variables
    assert value.parse_script_word("%cue%", new_uuid, test_variables,
                                   arg_input=arg_input) == dynamic_variables[0].var_value
    assert value.parse_script_word("%Cue%", new_uuid, test_variables,
                                   arg_input=arg_input) == dynamic_variables[0].var_value
    assert value.parse_script_word("%random%", new_uuid, test_variables,
                                   arg_input=arg_input) == None
    assert value.parse_script_word("%cue", new_uuid, test_variables,
                                   arg_input=arg_input) == "%cue"

    # Argument inputs
    assert value.parse_script_word("@0@", new_uuid, test_variables,
                                   arg_input=arg_input) == arg_input[0]
    assert value.parse_script_word("@1@", new_uuid, test_variables,
                                   arg_input=arg_input) == None
    assert value.parse_script_word("@random@", new_uuid, test_variables,
                                   arg_input=arg_input) == None
    assert value.parse_script_word("@0", new_uuid, test_variables,
                                   arg_input=arg_input) == "@0"

    # Raw values
    assert value.parse_script_word("", new_uuid, test_variables, arg_input=arg_input) == ""
    assert value.parse_script_word("None", new_uuid, test_variables, arg_input=arg_input) == "None"
    assert value.parse_script_word("0", new_uuid, test_variables, arg_input=arg_input) == 0
    assert value.parse_script_word("-1", new_uuid, test_variables, arg_input=arg_input) == -1
    assert value.parse_script_word("1", new_uuid, test_variables, arg_input=arg_input) == 1
    assert value.parse_script_word("0.0", new_uuid, test_variables, arg_input=arg_input) == 0
    assert value.parse_script_word("-1.0", new_uuid, test_variables, arg_input=arg_input) == -1
    assert value.parse_script_word("1.0", new_uuid, test_variables, arg_input=arg_input) == 1
    assert value.parse_script_word("0.1", new_uuid, test_variables, arg_input=arg_input) == 0.1
    assert value.parse_script_word("-1.1", new_uuid, test_variables, arg_input=arg_input) == -1.1
    assert value.parse_script_word("1.1", new_uuid, test_variables, arg_input=arg_input) == 1.1
    assert value.parse_script_word("True", new_uuid, test_variables, arg_input=arg_input) == True
    assert value.parse_script_word("False", new_uuid, test_variables, arg_input=arg_input) == False
    assert value.parse_script_word("Test", new_uuid, test_variables, arg_input=arg_input) == "Test"
    assert value.parse_script_word("Two words", new_uuid, test_variables, arg_input=arg_input) == "Two words"
    assert value.parse_script_word("underscore_words", new_uuid, test_variables, arg_input=arg_input) == "underscore_words"

    # Eos Queries and eos_query_count incrementing
    assert (value.parse_script_word("eos(test)", new_uuid, test_variables, arg_input=arg_input) == ("True", 1))
    test_variables["eos_query_count"] = 1
    assert (value.parse_script_word("eos(test_1)", new_uuid, test_variables, arg_input=arg_input) == ("False", 2))
    test_variables["eos_query_count"] = 2
    assert (value.parse_script_word("eos(test_2)", new_uuid, test_variables, arg_input=arg_input) == (None, 3))


def test_regex_osc_trigger():
    """Tests that regex_osc_trigger formats wildcards and arguments properly"""
    # Address wildcards
    assert value.regex_osc_trigger("/eos/*") == ("\/eos\/.*", [])
    assert value.regex_osc_trigger("/eos/*/ping") == ("\/eos\/[^/]*\/ping", [])
    assert value.regex_osc_trigger("/eos/*/ping/*") == ("\/eos\/[^/]*\/ping\/.*", [])
    assert value.regex_osc_trigger("/eos/ping") == ("\/eos\/ping", [])

    # Argument matching
    assert value.regex_osc_trigger("/eos/active/wheel/*=[^/Pan [*]") == ("\\/eos\\/active\\/wheel\\/.*", ["^\/Pan [.*"])
    assert value.regex_osc_trigger("/eos/active/wheel/*=[^/Pan [*, ^/Ma*tch *]") == ("\\/eos\\/active\\/wheel\\/.*", ["^\\/Pan [.*", "^\\/Ma.*tch .*"])