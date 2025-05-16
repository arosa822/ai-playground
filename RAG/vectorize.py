import faiss
import numpy as np
from typing import List, Dict
from log_parser import read_log_file
from sentence_transformers import SentenceTransformer

def create_faiss_index(dimension: int, index_type: str = 'Flat') -> faiss.Index:
    """
    Creates a FAISS index.

    Args:
        dimension (int): The dimensionality of the vectors.
        index_type (str, optional): The type of FAISS index to create.
            Defaults to 'Flat' (brute-force search).  Other options include
            'IVFFlat' for larger datasets and faster search (but requires training).

    Returns:
        faiss.Index: The created FAISS index.
    """
    index = faiss.index_factory(dimension, index_type)
    return index

def add_data_to_faiss_index(index: faiss.Index, vectors: List[List[float]], metadata: List[Dict]):
    """
    Adds vectors and metadata to a FAISS index.

    Args:
        index (faiss.Index): The FAISS index to add data to.
        vectors (List[List[float]]): A list of vectors (each vector is a list of floats).
        metadata (List[Dict]): A list of dictionaries, where each dictionary
            contains the metadata associated with the corresponding vector.
    """
    # Ensure that vectors are in a float32 numpy array
    vectors_np = np.array(vectors, dtype=np.float32)
    index.add(vectors_np)  # Add vectors to the index

    # Store metadata in a separate list, aligned with the vectors.
    index.metadata = metadata  # Custom attribute to store metadata.  FAISS doesn't directly store metadata.

def search_faiss_index(index: faiss.Index, query_vector: List[float], top_k: int = 5) -> (np.ndarray, np.ndarray):
    """
    Performs a similarity search in a FAISS index.

    Args:
        index (faiss.Index): The FAISS index to search.
        query_vector (List[float]): The query vector (list of floats).
        top_k (int, optional): The number of nearest neighbors to retrieve.
            Defaults to 5.

    Returns:
        tuple: A tuple containing:
            - np.ndarray: The distances to the top-k nearest neighbors.
            - np.ndarray: The indices of the top-k nearest neighbors in the index.
    """
    query_vector_np = np.array([query_vector], dtype=np.float32)
    distances, indices = index.search(query_vector_np, top_k)
    return distances, indices

def get_relevant_metadata(index: faiss.Index, indices: np.ndarray) -> List[Dict]:
    """
    Retrieves the metadata for the given indices from the FAISS index.

    Args:
        index (faiss.Index): The FAISS index.
        indices (np.ndarray): The indices of the items to retrieve metadata for.

    Returns:
        List[Dict]: A list of metadata dictionaries.
    """
    results = []
    if hasattr(index, "metadata"):
        for i in indices[0]:  # indices is a 2D array
            if 0 <= i < len(index.metadata):
                results.append(index.metadata[i])
            else:
                results.append({}) # Return empty dict if index is out of bounds
    return results

def extract_log_data_for_vector_db(parsed_logs: List[Dict]) -> List[Dict]:
    """
    Extracts relevant data from the parsed logs, formatting it for
    insertion into a vector database.  This creates the 'documents'
    that will be embedded.  Each document contains enough
    information for the LLM to provide context.

    Args:
        parsed_logs (list): A list of dictionaries representing parsed log entries.

    Returns:
        list: A list of dictionaries, where each dictionary is formatted as a
              document for the vector database.  Returns an empty list if no
              valid data is provided.
    """
    documents = []
    if not parsed_logs:
        return []

    for log_entry in parsed_logs:
        #  Create a single string with all the relevant information for the LLM
        #  Handle potential missing keys gracefully
        timestamp = log_entry.get('timestamp', 'N/A')
        test_name = log_entry.get('test_name', 'N/A')
        level = log_entry.get('level', 'N/A')
        message = log_entry.get('message', 'N/A')
        result = log_entry.get('result', 'N/A')
        test_summary = log_entry.get('test_summary', 'N/A')  # Get test summary
        warning_message = log_entry.get('warning_message', 'N/A') # Get warning message
        duration_message = log_entry.get('duration_message', 'N/A') # Get duration message
        stack_trace_line = log_entry.get('stack_trace_line', 'N/A') # Get stack trace line

        content = f"Timestamp: {timestamp}, Test Name: {test_name}, Level: {level}, Message: {message}, Result: {result}, Test Summary: {test_summary}, Warning: {warning_message}, Duration: {duration_message}, StackTrace: {stack_trace_line}"
        document = {
            "page_content": content,
            "metadata": {
                "timestamp": timestamp,
                "test_name": test_name,
                "level": level,
                "message": message,
                "result": result,
                "test_summary": test_summary,  # Include test summary
                "warning_message": warning_message, # Include warning message
                "duration_message": duration_message, # Include duration message
                "stack_trace_line": stack_trace_line
            },
        }
        documents.append(document)
    return documents

if __name__ == "__main__":
    # Example usage:
    # 1.  Load and parse log data (using the function from the previous step)
    log_file_path = 'sample_log.txt'
    parsed_logs = read_log_file(log_file_path)
    documents = extract_log_data_for_vector_db(parsed_logs)

    # 2.  Generate embeddings for the log data using a Sentence Transformer model.
    embedding_model = SentenceTransformer('all-mpnet-base-v2')  # Or any other suitable model
    log_embeddings = [embedding_model.encode(doc["page_content"]).tolist() for doc in documents]

    # 3. Create FAISS index and add the embeddings and metadata
    dimension = len(log_embeddings[0])  # Get the dimension of the embeddings
    faiss_index = create_faiss_index(dimension)
    add_data_to_faiss_index(faiss_index, log_embeddings, [doc["metadata"] for doc in documents])

    # 4. Perform a sample search
    query = "tell me how many tests passed/failed error?" # Added test summary to the query
    query_embedding = embedding_model.encode(query).tolist()
    distances, indices = search_faiss_index(faiss_index, query_embedding, top_k=5)

    # 5. Get the metadata for the retrieved indices
    results_metadata = get_relevant_metadata(faiss_index, indices)

    print("\nSearch Results:")
    for i, (distance, metadata) in enumerate(zip(distances[0], results_metadata)):
        print(f"\nResult {i + 1}: Distance = {distance}")
        print(f"  Metadata: {metadata}")