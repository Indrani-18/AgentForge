from backend.tools.calculator_tool import calculate


def test_basic_multiplication():
    assert calculate("125 * 8") == "1000"


def test_handles_question_style_input():
    assert calculate("What is 25 + 75?") == "100"


def test_handles_calculate_prefix():
    assert calculate("Calculate (10 + 5) * 2") == "30"


def test_division_by_zero():
    assert calculate("10 / 0") == "Error: Cannot divide by zero."


def test_rejects_non_math_input():
    assert calculate("hello + 10") == "Error: Invalid characters in expression."


def test_rejects_empty_input():
    assert calculate("") == "Error: Empty expression."