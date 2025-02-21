import uuid

import macros
import scripting
import variables
import osc


def test_eval_expression():
    """Test that evaluate expression returns the proper responses."""
    new_uuid = uuid.uuid4()
    internal_variables = [variables.InternalVar("#internal_0#", "ping")]
    user_variables = [variables.InternalVar("*user_0*", "ping")]
    dynamic_variables = [variables.InternalVar("%cue%", "ping")]
    arg_input = ["Arg one"]

    # One word expressions:
    assert scripting.eval_expression(["True"], new_uuid, internal_variables, user_variables,
                                     dynamic_variables,
                                     arg_input=arg_input, debug=False) == True
    assert scripting.eval_expression(["False"], new_uuid, internal_variables, user_variables,
                                     dynamic_variables,
                                     arg_input=arg_input, debug=False) == False
    assert scripting.eval_expression(["#internal_0#"], new_uuid, internal_variables, user_variables,
                                     dynamic_variables,
                                     arg_input=arg_input, debug=False) == "ping"
    assert scripting.eval_expression(["#internal_1#"], new_uuid, internal_variables, user_variables,
                                     dynamic_variables,
                                     arg_input=arg_input, debug=False) == None
    assert scripting.eval_expression(["*user_0*"], new_uuid, internal_variables, user_variables,
                                     dynamic_variables,
                                     arg_input=arg_input, debug=False) == "ping"
    assert scripting.eval_expression(["*user_1*"], new_uuid, internal_variables, user_variables,
                                     dynamic_variables,
                                     arg_input=arg_input, debug=False) == None
    assert scripting.eval_expression(["%cue%"], new_uuid, internal_variables, user_variables,
                                     dynamic_variables,
                                     arg_input=arg_input, debug=False) == "ping"
    assert scripting.eval_expression(["%random%"], new_uuid, internal_variables, user_variables,
                                     dynamic_variables,
                                     arg_input=arg_input, debug=False) == None
    assert scripting.eval_expression(["@0@"], new_uuid, internal_variables, user_variables,
                                     dynamic_variables,
                                     arg_input=arg_input, debug=False) == "Arg one"
    assert scripting.eval_expression(["@1@"], new_uuid, internal_variables, user_variables,
                                     dynamic_variables,
                                     arg_input=arg_input, debug=False) == None

    # Three word expressions
    # Addition

    assert scripting.eval_expression([1.0, "+", 2], new_uuid, internal_variables, user_variables,
                                     dynamic_variables,
                                     arg_input=arg_input, debug=True) == 3
    assert scripting.eval_expression([1, "+", 2], new_uuid, internal_variables, user_variables,
                                     dynamic_variables,
                                     arg_input=arg_input, debug=True) == 3
    assert scripting.eval_expression(["1", "+", 2], new_uuid, internal_variables, user_variables,
                                     dynamic_variables,
                                     arg_input=arg_input, debug=True) == 3
    assert scripting.eval_expression(["1", "+", "2"], new_uuid, internal_variables, user_variables,
                                     dynamic_variables,
                                     arg_input=arg_input, debug=True) == 3
    assert scripting.eval_expression(["One", "+", "Two"], new_uuid, internal_variables,
                                     user_variables, dynamic_variables,
                                     arg_input=arg_input, debug=True) == "OneTwo"

    # Subtraction
    assert scripting.eval_expression([1.0, "-", 0.5], new_uuid, internal_variables, user_variables,
                                     dynamic_variables,
                                     arg_input=arg_input, debug=True) == 0.5
    assert scripting.eval_expression([4, "-", "2"], new_uuid, internal_variables, user_variables,
                                     dynamic_variables,
                                     arg_input=arg_input, debug=True) == 2
    assert scripting.eval_expression(["3", "-", "1"], new_uuid, internal_variables, user_variables,
                                     dynamic_variables,
                                     arg_input=arg_input, debug=True) == 2
    assert scripting.eval_expression(["One", "-", "Two"], new_uuid, internal_variables,
                                     user_variables, dynamic_variables,
                                     arg_input=arg_input, debug=True) == "One"

    # Unknown Operator
    assert scripting.eval_expression(["True", "==" "True"], new_uuid, internal_variables,
                                     user_variables, dynamic_variables,
                                     arg_input=arg_input, debug=False) == None

    # Invalid syntax
    assert scripting.eval_expression(["True", "==", "==" "True"], new_uuid, internal_variables,
                                     user_variables, dynamic_variables,
                                     arg_input=arg_input, debug=False) == None


def test_handle_string_end():
    """Test that handle_string_end puts completed strings in the proper place and resets variables."""
    active_expression_count = 0
    expressions = []

    string_buffer = ["Luck", "be", "a"]
    split_line = []
    assert scripting.handle_string_end("lady\"", string_buffer, active_expression_count,
                                       expressions, split_line) == (
               [], [], ["Luck be a lady"])

    string_buffer = ["Luck", "be", "a"]
    split_line = ["set", "*song*", "="]
    assert scripting.handle_string_end("lady\"", string_buffer, active_expression_count,
                                       expressions, split_line) == (
               [], [], ["set", "*song*", "=", "Luck be a lady"])

    active_expression_count = 1
    expressions = [["Me and ", "+"]]
    string_buffer = []
    split_line = []
    assert scripting.handle_string_end("You\"", string_buffer, active_expression_count, expressions,
                                       split_line) == (
               [], [["Me and ", "+", "You"]], [])

    active_expression_count = 2
    expressions = [["Me and You", "+"], ["Are like berries and ", "+"]]
    string_buffer = []
    split_line = []
    assert scripting.handle_string_end("cream.\"", string_buffer, active_expression_count,
                                       expressions, split_line) == (
               [], [['Me and You', '+'], ['Are like berries and ', '+', 'cream.']], [])


def test_handle_endloop():
    """Test that handle_endloop ends loops properly"""
    loop_active = False
    loop_start_line = None
    loop_count = 0
    loop_limit = 99
    skip_to_endloop = False
    current_line = 10

    assert scripting.handle_endloop(loop_active, loop_start_line, loop_count, loop_limit,
                                    skip_to_endloop, current_line) == (False, None, 9, 0, False, 10)
    loop_active = True
    loop_start_line = 5
    assert scripting.handle_endloop(loop_active, loop_start_line, loop_count, loop_limit,
                                    skip_to_endloop, current_line) == (True, 5, 9, 1, False, 5)
    loop_count = 100
    assert scripting.handle_endloop(loop_active, loop_start_line, loop_count, loop_limit,
                                    skip_to_endloop, current_line) == (
           False, None, None, 0, False, 10)


def test_pre_process_script_line():
    """Test that pre_process_script_line handles all variables, strings and expressions properly"""
    new_uuid = uuid.uuid4()
    internal_variables = [variables.InternalVar("#internal_0#", "ping")]
    user_variables = [variables.InternalVar("*user_0*", "ping")]
    dynamic_variables = [variables.InternalVar("%cue%", "ping")]
    eos_query_count = 0
    arg_input = ["Arg one"]

    # Empty line
    assert scripting.pre_process_script_line("", new_uuid, internal_variables, user_variables,
                                             dynamic_variables, eos_query_count=eos_query_count,
                                             arg_input=arg_input) == ([""], 0)

    # No strings, expressions, or outside variables
    assert scripting.pre_process_script_line("comment test line", new_uuid, internal_variables,
                                             user_variables,
                                             dynamic_variables, eos_query_count=eos_query_count,
                                             arg_input=arg_input) == (
           ["comment", "test", "line"], 0)

    # No strings or expressions, outside variables
    assert scripting.pre_process_script_line("comment test *user_1*", new_uuid, internal_variables,
                                             user_variables,
                                             dynamic_variables, eos_query_count=eos_query_count,
                                             arg_input=arg_input) == (
           ["comment", "test", "*user_1*"], 0)
    # One string, no expressions
    assert scripting.pre_process_script_line("set *user_1* = 'Multiple words'", new_uuid,
                                             internal_variables, user_variables,
                                             dynamic_variables, eos_query_count=eos_query_count,
                                             arg_input=arg_input) == (
           ["set", "*user_1*", "=", "Multiple words"], 0)
    # No strings, one expression
    assert scripting.pre_process_script_line("set *user_1* = (1+1)", new_uuid, internal_variables,
                                             user_variables,
                                             dynamic_variables, eos_query_count=eos_query_count,
                                             arg_input=arg_input) == (
           ["set", "*user_1*", "=", 2], 0)
    # No strings, multiple sequential expressions
    assert scripting.pre_process_script_line("set *user_1* = (1+1) + (2+2)", new_uuid,
                                             internal_variables, user_variables,
                                             dynamic_variables, eos_query_count=eos_query_count,
                                             arg_input=arg_input) == (
           ["set", "*user_1*", "=", 2, "+", 4], 0)
    # No strings, one set of nested expressions
    assert scripting.pre_process_script_line("set *user_1* = ( (2+3) + 1)", new_uuid,
                                             internal_variables, user_variables,
                                             dynamic_variables, eos_query_count=eos_query_count,
                                             arg_input=arg_input) == (
           ["set", "*user_1*", "=", 6], 0)
    # No strings, multiple sequential sets of nested expressions
    assert scripting.pre_process_script_line("set *user_1* = ( (1+1) + (2+2) )", new_uuid,
                                             internal_variables, user_variables,
                                             dynamic_variables, eos_query_count=eos_query_count,
                                             arg_input=arg_input) == (
           ["set", "*user_1*", "=", 6], 0)
    # One string, one expression
    assert scripting.pre_process_script_line("set *user_1* = 'string'+1", new_uuid,
                                             internal_variables, user_variables,
                                             dynamic_variables, eos_query_count=eos_query_count,
                                             arg_input=arg_input) == (
           ["set", "*user_1*", "=", "string", "+", "1"], 0)
    # One string, multiple sequential expressions
    assert scripting.pre_process_script_line("set *user_1* = 'string' + (1+2) + 'another string'",
                                             new_uuid, internal_variables, user_variables,
                                             dynamic_variables, eos_query_count=eos_query_count,
                                             arg_input=arg_input) == (
           ["set", "*user_1*", "=", "string", "+", 3, "+", "another string"], 0)
    # One string, one set of nested expressions
    assert scripting.pre_process_script_line("set *user_1* = 'string' + (1 + (2 + 1) )", new_uuid,
                                             internal_variables, user_variables,
                                             dynamic_variables, eos_query_count=eos_query_count,
                                             arg_input=arg_input) == (
           ["set", "*user_1*", "=", "string", "+", 4], 0)
    # One string, multiple sequential sets of nested expressions
    assert scripting.pre_process_script_line("set *user_1* = 'string' + ( (1+1) + (2+2) )",
                                             new_uuid, internal_variables, user_variables,
                                             dynamic_variables, eos_query_count=eos_query_count,
                                             arg_input=arg_input) == (
           ["set", "*user_1*", "=", "string", "+", 6], 0)
    # Multiple strings, one expression
    assert scripting.pre_process_script_line("set *user_1* = ('multiple '+'words')", new_uuid,
                                             internal_variables, user_variables,
                                             dynamic_variables, eos_query_count=eos_query_count,
                                             arg_input=arg_input) == (
           ["set", "*user_1*", "=", "multiple words"], 0)
    # Multiple strings, multiple sequential expressions
    assert scripting.pre_process_script_line(
        "set *user_1* = ('multiple '+'words') + ('and '+'more')", new_uuid, internal_variables,
        user_variables,
        dynamic_variables, eos_query_count=eos_query_count,
        arg_input=arg_input) == (["set", "*user_1*", "=", "multiple words", "+", "and more"], 0)
    # Multiple strings, one set of nested expressions
    assert scripting.pre_process_script_line(
        "set *user_1* = ('multiple '+'words') + ('count ' + (2+1) )", new_uuid, internal_variables,
        user_variables,
        dynamic_variables, eos_query_count=eos_query_count,
        arg_input=arg_input) == (["set", "*user_1*", "=", "multiple words", "+", "count 3"], 0)
    # Multiple strings, multiple sequential sets of nested expressions
    assert scripting.pre_process_script_line(
        "set *user_1* = ('multiple' + ('wo'+'rds') ) + ('count ' + (2+1) )", new_uuid,
        internal_variables, user_variables,
        dynamic_variables, eos_query_count=eos_query_count,
        arg_input=arg_input) == (["set", "*user_1*", "=", "multiplewords", "+", "count 3"], 0)


def test_run_script():
    test_script = [""]
    osc_client = osc.start_osc_client(["127.0.0.1", 8000])
    new_uuid = uuid.uuid4()
    internal_macros = [macros.Macro("", "osc", "/eos/out/ping", [], ["pass"], new_uuid)]
    internal_variables = [variables.InternalVar("#internal_0#", "ping")]
    user_variables = [variables.InternalVar("*user_0*", "ping")]
    dynamic_variables = [variables.InternalVar("%cue%", "ping")]
    eos_query_count = 0
    arg_input = ["Arg one"]

    assert scripting.run_script(test_script, osc_client, new_uuid, internal_macros,
                                internal_variables, user_variables, dynamic_variables,
                                eos_query_count=eos_query_count, arg_input=arg_input) == (
           "done", "", internal_macros)

    # TODO: Write real tests. This will require breaking out opcodes into functions.
