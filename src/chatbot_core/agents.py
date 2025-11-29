"""Agent classes.

This file adapts the BaseAgent / specialized agents from the separate
`import os.py` implementation and keeps them small and testable.

Agents implement a simple `invoke(user_query, rag_context)` interface
and call an LLM. The implementation uses the openai python API by default
but is written so you can replace the invocation with langchain or other
libraries in one place.
"""
from typing import Optional
import os

try:
    import openai
except Exception:  # openai might not be installed in some environments
    openai = None


class BaseAgent:
    def __init__(self, name: str, system_prompt: str):
        self.name = name
        self.system_prompt = system_prompt

    def _prepare_messages(self, user_query: str, rag_context: str) -> list:
        messages = [{"role": "system", "content": self.system_prompt}]
        if rag_context:
            messages.append({"role": "assistant", "content": f"Relevant documents:\n{rag_context}"})
        messages.append({"role": "user", "content": user_query})
        return messages

    def invoke(self, user_query: str, rag_context: str = "") -> str:
        """Invoke the LLM with messages + optional RAG context.

        By default this uses the openai.ChatCompletion API. If the `openai`
        package isn't available or an alternative is configured, replace this
        method to plug in another client.
        """
        msgs = self._prepare_messages(user_query, rag_context)

        # prefer openai python client if installed
        if openai is not None:
            api_key = os.environ.get("OPENAI_API_KEY")
            if not api_key:
                raise RuntimeError("OPENAI_API_KEY not set in env")
            openai.api_key = api_key
            response = openai.ChatCompletion.create(
                model="gpt-5.1",
                messages=msgs,
                temperature=0.1,
                max_tokens=1500,
            )
            return response["choices"][0]["message"]["content"].strip()

        # fallback behaviour returns a simple deterministic placeholder
        return "[LLM client not configured] This agent would call an LLM here."


FORM_AGENT_PROMPT = """
Jsi FormAgent. Pomáháš uživateli krok za krokem vyplnit formuláře.\nNikdy nepřeskakuj více kroků.
"""

PROCESS_AGENT_PROMPT = """
Jsi ProcessAgent. Pomáháš uživateli krok za krokem projít nemocniční proces.\nPoužívej jen informace z RAG dokumentů.
"""

ORG_AGENT_PROMPT = """
Jsi OrgAgent. Pomáháš uživateli najít správné oddělení nebo kontaktní místo.\nPoužívej jen informace z RAG dokumentů.
"""


class FormAgent(BaseAgent):
    def __init__(self):
        super().__init__("FORM_AGENT", FORM_AGENT_PROMPT)


class ProcessAgent(BaseAgent):
    def __init__(self):
        super().__init__("PROCESS_AGENT", PROCESS_AGENT_PROMPT)


class OrgAgent(BaseAgent):
    def __init__(self):
        super().__init__("ORG_AGENT", ORG_AGENT_PROMPT)
