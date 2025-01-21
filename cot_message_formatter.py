"""
title: Chain of Thought Formatter
author: Assistant
date: 2024-03-19
version: 1.1
license: MIT
description: Converts all text before </think> into a collapsible thinking section
"""

from typing import List, Optional
from pydantic import BaseModel
from schemas import OpenAIChatMessage
import re

class Pipeline:
    class Valves(BaseModel):
        pipelines: List[str] = ["*"]
        priority: int = 0
        max_turns: int = 9999

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
                # Also remove any stray </details> tags
                modified_content = modified_content.replace("</details>", "")
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
                # Split the response at </think>
                parts = model_response.split("</think>", 1)
                
                # Get everything before </think> and after it
                thinking_part = parts[0].replace("</details>", "").strip()
                remaining_part = parts[1].strip() if len(parts) > 1 else ""
                
                # Remove <think> tag if it exists
                thinking_part = thinking_part.replace("<think>", "").strip()
                
                # Construct the new response with proper formatting
                formatted_response = f"<details>\n<summary>Thoughts...</summary>\n\n{thinking_part}\n\n---\n\n</details>"
                
                # Add the remaining part if it exists
                if remaining_part:
                    formatted_response += f"\n\n{remaining_part}"
                
                messages[-1]["content"] = formatted_response
                body["messages"] = messages

        return body
