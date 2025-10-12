from typing import List
import os
import logging
import json
import pandas as pd
from langchain.schema import Document
from langchain_community.document_loaders import (
    PyPDFLoader,
    UnstructuredExcelLoader,
    UnstructuredWordDocumentLoader,
    TextLoader,
    CSVLoader
)
from langchain_chroma import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter

logger = logging.getLogger(__name__)

def get_field_path(row: pd.Series, max_level: int = 6) -> str:
    """
    Calculates the hierarchical path (e.g., Head.ver, Merchant.Address.city) 
    using the Level 1, Level 2, ... columns.
    """
    path_parts = []
    # Loop from Level 1 up to max_level (e.g., Level 6)
    for i in range(1, max_level + 1):
        level_col = f'Level {i}'
        if level_col in row.index and str(row[level_col]).strip():
            # Clean up the part by removing commas/spaces and prepending with the previous path
            part = str(row[level_col]).strip()
            path_parts.append(part)

    # The first element is often a source detail, we only want the API field path.
    # The actual API field path starts from the first non-empty Level column.
    # We join them with a dot.
    return ".".join(path_parts)


def dataframe_to_natural_text(df: pd.DataFrame, sheet_name: str, file_path: str) -> List[Document]:
    """
    Converts a pandas DataFrame into natural-language and structured text for LLM ingestion.
    """
    documents = []
    df = df.fillna("").astype(str)

    if len(df.columns) == 0:
        return documents

    # ✅ Ensure column names are stripped of leading/trailing spaces and special chars
    df.columns = df.columns.str.strip().str.replace(r'[^\w\s]', '', regex=True)

    columns = list(df.columns)
    
    # Identify key columns for the request specification format
    level_cols = [col for col in columns if col.startswith('Level')]
    
    # 🔹 1. Row-level content for fine-grained embedding
    for i, row in df.iterrows():
        # Get the full hierarchical path for the row
        field_path = get_field_path(row, max_level=6) 
        
        # Skip rows that don't define a field (like empty separator rows)
        if not field_path: 
             continue

        structured_json = {col: row[col] for col in columns if str(row[col]).strip() != ""}
        json_text = json.dumps(structured_json, ensure_ascii=False, indent=2)
        
        # Add the field path to the summary for RAG
        row_summary = f"Field Path: {field_path}, " + ", ".join([f"{col}: {row[col]}" for col in columns if str(row[col]).strip() != "" and not col.startswith('Level')])
        if not row_summary:
            continue

        text = (
            f"Sheet: {sheet_name}, Field Path: {field_path}, Source: {os.path.basename(file_path)}\n"
            f"Structured JSON for {field_path}:\n{json_text}\n\n"
            f"Natural Summary: {row_summary}"
        )

        metadata = {
            "source": file_path,
            "sheet": sheet_name,
            "row_number": i + 1,
            "file_type": "excel",
            "field_path": field_path, # <-- New key
            "columns": ", ".join(columns)
        }
        documents.append(Document(page_content=text, metadata=metadata))

    # 🔹 2. Add full-sheet markdown for structure recognition (kept for completeness)
    if len(df) > 0:
        # We don't want the LLM to hallucinate from the raw Markdown, 
        # so we will use the raw text for the full sheet context
        markdown_table = df.to_markdown(index=False)
        sheet_text = (
            f"📄 Full Sheet Context: {sheet_name}\n"
            f"Columns: {', '.join(columns)}\n\n"
            f"{markdown_table}"
        )
        metadata = {
            "source": file_path,
            "sheet": sheet_name,
            "type": "full_sheet",
            "file_type": "excel",
            "columns": ", ".join(columns)
        }
        documents.append(Document(page_content=sheet_text, metadata=metadata))

    return documents

# ... (rest of the ingest_pdf.py code) ...

def load_document(file_path: str) -> List[Document]:
    """
    Dynamically loads documents from multiple formats (PDF, Excel, Word, CSV, TXT).
    Automatically converts structured data into readable, LLM-friendly text.
    """
    ext = os.path.splitext(file_path)[1].lower()
    documents = []

    try:
        if ext == ".pdf":
            loader = PyPDFLoader(file_path)
            documents = loader.load()

        elif ext in [".xls", ".xlsx"]:
            try:
                excel_data = pd.read_excel(file_path, sheet_name=None)
                for sheet_name, df in excel_data.items():
                    documents.extend(dataframe_to_natural_text(df, sheet_name, file_path))
            except Exception as e:
                logger.warning(f"Pandas failed for {file_path}, fallback to UnstructuredExcelLoader: {e}")
                loader = UnstructuredExcelLoader(file_path)
                documents = loader.load()

        elif ext in [".doc", ".docx"]:
            loader = UnstructuredWordDocumentLoader(file_path)
            documents = loader.load()

        elif ext == ".csv":
            try:
                df = pd.read_csv(file_path)
                documents.extend(dataframe_to_natural_text(df, "CSV", file_path))
            except Exception as e:
                logger.warning(f"Pandas failed for CSV {file_path}, fallback to CSVLoader: {e}")
                loader = CSVLoader(file_path)
                documents = loader.load()

        elif ext == ".txt":
            loader = TextLoader(file_path)
            documents = loader.load()

        else:
            logger.warning(f"Unsupported file type: {ext}")

    except Exception as e:
        logger.error(f"❌ Error loading {file_path}: {e}")

    return documents


def ingest_documents_to_chroma(file_paths: List[str], vectorstore: Chroma):
    """
    Loads, splits, and adds documents to the given Chroma vectorstore.
    Works for PDF, Excel, Word, CSV, TXT — structured for natural Q&A.
    """
    all_documents = []

    for path in file_paths:
        logger.info(f"📥 Loading document: {os.path.basename(path)}")
        docs = load_document(path)
        all_documents.extend(docs)

    if not all_documents:
        logger.warning("⚠️ No documents were successfully loaded.")
        return {"status": "empty"}

    # 🔹 Intelligent text splitter
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        separators=["\n\n", "\n", " ", ""]
    )
    split_docs = splitter.split_documents(all_documents)

    logger.info(f"📄 Split {len(all_documents)} docs into {len(split_docs)} chunks")

    try:
        vectorstore.add_documents(split_docs)
        logger.info(f"✅ Successfully added {len(split_docs)} chunks to Chroma collection: {vectorstore._collection.name}")
        return {
            "status": "success",
            "files_ingested": len(file_paths),
            "chunks_added": len(split_docs)
        }
    except Exception as e:
        logger.exception(f"❌ Error adding docs to Chroma: {e}")
        return {"status": "failed", "error": str(e)}


if __name__ == "__main__":
    print("Run `server.py` to use ingestion through API endpoints.")


# # ingest_pdf.py
# from typing import List
# import os
# import logging
# import pandas as pd
# from langchain.schema import Document
# from langchain_community.document_loaders import (
#     PyPDFLoader,
#     UnstructuredExcelLoader,
#     UnstructuredWordDocumentLoader,
#     TextLoader,
#     CSVLoader
# )
# from langchain_chroma import Chroma
# from langchain.text_splitter import RecursiveCharacterTextSplitter

# logger = logging.getLogger(__name__)


# def dataframe_to_natural_text(df: pd.DataFrame, sheet_name: str, file_path: str) -> List[Document]:
#     """
#     Converts a pandas DataFrame into natural language text blocks for LLM understanding.
#     Example output: "Field: ver, Sheet: API_Fields, Row 1: ver: ver, Required/Optional: Required, ..."
#     """
#     documents = []
#     df = df.fillna("")
#     if len(df.columns) > 0:
#         key_col = df.columns[0]
#         for i, row in df.iterrows():
#             row_content = ", ".join([f"{col}: {row[col]}" for col in df.columns if str(row[col]).strip() != ""])
#             if not row_content:
#                 continue
#             text = f"{key_col}: {row[key_col]}, Sheet: {sheet_name}, Row {i + 1}: {row_content}"
#             metadata = {
#                 "source": file_path,
#                 "sheet": sheet_name,
#                 "row_number": i + 1,
#                 "file_type": "excel"
#             }
#             documents.append(Document(page_content=text, metadata=metadata))
#     # Add full sheet summary
#     if len(df) > 0:
#         markdown_table = df.to_markdown(index=False)
#         sheet_text = f"Full Sheet: {sheet_name}\n{markdown_table}"
#         metadata = {
#             "source": file_path,
#             "sheet": sheet_name,
#             "type": "full_sheet",
#             "file_type": "excel"
#         }
#         documents.append(Document(page_content=sheet_text, metadata=metadata))
#     return documents


# def load_document(file_path: str) -> List[Document]:
#     """
#     Dynamically loads documents from multiple formats (PDF, Excel, Word, CSV, TXT).
#     Automatically converts structured data into readable text.
#     """
#     ext = os.path.splitext(file_path)[1].lower()
#     documents = []

#     try:
#         if ext == ".pdf":
#             loader = PyPDFLoader(file_path)
#             documents = loader.load()

#         elif ext in [".xls", ".xlsx"]:
#             try:
#                 excel_data = pd.read_excel(file_path, sheet_name=None)
#                 for sheet_name, df in excel_data.items():
#                     documents.extend(dataframe_to_natural_text(df, sheet_name, file_path))
#             except Exception as e:
#                 logger.warning(f"Pandas failed for {file_path}, fallback to UnstructuredExcelLoader: {e}")
#                 loader = UnstructuredExcelLoader(file_path)
#                 documents = loader.load()

#         elif ext in [".doc", ".docx"]:
#             loader = UnstructuredWordDocumentLoader(file_path)
#             documents = loader.load()

#         elif ext == ".csv":
#             try:
#                 df = pd.read_csv(file_path)
#                 documents.extend(dataframe_to_natural_text(df, "Sheet1", file_path))
#             except Exception as e:
#                 logger.warning(f"Pandas failed for CSV {file_path}, fallback to CSVLoader: {e}")
#                 loader = CSVLoader(file_path)
#                 documents = loader.load()

#         elif ext == ".txt":
#             loader = TextLoader(file_path)
#             documents = loader.load()

#         else:
#             logger.warning(f"Unsupported file type: {ext}")

#     except Exception as e:
#         logger.error(f"Error loading {file_path}: {e}")

#     return documents


# def ingest_documents_to_chroma(file_paths: List[str], vectorstore: Chroma):
#     """
#     Loads, splits, and adds documents to the given Chroma vectorstore.
#     Works for PDF, Excel, Word, CSV, TXT — automatically structured for natural language.
#     """
#     all_documents = []

#     for path in file_paths:
#         logger.info(f"Loading: {os.path.basename(path)}")
#         docs = load_document(path)
#         all_documents.extend(docs)

#     if not all_documents:
#         logger.warning("⚠️ No documents were successfully loaded.")
#         return {"status": "empty"}

#     # Split into smaller text chunks for vector embeddings
#     splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
#     split_docs = splitter.split_documents(all_documents)

#     logger.info(f"📄 Split {len(all_documents)} docs into {len(split_docs)} chunks")

#     try:
#         vectorstore.add_documents(split_docs)
#         logger.info(f"✅ Added {len(split_docs)} chunks to Chroma collection: {vectorstore._collection.name}")
#         return {
#             "status": "success",
#             "files_ingested": len(file_paths),
#             "chunks_added": len(split_docs)
#         }
#     except Exception as e:
#         logger.exception(f"Error adding docs to Chroma: {e}")
#         return {"status": "failed", "error": str(e)}


# if __name__ == "__main__":
#     print("Run `server.py` to use ingestion through API endpoints.")
