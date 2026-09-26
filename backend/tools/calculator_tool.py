# ============================================================
# AgentForge - Calculator Tool
# File: backend/tools/calculator_tool.py
# ============================================================

import ast
import operator
import re


class CalculatorTool:
    """
    Safe mathematical calculator for AgentForge.

    Supports:
        +   Addition
        -   Subtraction
        *   Multiplication
        /   Division
        %   Modulus
        **  Power
        ()  Parentheses

    Examples:
        25 + 75
        125 * 8
        100 / 4
        (10 + 5) * 2
        What is 125 * 8?
    """

    # --------------------------------------------------------
    # Allowed operators
    # --------------------------------------------------------

    OPERATORS = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.Mod: operator.mod,
        ast.Pow: operator.pow,
        ast.USub: operator.neg,
        ast.UAdd: operator.pos,
    }

    # --------------------------------------------------------
    # Make object callable
    # --------------------------------------------------------

    def __call__(self, expression: str):
        """
        Allows:

            calculator("25 + 75")

        instead of only:

            calculator.calculate("25 + 75")
        """

        return self.calculate(expression)

    # --------------------------------------------------------
    # Main calculation function
    # --------------------------------------------------------

    def calculate(self, expression: str):

        if expression is None:
            return "Error: Empty expression."

        expression = str(expression).strip()

        if not expression:
            return "Error: Empty expression."

        # ----------------------------------------------------
        # Handle natural-language "average/sum of N, N, ..." phrasing
        # before the strict math-only check below, since these show up
        # often (e.g. "Calculate the average of 10, 20, and 30") but
        # aren't valid arithmetic expressions on their own.
        # ----------------------------------------------------

        average_match = re.search(
            r"average\s+of\s+([0-9,\s.]+?and[0-9,\s.]*[0-9]|[0-9,\s.]+[0-9])",
            expression,
            flags=re.IGNORECASE
        )

        if average_match:
            numbers = re.findall(r"-?\d+(?:\.\d+)?", average_match.group(1))

            if numbers:
                numbers = [float(n) for n in numbers]
                expression = f"({'+'.join(str(n) for n in numbers)})/{len(numbers)}"

        else:
            sum_match = re.search(
                r"sum\s+of\s+([0-9,\s.]+?and[0-9,\s.]*[0-9]|[0-9,\s.]+[0-9])",
                expression,
                flags=re.IGNORECASE
            )

            if sum_match:
                numbers = re.findall(r"-?\d+(?:\.\d+)?", sum_match.group(1))

                if numbers:
                    expression = "+".join(numbers)

        # ----------------------------------------------------
        # Remove common question prefixes
        # ----------------------------------------------------

        expression = re.sub(
            r"^(what\s+is|calculate|compute|solve|find)\s+",
            "",
            expression,
            flags=re.IGNORECASE
        )

        # ----------------------------------------------------
        # Remove common punctuation
        # ----------------------------------------------------

        expression = expression.rstrip("?.!")

        # ----------------------------------------------------
        # Remove spaces
        # ----------------------------------------------------

        expression = expression.replace(" ", "")

        if not expression:
            return "Error: Empty expression."

        # ----------------------------------------------------
        # Only allow mathematical characters
        # ----------------------------------------------------

        if not re.fullmatch(
            r"[0-9+\-*/%().]+",
            expression
        ):
            return "Error: Invalid characters in expression."

        # ----------------------------------------------------
        # Parse expression safely
        # ----------------------------------------------------

        try:

            tree = ast.parse(
                expression,
                mode="eval"
            )

            result = self._evaluate(tree.body)

            # ------------------------------------------------
            # Clean floating-point results
            # ------------------------------------------------

            if isinstance(result, float):

                if result != result:
                    return "Error: Invalid result."

                if result == float("inf"):
                    return "Error: Result is too large."

                if result == float("-inf"):
                    return "Error: Result is too large."

                if result.is_integer():
                    result = int(result)

            return str(result)

        # ----------------------------------------------------
        # Errors
        # ----------------------------------------------------

        except ZeroDivisionError:

            return "Error: Cannot divide by zero."

        except SyntaxError:

            return "Error: Invalid mathematical expression."

        except ValueError:

            return "Error: Invalid mathematical expression."

        except TypeError:

            return "Error: Invalid mathematical expression."

        except OverflowError:

            return "Error: Result is too large."

        except Exception as e:

            print(
                f"Calculator error: {e}"
            )

            return "Error: Unable to calculate expression."

    # --------------------------------------------------------
    # Safe AST evaluator
    # --------------------------------------------------------

    def _evaluate(self, node):

        # ----------------------------------------------------
        # Numbers
        # ----------------------------------------------------

        if isinstance(node, ast.Constant):

            if isinstance(
                node.value,
                (int, float)
            ):

                return node.value

            raise ValueError(
                "Invalid constant"
            )

        # ----------------------------------------------------
        # Binary operations
        # ----------------------------------------------------

        if isinstance(node, ast.BinOp):

            operator_type = type(node.op)

            if operator_type not in self.OPERATORS:

                raise ValueError(
                    "Operator not allowed"
                )

            left = self._evaluate(
                node.left
            )

            right = self._evaluate(
                node.right
            )

            # ------------------------------------------------
            # Protect against extremely large powers
            # ------------------------------------------------

            if isinstance(
                node.op,
                ast.Pow
            ):

                if abs(right) > 100:

                    raise ValueError(
                        "Power too large"
                    )

                if abs(left) > 100000:

                    raise ValueError(
                        "Base too large"
                    )

            return self.OPERATORS[
                operator_type
            ](
                left,
                right
            )

        # ----------------------------------------------------
        # Positive / negative values
        # ----------------------------------------------------

        if isinstance(node, ast.UnaryOp):

            operator_type = type(node.op)

            if operator_type not in self.OPERATORS:

                raise ValueError(
                    "Unary operator not allowed"
                )

            operand = self._evaluate(
                node.operand
            )

            return self.OPERATORS[
                operator_type
            ](
                operand
            )

        # ----------------------------------------------------
        # Reject everything else
        # ----------------------------------------------------

        raise ValueError(
            "Invalid expression"
        )


# ============================================================
# GLOBAL CALCULATOR INSTANCE
# ============================================================

calculator = CalculatorTool()


# ============================================================
# CONVENIENCE FUNCTION
# ============================================================

def calculate(expression: str):

    return calculator.calculate(
        expression
    )


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    tests = [

        "25 + 75",

        "125 * 8",

        "100 / 4",

        "50 - 20",

        "10 % 3",

        "2 ** 5",

        "(10 + 5) * 2",

        "What is 25 + 75?",

        "What is 125 * 8?",

        "Calculate 125 * 8",

        "Compute (20 + 10) * 3",

        "10 / 0",

        "hello + 10"
    ]

    print()
    print("=" * 55)
    print("        AgentForge Calculator Test")
    print("=" * 55)

    for expression in tests:

        result = calculator(
            expression
        )

        print(
            f"{expression:<35} -> {result}"
        )

    print("=" * 55)
    print()