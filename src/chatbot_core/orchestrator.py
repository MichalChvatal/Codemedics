"""Orchestrator glue code.

This orchestrator merges the document helpers and the routing logic
from the large notebook with the lightweight agent/orchestrator CLI
approach used by the separate script.

The goal is to preserve the notebook's document helper functions and the
RAG integration while centralising routing and agent invocation here.
"""
import os
import difflib
from typing import Optional
from .agents import BaseAgent, FormAgent, ProcessAgent, OrgAgent
from .rag import RAGEngine
# import docx locally where needed (avoid hard dependency at module import time)


class Orchestrator:
    def __init__(self, doc_root: str = "./data/"):
        self.doc_root = doc_root
        self.current_doc = None
        self.current_doc_path = None
        self.current_doc_name = None

        # in-memory RAG engine (documents can be added, or this can be bypassed)
        self.rag = RAGEngine()

        # agent registry
        self.agents = {
            "FORM_AGENT": FormAgent(),
            "PROCESS_AGENT": ProcessAgent(),
            "ORG_AGENT": OrgAgent(),
        }

    # ----------------- DOCUMENT HELPERS (kept from the notebook) -----------------

    @staticmethod
    def _replace_in_paragraph(paragraph, placeholder: str, value: str):
        if placeholder not in paragraph.text:
            return
        full_text = "".join(run.text for run in paragraph.runs)
        new_text = full_text.replace(placeholder, value)
        for run in paragraph.runs:
            run.text = ""
        if paragraph.runs:
            paragraph.runs[0].text = new_text

    def _replace_placeholder_in_doc(self, doc: object, placeholder: str, value: str):
        for paragraph in doc.paragraphs:
            self._replace_in_paragraph(paragraph, placeholder, value)
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    for paragraph in cell.paragraphs:
                        self._replace_in_paragraph(paragraph, placeholder, value)

    def _doc_to_text(self, doc: object, max_chars: int = 4000) -> str:
        parts = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
        text = "\n".join(parts)
        if len(text) > max_chars:
            text = text[:max_chars] + "\n\n[Text zkrácen kvůli délce…]"
        return text

    def _list_docx_files(self):
        if not os.path.isdir(self.doc_root):
            return []
        return [
            f for f in os.listdir(self.doc_root)
            if f.lower().endswith(".docx") and os.path.isfile(os.path.join(self.doc_root, f))
        ]

    def _find_best_matching_doc(self, query: str) -> tuple[Optional[str], str]:
        files = self._list_docx_files()
        if not files:
            return None, "V adresáři šablon nejsou žádné .docx soubory."

        q = query.strip().lower()
        if not q:
            return None, "Dotaz je prázdný."

        for f in files:
            if f.lower() == q:
                return f, f"Použit přesný název souboru '{f}'."

        contains = [f for f in files if q in f.lower()]
        if len(contains) == 1:
            return contains[0], f"Nalezeno podle podřetězce v názvu souboru '{contains[0]}'."
        if len(contains) > 1:
            main = contains[0]
            alts = ", ".join(contains[1:])
            return main, (
                f"Nalezeno více souborů podle popisu. Vybrán '{main}'. "
                f"Další možné: {alts}"
            )

        matches = difflib.get_close_matches(q, files, n=3, cutoff=0.3)
        if not matches:
            available = ", ".join(files)
            return None, (
                "Nepodařilo se najít vhodný dokument podle popisu. "
                f"Dostupné šablony: {available}"
            )

        main = matches[0]
        if len(matches) == 1:
            return main, f"Dokument přibližně odpovídá popisu: '{main}'."
        alts = ", ".join(matches[1:])
        return main, (
            f"Dokument nejlépe odpovídající popisu: '{main}'. "
            f"Další kandidáti: {alts}"
        )

    # ----------------- RAG / VECTOR SEARCH -----------------
    def add_local_document(self, filename: str, content: str):
        """Add a document to the in-memory RAG store."""
        self.rag.add_document(filename, content)

    # ----------------- AGENT ROUTING / INVOCATION -----------------
    def route_agent(self, query: str) -> str:
        q = query.lower()
        if any(k in q for k in ['formulář', 'vyplnit', 'přihláška']):
            return 'FORM_AGENT'
        if any(k in q for k in ['oddělení', 'kontakt', 'ústav']):
            return 'ORG_AGENT'
        return 'PROCESS_AGENT'

    def handle_query(self, query: str) -> str:
        # 1) RAG search
        results = self.rag.vector_search(query)
        rag_context = '\n'.join([f'Z dokumentu {fn} -> {content}' for fn, content in results])

        # 2) Route to agent
        agent_name = self.route_agent(query)
        agent = self.agents[agent_name]

        # 3) Invoke agent
        response = agent.invoke(query, rag_context)

        # 4) Append doc references
        if results:
            doc_refs = ', '.join([fn for fn, _ in results])
            response += f'\n\nDále se můžete obrátit na dokumenty: {doc_refs}'

        return response
