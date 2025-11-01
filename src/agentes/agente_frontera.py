import os
import re
from typing import List, Dict
from sentence_transformers import SentenceTransformer
from agentes.agente import Agente
from groq import Groq


class AgenteFrontera(Agente):

    name = "Agente Frontera"
    color = Agente.BLUE

    MODEL = "llama-3.3-70b-versatile"

    def __init__(self, collection):
        """
        Configura esta instancia conectando a Groq u OpenAI,
        configurando el datastore Chroma y el modelo de embeddings.
        """
        self.log("Inicializando el Agente Frontera")

        # 1️⃣ Usa Groq si hay clave configurada
        if os.getenv("GROQ_API_KEY"):
            self.client = Groq()
            self.MODEL = "llama-3.3-70b-versatile"  # o "llama-3.3-70b-versatile"
            self.log("El Agente Frontera está configurado con Groq")

        # 2️⃣ De lo contrario, usa OpenAI como respaldo
        else:
            from openai import OpenAI
            self.client = OpenAI()
            self.MODEL = "gpt-4o-mini"
            self.log("El Agente Frontera está configurado con OpenAI")

        # Configura la colección vectorial y el modelo de embeddings
        self.collection = collection
        try:
            self.model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2', device='cpu')
        except RuntimeError:
            self.model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2').to('cpu')
        self.log("El Agente Frontera está listo")

    def make_context(self, similars: List[str], prices: List[float]) -> str:
        message = "Para brindar algo de contexto, aquí hay algunos otros artículos que podrían ser similares al elemento.\n\n"
        for similar, price in zip(similars, prices):
            message += f"Producto potencialmente relacionado:\n{similar}\nPrecio ${price:.2f}\n\n"
        return message

    def messages_for(self, description: str, similars: List[str], prices: List[float]) -> List[Dict[str, str]]:
        system_message = "Estimas el precio de los artículos. Respondes solo con el precio, sin explicaciones."
        user_prompt = self.make_context(similars, prices)
        user_prompt += "Y la pregunta para tí es:\n\n¿Cuánto cuesta el artículo?\n\n" + description
        return [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_prompt},
            {"role": "assistant", "content": "Precio $"}
        ]

    def find_similars(self, description: str):
        self.log("El Agente Frontera realiza una búsqueda RAG en el datastore de Chroma para encontrar 5 productos similares")
        vector = self.model.encode([description])
        results = self.collection.query(query_embeddings=vector.astype(float).tolist(), n_results=5)
        documents = results['documents'][0][:]
        prices = [m['price'] for m in results['metadatas'][0][:]]
        self.log("El Agente Frontera ha encontrado productos similares")
        return documents, prices

    def get_price(self, s) -> float:
        s = s.replace('$', '').replace(',', '')
        match = re.search(r"[-+]?\d*\.\d+|\d+", s)
        return float(match.group()) if match else 0.0

    def price(self, description: str) -> float:
        """
        Consulta Groq (preferido) u OpenAI para estimar el precio de un producto
        basándose en productos similares del datastore de Chroma.
        """
        documents, prices = self.find_similars(description)
        self.log(f"El Agente Frontera está a punto de llamar a {self.MODEL} con contexto que incluye 5 productos similares")

        response = self.client.chat.completions.create(
            model=self.MODEL,
            messages=self.messages_for(description, documents, prices),
            max_tokens=5,
            temperature=0.2,
        )

        reply = response.choices[0].message.content
        result = self.get_price(reply)
        self.log(f"El Agente Frontera ha terminado - predicción: ${result:.2f}")
        return result