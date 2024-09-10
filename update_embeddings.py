import os
import json
import asyncio
from dotenv import load_dotenv
from openai import AsyncOpenAI
import numpy as np

load_dotenv()

class EmbeddingUpdater:
    def __init__(self):
        self.client = AsyncOpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.model = "text-embedding-ada-002"
        self.knowledge_base_file = 'knowledge_base.json'
        self.cache_file = "embeddings_cache.json"
        self.knowledge_base = self.load_knowledge_base()
        self.embeddings = self.load_cache()

    def load_knowledge_base(self):
        with open(self.knowledge_base_file, 'r') as f:
            return json.load(f)

    def load_cache(self):
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r') as f:
                    cache = json.load(f)
                return {k: np.array(v) for k, v in cache.items()}
            except json.JSONDecodeError:
                print(f"Warning: {self.cache_file} is empty or contains invalid JSON. Starting with an empty cache.")
        return {}

    def save_cache(self):
        cache = {k: v.tolist() for k, v in self.embeddings.items()}
        with open(self.cache_file, 'w') as f:
            json.dump(cache, f)

    async def get_embedding(self, text):
        try:
            response = await self.client.embeddings.create(input=text, model=self.model)
            return response.data[0].embedding
        except Exception as e:
            print(f"Error generating embedding for '{text}': {e}")
            return None

    async def update_embeddings(self):
        for item in self.knowledge_base:
            question = item['question']
            if question not in self.embeddings:
                print(f"Generating embedding for: {question}")
                embedding = await self.get_embedding(question)
                if embedding:
                    self.embeddings[question] = np.array(embedding)
            else:
                print(f"Embedding already exists for: {question}")

        self.save_cache()
        print("Embeddings update complete.")

async def main():
    updater = EmbeddingUpdater()
    await updater.update_embeddings()

if __name__ == "__main__":
    asyncio.run(main())