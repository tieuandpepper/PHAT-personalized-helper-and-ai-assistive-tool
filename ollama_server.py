from openai import OpenAI

OLLAMA_DEFAULT_PORT = 'http://localhost:11434/v1/'
OLLAMA_DEFAULT_MODEL= "llama3.2"

class OllamaServer:
    def __init__(self,model_name=OLLAMA_DEFAULT_MODEL, port=OLLAMA_DEFAULT_PORT):
        self.model_name = model_name
        self.port=port
        self.start_model()
    
    def start_model(self):
        print("Loading the model... ", end = "")
        self.model = OpenAI(
            base_url=self.port,
            # required but ignored
            api_key='ollama',
        )
        print("Completed!")

    def invoke_model(self,prompt:str)->str:
        try:
            chat_completion = self.model.chat.completions.create(
                messages=[
                    {
                        'role': 'user',
                        'content': prompt,
                    }
                ],
                model=self.model_name, 
            )
            output = chat_completion.choices[0].message.content
        except Exception as e:
            output = f"Exception: {e}"
        
        return output

    def stop_model(self):
        return self.invoke_model("\\bye")


# llm_model = OllamaServer()
# print(llm_model.invoke_model("How to make pancakes?"))
# print(llm_model.stop_server())