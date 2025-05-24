# In hercules/backend/app/autogen_manager.py
import autogen
# import os # No longer needed for direct LLM config here
import json
from pathlib import Path
import datetime

from .websocket_manager import websocket_manager
from .supabase_client import store_ai_message_in_supabase
from .llm_router import get_llm_config # Import the new LLM router function

BASE_ROOMS_PATH = Path("data/rooms")

# LLM configuration is now fetched from the router
# llm_config = get_llm_config() # This can be called per agent if needed, or once globally

async def run_autogen_chat(user_prompt: str, room_id: str):
    """
    Initiates an async chat using LLM config from the router, 
    broadcasts messages via WebSocket, and stores them in Supabase.
    """
    
    # Get LLM config for this session/task.
    # Could pass hints like preferred_llm based on room settings or user choice in future.
    current_llm_config = get_llm_config() 

    if not current_llm_config["config_list"] or \
       current_llm_config["config_list"][0]["api_key"].startswith("sk-THIS_IS_A_PLACEHOLDER"):
        warning_msg = "Critical: Autogen agents running with a placeholder LLM key. Real LLM calls will fail."
        print(warning_msg)
        # Broadcast this critical warning to the room as well
        await websocket_manager.broadcast_to_room(
            room_id,
            {"agent": "System", "error": warning_msg, "message_type": "llm_config_warning"}
        )
        # Storing this warning in ai_messages as well
        await store_ai_message_in_supabase({
            "room_id": room_id, "agent_name": "System", 
            "content": warning_msg, "custom_type": "llm_config_warning" # Example of custom type
        })


    async def message_processing_callback(sender, recipient, message_dict):
        # callback logic remains the same as defined in the previous step (Subtask 17)
        # For brevity, I'm using the version from this task description
        content_to_process = message_dict.get("content") if isinstance(message_dict, dict) else str(message_dict)
        agent_name = sender.name if hasattr(sender, 'name') else "UnknownAgent"

        # Broadcast non-TERMINATE messages
        if content_to_process and content_to_process.strip() and content_to_process.strip().upper() != "TERMINATE":
            await websocket_manager.broadcast_to_room(
                room_id,
                {"agent": agent_name, "message": content_to_process}
            )
        # Broadcast TERMINATE event
        elif content_to_process and content_to_process.strip().upper() == "TERMINATE":
            print(f"Agent {agent_name} is terminating.")
            await websocket_manager.broadcast_to_room(
                room_id,
                {"agent": agent_name, "event": "TERMINATE", "message": f"{agent_name} has finished."}
            )

        # Store non-TERMINATE messages in Supabase
        if content_to_process and content_to_process.strip() and content_to_process.strip().upper() != "TERMINATE":
            message_to_store = {
                "room_id": room_id, "agent_name": agent_name, "content": content_to_process,
            }
            if hasattr(sender, 'llm_config') and sender.llm_config: # Log model used by this agent
                config_list = sender.llm_config.get("config_list")
                if config_list and len(config_list) > 0:
                    message_to_store["model_used"] = config_list[0].get("model", "unknown")
            
            # Add tool_calls if present (as from Subtask 17's implementation)
            if isinstance(message_dict, dict) and message_dict.get("tool_calls"):
                message_to_store["tool_calls"] = message_dict.get("tool_calls")

            db_data, db_error = await store_ai_message_in_supabase(message_to_store)
            if db_error:
                print(f"Error storing AI message from {agent_name} in Supabase: {db_error.get('message')}")
                await websocket_manager.broadcast_to_room(
                    room_id,
                    {"agent": "System", "error": f"Failed to store message from {agent_name} to database."}
                )
        return False


    user_proxy = autogen.UserProxyAgent(
        name="UserProxy",
        human_input_mode="NEVER",
        max_consecutive_auto_reply=5,
        is_termination_msg=lambda x: x.get("content", "").rstrip().upper().endswith("TERMINATE"),
        code_execution_config=False, 
    )
    
    assistant = autogen.AssistantAgent(
        name="Assistant",
        llm_config=current_llm_config, # Use routed LLM config
        system_message="You are a helpful AI assistant. Provide concise answers. When the task is fully resolved or you have no more to say, end your response with TERMINATE."
    )

    # Register the callback
    # Using trigger_llm_reply=False from Subtask 17's implementation
    user_proxy.register_reply([autogen.Agent, None], reply_func=message_processing_callback, config=None, trigger_llm_reply=False)
    assistant.register_reply([autogen.Agent, None], reply_func=message_processing_callback, config=None, trigger_llm_reply=False)
    
    initial_prompt_to_log = {"room_id": room_id, "agent_name": user_proxy.name, "content": user_prompt}
    await store_ai_message_in_supabase(initial_prompt_to_log)
    await websocket_manager.broadcast_to_room(room_id, {"agent": user_proxy.name, "message": user_prompt})

    first_assistant_response_content = None
    try:
        await user_proxy.a_initiate_chat(assistant, message=user_prompt)
        # Corrected way to get history as per Autogen's ConversableAgent
        chat_result_history = user_proxy.chat_messages.get(assistant, []) 
        if chat_result_history:
            for msg_dict in chat_result_history:
                if msg_dict.get("role") == "assistant" and msg_dict.get("content"):
                    processed_content = msg_dict.get("content").strip()
                    if processed_content and not processed_content.upper() == "TERMINATE":
                        first_assistant_response_content = processed_content
                        break 
    except Exception as e:
        print(f"Error during Autogen chat for room {room_id}: {e}")
        error_message_content = f"Autogen Error: {str(e)}"
        await websocket_manager.broadcast_to_room(room_id, {"agent": "System", "error": error_message_content, "message_type": "autogen_error"})
        await store_ai_message_in_supabase({
            "room_id": room_id, "agent_name": "System", "content": error_message_content, "custom_type": "autogen_error"
        })
        return None 

    room_data_path = BASE_ROOMS_PATH / room_id
    room_data_path.mkdir(parents=True, exist_ok=True)
    log_entry = {
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "event": "Autogen chat session processing complete.",
        "prompt": user_prompt,
        "first_assistant_response_captured_for_log_file": first_assistant_response_content if first_assistant_response_content else "No specific initial response captured / only TERMINATE."
    }
    with open(room_data_path / "agent_log.json", "a") as f:
        json.dump(log_entry, f)
        f.write("\n")

    return first_assistant_response_content

# Removed the if __name__ == '__main__': block from autogen_manager.py
# as llm_router.py now has its own test block.
