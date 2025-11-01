from typing import Optional, List
from openai import OpenAI
from agentes.deals import ScrapedDeal, DealSelection
from agentes.agente import Agente


class AgenteScanner(Agente):

    MODEL = "gpt-4o-mini"

    SYSTEM_PROMPT = """Tú identificas y resumes las 5 ofertas más detalladas de una lista, seleccionando aquellas que tengan la descripción de producto más completa y detallada, y un precio claramente definido.
    Responde estrictamente en formato JSON sin explicación adicional, utilizando este formato. Debes proporcionar el precio como un número obtenido de la descripción. Si el precio de una oferta no es claro, no la incluyas en tu respuesta.
    Lo más importante es que respondas con las 5 ofertas que tengan la descripción de producto más detallada y clara. No es importante mencionar las condiciones del descuento; lo más relevante es la descripción del producto.
    Ten cuidado con productos descritos como “$XXX de descuento” o “rebajado $XXX” — esto no es el precio real del producto. Solo responde cuando estés muy seguro del precio real.
    
    {"deals": [
        {
            "product_description": "Tu resumen claro del producto en 4–5 frases. Los detalles del producto son mucho más importantes que explicar por qué es una buena oferta. Evita mencionar descuentos o cupones; concéntrate en el artículo en sí. Debe haber un párrafo para cada producto elegido.",
            "price": 99.99,
            "url": "the url as provided"
        },
        ...
    ]}"""
    
    USER_PROMPT_PREFIX = """Responde con las 5 ofertas más prometedoras de esta lista, seleccionando aquellas que tengan la descripción del producto más detallada y de mayor calidad, y un precio claro mayor que 0.
    Responde estrictamente en JSON, y solo JSON. Debes reescribir la descripción como un resumen del producto en sí, no de las condiciones de la oferta.
    Recuerda incluir un párrafo completo de descripción por cada uno de los 5 productos seleccionados.
    Ten cuidado con productos descritos como “$XXX de descuento” o “rebajado $XXX” — ese no es el precio real del artículo. Solo responde cuando estés muy seguro del precio real.
    
    Ofertas:
    
    """

    USER_PROMPT_SUFFIX = "\n\nResponde estrictamente en JSON e incluye exactamente 5 ofertas, ni más ni menos."

    name = "Agente Scanner"
    color = Agente.CYAN

    def __init__(self):
        """
        Configura esta instancia inicializando OpenAI
        """
        self.log("El Agente Scanner se está inicializando")
        self.openai = OpenAI()
        self.log("El Agente Scanner está listo")

    def fetch_deals(self, memory) -> List[ScrapedDeal]:
        """
        Busca ofertas publicadas en feeds RSS.
        Devuelve las nuevas ofertas que no están ya en la memoria proporcionada.
        """
        self.log("El Agente Scanner va a obtener ofertas del feed RSS")
        urls = [opp.deal.url for opp in memory]
        scraped = ScrapedDeal.fetch()
        result = [scrape for scrape in scraped if scrape.url not in urls]
        self.log(f"El Agente Scanner recibió {len(result)} ofertas que no estaban en la memoria")
        return result

    def make_user_prompt(self, scraped) -> str:
        """
        Crea un prompt de usuario para OpenAI basado en las ofertas recopiladas
        """
        user_prompt = self.USER_PROMPT_PREFIX
        user_prompt += '\n\n'.join([scrape.describe() for scrape in scraped])
        user_prompt += self.USER_PROMPT_SUFFIX
        return user_prompt

    def scan(self, memory: List[str]=[]) -> Optional[DealSelection]:
        """
        Llama a OpenAI para proporcionar una lista de alto potencial con ofertas que tengan buenas descripciones y precios.
        Usa StructuredOutputs para asegurar que cumple nuestras especificaciones.
        :param memory: una lista de URLs que representan ofertas ya procesadas
        :return: una selección de buenas ofertas, o None si no hay ninguna
        """
        scraped = self.fetch_deals(memory)
        if scraped:
            user_prompt = self.make_user_prompt(scraped)
            self.log("El Agente Scanner está llamando a OpenAI usando Structured Output")
            result = self.openai.beta.chat.completions.parse(
                model=self.MODEL,
                messages=[
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt}
              ],
                response_format=DealSelection
            )
            result = result.choices[0].message.parsed
            result.deals = [deal for deal in result.deals if deal.price>0]
            self.log(f"El Agente Scanner recibió {len(result.deals)} ofertas seleccionadas con precio>0 de OpenAI")
            return result
        return None