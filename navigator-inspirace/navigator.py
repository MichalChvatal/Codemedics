# naplni tabulku DEMO_APP.NAVIGATOR daty
import iris
import os, pandas as pd
from sentence_transformers import SentenceTransformer
import getpass


IRIS_CONNECTION_STRING = "localhost:1972/PYTHON"           # os.getenv("CONNECTION_STRING")

# Load the CSV file
df = pd.read_csv('./prompts.csv')

# Load a pre-trained sentence transformer model. This model's output vectors are of size 384
model = SentenceTransformer('all-MiniLM-L6-v2') 
# Generate embeddings for all descriptions at once. Batch processing makes it faster
embeddings = model.encode(df['prompt'].tolist(), normalize_embeddings=True)

# Add the embeddings to the DataFrame
df['prompt_vector'] = embeddings.tolist()

username = input("Username: ")
password = getpass.getpass("Password: ")

connect = iris.connect(IRIS_CONNECTION_STRING,username,password)
cursor = connect.cursor()
cursor.execute('CREATE TABLE IF NOT EXISTS Demo_App.NAVIGATOR (prompt VARCHAR(5000), \
        menu_link VARCHAR(250), menu_ref VARCHAR(250), prompt_vector VECTOR(DOUBLE,384))')

#resetuj data
sql = "DELETE FROM DEMO_APP.NAVIGATOR"
cursor.execute(sql)

# Seznam polozek pro vyplneni tabulky
sql = f"INSERT INTO DEMO_APP.NAVIGATOR (prompt, menu_link, menu_ref, prompt_vector) values (?,?,?, TO_VECTOR(?,DOUBLE))"

# Prepare the list of tuples (parameters for each row)
data = [
    (
        row['prompt'], 
        row['menu_link'], 
        row['menu_ref'],
        str(row['prompt_vector']) 
    )
    for index, row in df.iterrows()
]
cursor.executemany(sql, data)
print("Rows inserted: ", cursor.rowcount)
connect.commit()
connect.close()


