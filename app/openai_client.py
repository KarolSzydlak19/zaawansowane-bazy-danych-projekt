import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

def read_txt(filepath):
    with open(filepath, "r") as f:
        return f.read()

class oai_client():
    def __init__(self, number_of_records):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.number_of_records = number_of_records
        self.system_prompt = read_txt("prompt.txt")
            
    async def generate_sample_data(self, user_prompt: str):
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages = [
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                max_tokens = 500
            )
            return response.choices[0].message.content
        except Exception as e:
            print(e)