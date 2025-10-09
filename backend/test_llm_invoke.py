# test_llm_invoke.py

import os
import logging
from langchain.prompts import PromptTemplate
from langchain.llms import LlamaCpp

MODEL_PATH = "./models/mistral-7b-instruct-v0.2.Q4_K_M.gguf"
logger = logging.getLogger(__name__)

def test_llm():
    if not os.path.exists(MODEL_PATH):
        print(f"ERROR: LLM model not found at {MODEL_PATH}.")
        print("Please download 'mistral-7b-instruct-v0.2.Q4_K_M.gguf' and place it in the 'models/' folder.")
        return

    print("--- Starting LLM Test Invocation ---")
    try:
        # Initialize LlamaCpp
        llm = LlamaCpp(
            model_path=MODEL_PATH,
            temperature=0.1,
            max_tokens=256,
            n_ctx=2048,
            verbose=False,
        )

        # Define a simple prompt
        template = """
        [INST] You are a brief and factual assistant. Answer the following question concisely.
        Question: What is the main benefit of a High-Yield Savings Account?
        [/INST]
        """
        
        # Invoke the LLM
        print(f"Invoking LLM with model: {os.path.basename(MODEL_PATH)}...")
        response = llm.invoke(template)

        print("\n--- LLM Response ---")
        print(response.strip())
        print("--------------------")
        print("\nLLM test completed successfully!")

    except Exception as e:
        print(f"\nERROR: LLM invocation failed.")
        print(f"Exception details: {e}")

if __name__ == "__main__":
    # Ensure models directory exists
    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    test_llm()