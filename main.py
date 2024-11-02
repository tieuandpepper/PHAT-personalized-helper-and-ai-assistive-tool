from src import ollama_server

model = ollama_server.OllamaServer()
output = model.invoke_model("How to close a door?")
print(output)
print(model.stop_model())

