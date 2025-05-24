# hercules/backend/app/llm_router.py
import os

# Default model configurations
# These would ideally be more detailed and potentially loaded from a config file or env vars.
DEFAULT_OPENAI_MODEL = "gpt-3.5-turbo"
# Example for Gemini (actual config might differ based on SDK)
# DEFAULT_GEMINI_MODEL = "gemini-pro" 

def get_llm_config(preferred_llm: str | None = None, api_key: str | None = None) -> dict:
    """
    Provides a basic LLM configuration list for Autogen.
    Currently supports OpenAI via OPENAI_API_KEY environment variable.
    A placeholder for future routing logic (e.g., to Gemini or other models).

    Args:
        preferred_llm (str, optional): A hint for which LLM to use (e.g., "openai", "gemini"). Not fully used yet.
        api_key (str, optional): An API key provided directly. If None, tries environment variables.

    Returns:
        dict: An LLM configuration suitable for Autogen's `llm_config`.
              Returns a config with a placeholder key if no valid keys are found,
              to allow structural setup but prevent actual LLM calls.
    """
    
    # Prioritize provided API key if available
    openai_api_key = api_key if api_key else os.environ.get("OPENAI_API_KEY")
    # gemini_api_key = os.environ.get("GEMINI_API_KEY") # Example for Gemini

    config_list = []

    # OpenAI Configuration
    if openai_api_key:
        config_list.append({
            "model": os.environ.get("OPENAI_MODEL_NAME", DEFAULT_OPENAI_MODEL),
            "api_key": openai_api_key,
            # "api_type": "open_ai", # Usually not needed for direct OpenAI
            # "api_base": os.environ.get("OPENAI_API_BASE_URL"), # For custom endpoints
        })
    
    # Placeholder for Gemini Configuration (illustrative)
    # if gemini_api_key:
    #     config_list.append({
    #         "model": os.environ.get("GEMINI_MODEL_NAME", DEFAULT_GEMINI_MODEL),
    #         "api_key": gemini_api_key,
    #         "api_type": "google", # This would depend on Autogen's Gemini integration specifics
    #     })

    if not config_list:
        print("Warning: No valid LLM API keys found (e.g., OPENAI_API_KEY). Using a placeholder API key for Autogen config.")
        # Provide a placeholder config to prevent Autogen from crashing if no keys are found.
        # This allows the application to run structurally but LLM calls will fail.
        config_list.append({
            "model": DEFAULT_OPENAI_MODEL,
            "api_key": "sk-THIS_IS_A_PLACEHOLDER_KEY_DO_NOT_USE_IT",
        })

    return {
        "config_list": config_list,
        "cache_seed": 42,  # Enable caching
        # "temperature": 0, # Example for deterministic output
        # Add other common parameters like 'timeout' if needed
    }

if __name__ == '__main__':
    print("Testing LLM Router:")
    
    # Test case 1: No env var set (should return placeholder)
    print("\n--- Test Case 1: No API Key (Expecting Placeholder) ---")
    # Unset env var for testing this case if it was set locally
    original_openai_key = os.environ.pop("OPENAI_API_KEY", None) 
    cfg_no_key = get_llm_config()
    print(f"Config (no key): {cfg_no_key}")
    assert cfg_no_key["config_list"][0]["api_key"].startswith("sk-THIS_IS_A_PLACEHOLDER")

    # Test case 2: Env var set
    print("\n--- Test Case 2: OPENAI_API_KEY from Environment ---")
    if original_openai_key and original_openai_key != "sk-THIS_IS_A_PLACEHOLDER_KEY_DO_NOT_USE_IT":
        os.environ["OPENAI_API_KEY"] = original_openai_key # Restore if it was set
        cfg_env_key = get_llm_config()
        print(f"Config (env key): {cfg_env_key}")
        assert cfg_env_key["config_list"][0]["api_key"] == original_openai_key
    else:
        # Simulate setting it for the test
        os.environ["OPENAI_API_KEY"] = "sk-testkey12345"
        cfg_env_key_simulated = get_llm_config()
        print(f"Config (simulated env key): {cfg_env_key_simulated}")
        assert cfg_env_key_simulated["config_list"][0]["api_key"] == "sk-testkey12345"
        del os.environ["OPENAI_API_KEY"] # Clean up simulated key
        if original_openai_key: # Restore original if it existed
            os.environ["OPENAI_API_KEY"] = original_openai_key


    # Test case 3: API key passed directly
    print("\n--- Test Case 3: API Key Passed Directly ---")
    cfg_direct_key = get_llm_config(api_key="sk-directkey67890")
    print(f"Config (direct key): {cfg_direct_key}")
    assert cfg_direct_key["config_list"][0]["api_key"] == "sk-directkey67890"
    
    print("\nLLM Router tests completed.")
    # Restore original key if it was popped and not restored by test case 2 logic
    if original_openai_key:
        os.environ["OPENAI_API_KEY"] = original_openai_key
