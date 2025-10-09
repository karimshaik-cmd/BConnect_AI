# TODO: Update Banking Chatbot to Support Excel and Word Document Uploads

## Tasks
- [x] Update backend/requirements.txt: Add unstructured[local-inference] for Excel and Word loaders
- [x] Update backend/ingest_pdf.py: Extend ingest_pdfs_to_chroma to handle .xls, .xlsx, .doc, .docx
- [x] Update backend/server.py: Modify /upload-pdfs endpoint to accept Excel and Word files
- [x] Update frontend/src/BankingChat.jsx: Update accept attribute for banking upload
- [x] Install new dependencies
- [x] Test uploads for PDF, Excel, Word files
- [x] Verify ingestion and vector store reloading
- [x] Ensure no impact on JSON error uploads
