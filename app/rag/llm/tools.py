"""Tool Definitions"""

from typing import List, Dict, Callable, Any
import ast
import operator as op
from datetime import datetime
from app.utils.logger import get_logger

logger = get_logger(__name__)


class ToolRegistry:
    """Registry for available tools"""

    def __init__(self):
        """Initialize tool registry"""
        self.tools: Dict[str, Callable] = {}
        self._register_default_tools()

    def _register_default_tools(self):
        """Register default tools"""
        self.register_tool("get_current_date", self.get_current_date)
        self.register_tool("calculate", self.calculate)

    def register_tool(self, name: str, func: Callable):
        """Register a tool"""
        self.tools[name] = func
        logger.info("Registered tool: %s", name)

    def get_tool(self, name: str) -> Callable:
        """Get a tool by name"""
        return self.tools.get(name)

    def list_tools(self) -> List[str]:
        """List all available tools"""
        return list(self.tools.keys())

    @staticmethod
    def get_current_date() -> str:
        """Get current date"""
        return datetime.now().strftime("%Y-%m-%d %H:%M:S")

    @staticmethod
    def _safe_eval(expression: str) -> Any:
        """
        Safely evaluate a mathematical expression using AST.
        """
        operators = {
            ast.Add: op.add,
            ast.Sub: op.sub,
            ast.Mult: op.mul,
            ast.Div: op.truediv,
            ast.Mod: op.mod,
            ast.Pow: op.pow,
            ast.UAdd: op.pos,
            ast.USub: op.neg,
        }

        def _eval(node):
            if isinstance(node, ast.Num):  # For older Python versions
                return node.n
            elif isinstance(node, ast.Constant):  # For Python 3.8+
                if not isinstance(node.value, (int, float)):
                    raise TypeError(f"Unsupported constant type: {type(node.value)}")
                return node.value
            elif isinstance(node, ast.BinOp):
                return operators[type(node.op)](_eval(node.left), _eval(node.right))
            elif isinstance(node, ast.UnaryOp):
                return operators[type(node.op)](_eval(node.operand))
            elif isinstance(node, ast.Expr):
                return _eval(node.value)
            else:
                raise TypeError(f"Unsupported AST node: {type(node)}")

        try:
            tree = ast.parse(expression, mode="eval")
            return _eval(tree.body)
        except (SyntaxError, KeyError, TypeError, ZeroDivisionError) as e:
            raise ValueError(f"Invalid expression: {str(e)}") from e

    @staticmethod
    def calculate(expression: str) -> str:
        """Calculate a mathematical expression"""
        try:
            # Keep the basic character check as a quick pre-filter
            allowed_chars = set("0123456789+-*/()%. ")
            if not all(c in allowed_chars for c in expression):
                return "Error: Invalid characters in expression"

            result = ToolRegistry._safe_eval(expression)
            return str(result)
        except Exception as e:
            return f"Error: {str(e)}"


tool_registry = ToolRegistry()
