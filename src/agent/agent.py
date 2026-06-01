import os
import re
import json
from typing import List, Dict, Any, Optional
from src.core.llm_provider import LLMProvider
from src.telemetry.logger import logger

class ReActAgent:
    """
    A ReAct-style Agent that follows the Thought-Action-Observation loop.
    Implements the core loop logic and flight tool execution.
    """
    
    def __init__(self, llm: LLMProvider, tools: List[Dict[str, Any]], max_steps: int = 5):
        self.llm = llm
        self.tools = tools
        self.max_steps = max_steps
        self.history = []

    def get_system_prompt(self) -> str:
        """
        System prompt instructing the agent to follow ReAct logic.
        """
        tool_descriptions = "\n".join([f"- {t['name']}: {t['description']}" for t in self.tools])
        return f"""You are an intelligent travel assistant. You must answer the user request by calling the appropriate tools.
You have access to the following tools:
{tool_descriptions}

Use the following exact format:
Thought: your line of reasoning about what you need to do next.
Action: tool_name(arguments)
Observation: the result returned by the tool.

... (repeat Thought, Action, Observation as many times as needed to resolve the request)

Thought: I have solved the request.
Final Answer: your final response to the user.

Ensure that:
1. Every time you want to execute a tool, write "Action: tool_name(arguments)" followed by a newline and nothing else.
2. Every time you write an "Action", you must STOP and wait for the "Observation:".
3. Write "Final Answer:" when you are finished and have the final resolution.
"""

    def run(self, user_input: str) -> str:
        """
        Executes the ReAct Thought-Action-Observation loop.
        """
        logger.log_event("AGENT_START", {"input": user_input, "model": self.llm.model_name})
        
        conversation_context = f"User Request: {user_input}\n"
        steps = 0

        while steps < self.max_steps:
            # Generate response from the LLM fallback chain
            response = self.llm.generate(
                prompt=conversation_context,
                system_prompt=self.get_system_prompt(),
                stop=["Observation:", "Observation: "]
            )
            
            content = response.get("content", "").strip()
            latency = response.get("latency_ms", 0)
            logger.log_event("LLM_RESPONSE", {"content": content, "latency_ms": latency})
            
            print(f"\n{content}")
            
            # 1. Check if the LLM reached a Final Answer
            if "Final Answer:" in content:
                final_answer_match = re.search(r"Final Answer:\s*(.*)", content, re.DOTALL)
                final_answer = final_answer_match.group(1).strip() if final_answer_match else content
                logger.log_event("AGENT_END", {"steps": steps + 1, "status": "success"})
                return final_answer
                
            # 2. Check if the LLM decided to take an Action
            action_match = re.search(r"Action:\s*([a-zA-Z0-9_]+)(?:\((.*)\))?", content)
            if action_match:
                tool_name = action_match.group(1).strip()
                tool_args = action_match.group(2).strip() if action_match.group(2) else ""
                
                # Execute the tool
                observation = self._execute_tool(tool_name, tool_args)
                logger.log_event("TOOL_EXECUTE", {"tool": tool_name, "args": tool_args, "observation": observation})
                
                print(f"Observation: {observation}")
                
                # Append to conversation context
                conversation_context += f"\n{content}\nObservation: {observation}\n"
            else:
                # If neither is found, fallback to treating content as the answer
                logger.log_event("AGENT_END", {"steps": steps + 1, "status": "no_action_fallback"})
                return content
                
            steps += 1
            
        logger.log_event("AGENT_END", {"steps": steps, "status": "timeout"})
        return "The agent timed out before reaching a final answer."

    def _execute_tool(self, tool_name: str, args_str: str) -> str:
        """
        Helper method to execute tools dynamically. Parses various argument string formats.
        """
        from src.tools import flight_tools

        tool_mapping = {
            "find_productivity_flights": flight_tools.find_productivity_flights,
            "time_until_flight": flight_tools.time_until_flight,
            "parse_flight_details": flight_tools.parse_flight_details,
            "get_current_time": flight_tools.get_current_time
        }
        
        if tool_name not in tool_mapping:
            # Check standard fallback from skeleton
            for tool in self.tools:
                if tool['name'] == tool_name:
                    return f"Result of {tool_name}"
            return f"Tool {tool_name} not found."
            
        func = tool_mapping[tool_name]
        
        try:
            cleaned_args = args_str.strip()
            # 1. Parse JSON argument block
            if cleaned_args.startswith("{") and cleaned_args.endswith("}"):
                args = json.loads(cleaned_args)
                if isinstance(args, dict):
                    return func(**args)
                    
            # 2. Parse standard parentheses function args (e.g. ("BA 303", "2026-03-03 08:30"))
            if cleaned_args.startswith("(") and cleaned_args.endswith(")"):
                cleaned_args = cleaned_args[1:-1]
                
            if not cleaned_args:
                return func()
                
            # Split by comma but respect quotes
            import csv
            reader = csv.reader([cleaned_args], skipinitialspace=True)
            args = next(reader)
            
            # Clean named argument mapping if LLM generated them like: flight_number="BA 191"
            # Or current_time_str='2026-03-03 08:30'
            kwargs = {}
            positional_args = []
            for arg in args:
                arg_cleaned = arg.strip()
                if "=" in arg_cleaned:
                    parts = arg_cleaned.split("=", 1)
                    key = parts[0].strip()
                    val = parts[1].strip().strip('\'"')
                    kwargs[key] = val
                else:
                    positional_args.append(arg_cleaned.strip('\'"'))
            
            if kwargs:
                return func(*positional_args, **kwargs)
            elif positional_args:
                return func(*positional_args)
            else:
                return func()
        except Exception as e:
            return f"Error executing tool '{tool_name}' with args '{args_str}': {e}"

