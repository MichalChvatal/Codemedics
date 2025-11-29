from flask import url_for
from sentence_transformers import SentenceTransformer

from .app import app

from .openai import chat_with_GPT

# Load a pre-trained sentence transformer model. This model's output vectors are of size 384
model = SentenceTransformer('all-MiniLM-L6-v2') 

def perform_search(payload):
    cursor = app.config["IRIS_CONNECTION"].cursor()
    try:
        # zavolame Vector Store Similarity Search
        # Convert search phrase into a vector
        search_vector = model.encode(payload["message"], normalize_embeddings=True).tolist() 
        # Define the SQL query with placeholders for the vector and limit
        
        # IRIS 2024.3+ requires specifying data type as second argument to TO_VECTOR() function
        sql = """
            SELECT TOP 1 menu_link, menu_ref, VECTOR_DOT_PRODUCT(prompt_vector, TO_VECTOR(?,DOUBLE)) score
            FROM Demo_App.NAVIGATOR 
            ORDER BY score DESC
        """

        # app.logger.info(str(search_vector))
        # Execute the query with the number of results and search vector as parameters
        cursor.execute(sql, [str(search_vector)])
        # Fetch all results
        results = cursor.fetchall()

        message = {}
        
        for row in results:
            message["message"] = payload["message"]
            app.logger.info("Vector Search Result: row = " + str(row))
            if float(row[2]) <0.5:
                message["reaction"] = "Sorry, I could not satisfy your request, please rephrase, or provide more details."                
            else:
                if row[0] == "LLM":
                    sql = "SELECT llm_context, prompt FROM Demo_App.LLM WHERE app_context = ?"
                    cursor.execute(sql, [payload["context"]])
                    llm_context, llm_prompt = cursor.fetchone()

                    prompt = construct_prompt(payload["message"],llm_prompt)

                    messages = [
                        {"role": "system", "content": llm_context}, 
                        {"role": "user", "content": prompt}
                    ]

                    #app.logger.info("*** ChatGPT prompt ***")
                    #app.logger.info(prompt)
                    answer = chat_with_GPT(messages)
        
                    app.logger.info("*** ChatGPT answer ***")
                    app.logger.info(answer)
                    message["rag"] = answer
                    message["reaction"] = "Sure, here you are."
                else:
                    # DK - rozsireni o samouceni - asi bude nutno predelat na verzi s javascriptem 
                    # misto odkazu aby se v javascriptu dal volat AJAX do IRIS
                    # ale je otazkou, zda je to vubec ve Flasku mozne
                    reaction = "Sure, try this &nbsp;<a href='" + url_for(row[0]) + "'>" + row[1] + "</a>"   
                    # (" + row[2] + ")"
                    message["reaction"] = reaction
                    # pro samouceni
                    message["menu_link"] = row[0]
                    message["menu_ref"] = row[1]
    except RuntimeError as e:
        message = {
                "message": payload["message"],
                "reaction": str(e)
                }
        app.logger.error(e)
    return message

def construct_prompt(*args) -> str:
    out= ""
    for arg in args:
        out = out + arg
    return out + " return pure JSON object, nothing else."