# TODO: Integrate ChatEngine into server.py

## Completed Tasks
- [x] Import ChatEngine in server.py
- [x] Create EmbeddingManager class to wrap Chroma vectorstores for ChatEngine compatibility
- [x] Initialize EmbeddingManager and ChatEngine instances
- [x] Modify ask_question endpoint to use ChatEngine.generate_response with fallback to LLM
- [x] Pass RAG context and conversation history to ChatEngine
- [x] Simplify vectorstore selection logic

## Followup Steps
- [ ] Test end-to-end integration
- [ ] Verify API troubleshooting mode detection
- [ ] Ensure conversation history is properly passed
- [ ] Test fallback to LLM when ChatEngine is not available
- [ ] Validate RAG context retrieval for different query types (banking, support, excel)
- [ ] Check error handling and logging
