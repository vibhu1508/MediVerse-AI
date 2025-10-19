import chromadb
import os
from dotenv import load_dotenv

load_dotenv()

chromadb_key = os.getenv("CHROMA_API_KEY")
tenant_key = os.getenv("CHROMA_TENANT")
database_name = os.getenv("CHROMA_DATABASE")

client = chromadb.CloudClient(
  api_key=chromadb_key,
  tenant=tenant_key,
  database=database_name
)

def get_vector_store_collection(collection_name):
    """
    Retrieve a ChromaDB collection by name.
    """
    collection = client.get_collection(name=collection_name)
    return collection
# Usage
collection_name = "Test"
collection = get_vector_store_collection(collection_name)
print(f"Retrieved collection: {collection.name}")
