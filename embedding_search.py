import os
import json
import numpy as np
from openai import AsyncOpenAI
from dotenv import load_dotenv
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()

class EmbeddingSearch:
    def __init__(self, knowledge_base):
        self.client = AsyncOpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.knowledge_base = knowledge_base
        self.embeddings = {}
        self.model = "text-embedding-ada-002"
        self.cache_file = "embeddings_cache.json"
        self.load_cache()

    def load_cache(self):
        if os.path.exists(self.cache_file):
            with open(self.cache_file, 'r') as f:
                cache = json.load(f)
                self.embeddings = {k: np.array(v) for k, v in cache.items()}
        else:
            logger.info(f"Cache file {self.cache_file} not found. Starting with empty cache.")

    def save_cache(self):
        cache = {k: v.tolist() for k, v in self.embeddings.items()}
        with open(self.cache_file, 'w') as f:
            json.dump(cache, f)

    async def get_embedding(self, text):
        if text in self.embeddings:
            return self.embeddings[text]

        try:
            response = await self.client.embeddings.create(input=text, model=self.model)
            embedding = response.data[0].embedding
            self.embeddings[text] = np.array(embedding)
            self.save_cache()
            return embedding
        except Exception as e:
            logger.error(f"Error getting embedding: {str(e)}")
            raise

    async def initialize_embeddings(self):
        for item in self.knowledge_base:
            if item['question'] not in self.embeddings:
                await self.get_embedding(item['question'])

    async def find_best_match(self, query, top_k=1):
        query_embedding = await self.get_embedding(query)
        
        similarities = []
        for item in self.knowledge_base:
            question = item['question']
            if question not in self.embeddings:
                await self.get_embedding(question)
            embedding = self.embeddings[question]
            similarity = np.dot(query_embedding, embedding) / (np.linalg.norm(query_embedding) * np.linalg.norm(embedding))
            similarities.append((item, similarity))
            logger.info(f"Query: '{query}', Question: '{question}', Similarity: {similarity}")
        
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        return similarities[:top_k]

    async def search(self, query, threshold=0.8):
        if not self.embeddings:
            await self.initialize_embeddings()
        
        logger.info(f"Searching for query: '{query}'")
        matches = await self.find_best_match(query)
        if matches:
            best_match, best_score = matches[0]
            logger.info(f"Best match: '{best_match['question']}', Score: {best_score}")
            if best_score >= threshold:
                logger.info(f"Match found above threshold {threshold}")
                return f"Q: {best_match['question']}\n\nA: {best_match['answer']}"
            else:
                logger.info(f"Best match score {best_score} below threshold {threshold}")
                return f"The best match I found was: Q: {best_match['question']}\nBut it didn't meet the confidence threshold. Score: {best_score}"
        else:
            logger.info("No matches found in knowledge base")
        return "I couldn't find a good match for your query in my knowledge base."

# Example usage:
async def main():
    # Example knowledge base
    knowledge_base = [
        {"question": "Where or how can I stake Jackal or JKL tokens?", "answer": "You can stake Jackal (JKL) tokens on the official Jackal website or through supported wallets like Keplr."},
        {"question": "Where can I find Jackal tutorials?", "answer": "You can find Jackal tutorials on the official Jackal documentation website and their YouTube channel."},
        # Add more items to your knowledge base as needed
    ]

    embedding_search = EmbeddingSearch(knowledge_base)
    query = "How do I stake my JKL tokens?"
    result = await embedding_search.search(query)
    print(result)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())