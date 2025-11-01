import modal
from agentes.agente import Agente


class AgenteEspecialista(Agente):
    """
    Un agente que ejecuta nuestro LLM afinado desplegado de forma remota en Modal.
    """

    name = "Agente Especialista"
    color = Agente.RED

    def __init__(self):
        """
        Configura este agente creando una instancia de la clase de Modal.
        """
        self.log("El Agente Especialista se está inicializando: conectando a Modal")
        Pricer = modal.Cls.from_name("pricer-service", "Pricer")
        self.pricer = Pricer()
        self.log("El Agente Especialista está listo")
        
    def price(self, description: str) -> float:
        """
        Realiza una llamada remota para devolver la estimación del precio de este artículo.
        """
        self.log("El Agente Especialista está llamando al modelo afinado remoto")
        result = self.pricer.price.remote(description)
        self.log(f"El Agente Especialista ha terminado - predicción: ${result:.2f}")
        return result