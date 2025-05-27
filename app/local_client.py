from transformers import pipeline
import torch

#Model needs to be changed
model_id = "nvidia/Llama-3.1-Nemotron-Nano-4B-v1.1"

pipe = pipeline("text-generation", model=model_id, torch_dtype=torch.bfloat16, device_map="auto")

def read_txt(filepath):
    with open(filepath, "r") as f:
        return f.read()
class local_client():
    def __init__(self, number_of_records):
        self.system_prompt = read_txt("prompt.txt")
        self.number_of_records = number_of_records

    async def generate_sample_data(self, user_prompt: str):
        messages = [
            {
                "role": "system",
                "content": self.system_prompt,
            },
            {
                "role": "user",
                "content": user_prompt
            }
        ]
        try:
            prompt = pipe.tokenizer.apply_chat_template(messages, tokenize=False)
            outputs = pipe(prompt, max_new_tokens=500, return_full_text=False)
            return outputs[0]["generated_text"]
        except Exception as e:
            print(e)
