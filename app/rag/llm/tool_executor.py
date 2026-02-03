"""Tool Executor"""

from typing import Dict, Any, Optional
from app.rag.llm.tools import tool_registry
from app.utils.logger import get_logger

logger = get_logger(__name__)


class ToolExecutor:
    """Execute tools"""

    def __init__(self):
        """Initialize tool executor"""
        self.registry = tool_registry

    def execute_tool(
        self, tool_name: str, args: Optional[Dict[str, Any]] = None
    ) -> str:
        """Execute a tool"""
        tool = self.registry.get_tool(tool_name)
        if not tool:
            logger.warning("Tool not found: %s", tool_name)
            return f"Error: Tool '{tool_name}' not found"

        # Handle None args safely
        tool_args = args or {}

        try:
            result = tool(**tool_args)
            logger.info("Executed tool: %s", tool_name)
            return str(result)
        except Exception as e:
            logger.error("Error executing tool '%s': %s", tool_name, str(e))
            return f"Error executing tool: {str(e)}"
