import os
from dotenv import load_dotenv
from openai import OpenAI
from transformers import AutoTokenizer, AutoModelForCausalLM
from string import Template

#model_id = "HuggingFaceH4/zephyr-7b-beta"

#tokenizer = AutoTokenizer.from_pretrained(model_id)
#model = AutoModelForCausalLM.from_pretrained(model_id)

load_dotenv()


class oai_client():
    def __init__(self, number_of_records):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.number_of_records = number_of_records
        self.system_prompt = self.read_txt("prompt1.txt")
    
    def read_txt(self, filepath):
        with open(filepath, "r") as f:
            template =  Template(f.read())
        return template.substitute(number_of_records = self.number_of_records)
            
    async def generate_sample_data(self, user_prompt: str):
        try:
            response = self.client.chat.completions.create(
                model="gpt-4.1-nano",
                messages = [
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                max_tokens = 500
            )
            return response.choices[0].message.content
        except Exception as e:
            print(e)
    #def local_model_call(self, user_prompt : str):
     #   full_prompt = f"{self.system_prompt}\n{user_prompt}"
      #  inputs = tokenizer(full_prompt, return_tensors="pt")
       # outputs = model.generate(**inputs, max_new_tokens=50)
       # return tokenizer.decode(outputs[0], skip_special_tokens=True)
