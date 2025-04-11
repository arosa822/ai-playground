from flask import Flask, request, jsonify
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch
# for the chunker
from pathlib import Path
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np

app = Flask(__name__)

# Load the model
model_name = "ZeroXClem/Llama-3.1-8B-Athena-Apollo-exp"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name, torch_dtype="auto", device_map="auto")
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



@app.rout('/debug', methods=['GET'])
def print_var():
    return jsonify({"var": "1"})

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

    query = "What are the main errors in the test log?"
    retrieved_context = "\n".join(retrieve_chunks(query, index, chunks))

    prompt = f"""You are a helpful assistant reading test logs.

    Context:
    {retrieved_context}

    Question: {query}
    Answer:"""


    # Process the file content with the model
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    outputs = model.generate(**inputs, max_new_tokens=300)
    response_text = tokenizer.decode(outputs[0], skip_special_tokens=True)

    return jsonify({"response": response_text})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
