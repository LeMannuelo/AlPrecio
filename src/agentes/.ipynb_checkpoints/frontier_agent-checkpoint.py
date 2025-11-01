import os
import re
from typing import List, Dict
from sentence_transformers import SentenceTransformer
import chromadb
from items import Item
from testing import Tester
from agents.agent import Agent
from groq import Groq


class FrontierAgent(Agent):

    name = "Frontier Agent"
    color = Agent.BLUE

    MODEL = "llama-3.3-70b-versatile"

    def __init__(self, collection):
        """
        Set up this instance by connecting to Groq or OpenAI,
        setting up the Chroma Datastore and the embedding model.
        """
        self.log("Initializing Frontier Agent")

        # 1️⃣ Usa Groq si hay clave configurada
        if os.getenv("GROQ_API_KEY"):
            self.client = Groq()
            self.MODEL = "llama-3.3-70b-versatile"  # o "llama-3.3-70b-versatile"
            self.log("Frontier Agent is set up with Groq")

        # 2️⃣ De lo contrario, usa OpenAI como respaldo
        else:
            from openai import OpenAI
            self.client = OpenAI()
            self.MODEL = "gpt-4o-mini"
            self.log("Frontier Agent is set up with OpenAI")

        # Configura la colección vectorial y el modelo de embeddings
        self.collection = collection
        self.model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

        self.log("Frontier Agent is ready")

    def make_context(self, similars: List[str], prices: List[float]) -> str:
        message = "Para brindar algo de contexto, aquí hay algunos otros artículos que podrían ser similares al elemento.\n\n"
        for similar, price in zip(similars, prices):
            message += f"Potentially related product:\n{similar}\nPrice is ${price:.2f}\n\n"
        return message

    def messages_for(self, description: str, similars: List[str], prices: List[float]) -> List[Dict[str, str]]:
        system_message = "Estimas el precio de los artículos. Respondes solo con el precio, sin explicaciones."
        user_prompt = self.make_context(similars, prices)
        user_prompt += "Y la pregunta para tí es:\n\n¿Cuánto cuesta el artículo?\n\n" + description
        return [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_prompt},
            {"role": "assistant", "content": "Price is $"}
        ]

    def find_similars(self, description: str):
        self.log("Frontier Agent is performing a RAG search of the Chroma datastore to find 5 similar products")
        vector = self.model.encode([description])
        results = self.collection.query(query_embeddings=vector.astype(float).tolist(), n_results=5)
        documents = results['documents'][0][:]
        prices = [m['price'] for m in results['metadatas'][0][:]]
        self.log("Frontier Agent has found similar products")
        return documents, prices

    def get_price(self, s) -> float:
        s = s.replace('$', '').replace(',', '')
        match = re.search(r"[-+]?\d*\.\d+|\d+", s)
        return float(match.group()) if match else 0.0

    def price(self, description: str) -> float:
        """
        Query Groq (preferred) or OpenAI to estimate a product's price
        based on similar products from the Chroma datastore.
        """
        documents, prices = self.find_similars(description)
        self.log(f"Frontier Agent is about to call {self.MODEL} with context including 5 similar products")

        response = self.client.chat.completions.create(
            model=self.MODEL,
            messages=self.messages_for(description, documents, prices),
            max_tokens=5,
            temperature=0.2,
        )

        reply = response.choices[0].message.content
        result = self.get_price(reply)
        self.log(f"Frontier Agent completed - predicting ${result:.2f}")
        return result
