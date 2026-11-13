import os
from dotenv import load_dotenv
import litellm
import json
from tools import TOOLS_SCHEMA, AVAILABLE_TOOLS

# Load environment variables (API keys)
load_dotenv()

# We can define different roles and models
MODELS = {
    "planner": "gemini/gemini-1.5-pro", # Can also use gemini-1.5-flash
    "coder": "groq/llama3-70b-8192",    # Groq Llama 3 for fast coding
    "local_reviewer": "openai/qwencoder:7b-4bit", # Accessed via local endpoint
    "deepseek_agent": "deepseek/deepseek-chat",
    "nim_agent": "nim/meta-llama3-70b-instruct"
}

# Optional: set custom api bases for local or nim
litellm.api_base = os.getenv("LOCAL_MODEL_URL") if "openai" in MODELS["local_reviewer"] else None

class Agent:
    def __init__(self, name: str, role: str, model: str, system_prompt: str, has_tools: bool = False):
        self.name = name
        self.role = role
        self.model = model
        self.system_prompt = system_prompt
        self.has_tools = has_tools
        self.history = [{"role": "system", "content": system_prompt}]

    def chat(self, user_message: str, add_to_history: bool = True) -> str:
        if add_to_history and user_message:
            self.history.append({"role": "user", "content": user_message})

        print(f"[{self.name}] Thinking using {self.model}...")

        kwargs = {
            "model": self.model,
            "messages": self.history,
        }

        # We add tools if the agent has them and the provider supports it
        # Groq and Gemini support tool calling well. 
        if self.has_tools:
            kwargs["tools"] = TOOLS_SCHEMA
            kwargs["tool_choice"] = "auto"

        try:
            response = litellm.completion(**kwargs)
            response_message = response.choices[0].message
            
            # Handle tool calls if any
            if hasattr(response_message, "tool_calls") and response_message.tool_calls:
                self.history.append(response_message.model_dump()) # Add assistant's tool call request to history
                
                for tool_call in response_message.tool_calls:
                    function_name = tool_call.function.name
                    function_args = json.loads(tool_call.function.arguments)
                    
                    print(f"[{self.name}] Tool Call: {function_name}({function_args})")
                    
                    # Execute tool
                    if function_name in AVAILABLE_TOOLS:
                        tool_result = AVAILABLE_TOOLS[function_name](**function_args)
                    else:
                        tool_result = f"Error: Tool {function_name} not found."
                    
                    # Add tool result to history
                    self.history.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": function_name,
                        "content": str(tool_result)
                    })
                
                # Recursive call to let agent respond after seeing tool result
                return self.chat(user_message=None, add_to_history=False)
            
            # No tool calls, standard response
            final_content = response_message.content
            if add_to_history:
                self.history.append({"role": "assistant", "content": final_content})
            return final_content
            
        except Exception as e:
            error_msg = f"Error calling {self.model}: {str(e)}"
            print(error_msg)
            return error_msg
