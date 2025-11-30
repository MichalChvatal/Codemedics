#!/usr/bin/env python3
import pandas as pd
import iris
from sentence_transformers import SentenceTransformer
from langchain.agents import create_agent
from langchain.agents.middleware import SummarizationMiddleware
from langgraph.checkpoint.memory import InMemorySaver
from openai import OpenAI

from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from langchain.agents.middleware import SummarizationMiddleware
from langgraph.checkpoint.memory import InMemorySaver
from langchain_core.tools import tool
from docx import Document
from dotenv import load_dotenv

import difflib
import os


from openai import OpenAI

client = OpenAI(
  api_key=api_key
)
OPENAI_API_KEY = api_key

load_dotenv()

api_key = os.getenv("API_KEY")

class RAGChatbot:
    def __init__(self):
        self.message_count = 0

        # Directory with .docx templates
        self.doc_root = r"./data/"

        self.current_doc: Document | None = None
        self.current_doc_path: str | None = None
        self.current_doc_name: str | None = None

        conn = iris.connect("cuda1.ubmi.feec.vutbr.cz", 32782, "DEMO", "_SYSTEM", "ISCDEMO")
        self.cursor = conn.cursor()
        self.conn = conn

        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.agent = self.create_agent()
        self.config = {"configurable": {"thread_id": "1"}}
        self.table_name = "VectorSearch.ORGstruct"

    # ------------- MODELS / VECTOR SEARCH ------------- #

    def get_embedding_model(self):
        return self.embedding_model
    
    def create_table(self):
        create_table_query = f"""
        CREATE TABLE IF NOT EXISTS {self.table_name} (
        id INTEGER,
        filename LONGVARCHAR,
        content LONGVARCHAR,
        vector VECTOR(DOUBLE, 384)
        )
        """

        self.cursor.execute(create_table_query)
        # self.conn.commit()
        # self.conn.close()

    
    def vectorize_content(self, df):
        embeddings = self.get_embedding_model().encode(df['content'], normalize_embeddings=True, show_progress_bar=True)
        return embeddings

    def vectorize_filename(self, df):
        embeddings = self.get_embedding_model().encode(df['filename'], normalize_embeddings=True, show_progress_bar=True)
        return embeddings

    def insert_chunks_into_table(self, chunks: pd.DataFrame):

        chunks = pd.DataFrame(chunks)

        self.create_table()

        embeddings = self.vectorize_content(chunks)
        chunks["vector"] = embeddings.tolist()

        # IMPORTANT: convert vector (list) → string
        chunks["vector"] = chunks["vector"].apply(lambda v: str(v))

        insert_query = f"""
        INSERT INTO {self.table_name} (id, filename, content, vector)
        VALUES (?, ?, ?, TO_VECTOR(?))
        """

        rows_list = chunks[["id", "filename", "content", "vector"]].values.tolist()
        self.cursor.executemany(insert_query, rows_list)

        # self.conn.commit()
        # self.conn.close()
        print("Insertions done!")

    def vector_search(self, user_prompt: str):
        search_vector = self.embedding_model.encode(
            user_prompt,
            normalize_embeddings=False,
            show_progress_bar=False,
        ).tolist()

        search_sql = """
            SELECT TOP 5 filename, content
            FROM VectorSearch.ORGstruct
            ORDER BY VECTOR_COSINE(vector, TO_VECTOR(?,DOUBLE)) DESC
        """
        self.cursor.execute(search_sql, [str(search_vector)])
        results = self.cursor.fetchall()
        results = [f"Text z dokumentu {x} -> {y}" for x, y in results]
        return results

    # ------------- WORD DOCUMENT HELPERS ------------- #

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

    def _replace_placeholder_in_doc(self, doc: Document, placeholder: str, value: str):
        for paragraph in doc.paragraphs:
            self._replace_in_paragraph(paragraph, placeholder, value)
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    for paragraph in cell.paragraphs:
                        self._replace_in_paragraph(paragraph, placeholder, value)

    def _doc_to_text(self, doc: Document, max_chars: int = 4000) -> str:
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

    def _find_best_matching_doc(self, query: str) -> tuple[str | None, str]:
        """Return (filename, info) for the best match to query among .docx files."""
        files = self._list_docx_files()
        if not files:
            return None, "V adresáři šablon nejsou žádné .docx soubory."

        q = query.strip().lower()
        if not q:
            return None, "Dotaz je prázdný."

        # Exact match
        for f in files:
            if f.lower() == q:
                return f, f"Použit přesný název souboru '{f}'."

        # Substring match
        contains = [f for f in files if q in f.lower()]
        if len(contains) == 1:
            return contains[0], f"Nalezeno podle podřetězce v názvu souboru '{contains[0]}'."
        if len(contains) > 1:
            # Pick first, mention alternatives
            main = contains[0]
            alts = ", ".join(contains[1:])
            return main, (
                f"Nalezeno více souborů podle popisu. Vybrán '{main}'. "
                f"Další možné: {alts}"
            )

        # Fuzzy match
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


    def create_agent(self):
        checkpointer = InMemorySaver()

        llm = ChatOpenAI(
            model="gpt-5.1",
            temperature=0.1,
            api_key=OPENAI_API_KEY,
        )

        @tool
        def load_word_document(query: str) -> str:
            """
            Načti šablonu dokumentu podle názvu nebo slovního popisu
            (např. 'Žádost o dovolenou', 'stížnost na dokumentaci').
            """
            filename, info = self._find_best_matching_doc(query)
            if not filename:
                return info

            path = os.path.join(self.doc_root, filename)
            try:
                doc = Document(path)
            except Exception as e:
                return f"Dokument '{filename}' se nepodařilo načíst: {e}"

            self.current_doc = doc
            self.current_doc_path = path
            self.current_doc_name = filename

            preview = self._doc_to_text(doc, max_chars=1500)
            return (
                f"{info}\n\n"
                f"Dokument '{filename}' byl načten a je připraven k vyplňování.\n\n"
                f"Náhled obsahu:\n{preview}"
            )

        @tool
        def show_current_document() -> str:
            """
            Vrať text aktuálně načteného dokumentu.
            """
            if self.current_doc is None:
                return "Momentálně není načten žádný dokument. Použij nejdřív 'load_word_document'."
            text = self._doc_to_text(self.current_doc, max_chars=4000)
            return (
                f"Aktuálně načtený dokument: {self.current_doc_name}\n\n"
                f"Text dokumentu:\n{text}"
            )

        @tool
        def fill_placeholder(field_name: str, value: str) -> str:
            """
            Vyplň zástupný text ve tvaru {{FIELD_NAME}} v načteném dokumentu.
            """
            if self.current_doc is None or self.current_doc_path is None:
                return "Není načten žádný dokument. Použij nejdřív 'load_word_document'."

            placeholder = f"{{{{{field_name}}}}}"
            self._replace_placeholder_in_doc(self.current_doc, placeholder, value)
            self.current_doc.save(self.current_doc_path)

            return (
                f"Pole '{field_name}' bylo vyplněno hodnotou '{value}'. "
                f"Aktualizovaný dokument je uložen jako {self.current_doc_name}."
            )

        @tool
        def save_document_as(new_filename: str) -> str:
            """
            Ulož aktuálně načtený dokument pod novým názvem (.docx).
            """
            if self.current_doc is None:
                return "Není načten žádný dokument, není co ukládat."

            if not new_filename.lower().endswith(".docx"):
                new_filename = new_filename + ".docx"

            new_path = os.path.join(self.doc_root, new_filename)
            self.current_doc.save(new_path)
            return (
                f"Aktualizovaný dokument byl uložen jako '{new_filename}'. "
                f"Cesta: {new_path}"
            )

        tools = [
            load_word_document,
            show_current_document,
            fill_placeholder,
            save_document_as,
        ]

        agent = create_agent(
            model=llm,
            tools=tools,
            middleware=[
                SummarizationMiddleware(
                    model=llm,
                    trigger=("tokens", 4000),
                    keep=("messages", 20),
                ),
            ],
            checkpointer=checkpointer,
        )
        return agent


    def get_prompt(self):
        return input(
            "\n\nHi, I'm a chatbot used for searching a patient's medical history. "
            "How can I help you today?\n\n - User: "
        )

    def validation(self, result):
        return result

    def return_response(self, query=None):
        if (query is None):
            query = self.get_prompt()
        results = self.vector_search(query)



        system_prompt = """
Základy:
    1. Jsi užitečný asistent, chatbot fungující v nemocnici.
    2. Tvým posláním je odpovídat na dotazy zaměstnanců týkající se jejich práce a provádět je organizační strukturou nemocnice a administrativními procesy.
    3. Poskytuj odpovědi přesně podle interních dokumentů, které jsou dostupné prostřednictvím RAG (retrieved context).
    4. Uživatel má být bezpečně a krok za krokem proveden procesem či postupem tak, aby splnil veškeré požadavky směrnic a nic nevynechal.

Tvůj způsob práce:
    1. Odpovídej v jazyku, jakým mluví uživatel.
    2. Ptej se uživatele na jeden konkrétní krok procesu. Nikdy nepřeskakuj více kroků najednou.
    3. Vysvětluj pouze to, co uživatel potřebuje vědět pro aktuální krok.
    4. Pokud je dotaz faktický, vždy nejprve vyhledej informace v dokumentech RAG.
    5. Neodpovídej věci, které nejsou v podkladech, raději uveď, že nejsou uvedeny, nebo navrhni, kde se hledají.
    6. Pokud uživatel neví, co má dělat, navrhni další krok.
    7. Vyhýbej se nepodloženému nebo podlézavému lichocení
    8. Zachovej profesionalitu a střízlivou upřímnost

Co nesmíš dělat:
    1. Nevymýšlej si pravidla, která nejsou ve zdrojových dokumentech.
    2. Nevytvářej interní postupy, pokud nejsou výslovně uvedené.
    3. Nehádej hodnoty (např. sazby stravného).

Práce s dokumenty:
    - Pokud chce uživatel vyplnit formulář/dokument:
    1. Rozhodni, jaký dokument potřebuje, podle dotazu a RAG kontextu.
    2. Zavolej nástroj 'load_word_document' a jako argument použij:
        - buď přesný název souboru (např. 'Formular_XY.docx'),
        - nebo slovní popis (např. 'žádost o dovolenou', 'stížnost na dokumentaci').
    3. Pokud potřebuješ znát strukturu, použij 'show_current_document'.
    4. U každé kategorie údajů (např údaje o cestě či způsob dopravy) si vyžádej údaje o všech podůdajích od uživatele a použij 'fill_placeholder' s názvem pole (bez složených závorek) a hodnotou.
    5. Po dokončení použij 'save_document_as' a pojmenuj soubor podle kontextu.

Pokud se uživatel dotazuje na nějaký proces v nemocnici (např. \"Chci si stěžovat na nedostatečnou dokumentaci k webové aplikaci vyvinuté v Centru Informatiky (CI)\"),
  1. Odpovídej jasně a požádej uživatele o upřesnění, pokud nemůžeš přesně určit proces, který je pro uživatele relevantní (v tomto případě proces dokumentace ze strany oddělení nezdravotnických aplikací, které je součástí CI).
  2. Pokud má uživatel podle předpisů více možností, jak dosáhnout svého cíle, popiš dostupné možnosti a zeptej se uživatele, kterou si chce vybrat.
    - Pokud musí kontaktovat jiného zaměstnance, ale nemáš jeho kontaktní údaje, *jasně mu sděl, že je nemáš*.
    - Pokud musí kontaktovat jiného zaměstnance a ty máš jeho kontaktní údaje, poskytni mu tyto informace (jméno, telefonní číslo, e-mail).
  3. Při odpovídání *vždy* upřednostňuj organizační informace z dodaných dokumentů. Pokud tam informace není dostupná, *informuj o tom uživatele* a nic si nevymýšlej.
  4. Pokud nemáš informace o uživatelově dotazu nebo o tom, jak by měl uživatel v daném procesu postupovat, ale *máš* informace o tom, kde může uživatel získat kvalifikovanou pomoc, doporuč mu osoby, které má kontaktovat, a poskytni kontaktní informace (V tomto případě by měl uživatel kontaktovat oddělení nezdravotnických aplikací).
  5. Na konci své odpovědi odkazuj k dokumentům (text "Z dokumentu XYZ.docx", před ->), ze kterých jsi čerpal informace, pokud jsou relevantní. Vypiš je na konci odpovědi ve formátu: "Dále se můžete obrátit na dokument XYZ".
  6. Pokud uživatel poprosí o pomoc s procesem, proveď ho tím několika kroky, které musí podniknout, aby dosáhl svého cíle.

"""




        context_msg = ""
        if results:
            joined = "\n".join(results)
            context_msg = (
                "Následuje kontext z nemocničních dokumentů. Při odpovědi se drž těchto informací a na konci odpovědi odkaž na příslušné dokumenty.\n\n"
                f"{joined}"
            )

        messages = [("system", system_prompt)]
        if context_msg:
            messages.append(("system", context_msg))
        messages.append(("user", query))

        response = self.agent.invoke({"messages": messages}, self.config)
        self.message_count += 1
        validated_response = self.validation(response)

        return validated_response["messages"][-1].content
