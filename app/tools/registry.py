from typing import Dict, Any, List
import importlib
import logging

logger = logging.getLogger(__name__)

# Simple tool registry mapping tool names to callable implementations.
# In a production system this might be more dynamic and support permissions per agent.
_TOOL_MAP = {
    # customer tools
    "get_customer_profile": ("app.tools.customer_tools", "get_customer_profile"),
    "search_menu": ("app.tools.customer_tools", "search_menu"),
    "get_item_details": ("app.tools.customer_tools", "get_item_details"),
    "add_to_order": ("app.tools.customer_tools", "add_to_order"),
    "remove_from_order": ("app.tools.customer_tools", "remove_from_order"),
    "calculate_total": ("app.tools.customer_tools", "calculate_total"),
    "verify_address": ("app.tools.customer_tools", "verify_address"),
    "place_order": ("app.tools.customer_tools", "place_order"),

    # restaurant tools
    "notify_restaurant": ("app.tools.restaurant_tools", "notify_restaurant"),
    "confirm_preparation_time": ("app.tools.restaurant_tools", "confirm_preparation_time"),
    "handle_unavailable_item": ("app.tools.restaurant_tools", "handle_unavailable_item"),
    "update_restaurant_status": ("app.tools.restaurant_tools", "update_restaurant_status"),

    # driver tools
    "find_available_drivers": ("app.tools.driver_tools", "find_available_drivers"),
    "calculate_distance": ("app.tools.driver_tools", "calculate_distance"),
    # ... add other tools as needed
}


class ToolRegistry:
    """Simple registry to locate and execute tools by name."""

    def __init__(self):
        self.tool_map = _TOOL_MAP

    def get_tools_for_agent(self, agent_name: str) -> List[Dict[str, Any]]:
        """
        Return a list of tool descriptors available to the agent.
        For simplicity, return all tools; you can restrict per-agent as needed.
        """
        tools = []
        for name in self.tool_map:
            tools.append({
                "name": name,
                "description": f"Tool: {name}"
            })
        return tools

    def get_tool_parameters(self, tool_name: str) -> List[str]:
        """
        Return parameter names expected by a tool, used to decide whether to inject session_data.
        This is a lightweight heuristic: many tools accept 'session_data'.
        """
        # In a real registry, you'd introspect the function signature.
        if tool_name in ["add_to_order", "remove_from_order", "place_order"]:
            return ["session_data"]
        return []

    async def execute_tool(self, tool_name: str, arguments: Dict[str, Any]):
        """Dynamically import and execute a tool function. Supports both sync and async callables."""
        if tool_name not in self.tool_map:
            raise ValueError(f"Tool {tool_name} not found in registry")

        module_path, func_name = self.tool_map[tool_name]
        module = importlib.import_module(module_path)
        func = getattr(module, func_name)

        # Call function; if coroutine, await it
        if callable(func):
            result = func(arguments) if not getattr(func, "__code__", None) or func.__code__.co_flags & 0x80 == 0 else None
            # The above attempt to detect coroutines via flags can be unreliable; prefer:
            import inspect
            if inspect.iscoroutinefunction(func):
                return await func(**arguments) if isinstance(arguments, dict) else await func(arguments)
            else:
                # call synchronous
                return func(**arguments) if isinstance(arguments, dict) else func(arguments)
        else:
            raise ValueError(f"Tool {tool_name} is not callable")
