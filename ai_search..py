import os
from openai import AzureOpenAI
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizedQuery
# ==========================================
# 1. Configuration (Keep your AOAI, add Search)
# ==========================================
# Azure OpenAI Settings

AOAI_ENDPOINT = ""
AOAI_KEY = ""
AZURE_API_VERSION = "2024-02-01" 

AOAI_VERSION = "2024-02-01"
DEPLOYMENT_NAME = "text-embedding-3-small"

# Azure AI Search Settings
SEARCH_ENDPOINT = "t"
SEARCH_KEY = "
INDEX_NAME = "azure-knowledge-base"

# Clients
aoai_client = AzureOpenAI(azure_endpoint=AOAI_ENDPOINT, api_key=AOAI_KEY, api_version=AOAI_VERSION)
search_client = SearchClient(SEARCH_ENDPOINT, INDEX_NAME, AzureKeyCredential(SEARCH_KEY))

# ==========================================
# 2. Data Preparation & Vectorization
# ==========================================
documents = [
    "The Azure cloud platform has over 200 physical data centers.",
    "Quantum computing uses qubits to perform complex calculations.",
    "Espresso is made by forcing hot water through finely-ground coffee."
]
document_ids = ["1", "2", "3"]

# Generate Vectors
response = aoai_client.embeddings.create(input=documents, model=DEPLOYMENT_NAME)
embeddings = [item.embedding for item in response.data]

# ==========================================
# 3. Store in Azure AI Search (Replaces collection.add)
# ==========================================
upload_data = []
for i in range(len(documents)):
    upload_data.append({
        "id": document_ids[i],
        "content": documents[i],
        "content_vector": embeddings[i]
    })

search_client.upload_documents(documents=upload_data)
print(f"Uploaded {len(upload_data)} documents to Azure AI Search.")

# ==========================================
# 4. Query (Replaces collection.query)
# ==========================================
query_text = "coffee"
query_vector = aoai_client.embeddings.create(input=[query_text], model=DEPLOYMENT_NAME).data[0].embedding
results = search_client.search(  
    search_text=None, # Still None for pure vector search
    vector_queries=[
        VectorizedQuery(
            vector=query_vector, 
            k_nearest_neighbors=1, 
            fields="content_vector"
        )
    ],
    select=["content"]
)

for result in results:
    print(f"\nQuery: {query_text}")
    print(f"Top Match: {result['content']}")
