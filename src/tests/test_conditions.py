import uuid
import variables
import conditions
def test_check_soft_equality():
    new_uuid = uuid.uuid4()
    internal_variables = [variables.InternalVar("#internal_0#", "ping")]
    user_variables = [variables.InternalVar("*user_0*", "ping")]
    dynamic_variables = [variables.InternalVar("%cue%", "ping")]
    collected_variables = {
        "internal_variables": internal_variables,
        "user_variables": user_variables,
        "dynamic_variables": dynamic_variables
    }

    # == Operator
    assert conditions.check_soft_equality([True, True], new_uuid, collected_variables,
                                     arg_input=None) == (True, 0)
    assert conditions.check_soft_equality([True, False], new_uuid, collected_variables,
                                     arg_input=None) == (False, 0)
    assert conditions.check_soft_equality([1, 1], new_uuid, collected_variables,
                                     arg_input=None) == (True, 0)
    assert conditions.check_soft_equality([1, 2], new_uuid, collected_variables,
                                     arg_input=None) == (False, 0)
    assert conditions.check_soft_equality(["1", 1], new_uuid, collected_variables,
                                     arg_input=None) == (True, 0)
    assert conditions.check_soft_equality(["1", 2], new_uuid, collected_variables,
                                     arg_input=None) == (False, 0)
    assert conditions.check_soft_equality(["1", "1"], new_uuid, collected_variables,
                                     arg_input=None) == (True, 0)
    assert conditions.check_soft_equality(["1", "2"], new_uuid, collected_variables,
                                     arg_input=None) == (False, 0)


def test_check_hard_equality():
    new_uuid = uuid.uuid4()
    internal_variables = [variables.InternalVar("#internal_0#", "ping")]
    user_variables = [variables.InternalVar("*user_0*", "ping")]
    dynamic_variables = [variables.InternalVar("%cue%", "ping")]
    collected_variables = {
        "internal_variables": internal_variables,
        "user_variables": user_variables,
        "dynamic_variables": dynamic_variables
    }

    assert conditions.check_hard_equality([True, True], new_uuid, collected_variables,
                                     arg_input=None) == (True, 0)
    assert conditions.check_hard_equality([True, "True"], new_uuid, collected_variables,
                                     arg_input=None) == (True, 0)
    assert conditions.check_hard_equality([True, "False"], new_uuid, collected_variables,
                                     arg_input=None) == (False, 0)
    assert conditions.check_hard_equality([1, 1], new_uuid, collected_variables,
                                     arg_input=None) == (True, 0)
    assert conditions.check_hard_equality([1, "2"], new_uuid, collected_variables,
                                     arg_input=None) == (False, 0)
    assert conditions.check_hard_equality(["True", "True"], new_uuid, collected_variables,
                                     arg_input=None) == (True, 0)
    assert conditions.check_hard_equality(["True", "False"], new_uuid, collected_variables,
                                     arg_input=None) == (False, 0)


def test_check_greater_than():
    new_uuid = uuid.uuid4()
    internal_variables = [variables.InternalVar("#internal_0#", "ping")]
    user_variables = [variables.InternalVar("*user_0*", "ping")]
    dynamic_variables = [variables.InternalVar("%cue%", "ping")]
    collected_variables = {
        "internal_variables": internal_variables,
        "user_variables": user_variables,
        "dynamic_variables": dynamic_variables
    }

    assert conditions.check_greater_than([True, True], new_uuid, collected_variables,
                                     arg_input=None) == (False, 0)
    assert conditions.check_greater_than([True, False], new_uuid, collected_variables,
                                     arg_input=None) == (True, 0)
    assert conditions.check_greater_than([2, 1], new_uuid, collected_variables,
                                     arg_input=None) == (True, 0)
    assert conditions.check_greater_than([1, 1], new_uuid, collected_variables,
                                     arg_input=None) == (False, 0)
    assert conditions.check_greater_than([1, 2], new_uuid, collected_variables,
                                     arg_input=None) == (False, 0)
    assert conditions.check_greater_than(["1", 1], new_uuid, collected_variables,
                                     arg_input=None) == (False, 0)
    assert conditions.check_greater_than(["1", 2], new_uuid, collected_variables,
                                     arg_input=None) == (False, 0)
    assert conditions.check_greater_than(["1", "1"], new_uuid, collected_variables,
                                     arg_input=None) == (False, 0)
    assert conditions.check_greater_than(["2", "1"], new_uuid, collected_variables,
                                     arg_input=None) == (True, 0)
    assert conditions.check_greater_than(["1", "2"], new_uuid, collected_variables,
                                     arg_input=None) == (False, 0)


def test_check_grater_than_equal():
    new_uuid = uuid.uuid4()
    internal_variables = [variables.InternalVar("#internal_0#", "ping")]
    user_variables = [variables.InternalVar("*user_0*", "ping")]
    dynamic_variables = [variables.InternalVar("%cue%", "ping")]
    collected_variables = {
        "internal_variables": internal_variables,
        "user_variables": user_variables,
        "dynamic_variables": dynamic_variables
    }

    assert conditions.check_greater_than_equal([True, True], new_uuid, collected_variables,
                                     arg_input=None) == (True, 0)
    assert conditions.check_greater_than_equal([True, False], new_uuid, collected_variables,
                                     arg_input=None) == (True, 0)
    assert conditions.check_greater_than_equal([2, 1], new_uuid, collected_variables,
                                     arg_input=None) == (True, 0)
    assert conditions.check_greater_than_equal([1, 1], new_uuid, collected_variables,
                                     arg_input=None) == (True, 0)
    assert conditions.check_greater_than_equal([1, 2], new_uuid, collected_variables,
                                     arg_input=None) == (False, 0)
    assert conditions.check_greater_than_equal(["1", 1], new_uuid, collected_variables,
                                     arg_input=None) == (True, 0)
    assert conditions.check_greater_than_equal(["1", 2], new_uuid, collected_variables,
                                     arg_input=None) == (False, 0)
    assert conditions.check_greater_than_equal(["1", "1"], new_uuid, collected_variables,
                                     arg_input=None) == (True, 0)
    assert conditions.check_greater_than_equal(["2", "1"], new_uuid, collected_variables,
                                     arg_input=None) == (True, 0)
    assert conditions.check_greater_than_equal(["1", "2"], new_uuid, collected_variables,
                                     arg_input=None) == (False, 0)


def test_check_less_than():
    new_uuid = uuid.uuid4()
    internal_variables = [variables.InternalVar("#internal_0#", "ping")]
    user_variables = [variables.InternalVar("*user_0*", "ping")]
    dynamic_variables = [variables.InternalVar("%cue%", "ping")]
    collected_variables = {
        "internal_variables": internal_variables,
        "user_variables": user_variables,
        "dynamic_variables": dynamic_variables
    }

    assert conditions.check_less_than([False, True], new_uuid, collected_variables,
                                     arg_input=None) == (True, 0)
    assert conditions.check_less_than([True, False], new_uuid, collected_variables,
                                     arg_input=None) == (False, 0)
    assert conditions.check_less_than([True, True], new_uuid, collected_variables,
                                     arg_input=None) == (False, 0)
    assert conditions.check_less_than([1, 2], new_uuid, collected_variables,
                                     arg_input=None) == (True, 0)
    assert conditions.check_less_than([1, 1], new_uuid, collected_variables,
                                     arg_input=None) == (False, 0)
    assert conditions.check_less_than([2, 1], new_uuid, collected_variables,
                                     arg_input=None) == (False, 0)
    assert conditions.check_less_than(["1", 1], new_uuid, collected_variables,
                                     arg_input=None) == (False, 0)
    assert conditions.check_less_than(["1", 2], new_uuid, collected_variables,
                                     arg_input=None) == (True, 0)
    assert conditions.check_less_than(["1", "1"], new_uuid, collected_variables,
                                     arg_input=None) == (False, 0)
    assert conditions.check_less_than(["1", "2"], new_uuid, collected_variables,
                                     arg_input=None) == (True, 0)
    assert conditions.check_less_than(["2", "1"], new_uuid, collected_variables,
                                     arg_input=None) == (False, 0)


def test_check_less_than_equal():
    new_uuid = uuid.uuid4()
    internal_variables = [variables.InternalVar("#internal_0#", "ping")]
    user_variables = [variables.InternalVar("*user_0*", "ping")]
    dynamic_variables = [variables.InternalVar("%cue%", "ping")]
    collected_variables = {
        "internal_variables": internal_variables,
        "user_variables": user_variables,
        "dynamic_variables": dynamic_variables
    }

    # <= Operator
    assert conditions.check_less_than_equal([True, True], new_uuid, collected_variables,
                                     arg_input=None) == (True, 0)
    assert conditions.check_less_than_equal([True, False], new_uuid, collected_variables,
                                     arg_input=None) == (False, 0)
    assert conditions.check_less_than_equal([False, True], new_uuid, collected_variables,
                                     arg_input=None) == (True, 0)
    assert conditions.check_less_than_equal([2, 1], new_uuid, collected_variables,
                                     arg_input=None) == (False, 0)
    assert conditions.check_less_than_equal([1, 1], new_uuid, collected_variables,
                                     arg_input=None) == (True, 0)
    assert conditions.check_less_than_equal([1, 2], new_uuid, collected_variables,
                                     arg_input=None) == (True, 0)
    assert conditions.check_less_than_equal(["1", 1], new_uuid, collected_variables,
                                     arg_input=None) == (True, 0)
    assert conditions.check_less_than_equal(["1", 2], new_uuid, collected_variables,
                                     arg_input=None) == (True, 0)
    assert conditions.check_less_than_equal(["1", "1"], new_uuid, collected_variables,
                                     arg_input=None) == (True, 0)
    assert conditions.check_less_than_equal(["2", "1"], new_uuid, collected_variables,
                                     arg_input=None) == (False, 0)
    assert conditions.check_less_than_equal(["1", "2"], new_uuid, collected_variables,
                                     arg_input=None) == (True, 0)


def test_inequality():
    new_uuid = uuid.uuid4()
    internal_variables = [variables.InternalVar("#internal_0#", "ping")]
    user_variables = [variables.InternalVar("*user_0*", "ping")]
    dynamic_variables = [variables.InternalVar("%cue%", "ping")]
    collected_variables = {
        "internal_variables": internal_variables,
        "user_variables": user_variables,
        "dynamic_variables": dynamic_variables
    }

    assert conditions.check_inequality([True, True], new_uuid, collected_variables,
                                     arg_input=None) == (False, 0)
    assert conditions.check_inequality([True, False], new_uuid, collected_variables,
                                     arg_input=None) == (True, 0)
    assert conditions.check_inequality([2, 1], new_uuid, collected_variables,
                                     arg_input=None) == (True, 0)
    assert conditions.check_inequality([1, 1], new_uuid, collected_variables,
                                     arg_input=None) == (False, 0)
    assert conditions.check_inequality([1, 2], new_uuid, collected_variables,
                                     arg_input=None) == (True, 0)
    assert conditions.check_inequality(["1", 1], new_uuid, collected_variables,
                                     arg_input=None) == (False, 0)
    assert conditions.check_inequality(["1", 2], new_uuid, collected_variables,
                                     arg_input=None) == (True, 0)
    assert conditions.check_inequality(["1", "1"], new_uuid, collected_variables,
                                     arg_input=None) == (False, 0)
    assert conditions.check_inequality(["2", "1"], new_uuid, collected_variables,
                                     arg_input=None) == (True, 0)
    assert conditions.check_inequality(["1", "2"], new_uuid, collected_variables,
                                     arg_input=None) == (True, 0)


def test_check_condition():
    """Test that check_condition returns proper condition evaluations for raw values."""
    new_uuid = uuid.uuid4()
    internal_variables = [variables.InternalVar("#internal_0#", "ping")]
    user_variables = [variables.InternalVar("*user_0*", "ping")]
    dynamic_variables = [variables.InternalVar("%cue%", "ping")]
    collected_variables = {
        "internal_variables": internal_variables,
        "user_variables": user_variables,
        "dynamic_variables": dynamic_variables
    }

    # == Operator
    assert conditions.check_condition([True, "==", True], new_uuid, collected_variables,
                                     arg_input=None) == True
    assert conditions.check_condition([True, "==", False], new_uuid, collected_variables,
                                     arg_input=None) == False
    assert conditions.check_condition([1, "==", 1], new_uuid, collected_variables,
                                     arg_input=None) == True
    assert conditions.check_condition([1, "==", 2], new_uuid, collected_variables,
                                     arg_input=None) == False
    assert conditions.check_condition(["1", "==", 1], new_uuid, collected_variables,
                                     arg_input=None) == True
    assert conditions.check_condition(["1", "==", 2], new_uuid, collected_variables,
                                     arg_input=None) == False
    assert conditions.check_condition(["1", "==", "1"], new_uuid, collected_variables,
                                     arg_input=None) == True
    assert conditions.check_condition(["1", "==", "2"], new_uuid, collected_variables,
                                     arg_input=None) == False

    # === Operator
    assert conditions.check_condition([True, "===", True], new_uuid, collected_variables,
                                     arg_input=None) == True
    assert conditions.check_condition([True, "===", "True"], new_uuid, collected_variables,
                                     arg_input=None) == True
    assert conditions.check_condition([True, "===", "False"], new_uuid, collected_variables,
                                     arg_input=None) == False
    assert conditions.check_condition([1, "===", 1], new_uuid, collected_variables,
                                     arg_input=None) == True
    assert conditions.check_condition([1, "===", "2"], new_uuid, collected_variables,
                                     arg_input=None) == False
    assert conditions.check_condition(["True", "===", "True"], new_uuid, collected_variables,
                                     arg_input=None) == True
    assert conditions.check_condition(["True", "===", "False"], new_uuid, collected_variables,
                                     arg_input=None) == False
    # > Operator
    assert conditions.check_condition([True, ">", True], new_uuid, collected_variables,
                                     arg_input=None) == False
    assert conditions.check_condition([True, ">", False], new_uuid, collected_variables,
                                     arg_input=None) == True
    assert conditions.check_condition([2, ">", 1], new_uuid, collected_variables,
                                     arg_input=None) == True
    assert conditions.check_condition([1, ">", 1], new_uuid, collected_variables,
                                     arg_input=None) == False
    assert conditions.check_condition([1, ">", 2], new_uuid, collected_variables,
                                     arg_input=None) == False
    assert conditions.check_condition(["1", ">", 1], new_uuid, collected_variables,
                                     arg_input=None) == False
    assert conditions.check_condition(["1", ">", 2], new_uuid, collected_variables,
                                     arg_input=None) == False
    assert conditions.check_condition(["1", ">", "1"], new_uuid, collected_variables,
                                     arg_input=None) == False
    assert conditions.check_condition(["2", ">", "1"], new_uuid, collected_variables,
                                     arg_input=None) == True
    assert conditions.check_condition(["1", ">", "2"], new_uuid, collected_variables,
                                     arg_input=None) == False

    # >= Operator
    assert conditions.check_condition([True, ">=", True], new_uuid, collected_variables,
                                     arg_input=None) == True
    assert conditions.check_condition([True, ">=", False], new_uuid, collected_variables,
                                     arg_input=None) == True
    assert conditions.check_condition([2, ">=", 1], new_uuid, collected_variables,
                                     arg_input=None) == True
    assert conditions.check_condition([1, ">=", 1], new_uuid, collected_variables,
                                     arg_input=None) == True
    assert conditions.check_condition([1, ">=", 2], new_uuid, collected_variables,
                                     arg_input=None) == False
    assert conditions.check_condition(["1", ">=", 1], new_uuid, collected_variables,
                                     arg_input=None) == True
    assert conditions.check_condition(["1", ">=", 2], new_uuid, collected_variables,
                                     arg_input=None) == False
    assert conditions.check_condition(["1", ">=", "1"], new_uuid, collected_variables,
                                     arg_input=None) == True
    assert conditions.check_condition(["2", ">=", "1"], new_uuid, collected_variables,
                                     arg_input=None) == True
    assert conditions.check_condition(["1", ">=", "2"], new_uuid, collected_variables,
                                     arg_input=None) == False

    # < Operator
    assert conditions.check_condition([False, "<", True], new_uuid, collected_variables,
                                     arg_input=None) == True
    assert conditions.check_condition([True, "<", False], new_uuid, collected_variables,
                                     arg_input=None) == False
    assert conditions.check_condition([True, "<", True], new_uuid, collected_variables,
                                     arg_input=None) == False
    assert conditions.check_condition([1, "<", 2], new_uuid, collected_variables,
                                     arg_input=None) == True
    assert conditions.check_condition([1, "<", 1], new_uuid, collected_variables,
                                     arg_input=None) == False
    assert conditions.check_condition([2, "<", 1], new_uuid, collected_variables,
                                     arg_input=None) == False
    assert conditions.check_condition(["1", "<", 1], new_uuid, collected_variables,
                                     arg_input=None) == False
    assert conditions.check_condition(["1", "<", 2], new_uuid, collected_variables,
                                     arg_input=None) == True
    assert conditions.check_condition(["1", "<", "1"], new_uuid, collected_variables,
                                     arg_input=None) == False
    assert conditions.check_condition(["1", "<", "2"], new_uuid, collected_variables,
                                     arg_input=None) == True
    assert conditions.check_condition(["2", "<", "1"], new_uuid, collected_variables,
                                     arg_input=None) == False

    # <= Operator
    assert conditions.check_condition([True, "<=", True], new_uuid, collected_variables,
                                     arg_input=None) == True
    assert conditions.check_condition([True, "<=", False], new_uuid, collected_variables,
                                     arg_input=None) == False
    assert conditions.check_condition([False, "<=", True], new_uuid, collected_variables,
                                     arg_input=None) == True
    assert conditions.check_condition([2, "<=", 1], new_uuid, collected_variables,
                                     arg_input=None) == False
    assert conditions.check_condition([1, "<=", 1], new_uuid, collected_variables,
                                     arg_input=None) == True
    assert conditions.check_condition([1, "<=", 2], new_uuid, collected_variables,
                                     arg_input=None) == True
    assert conditions.check_condition(["1", "<=", 1], new_uuid, collected_variables,
                                     arg_input=None) == True
    assert conditions.check_condition(["1", "<=", 2], new_uuid, collected_variables,
                                     arg_input=None) == True
    assert conditions.check_condition(["1", "<=", "1"], new_uuid, collected_variables,
                                     arg_input=None) == True
    assert conditions.check_condition(["2", "<=", "1"], new_uuid, collected_variables,
                                     arg_input=None) == False
    assert conditions.check_condition(["1", "<=", "2"], new_uuid, collected_variables,
                                     arg_input=None) == True

    # != Operator
    assert conditions.check_condition([True, "!=", True], new_uuid, collected_variables,
                                     arg_input=None) == False
    assert conditions.check_condition([True, "!=", False], new_uuid, collected_variables,
                                     arg_input=None) == True
    assert conditions.check_condition([2, "!=", 1], new_uuid, collected_variables,
                                     arg_input=None) == True
    assert conditions.check_condition([1, "!=", 1], new_uuid, collected_variables,
                                     arg_input=None) == False
    assert conditions.check_condition([1, "!=", 2], new_uuid, collected_variables,
                                     arg_input=None) == True
    assert conditions.check_condition(["1", "!=", 1], new_uuid, collected_variables,
                                     arg_input=None) == False
    assert conditions.check_condition(["1", "!=", 2], new_uuid, collected_variables,
                                     arg_input=None) == True
    assert conditions.check_condition(["1", "!=", "1"], new_uuid, collected_variables,
                                     arg_input=None) == False
    assert conditions.check_condition(["2", "!=", "1"], new_uuid, collected_variables,
                                     arg_input=None) == True
    assert conditions.check_condition(["1", "!=", "2"], new_uuid, collected_variables,
                                     arg_input=None) == True

    # Unknown Operator
    assert conditions.check_condition(["1", "$", "2"], new_uuid, collected_variables,
                                     arg_input=None) == False

    # Not Operator
    assert conditions.check_condition(["not", True, "==", True], new_uuid, collected_variables,
                                     arg_input=None) == False
    assert conditions.check_condition(["not", True, "==", False], new_uuid, collected_variables,
                                     arg_input=None) == True
    assert conditions.check_condition(["not", 1, "==", 1], new_uuid, collected_variables,
                                     arg_input=None) == False
    assert conditions.check_condition(["not", 1, "==", 2], new_uuid, collected_variables,
                                     arg_input=None) == True
    assert conditions.check_condition(["not", "1", "==", 1], new_uuid, collected_variables,
                                     arg_input=None) == False
    assert conditions.check_condition(["not", "1", "==", 2], new_uuid, collected_variables,
                                     arg_input=None) == True
    assert conditions.check_condition(["not", "1", "==", "1"], new_uuid, collected_variables,
                                     arg_input=None) == False
    assert conditions.check_condition(["not", "1", "==", "2"], new_uuid, collected_variables,
                                     arg_input=None) == True

    # Improper Syntax
    assert conditions.check_condition(["1", "=", ">", "2"], new_uuid, collected_variables,
                                     arg_input=None) == False
