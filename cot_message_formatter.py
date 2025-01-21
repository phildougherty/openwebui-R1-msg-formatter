"""
title: Chain of Thought Formatter
author: Assistant
date: 2024-03-19
version: 1.1
license: MIT
description: Converts model's thinking process in <think> tags into collapsible sections
"""

from typing import List, Optional
from pydantic import BaseModel
from schemas import OpenAIChatMessage
import re

class Pipeline:
    class Valves(BaseModel):
        pipelines: List[str] = ["*"]  # Apply to all models
        priority: int = 0

    def __init__(self):
        self.type = "filter"
        self.name = "Chain of Thought Formatter"
        self.valves = self.Valves()

    async def on_startup(self):
        print(f"on_startup:{__name__}")

    async def on_shutdown(self):
        print(f"on_shutdown:{__name__}")

    async def inlet(self, body: dict, user: Optional[dict] = None) -> dict:
        messages = body.get("messages", [])
        modified_messages = []
        
        for message in messages:
            if message.get("role") == "assistant":
                message_content = message.get("content", "")
                # Remove any existing details tags
                pattern = r"<details[^>]*>.*?</details>"
                modified_content = re.sub(pattern, "", message_content, flags=re.DOTALL)
                modified_message = {"role": "assistant", "content": modified_content}
            else:
                modified_message = message
            modified_messages.append(modified_message)
            
        body["messages"] = modified_messages
        return body

    async def outlet(self, body: dict, user: Optional[dict] = None) -> dict:
        messages = body.get("messages", [])
        if not messages:
            return body

        if len(messages) >= 1:
            model_response = messages[-1].get("content", "")
            if model_response and "</think>" in model_response:
                # Try to find content between <think> tags first
                if "<think>" in model_response:
                    parts = model_response.split("<think>", 1)
                    think_parts = parts[1].split("</think>", 1)
                    thinking_content = think_parts[0].strip()
                    remaining_content = think_parts[1].strip() if len(think_parts) > 1 else ""
                else:
                    # Fallback: take everything before </think>
                    parts = model_response.split("</think>", 1)
                    thinking_content = parts[0].strip()
                    remaining_content = parts[1].strip() if len(parts) > 1 else ""

                # Format the response with collapsible section
                formatted_response = (
                    f"<details>\n<summary>Thoughts...</summary>\n\n{thinking_content}\n\n"
                    f"---\n\n</details>\n\n{remaining_content}"
                )
                
                messages[-1]["content"] = formatted_response
                body["messages"] = messages

        return body
