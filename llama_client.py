import os
import logging
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LLaMAClient:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv('LLAMA_API_KEY')
        self.api_url = os.getenv('LLAMA_API_URL', 'https://chatapi.akash.network/api/v1')
        if not self.api_key:
            raise ValueError("LLAMA_API_KEY is not set in the environment variables")
        
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.api_url
        )

    async def generate_response(self, prompt, max_tokens=100):
        try:
            response = self.client.chat.completions.create(
                model="Meta-Llama-3-1-8B-Instruct-FP8",
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=max_tokens
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Error generating response from LLaMA API: {e}")
            return None

    async def generate_jackal_response(self, content):
        prompt = f"""You are an AI assistant for the Jackal Protocol, a decentralized storage solution built on the Cosmos ecosystem. 
        Please rewrite the following content in a more conversational, friendly tone. Remove any asterisks or other formatting artifacts. 
        Ensure the response is clear, engaging, and easy to understand:

        Content: {content}

        Rewritten Response:"""

        response = await self.generate_response(prompt, max_tokens=300)
        return response if response else content  # Fall back to original content if LLaMA fails