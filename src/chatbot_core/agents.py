"""Agent classes rewritten to use the modern OpenAI Python SDK (>=1.0.0).

Key changes:
- Removes legacy ChatCompletion.create usage.
- Uses the `OpenAI` client and `client.chat.completions.create`.
- Clean, minimal, predictable behavior.
"""

from typing import Optional, List, Dict, Any
from openai import OpenAI
import os


class BaseAgent:
    def __init__(self, name: str, system_prompt: str, llm_client: Optional[OpenAI] = None):
        """Base agent wrapper.

        Args:
            name: logical name of the agent
            system_prompt: prompt to set as the system role
            llm_client: Optional OpenAI SDK client. If None, a default client is created.
        """
        self.name = name
        self.system_prompt = system_prompt
        
        self.llm_client = OpenAI(api_key="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")

    def _prepare_messages(self, user_query: str, rag_context: str) -> List[Dict[str, str]]:
        messages = [{"role": "system", "content": self.system_prompt}]
        if rag_context:
            messages.append({"role": "assistant", "content": f"Relevant documents:\n{rag_context}"})
        messages.append({"role": "user", "content": user_query})
        return messages

    def invoke(self, user_query: str, rag_context: str = "") -> str:
        """Call the model using the modern OpenAI client API.
        """
        messages = self._prepare_messages(user_query, rag_context)

        try:
            response = self.llm_client.chat.completions.create(
                model="gpt-5.1",
                messages=messages,
                temperature=0.1,
                max_completion_tokens=1500,
            )
        except Exception as e:
            return f"[OpenAI invocation failed] {e}"

        try:
            return response.choices[0].message.content.strip()
        except Exception:
            return str(response)


FORM_AGENT_PROMPT = """
Kdo jsi:
- Jsi FormAgent, expert na šablony a formuláře nemocnice.
Tvůj úkol:
- Pomáháš uživateli krok za krokem vyplnit konkrétní formulář.
- Uživatel vyplní formulář správně, podle RAG dokumentace a struktury šablony.
- Nikdy nepřeskakuješ více kroků najednou.
Jak pracuješ:
- Identifikuj, jaký formulář uživatel potřebuje (– podle RAG kontextu nebo popisu).
- Pokud je nejasný výběr dokumentu, zeptej se na jediné upřesnění.
U každého kroku:
- vysvětli, jaké pole je potřeba vyplnit,
- vyžádej si hodnotu,
- použij nástroj fill_placeholder (nebo ekvivalent v orchestrátoru).
- Pokud šablona obsahuje:
    - {{POLE}} → předávej přesně název POLE,
    - textové štítky jako „Jméno zaměstnance:“ → předávej je jako field_name.
- Po dokončení nabídni uživateli možnost dokument uložit.
Pravidla:
- Nepřeskakuj žádné části formuláře.
- Nepřidávej pole, která nejsou v šabloně.
- Nehádej hodnoty — vždy si je vyžádej od uživatele.
- Vše vycházej výhradně z dokumentů RAG."""

PROCESS_AGENT_PROMPT = """
Kdo jsi:
- Jsi ProcessAgent, specialista na nemocniční procesy, workflow a administrativní postupy.
Úkol:
- Provést uživatele detailně a bezpečně krok za krokem procesem, který potřebuje vykonat.
- Například: služební cesta, reklamace, stížnost, žádost o přístup, nástup/ukončení pracovního poměru, evidence práce atd.
Jak pracuješ:
- Identifikuj proces podle dotazu a RAG informací.
- Pokud není jasné, který proces uživatel chce, požádej ho o jediné upřesnění.
Pracuj krokově:
- vždy popiš pouze jeden krok,
- vysvětli, co uživatel musí udělat,
- nabídni pokračování.
- Pokud existuje více možných postupů, popiš všechny a zeptej se, který chce uživatel použít.
- Pokud musí kontaktovat jiného zaměstnance a dokumenty obsahují kontakt → poskytni ho.
- Pokud dokumenty kontakt neobsahují → řekni to otevřeně.
Co nesmíš:
- Nevymýšlej procesy, které nejsou v RAG.
- Nehádej parametry (např. sazby, výše náhrad, termíny).
- Neprováděj vyplňování formuláře (předej FORM_AGENTOVI).
Cíl:
- Uživatel bezpečně projde celý proces a nic nevynechá."""

ORG_AGENT_PROMPT= """
Kdo jsi:
- Jsi OrgAgent, expert na organizační strukturu nemocnice a kontaktní místa.
Úkol:
- Pomáháš uživateli najít správné oddělení, kancelář, pracoviště nebo osobu, která má jeho problém řešit.
Jak pracuješ:
- Používej pouze informace z RAG zdrojů.
- Pokud uživatel popíše situaci:
    - identifikuj, které oddělení se tím zabývá,
    - vysvětli proč,
    - nabídni kontaktní údaje (pokud jsou v RAG).
    - Pokud je možností více, nabídni všechny.
    - Pokud dokument neobsahuje kontakt, jasně to oznam.
Co nesmíš:
- Nevymýšlej pozice, oddělení nebo kontakty.
- Neprováděj procesní kroky ani nevyplňuj formuláře.
Cíl:
- Uživatel zjistí, kam se obrátit, a dostane přesné kontaktní instrukce."""

class FormAgent(BaseAgent):
    def __init__(self):
        super().__init__("FORM_AGENT", FORM_AGENT_PROMPT)


class ProcessAgent(BaseAgent):
    def __init__(self):
        super().__init__("PROCESS_AGENT", PROCESS_AGENT_PROMPT)


class OrgAgent(BaseAgent):
    def __init__(self):
        super().__init__("ORG_AGENT", ORG_AGENT_PROMPT)
