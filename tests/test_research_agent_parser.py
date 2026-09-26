from backend.agents.research_agent import ResearchAgent


# _parse_action doesn't touch self at all, but it's an instance method,
# so we still need an instance. ResearchAgent() only needs GROQ_API_KEY
# to construct (set by conftest.py) -- it never makes a real API call here.
def make_agent():
    return ResearchAgent()


def test_parses_search_action():
    agent = make_agent()
    raw = "Thought: I need current pricing info.\nAction: SEARCH[Groq API pricing 2026]"

    thought, action_type, query = agent._parse_action(raw)

    assert action_type == "SEARCH"
    assert query == "Groq API pricing 2026"
    assert "current pricing" in thought


def test_parses_finish_action():
    agent = make_agent()
    raw = "Thought: I already have enough information.\nAction: FINISH"

    thought, action_type, query = agent._parse_action(raw)

    assert action_type == "FINISH"
    assert query is None


def test_search_query_with_special_characters():
    agent = make_agent()
    raw = "Thought: need specifics.\nAction: SEARCH[iPhone 17 price (India) vs iPhone 16 launch price]"

    _, action_type, query = agent._parse_action(raw)

    assert action_type == "SEARCH"
    assert query == "iPhone 17 price (India) vs iPhone 16 launch price"


def test_malformed_response_defaults_to_finish():
    # If the model doesn't follow the format at all, the parser must not
    # crash and must not loop forever -- it should default to FINISH.
    agent = make_agent()
    raw = "I think the answer is 42."

    _, action_type, query = agent._parse_action(raw)

    assert action_type == "FINISH"
    assert query is None