# ingest_errors.py

from typing import List, Dict, Any
import json
import os
import logging

from langchain.schema import Document
from langchain_chroma import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter

logger = logging.getLogger(__name__)

def ingest_json_to_chroma(json_paths: List[str], vectorstore: Chroma):
    """
    Loads, processes, and adds JSON error documents to the specified Chroma vector store.
    Assumes JSON files contain a list of objects with 'error_title', 'error_description', and 'solution'.
    """
    all_documents = []

    for json_path in json_paths:
        try:
            logger.info(f"Processing error file: {os.path.basename(json_path)}")
            with open(json_path, 'r') as f:
                data: List[Dict[str, Any]] = json.load(f)

            for item in data:
                # Create a comprehensive page_content for RAG
                content = (
                    f"Error Title: {item.get('error_title', 'N/A')}\n"
                    f"Description: {item.get('error_description', 'N/A')}\n"
                    f"Solution Steps: {item.get('solution', 'N/A')}"
                )
                
                # Metadata to track source
                metadata = {"source": os.path.basename(json_path), "title": item.get('error_title')}

                all_documents.append(Document(page_content=content, metadata=metadata))
                
        except json.JSONDecodeError:
            logger.error(f"Failed to parse JSON file: {json_path}. Skipping.")
            continue
        except Exception as e:
            logger.error(f"Failed to process error file {json_path}: {e}")
            continue

    if not all_documents:
        logger.warning("No documents were loaded for ingestion from JSON files.")
        return

    # Split documents (optional for structured data, but good practice for RAG)
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=100,
        length_function=len
    )
    
    texts = text_splitter.split_documents(all_documents)
    logger.info(f"Split {len(all_documents)} records into {len(texts)} chunks.")

    # Add to vector store
    try:
        vectorstore.add_documents(texts)
        logger.info(f"Successfully added {len(texts)} error documents to ChromaDB collection: {vectorstore._collection.name}")
    except Exception as e:
        logger.error(f"Failed to add error documents to ChromaDB: {e}")

if __name__ == '__main__':
    print("Run `server.py` to use the ingestion functionality via API endpoints.")