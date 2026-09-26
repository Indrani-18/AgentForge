import re

import time

from concurrent.futures import ThreadPoolExecutor, as_completed

from backend.agents.coding_agent import CodingAgent

from backend.agents.research_agent import ResearchAgent

from backend.agents.sql_agent import SQLAgent

from backend.agents.planner_agent import PlannerAgent

from backend.agents.final_answer_agent import FinalAnswerAgent

from backend.memory.memory import ConversationMemory

from backend.memory.shared_memory import SharedWorkingMemory



from backend.models.agent_message import AgentMessage



from backend.graph.workflow_graph import WorkflowGraph

from backend.graph.graph_executor import GraphExecutor



from backend.tools.calculator_tool import calculator

from backend.utils.logger import logger







class RoutingMixin:
    """
    Mixin split out of the original monolithic Orchestrator class.
    See orchestrator.py for how this is combined with the other mixins.
    """

    def is_sql(self, question):

        """

        Detect whether the question is related to SQL/database

        tasks.

        """



        q = question.lower()



        sql_keywords = [

            "sql",

            "database",

            "table",

            "query",

            "select",

            "insert",

            "update",

            "delete",

            "join",

            "inner join",

            "left join",

            "right join",

            "mysql",

            "postgresql",

            "sqlite",

            "oracle",

            "primary key",

            "foreign key",

            "group by",

            "having",

            "second highest salary",

        ]



        return any(

            keyword in q

            for keyword in sql_keywords

        )



    # ---------------------------------------------------------



    def is_coding(self, question):

        """

        Detect programming/coding questions.

        """



        q = question.lower()



        coding_keywords = [

            "code",

            "coding",

            "program",

            "programming",

            "python",

            "javascript",

            "java",

            "c++",

            "c#",

            "html",

            "css",

            "debug",

            "debugging",

            "bug",

            "error in my code",

            "function",

            "algorithm",

            "data structure",

            "leetcode",

            "implement",

            "implementation",

        ]



        return any(

            keyword in q

            for keyword in coding_keywords

        )



    # ---------------------------------------------------------



    def is_calculation(self, question):

        """

        Detect mathematical/calculation questions.

        """



        q = question.lower()



        calculation_keywords = [

            "calculate",

            "calculation",

            "multiplication",

            "multiply",

            "divide",

            "division",

            "addition",

            "subtract",

            "percentage",

            "percent",

            "average",

            "sum",

        ]



        arithmetic_pattern = (

            r"\d+\s*[+\-*/x×]\s*\d+"

        )



        if re.search(arithmetic_pattern, q):

            return True



        return any(

            keyword in q

            for keyword in calculation_keywords

        )



    # ---------------------------------------------------------



    def is_web_search(self, question):

        """

        Detect questions that require current/recent information.



        ResearchAgent handles these questions.

        """



        q = question.lower()



        web_keywords = [

            "latest",

            "today",

            "current",

            "recent",

            "news",

            "search",

            "this week",

            "this month",

            "now",

            "2026",

        ]



        return any(

            keyword in q

            for keyword in web_keywords

        )



    # =========================================================

    # PLANNER DETECTION

    # =========================================================



    def should_use_planner(self, question):

        """

        Determine whether the question requires multiple steps

        or multiple specialized agents.

        """



        q = question.lower()



        multi_step_patterns = [

            "and then",

            "and also",

            "also calculate",

            "then calculate",

            "then write",

            "then create",

            "then generate",

            "research and",

            "analyze and",

            "compare and",

            "find and calculate",

            "explain and calculate",

            "research and calculate",

            "calculate and explain",

            "research and create",

            "research and write",

            "research and implement",

            "analyze and create",

            "explain and implement",

        ]



        return any(

            pattern in q

            for pattern in multi_step_patterns

        )



    # =========================================================

    # AGENT SELECTION

    # =========================================================



    def select_agent(self, question):

        """

        Select the appropriate single agent.



        Priority:

            SQL

            Coding

            Calculator

            Research

            General

        """



        if self.is_sql(question):

            return "SQL"



        if self.is_coding(question):

            return "CODING"



        if self.is_calculation(question):

            return "CALCULATOR"



        if self.is_web_search(question):

            return "RESEARCH"



        return "GENERAL"



    # =========================================================

    # CONTEXT

    # =========================================================