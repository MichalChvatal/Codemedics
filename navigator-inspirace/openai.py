import os
import openai


# API pro openai verze 1.0.0 +
def chat_with_GPT(messages, model="gpt-4"):
    try:
        # Nastavte svůj OpenAI API klíč
        openai.api_key = os.getenv("OPENAI_API_KEY")
        # Volání OpenAI API
        client = openai.OpenAI()
        response = client.chat.completions.create(
            model=model,
            messages=messages
        )
        # Extrakce odpovědi
        response_dict = response.model_dump()    # <--- convert to dictionary
        return response_dict["choices"][0]["message"]["content"]
    except Exception as e:
        return f"An Error occured: {str(e)}"

# Ukázkový dotaz
'''
potřebuji z tohoto textu "jméno Honza Novák, telefon 420123322, město Nový Jičín, země Česká republika a email honza.novak@gmail.com" vyrobit json objekt. jako json schéma použij toto: {
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "name": {
      "type": "string",
      "description": "Person full name"
    },
    "city": {
      "type": "string",
      "format": "string",
      "description": "Person's location"
    },
    "country": {
      "type": "string",
      "format": "string",
      "description": "Person's country of residence"
    },
    "phone": {
      "type": "string",
      "pattern": "^\\+?[0-9]+$",
      "description": "Phone with international code"
    },
    "email": {
      "type": "string",
      "format": "email",
      "description": "Person email"
    }
  },
  "required": ["name", "city", "country", "phone", "email"],
  "additionalProperties": false
}

vrať pouze json objekt
'''