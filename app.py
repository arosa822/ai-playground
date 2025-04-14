from flask import Flask, request, jsonify
import requests
# for the chunker
from pathlib import Path
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np

app = Flask(__name__)

MODEL_SERVICE_URL = "http://localhost:5001/generate"
embedder = SentenceTransformer("all-MiniLM-L6-v2")

def chunk_data(log_text):
    chunk_size = 500 # characters or adjust based on token estimates
    chunks = [log_text[i:i+chunk_size] for i in range(0, len(log_text), chunk_size)]

    return chunks

def create_index(chunks):
    embeddings = embedder.encode(chunks)
    # Create FAISS index
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(np.array(embeddings))

    return index

# define a query + retrieve relavant chunks
def retrieve_chunks(query, index, chunks, top_k=3):
    query_embedding = embedder.encode([query])
    distances, indices = index.search(query_embedding, top_k)
    return [chunks[i] for i in indices[0]]



@app.route('/debug', methods=['GET'])
def print_var():
    return jsonify({"var": "2"})

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy"}), 200

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    # Read the file content
    file_content = file.read().decode('utf-8')

    chunks = chunk_data(file_content)
    index = create_index(chunks)

    query = "What is the general state of the tests?, are there any authentication issues?"
    retrieved_context = "\n".join(retrieve_chunks(query, index, chunks))

    prompt = f"""You are a helpful assistant reading test logs. Give me a percentage of tests that have passed, failed and errored out. 

    Context:
    {retrieved_context}

    Question: {query}
    Answer:"""


    # Send the prompt to the model service
    response = requests.post(MODEL_SERVICE_URL, json={"prompt": prompt})
    response_text = response.json().get("response", "")

    return jsonify({"response": response_text})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
