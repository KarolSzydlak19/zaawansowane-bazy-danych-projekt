import os
from dotenv import load_dotenv
from openai import OpenAI
from string import Template
import sys
from pathlib import Path

dotenv_path = Path(__file__).resolve().parent / ".env"
prompt_path = Path(__file__).resolve().parent / "prompt.txt"
load_dotenv(dotenv_path)

REQUIRED_VAR = os.getenv("OPENAI_API_KEY")

if REQUIRED_VAR is None:
    print("OpenAI API key missing, no OPENAI_API_KEY variable in .env \nPlease provide a viable API key")
    sys.exit(1)

class oai_client():
    def __init__(self, number_of_records):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.number_of_records = number_of_records
        self.system_prompt = self.read_txt(prompt_path)
    
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
