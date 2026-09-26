import pytest

from backend.orchestrator.orchestrator import Orchestrator


@pytest.fixture(scope="module")
def orchestrator():
    # Built once and reused across tests in this file — the classification
    # methods below don't touch the network or any agent's internal state.
    return Orchestrator()


def test_routes_sql_question_to_sql_agent(orchestrator):
    question = "Write a SQL query to find the second highest salary"
    assert orchestrator.select_agent(question) == "SQL"


def test_routes_coding_question_to_coding_agent(orchestrator):
    question = "Write a Python function to reverse a string"
    assert orchestrator.select_agent(question) == "CODING"


def test_routes_arithmetic_question_to_calculator(orchestrator):
    question = "Calculate the average of 10, 20, and 30"
    assert orchestrator.select_agent(question) == "CALCULATOR"


def test_routes_current_events_question_to_research(orchestrator):
    question = "What are the latest developments in AI?"
    assert orchestrator.select_agent(question) == "RESEARCH"


def test_routes_generic_question_to_general(orchestrator):
    question = "Tell me a joke"
    assert orchestrator.select_agent(question) == "GENERAL"


def test_sql_takes_priority_over_coding(orchestrator):
    # A question that mentions both "SQL" and "python" should still route
    # to SQL, per the priority order documented in select_agent().
    question = "How do I run a SQL query from Python code?"
    assert orchestrator.select_agent(question) == "SQL"


@pytest.mark.parametrize(
    "expression,expected",
    [
        ("125 * 8", True),
        ("what is 25 + 75?", True),
        ("tell me about the history of Rome", False),
    ],
)
def test_is_calculation_detects_arithmetic(orchestrator, expression, expected):
    assert orchestrator.is_calculation(expression) is expected