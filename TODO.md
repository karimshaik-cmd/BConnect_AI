# Implementation Plan for IBM Cert Tool / ibmb-chatbot Features

## Backend Modifications
- [ ] Create backend/config/settings.py with Groq API config
- [ ] Add Groq LLM integration to backend/server.py
- [ ] Implement specialized SYSTEM_PROMPT for API troubleshooting
- [ ] Add error code extraction logic (regex patterns for IBM\d{3,4})
- [ ] Enhance RAG with multi-step search (error docs + API specs)
- [ ] Add new prompt template for API error analysis
- [ ] Modify determine_prompt() to detect API troubleshooting queries
- [ ] Update backend/requirements.txt to include groq package

## Vector Store Enhancements
- [ ] Enhance backend/ingest_pdf.py for API specs processing
- [ ] Enhance backend/ingest_errors.py for error code indexing
- [ ] Add separate collections for error_docs and api_specs

## Frontend Adaptations
- [ ] Update frontend/src/BankingChat.jsx for API troubleshooting mode
- [ ] Add file type detection for error docs vs API specs
- [ ] Update UI labels to support "API Troubleshooting" mode
- [ ] Add error code highlighting in responses

## Testing and Validation
- [ ] Test Groq API integration
- [ ] Validate error code extraction patterns
- [ ] Test multi-step RAG performance
- [ ] UI testing for new features
