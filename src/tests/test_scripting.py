import scripting
import variables

def test_check_condition():
    """Test that check_condition returns proper condition evaluations for raw values."""
    internal_variables = [variables.InternalVar("#internal_0#", "ping")]
    user_variables = [variables.InternalVar("*user_0*", "ping")]
    dynamic_variables = [variables.InternalVar("%cue%", "ping")]

    # With raw values
    # == Operator
    assert scripting.check_condition([True, "==", True], internal_variables, user_variables, dynamic_variables,
                                     arg_input=None) == True
    assert scripting.check_condition([True, "==", False], internal_variables, user_variables, dynamic_variables,
                                     arg_input=None) == False
    assert scripting.check_condition([1, "==", 1], internal_variables, user_variables, dynamic_variables,
                                     arg_input=None) == True
    assert scripting.check_condition([1, "==", 2], internal_variables, user_variables, dynamic_variables,
                                     arg_input=None) == False
    assert scripting.check_condition(["1", "==", 1], internal_variables, user_variables, dynamic_variables,
                                     arg_input=None) == True
    assert scripting.check_condition(["1", "==", 2], internal_variables, user_variables, dynamic_variables,
                                     arg_input=None) == False
    assert scripting.check_condition(["1", "==", "1"], internal_variables, user_variables, dynamic_variables,
                                     arg_input=None) == True
    assert scripting.check_condition(["1", "==", "2"], internal_variables, user_variables, dynamic_variables,
                                     arg_input=None) == False

    # === Operator
    assert scripting.check_condition([True, "===", True], internal_variables, user_variables, dynamic_variables,
                                     arg_input=None) == True
    assert scripting.check_condition([True, "===", "True"], internal_variables, user_variables, dynamic_variables,
                                     arg_input=None) == True
    assert scripting.check_condition([True, "===", "False"], internal_variables, user_variables, dynamic_variables,
                                     arg_input=None) == False
    assert scripting.check_condition([1, "===", 1], internal_variables, user_variables, dynamic_variables,
                                     arg_input=None) == True
    assert scripting.check_condition([1, "===", "2"], internal_variables, user_variables, dynamic_variables,
                                     arg_input=None) == False
    assert scripting.check_condition(["True", "===", "True"], internal_variables, user_variables, dynamic_variables,
                                     arg_input=None) == True
    assert scripting.check_condition(["True", "===", "False"], internal_variables, user_variables, dynamic_variables,
                                     arg_input=None) == False
    # > Operator
    assert scripting.check_condition([True, ">", True], internal_variables, user_variables, dynamic_variables,
                                     arg_input=None) == False
    assert scripting.check_condition([True, ">", False], internal_variables, user_variables, dynamic_variables,
                                     arg_input=None) == True
    assert scripting.check_condition([2, ">", 1], internal_variables, user_variables, dynamic_variables,
                                     arg_input=None) == True
    assert scripting.check_condition([1, ">", 1], internal_variables, user_variables, dynamic_variables,
                                     arg_input=None) == False
    assert scripting.check_condition([1, ">", 2], internal_variables, user_variables, dynamic_variables,
                                     arg_input=None) == False
    assert scripting.check_condition(["1", ">", 1], internal_variables, user_variables, dynamic_variables,
                                     arg_input=None) == False
    assert scripting.check_condition(["1", ">", 2], internal_variables, user_variables, dynamic_variables,
                                     arg_input=None) == False
    assert scripting.check_condition(["1", ">", "1"], internal_variables, user_variables, dynamic_variables,
                                     arg_input=None) == False
    assert scripting.check_condition(["2", ">", "1"], internal_variables, user_variables, dynamic_variables,
                                     arg_input=None) == True
    assert scripting.check_condition(["1", ">", "2"], internal_variables, user_variables, dynamic_variables,
                                     arg_input=None) == False

    # >= Operator
    assert scripting.check_condition([True, ">=", True], internal_variables, user_variables, dynamic_variables,
                                     arg_input=None) == True
    assert scripting.check_condition([True, ">=", False], internal_variables, user_variables, dynamic_variables,
                                     arg_input=None) == True
    assert scripting.check_condition([2, ">=", 1], internal_variables, user_variables, dynamic_variables,
                                     arg_input=None) == True
    assert scripting.check_condition([1, ">=", 1], internal_variables, user_variables, dynamic_variables,
                                     arg_input=None) == True
    assert scripting.check_condition([1, ">=", 2], internal_variables, user_variables, dynamic_variables,
                                     arg_input=None) == False
    assert scripting.check_condition(["1", ">=", 1], internal_variables, user_variables, dynamic_variables,
                                     arg_input=None) == True
    assert scripting.check_condition(["1", ">=", 2], internal_variables, user_variables, dynamic_variables,
                                     arg_input=None) == False
    assert scripting.check_condition(["1", ">=", "1"], internal_variables, user_variables, dynamic_variables,
                                     arg_input=None) == True
    assert scripting.check_condition(["2", ">=", "1"], internal_variables, user_variables, dynamic_variables,
                                     arg_input=None) == True
    assert scripting.check_condition(["1", ">=", "2"], internal_variables, user_variables, dynamic_variables,
                                     arg_input=None) == False

    # > Operator
    assert scripting.check_condition([False, "<", True], internal_variables, user_variables, dynamic_variables,
                                     arg_input=None) == True
    assert scripting.check_condition([True, "<", False], internal_variables, user_variables, dynamic_variables,
                                     arg_input=None) == False
    assert scripting.check_condition([True, "<", True], internal_variables, user_variables, dynamic_variables,
                                     arg_input=None) == False
    assert scripting.check_condition([1, "<", 2], internal_variables, user_variables, dynamic_variables,
                                     arg_input=None) == True
    assert scripting.check_condition([1, "<", 1], internal_variables, user_variables, dynamic_variables,
                                     arg_input=None) == False
    assert scripting.check_condition([2, "<", 1], internal_variables, user_variables, dynamic_variables,
                                     arg_input=None) == False
    assert scripting.check_condition(["1", "<", 1], internal_variables, user_variables, dynamic_variables,
                                     arg_input=None) == False
    assert scripting.check_condition(["1", "<", 2], internal_variables, user_variables, dynamic_variables,
                                     arg_input=None) == True
    assert scripting.check_condition(["1", "<", "1"], internal_variables, user_variables, dynamic_variables,
                                     arg_input=None) == False
    assert scripting.check_condition(["1", "<", "2"], internal_variables, user_variables, dynamic_variables,
                                     arg_input=None) == True
    assert scripting.check_condition(["2", "<", "1"], internal_variables, user_variables, dynamic_variables,
                                     arg_input=None) == False

    # <= Operator
    assert scripting.check_condition([True, "<=", True], internal_variables, user_variables, dynamic_variables,
                                     arg_input=None) == True
    assert scripting.check_condition([True, "<=", False], internal_variables, user_variables, dynamic_variables,
                                     arg_input=None) == False
    assert scripting.check_condition([False, "<=", True], internal_variables, user_variables, dynamic_variables,
                                     arg_input=None) == True
    assert scripting.check_condition([2, "<=", 1], internal_variables, user_variables, dynamic_variables,
                                     arg_input=None) == False
    assert scripting.check_condition([1, "<=", 1], internal_variables, user_variables, dynamic_variables,
                                     arg_input=None) == True
    assert scripting.check_condition([1, "<=", 2], internal_variables, user_variables, dynamic_variables,
                                     arg_input=None) == True
    assert scripting.check_condition(["1", "<=", 1], internal_variables, user_variables, dynamic_variables,
                                     arg_input=None) == True
    assert scripting.check_condition(["1", "<=", 2], internal_variables, user_variables, dynamic_variables,
                                     arg_input=None) == True
    assert scripting.check_condition(["1", "<=", "1"], internal_variables, user_variables, dynamic_variables,
                                     arg_input=None) == True
    assert scripting.check_condition(["2", "<=", "1"], internal_variables, user_variables, dynamic_variables,
                                     arg_input=None) == False
    assert scripting.check_condition(["1", "<=", "2"], internal_variables, user_variables, dynamic_variables,
                                     arg_input=None) == True

    # != Operator
    assert scripting.check_condition([True, "!=", True], internal_variables, user_variables, dynamic_variables,
                                     arg_input=None) == False
    assert scripting.check_condition([True, "!=", False], internal_variables, user_variables, dynamic_variables,
                                     arg_input=None) == True
    assert scripting.check_condition([2, "!=", 1], internal_variables, user_variables, dynamic_variables,
                                     arg_input=None) == True
    assert scripting.check_condition([1, "!=", 1], internal_variables, user_variables, dynamic_variables,
                                     arg_input=None) == False
    assert scripting.check_condition([1, "!=", 2], internal_variables, user_variables, dynamic_variables,
                                     arg_input=None) == True
    assert scripting.check_condition(["1", "!=", 1], internal_variables, user_variables, dynamic_variables,
                                     arg_input=None) == False
    assert scripting.check_condition(["1", "!=", 2], internal_variables, user_variables, dynamic_variables,
                                     arg_input=None) == True
    assert scripting.check_condition(["1", "!=", "1"], internal_variables, user_variables, dynamic_variables,
                                     arg_input=None) == False
    assert scripting.check_condition(["2", "!=", "1"], internal_variables, user_variables, dynamic_variables,
                                     arg_input=None) == True
    assert scripting.check_condition(["1", "!=", "2"], internal_variables, user_variables, dynamic_variables,
                                     arg_input=None) == True

    # Unknown Operator
    assert scripting.check_condition(["1", "$", "2"], internal_variables, user_variables, dynamic_variables,
                                     arg_input=None) == False

    # Not Operator
    assert scripting.check_condition(["not", True, "==", True], internal_variables, user_variables, dynamic_variables,
                                     arg_input=None) == False
    assert scripting.check_condition(["not", True, "==", False], internal_variables, user_variables, dynamic_variables,
                                     arg_input=None) == True
    assert scripting.check_condition(["not", 1, "==", 1], internal_variables, user_variables, dynamic_variables,
                                     arg_input=None) == False
    assert scripting.check_condition(["not", 1, "==", 2], internal_variables, user_variables, dynamic_variables,
                                     arg_input=None) == True
    assert scripting.check_condition(["not", "1", "==", 1], internal_variables, user_variables, dynamic_variables,
                                     arg_input=None) == False
    assert scripting.check_condition(["not", "1", "==", 2], internal_variables, user_variables, dynamic_variables,
                                     arg_input=None) == True
    assert scripting.check_condition(["not", "1", "==", "1"], internal_variables, user_variables, dynamic_variables,
                                     arg_input=None) == False
    assert scripting.check_condition(["not", "1", "==", "2"], internal_variables, user_variables, dynamic_variables,
                                     arg_input=None) == True

    # Improper Syntax
    assert scripting.check_condition(["1", "=", ">", "2"], internal_variables, user_variables, dynamic_variables,
                                     arg_input=None) == False


def test_eval_expression():
    """Test that evaluate expression returns the proper responses."""
    internal_variables = [variables.InternalVar("#internal_0#", "ping")]
    user_variables = [variables.InternalVar("*user_0*", "ping")]
    dynamic_variables = [variables.InternalVar("%cue%", "ping")]
    arg_input = ["Arg one"]

    # One word expressions:
    assert scripting.eval_expression(["True"], internal_variables, user_variables, dynamic_variables,
                                     arg_input=arg_input, debug=False) == True
    assert scripting.eval_expression(["False"], internal_variables, user_variables, dynamic_variables,
                                     arg_input=arg_input, debug=False) == False
    assert scripting.eval_expression(["#internal_0#"], internal_variables, user_variables, dynamic_variables,
                                     arg_input=arg_input, debug=False) == "ping"
    assert scripting.eval_expression(["#internal_1#"], internal_variables, user_variables, dynamic_variables,
                                     arg_input=arg_input, debug=False) == None
    assert scripting.eval_expression(["*user_0*"], internal_variables, user_variables, dynamic_variables,
                                     arg_input=arg_input, debug=False) == "ping"
    assert scripting.eval_expression(["*user_1*"], internal_variables, user_variables, dynamic_variables,
                                     arg_input=arg_input, debug=False) == None
    assert scripting.eval_expression(["%cue%"], internal_variables, user_variables, dynamic_variables,
                                     arg_input=arg_input, debug=False) == "ping"
    assert scripting.eval_expression(["%random%"], internal_variables, user_variables, dynamic_variables,
                                     arg_input=arg_input, debug=False) == None
    assert scripting.eval_expression(["@0@"], internal_variables, user_variables, dynamic_variables,
                                     arg_input=arg_input, debug=False) == "Arg one"
    assert scripting.eval_expression(["@1@"], internal_variables, user_variables, dynamic_variables,
                                     arg_input=arg_input, debug=False) == None

    # Three word expressions
    # Addition

    assert scripting.eval_expression([1.0, "+", 2], internal_variables, user_variables, dynamic_variables,
                                             arg_input=arg_input, debug=True) == 3
    assert scripting.eval_expression([1, "+", 2], internal_variables, user_variables, dynamic_variables,
                                         arg_input=arg_input, debug=True) == 3
    assert scripting.eval_expression(["1", "+", 2], internal_variables, user_variables, dynamic_variables,
                                     arg_input=arg_input, debug=True) == 3
    assert scripting.eval_expression(["1", "+", "2"], internal_variables, user_variables, dynamic_variables,
                                     arg_input=arg_input, debug=True) == 3
    assert scripting.eval_expression(["One", "+", "Two"], internal_variables, user_variables, dynamic_variables,
                                     arg_input=arg_input, debug=True) == "OneTwo"

    # Subtraction
    assert scripting.eval_expression([1.0, "-", 0.5], internal_variables, user_variables, dynamic_variables,
                                     arg_input=arg_input, debug=True) == 0.5
    assert scripting.eval_expression([4, "-", "2"], internal_variables, user_variables, dynamic_variables,
                                     arg_input=arg_input, debug=True) == 2
    assert scripting.eval_expression(["3", "-", "1"], internal_variables, user_variables, dynamic_variables,
                                     arg_input=arg_input, debug=True) == 2
    assert scripting.eval_expression(["One", "-", "Two"], internal_variables, user_variables, dynamic_variables,
                                     arg_input=arg_input, debug=True) == "One"

    # Unknown Operator
    assert scripting.eval_expression(["True", "==" "True"], internal_variables, user_variables, dynamic_variables,
                                     arg_input=arg_input, debug=False) == None

    # Invalid syntax
    assert scripting.eval_expression(["True", "==", "==" "True"], internal_variables, user_variables, dynamic_variables,
                                     arg_input=arg_input, debug=False) == None

def test_handle_string_end():
    """Test that handle_string_end puts completed strings in the proper place and resets variables."""
    active_expression_count = 0
    expressions = []

    string_buffer = ["Luck", "be", "a"]
    split_line = []
    assert scripting.handle_string_end("lady\"", string_buffer, active_expression_count, expressions, split_line) == (
    [], [], ["Luck be a lady"])

    string_buffer = ["Luck", "be", "a"]
    split_line = ["set", "*song*", "="]
    assert scripting.handle_string_end("lady\"", string_buffer, active_expression_count, expressions, split_line) == (
        [], [], ["set", "*song*", "=", "Luck be a lady"])

    active_expression_count = 1
    expressions = [["Me and ", "+"]]
    string_buffer = []
    split_line = []
    assert scripting.handle_string_end("You\"", string_buffer, active_expression_count, expressions, split_line) == (
        [], [["Me and ", "+", "You"]], [])

    active_expression_count = 2
    expressions = [["Me and You", "+"], ["Are like berries and ", "+"]]
    string_buffer = []
    split_line = []
    assert scripting.handle_string_end("cream.\"", string_buffer, active_expression_count, expressions, split_line) == (
        [], [['Me and You', '+'], ['Are like berries and ', '+', 'cream.']], [])


def test_handle_endloop():
    assert False


def test_pre_process_script_line():
    assert False


def test_run_script():
    assert False
