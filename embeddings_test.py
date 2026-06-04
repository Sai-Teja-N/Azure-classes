import os
import chromadb
from openai import AzureOpenAI

# ==========================================
# 1. Azure OpenAI Configuration
# ==========================================
# These values are found in your Azure AI Studio / Foundry portal
AZURE_ENDPOINT = ""
AZURE_API_KEY = ""
AZURE_API_VERSION = "2024-02-01" 
# This is the "Deployment Name" you chose when deploying the model
DEPLOYMENT_NAME = "text-embedding-3-small" 

client = AzureOpenAI(
    azure_endpoint=AZURE_ENDPOINT,
    api_key=AZURE_API_KEY,
    api_version=AZURE_API_VERSION
)

# ==========================================
# 2. Initialize ChromaDB (Local Persistence)
# ==========================================
db_path = "./azure_vectordb"
chroma_client = chromadb.PersistentClient(path=db_path)
collection = chroma_client.get_or_create_collection(name="azure_knowledge_base")

# ==========================================
# 3. Data Preparation
# ==========================================
documents = [
    "The Azure cloud platform has over 200 physical data centers.",
    "Quantum computing uses qubits to perform complex calculations.",
    "Espresso is made by forcing hot water through finely-ground coffee."
]
document_ids = ["azure_1", "quantum_1", "coffee_1"]

# ==========================================
# 4. Generate Embeddings via Azure
# ==========================================
print(f"Requesting embeddings from Azure deployment: {DEPLOYMENT_NAME}...")

response = client.embeddings.create(
    input=documents,
    model=DEPLOYMENT_NAME # On Azure, 'model' refers to your Deployment Name
)
#print(response)

# Extract vectors
embeddings = [item.embedding for item in response.data]

# ==========================================
# 5. Store and Query
# ==========================================
collection.add(
    embeddings=embeddings,
    documents=documents,
    ids=document_ids
)

print(f"Stored {collection.count()} documents.")

# --- Test Query ---
query_text = " coffee."
query_emb = client.embeddings.create(input=[query_text], model=DEPLOYMENT_NAME).data[0].embedding

results = collection.query(query_embeddings=[query_emb], n_results=1)

print(f"\nQuery: {query_text}")
print(f"Top Match: {results['documents'][0][0]}")

