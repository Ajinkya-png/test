from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Callable
import logging
from ..services.llm_service import LLMService
from ..tools.registry import ToolRegistry

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """
    Abstract base for agents. Implements conversation management and tool execution logic.
    Subclasses should override should_transfer() if they can transfer to other agents.
    """
    def __init__(self, name: str, system_prompt: str):
        self.name = name
        self.system_prompt = system_prompt
        self.llm_service = LLMService()
        self.tool_registry = ToolRegistry()
        self.conversation_history: List[Dict[str, str]] = []

        # Initialize conversation with system prompt
        self.conversation_history.append({
            "role": "system",
            "content": system_prompt
        })

    def add_message(self, role: str, content: str):
        """Add message to conversation history."""
        self.conversation_history.append({
            "role": role,
            "content": content
        })

    def get_available_tools(self) -> List[Dict]:
        """Return tools allowed for this agent from the registry."""
        return self.tool_registry.get_tools_for_agent(self.name)

    async def process_message(self, message: str, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process user message via LLM and optionally execute tool calls."""
        try:
            # Add user message to conversation
            self.add_message("user", message)

            # Get available tools
            tools = self.get_available_tools()

            # Generate LLM response
            response = await self.llm_service.generate_response(
                messages=self.conversation_history,
                tools=tools,
                tool_choice="auto"
            )

            # Handle tool calls
            if response.get("tool_calls"):
                tool_results = await self._execute_tool_calls(response["tool_calls"], session_data)

                # Append tool results to conversation and get final response
                final_response = await self._handle_tool_results(response, tool_results)

                # Add assistant response to conversation
                self.add_message("assistant", final_response.get("content", ""))

                return final_response
            else:
                # No tool calls, return direct response
                self.add_message("assistant", response.get("content", ""))
                return response

        except Exception as e:
            logger.error(f"Error in agent {self.name}: {e}")
            error_response = "I apologize, but I'm experiencing technical difficulties. Please try again."
            return {"content": error_response, "tool_calls": []}

    async def _execute_tool_calls(self, tool_calls: List[Dict], session_data: Dict[str, Any]) -> List[Dict]:
        """Execute tool calls and return results."""
        results = []

        for tool_call in tool_calls:
            try:
                tool_name = tool_call.get("name")
                arguments = tool_call.get("arguments", {})

                # Add session data to arguments if needed by tool
                if "session_data" in self.tool_registry.get_tool_parameters(tool_name):
                    arguments["session_data"] = session_data

                # Execute tool (tool implementations may be async)
                result = await self.tool_registry.execute_tool(tool_name, arguments)

                results.append({
                    "tool_call_id": tool_call.get("id"),
                    "tool_name": tool_name,
                    "result": result
                })

            except Exception as e:
                logger.error(f"Error executing tool {tool_call.get('name')}: {e}")
                results.append({
                    "tool_call_id": tool_call.get("id"),
                    "tool_name": tool_call.get("name"),
                    "result": f"Error: {str(e)}"
                })

        return results

    async def _handle_tool_results(self, initial_response: Dict, tool_results: List[Dict]) -> Dict[str, Any]:
        """Add tool results to conversation and request final LLM response."""
        # Add tool results to conversation
        for result in tool_results:
            self.conversation_history.append({
                "role": "tool",
                "content": str(result["result"]),
                "tool_call_id": result["tool_call_id"],
                "name": result["tool_name"]
            })

        # Request final response from LLM after tool execution
        final_response = await self.llm_service.generate_response(
            messages=self.conversation_history,
            tools=self.get_available_tools()
        )

        return final_response

    def should_transfer(self, session_data: Dict[str, Any]) -> Optional[str]:
        """Determine if agent should transfer to another agent. Default: no transfer."""
        return None

    def get_transfer_summary(self) -> str:
        """Generate a short summary for handing off to the next agent."""
        recent_messages = self.conversation_history[-4:]  # Last few exchanges
        summary = "Recent conversation:\n"
        for msg in recent_messages:
            if msg.get("role") in ["user", "assistant"]:
                summary += f"{msg.get('role')}: {msg.get('content')}\n"
        return summary

    def clear_conversation(self):
        """Clear conversation history but keep the system prompt."""
        self.conversation_history = [self.conversation_history[0]]  # Keep system prompt
