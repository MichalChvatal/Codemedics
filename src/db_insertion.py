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

model = SentenceTransformer('all-MiniLM-L6-v2') 

def vectorize_content(content):
    embeddings = model.encode([content], normalize_embeddings=True, show_progress_bar=True)
    return embeddings


def insert_chunks(chunks):
    conn = iris.connect("localhost", 32782, "DEMO", "_SYSTEM", "ISCDEMO")
    cursor = conn.cursor()

    table_name = "VectorSearch.ORGstruct"

    rows_to_insert = []

    for chunk in chunks:
        print("the chunk is ", chunk)
        content = chunk["content"]
        filename = chunk["filename"]
        id = chunk["id"]

        # Vectorize properly
        embedding = vectorize_content(content)        # returns numpy array
        embedding_str = ",".join(map(str, embedding)) # convert to CSV string

        print("inserting chunk ", chunk)

        rows_to_insert.append([
            int(id),
            filename,
            content,
            embedding_str
        ])

    insert_query = f"""
        INSERT INTO {table_name} (id, filename, content, vector)
        VALUES (?, ?, ?, TO_VECTOR(?))
    """
    print("the insert query is ", insert_query)

    cursor.executemany(insert_query, rows_to_insert)
    conn.commit()
    conn.close()

    print(f"Inserted {len(rows_to_insert)} chunks.")

        