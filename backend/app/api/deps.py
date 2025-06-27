from openai import OpenAI
import os
import uuid
from dotenv import load_dotenv
import json
load_dotenv()

client = OpenAI()
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")




def run_openai_model(system_prompt: str, query: str, model_id: str, temperature: float=0):
        """
        Run OpenAI text completion model
        """
        response = client.chat.completions.create(
            model=model_id,
            temperature=temperature,
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {"role": "user", "content": "The following is the json data: " + query},
            ],
        )
        result = response.choices[0].message.content
        json_result = json.loads(result)
        return json_result   


def run_openai_model_for_factual_allegations(system_prompt: str, query: str, model_id: str, temperature: float=0):
        """
        Run OpenAI text completion model
        """
        response = client.chat.completions.create(
            model=model_id,
            temperature=temperature,
            messages=[
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {"role": "user", "content": "The following the information about the plaintiff and defendant in json format: " + query},
            ],
        )
        result = response.choices[0].message.content
        return result   
