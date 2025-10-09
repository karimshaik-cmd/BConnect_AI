# ingest_pdf.py

from typing import List
import os
import logging

from langchain_community.document_loaders import PyPDFLoader, UnstructuredExcelLoader, UnstructuredWordDocumentLoader
from langchain_chroma import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter

logger = logging.getLogger(__name__)

def ingest_documents_to_chroma(file_paths: List[str], vectorstore: Chroma):
    """
    Loads, splits, and adds documents (PDF, Excel, Word) to the specified Chroma vector store.
    """
    all_documents = []

    for file_path in file_paths:
        try:
            logger.info(f"Loading document: {os.path.basename(file_path)}")
            file_ext = os.path.splitext(file_path)[1].lower()

            if file_ext == '.pdf':
                loader = PyPDFLoader(file_path)
            elif file_ext in ['.xls', '.xlsx']:
                loader = UnstructuredExcelLoader(file_path)
            elif file_ext in ['.doc', '.docx']:
                loader = UnstructuredWordDocumentLoader(file_path)
            else:
                logger.warning(f"Unsupported file type: {file_ext} for {file_path}")
                continue

            documents = loader.load()
            all_documents.extend(documents)
        except Exception as e:
            logger.error(f"Failed to load document {file_path}: {e}")
            continue

    if not all_documents:
        logger.warning("No documents were loaded for ingestion.")
        return

    # Split documents
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len
    )
    
    texts = text_splitter.split_documents(all_documents)
    logger.info(f"Split {len(all_documents)} pages into {len(texts)} chunks.")

    # Add to vector store
    try:
        # This will add the new documents to the existing collection
        vectorstore.add_documents(texts)
        logger.info(f"Successfully added {len(texts)} documents to ChromaDB collection: {vectorstore._collection.name}")
    except Exception as e:
        logger.error(f"Failed to add documents to ChromaDB: {e}")

if __name__ == '__main__':
    # This block can be used for local testing
    print("Run `server.py` to use the ingestion functionality via API endpoints.")