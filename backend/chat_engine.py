import re
import logging
from typing import List, Dict, Any, Optional
from groq import Groq
from langchain.schema import Document
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
try:
    from .config.settings import APP_CONFIG
except ImportError:
    from config.settings import APP_CONFIG

logger = logging.getLogger(__name__)

class ChatEngine:
    def __init__(self, embedding_manager=None):
        self.embedding_manager = embedding_manager
        self.groq_client = Groq(api_key=APP_CONFIG['GROQ_API_KEY'])

        # Enhanced error code patterns to match your format
        self.error_patterns = [
            r'\bIBM\d{3,4}\b',   # Pattern like IBM8082, IBM8017, etc.
            r'\b[A-Z]{3,5}\d{3,4}\b', # General pattern like ABCD123
            r'\bERR\d{3}\b',      # Pattern like ERR001
            r'\b[A-Z]{2}\-\d{3}\b', # Pattern like AB-001
        ]

        # Keywords that indicate API field-related issues
        self.api_field_keywords = [
            'field', 'parameter', 'attribute', 'element',
            'required', 'optional', 'mandatory', 'missing',
            'validation', 'format', 'type', 'data type',
            'reference id', 'transaction', 'request', 'response',
            'head', 'body', 'timestamp', 'correlation',
            # ... more keywords ...
            'not working', 'broken', 'invalid', 'incorrect', 'wrong',
            'timeout', 'rejected', 'denied', 'unauthorized', 'forbidden',
            'mismatch', 'duplicate', 'missing', 'null', 'empty'
        ]

    def extract_error_codes(self, query: str) -> List[str]:
        """Extract potential error codes from user query"""
        error_codes = []
        for pattern in self.error_patterns:
            matches = re.findall(pattern, query.upper())
            error_codes.extend(matches)

        # Remove duplicates while preserving order
        return list(dict.fromkeys(error_codes))

    def extract_api_terms_from_error(self, error_description: str) -> List[str]:
        """Extract API-related terms from error descriptions"""
        terms = []
        error_lower = error_description.lower()

        # Extract terms that appear in the error description
        for keyword in self.api_field_keywords:
            if keyword in error_lower:
                # Extract context around the keyword (5 words before and after)
                # ... (logic for context extraction) ...
                terms.append(keyword)
        return terms

    def search_error_documentation(self, error_codes: List[str]) -> List[Dict[str, Any]]:
        """Search for error code documentation with enhanced queries"""
        if not error_codes or not self.embedding_manager:
            return []

        results = []
        for code in error_codes:
            # Multiple Search strategies for better recall
            search_queries = [
                f"'{code}'",           # Exact error code
                f"'Error code {code}'",
                f"'{code} errorMsg'",  # Based on your output format
                f"'{code} description meaning'",
            ]

            for query in search_queries:
                code_results = self.embedding_manager.search_similar(
                    query,
                    top_k=2
                )

                for result in code_results:
                    # Check if the error code actually appears in the content
                    if code in result['context'].upper():
                        result['source_type'] = 'error_doc'
                        result['error_code'] = code
                        result['match_confidence'] = 'high'
                        results.append(result)

        return results

    def search_related_api_specs(self, error_info: List[Dict[str, Any]], query: str) -> List[Dict[str, Any]]:
        """Search for API specs related to the error with enhanced field matching"""
        if not self.embedding_manager:
            return []

        if not error_info:
            # If no error info, try to extract terms from the query
            api_terms = self.extract_api_terms_from_error(query)
        else:
            # Extract terms from error description
            api_terms = []
            for info in error_info:
                content = info.get('content', '')
                extracted_terms = self.extract_api_terms_from_error(content)
                api_terms.extend(extracted_terms)

        # Add terms extracted directly from the original query
        query_terms = self.extract_api_terms_from_error(query)
        api_terms.extend(query_terms)
        api_terms = list(dict.fromkeys(api_terms)) # Remove duplicates

        # Perform a combined, prioritized search for API specs
        api_results = []

        # Strategy 1: Find API field documentation required/optional, similar to error
        field_keywords = [
            'field required optional similar' # for max-relevance search, similar to error terms
        ]

        for term in api_terms:
            # ... search logic using embedding_manager.search_similar(term) ...
            # (check if any term in result['context'].lower() for term in ['req', 'opt', 'mandatory', 'response', 'field-related-term'])
            pass

        # Strategy 2: Search for validation/requirement documentation
        validation_queries = [
            'required fields mandatory validation',
            'optional fields data type format',
            'field standardization structure'
        ]

        for query in validation_queries:
            # ... search logic using embedding_manager.search_similar(query) ...
            pass

        return self._deduplicate_results(api_results)

    def analyze_error_query(self, query: str) -> Dict[str, Any]:
        """Comprehensive error analysis combining error codes and API specs"""
        # 1. Extract error codes
        error_codes = self.extract_error_codes(query)

        # 2. Search for error documentation
        error_docs = self.search_error_documentation(error_codes)

        # 3. Search related API specifications
        api_specs = self.search_related_api_specs(error_docs, query)

        # 4. Combine results with priority
        all_results = []

        # Prioritize high confidence error matches first
        high_conf_errors = [r for r in error_docs if r.get('match_confidence') == 'high']
        all_results.extend(high_conf_errors)

        # Add field specific API specs (assuming relevance is set)
        field_specs = [r for r in api_specs if r.get('relevance') == 'field_specific']
        all_results.extend(field_specs)

        # Add remaining errors (low confidence errors, general API specs, etc.)
        remaining_errors = [r for r in error_docs if r not in high_conf_errors]
        remaining_specs = [r for r in api_specs if r not in field_specs]

        all_results.extend(remaining_specs)
        all_results.extend(remaining_errors)

        all_results = self._deduplicate_results(all_results)

        # 5. Format the context for the LLM
        return self.format_context_for_llm(all_results, analysis_type="error analysis")

    def format_context_for_llm(self, analysis_results: List[Dict[str, Any]], analysis_type: str) -> str:
        """Format the analysis results as context for the LLM with enhanced structure"""
        context_parts = []

        # Part 1: Detected Error Codes
        if analysis_type == 'error analysis':
            # ... logic to append detected codes ...
            pass

        # Part 2: Error Documentation (high priority)
        context_parts.append("**ERROR CODE DOCUMENTATION FOR ANALYSIS**")
        for idx, doc in enumerate(analysis_results):
            if doc.get('source_type') == 'error_doc':
                # ... format error documentation content ...
                pass

        # Part 3: Related API Specifications (high priority)
        context_parts.append("\n**RELATED API SPECIFICATIONS**")
        for idx, spec in enumerate(analysis_results):
            if spec.get('source_type') == 'api_spec':
                # ... format API spec content ...
                pass

        # Part 4: Analysis Instructions
        context_parts.append("\n**ANALYSIS INSTRUCTIONS FOR API EXPERT**")
        context_parts.append("1. Match the error code(s) with their exact descriptions from the error documentation.")
        context_parts.append("2. Identify which API fields or parameters are mentioned in the error description.")
        context_parts.append("3. Cross-reference with API specifications to find:")
        context_parts.append("- Required vs Optional field status?")
        # ... more instructions ...

        return "\n\n".join(context_parts)

    def _deduplicate_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate results based on content"""
        seen = set()
        deduplicated = []
        for result in results:
            content = result.get('content', '')[:200]  # Use first 200 chars as identifier
            if content not in seen:
                seen.add(content)
                deduplicated.append(result)
        return deduplicated

    def generate_response(self, query: str, context: str = "", conversation_history: List[Dict] = None) -> str:
        """Generate response using Groq API with specialized prompts for API troubleshooting"""

        # Determine if this is an API troubleshooting query
        error_codes = self.extract_error_codes(query)
        is_api_troubleshooting = len(error_codes) > 0 or any(keyword in query.lower() for keyword in self.api_field_keywords)

        if is_api_troubleshooting:
            system_prompt = self._get_api_troubleshooting_prompt()
            # Get enhanced context for API troubleshooting
            enhanced_context = self.analyze_error_query(query)
            full_context = f"{enhanced_context}\n\n{context}" if context else enhanced_context
        else:
            system_prompt = self._get_general_banking_prompt()
            full_context = context

        # Prepare messages
        messages = [{"role": "system", "content": system_prompt}]

        # Add conversation history if provided
        if conversation_history:
            messages.extend(conversation_history[-APP_CONFIG['MAX_CONVERSATION_HISTORY']:])

        # Add current query with context
        user_message = f"Context:\n{full_context}\n\nQuestion: {query}" if full_context else query
        messages.append({"role": "user", "content": user_message})

        try:
            response = self.groq_client.chat.completions.create(
                model=APP_CONFIG['LLAMA_MODEL'],
                messages=messages,
                max_tokens=APP_CONFIG['MAX_TOKENS'],
                temperature=APP_CONFIG['TEMPERATURE']
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return "I apologize, but I encountered an error while processing your request. Please try again."

    def _get_api_troubleshooting_prompt(self) -> str:
        """Get the specialized system prompt for API troubleshooting"""
        return """You are an expert API troubleshooting assistant specializing in correlating error codes with API specifications.
**Your Core Capabilities:**
# 1. **Error Code Identification & Description**
- Extract error codes from queries (e.g., IBM8082, IBM8017)
- Locate exact error descriptions from error documentation
- Parse error messages to identify specific issues
# 1. **API Specification Cross-Reference**
- Match error descriptions with relevant API field specifications
- Identify which API fields are mentioned in error messages
- Correlate Required/Optional status with error deviations
- Match data types, formats, and validation rules
# 1. **Root Cause Analysis**
- Determine if errors are due to:
- Missing required fields
- Incorrect data types
- Format/validation failures
- Mismatched field names or structures
- Null/empty values in required fields
# **Response Structure:**
When analyzing error codes, ALWAYS structure your response as follows:
**ERROR CODE:** [Code Number]
**Description:** [Exact error message from documentation]
**Error Category:** [e.g., Validation Error, Field Missing, Type Mismatch, etc.]
**ROOT CAUSE ANALYSIS:**
**Affected API Fields:** [list specific field names from API specs]
**Field Requirements:**
- **[Field Name]:** [Required/Optional] - [Data Type] - [Current Issue]
**Likely Problem:** [Specific explanation based on cross-referencing]
**TROUBLESHOOTING STEPS:**
# 1. [Specific, actionable step based on API specs]
# 2. [Next verification step]

**RELATED API SPECIFICATIONS:**
**Field:** [Field Name]
**Requirement:** [Required/Optional]
**Data Type:** [Type]
**Format:** [if specified]
**Validation Rules:** [if any]
**SOURCE REFERENCES:**
**Error Documentation:** [Filename]
**API Specification:** [Sheet/Filename]
**CRITICAL RULES:**
**ALWAYS cite sources:** Indicate whether information comes from error documentation (PDF) or API specifications (Excel)
**Be specific:** Reference exact field names, not general descriptions
**Match precisely:** Only correlate error codes with API fields that are explicitly mentioned or strongly implied
**Admit uncertainty:** If you cannot find specific information in the documents, clearly state this
**No assumptions:** Base all analysis on provided documentation only"""

    def _get_general_banking_prompt(self) -> str:
        """Get the general banking prompt for non-API queries"""
        return """You are a helpful AI assistant that answers questions based on provided PDF documents.
Use the context from the documents to provide accurate and detailed answers.
If information is not available in the provided context, say so clearly.
Consider the conversation history to maintain context and provide coherent responses."""

    def has_documents(self) -> bool:
        """Check if documents are loaded"""
        return self.embedding_manager is not None and self.embedding_manager.has_documents()

    def clear_history(self):
        """Clear conversation history - placeholder for future implementation"""
        pass

    def get_stats(self) -> Dict[str, Any]:
        """Get document statistics"""
        if not self.embedding_manager:
            return {"documents": 0, "chunks": 0, "file_types": {}}
        return self.embedding_manager.get_stats()

    def get_recent_sources(self) -> List[str]:
        """Get recent document sources"""
        if not self.embedding_manager:
            return []
        return self.embedding_manager.get_recent_sources()

    def clear_documents(self):
        """Clear all documents"""
        if self.embedding_manager:
            self.embedding_manager.clear_documents()
