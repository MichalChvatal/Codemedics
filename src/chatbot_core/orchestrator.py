# Orchestrator updated to use ORCHESTRATOR_PROMPT for agent reasoning

from .agents import FormAgent, ProcessAgent, OrgAgent
from .rag import RAGEngine
from openai import OpenAI

ORCHESTRATOR_PROMPT = """
Role a poslání:
- Jsi OrchestratorAgent, ústřední řídicí jednotka asistentů nemocnice.
- Tvým úkolem je pomoci uživateli vyřešit jeho dotaz co nejefektivněji a bezpečně — správným výběrem specializovaného agenta.
- Dotazy se týkají pracovních úkonů, administrativy, procesů, formulářů a orientace v organizační struktuře nemocnice.
- Všechny odpovědi musí být založené na informacích z RAG dokumentů poskytnutých systémem.
Jak pracuješ:
- Přečti si uživatelův dotaz a dostupný RAG kontext.
- Urči, jaký typ problému uživatel řeší:
  - Formulář / šablona → FORM_AGENT
  - Proces / postup → PROCESS_AGENT
  - Organizační informace / kontakty / oddělení → ORG_AGENT
- Nerozhoduj podle jednoslovných klíčových slov. Posuzuj záměr uživatele:
  - „Jedeme na služební cestu, co mám dělat?“ = PROCES
  - „Chci ohlásit škodu, kam se obrátit?“ = ORGANIZACE
  - „Potřebuji žádost o dovolenou.“ = FORMULÁŘ
- Pokud záměr není zcela jasný, ptej se na jediné kritické upřesnění.
- Vždy vybírej agenta, který nejlépe dokáže uživateli pomoci dosáhnout jeho cíle krok po kroku.
Co nesmíš dělat:
- Nevymýšlej interní směrnice nebo postupy, pokud nejsou v RAG.
- Nevytvářej umělé procesy, které v dokumentech neexistují.
- Nevyplňuj formuláře — to dělá FORM_AGENT.
- Nedávej rady mimo oblast nemocniční administrativy.
Cíl:
- Vyber správného agenta.
- Předat mu dotaz a RAG kontext.
- Zajistit jednotné chování celého systému.
"""

class Orchestrator:
    def __init__(self, doc_root: str = "./data/"):
        self.doc_root = doc_root

        self.current_doc: Document | None = None
        self.current_doc_path: str | None = None
        self.current_doc_name: str | None = None

        self.rag = RAGEngine()
        self.llm = OpenAI(api_key="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")

        self.agents = {
            "FORM_AGENT": FormAgent(),
            "PROCESS_AGENT": ProcessAgent(),
            "ORG_AGENT": OrgAgent(),
        }

        # --- NEW: simple in-memory conversation history (user, response) ---
        self.conversation_history: list[tuple[str, str]] = []

    # --- NEW: tiny helper to turn history into text summary ---
    def get_or_build_summary(self, max_turns: int = 6) -> str:
        if not self.conversation_history:
            return ""
        last = self.conversation_history[-max_turns:]
        lines: list[str] = []
        for user, reply in last:
            lines.append(f"UŽIVATEL: {user}")
            lines.append(f"ASISTENT: {reply}")
        return "\n".join(lines)

    # LLM-based routing using orchestrator system prompt
    def route_agent(self, query: str, rag_context: str) -> str:
        messages = [
            {"role": "system", "content": ORCHESTRATOR_PROMPT},
            {"role": "assistant", "content": f"RAG informace:\n{rag_context}"},
            {"role": "user", "content": query},
        ]

        resp = self.llm.chat.completions.create(
            model="gpt-5.1",
            messages=messages,
            temperature=0.0,
            max_completion_tokens=300,
        )

        text = resp.choices[0].message.content.strip().upper()

        if "FORM" in text:
            return "FORM_AGENT"
        if "ORG" in text:
            return "ORG_AGENT"
        return "PROCESS_AGENT"

    # ---------------------- HANDLE QUERY --------------------------

    def handle_query(self, query: str) -> str:
        # 1) Standard RAG over current query
        results = self.rag.vector_search(query)
        
        docs_context = "\n".join([
            f"Z dokumentu {fn} -> {content}"
            for fn, content in results
        ])

        # 2) Add short conversation summary into rag_context (memory)
        history_summary = self.get_or_build_summary()
        if history_summary:
            rag_context = (
                docs_context
                + "\n\nShrnutí předchozí konverzace:\n"
                + history_summary
            )
        else:
            rag_context = docs_context

        # 3) Route and invoke agent with enriched rag_context
        agent_name = self.route_agent(query, rag_context)
        agent = self.agents[agent_name]

        response = agent.invoke(query, rag_context)

        if results:
            doc_refs = ", ".join([fn for fn, _ in results])
            response += f"\n\nDále se můžete obrátit na dokumenty: {doc_refs}"

        # 4) Store this turn in memory
        self.conversation_history.append((query, response))

        return response
