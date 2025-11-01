import os
from agentes.deals import Opportunity
import http.client
import urllib
from agentes.agente import Agente


DO_PUSH = True

class AgenteMensajero(Agente):

    name = "Agente Mensajero"
    color = Agente.WHITE

    def __init__(self):
        """
        Configura este objeto para enviar notificaciones push a través de Pushover
        """
        self.log(f"El Agente Mensajero se está inicializando")
        if DO_PUSH:
            self.pushover_user = os.getenv('PUSHOVER_USER')
            self.pushover_token = os.getenv('PUSHOVER_TOKEN')
            self.log("El Agente Mensajero ha inicializado Pushover")


    def push(self, text):
        """
        Envía una notificación push usando la API de Pushover
        """
        self.log("El Agente Mensajero está enviando una notificación push")
        conn = http.client.HTTPSConnection("api.pushover.net:443")
        conn.request("POST", "/1/messages.json",
          urllib.parse.urlencode({
            "token": self.pushover_token,
            "user": self.pushover_user,
            "message": text,
            "sound": "classical"
          }), { "Content-type": "application/x-www-form-urlencoded" })
        conn.getresponse()

    def alert(self, opportunity: Opportunity):
        """
        Genera una alerta sobre la oportunidad especificada
        """
        text = f"¡Alerta de Oferta! Precio=${opportunity.deal.price:.2f}, "
        text += f"Estimado=${opportunity.estimate:.2f}, "
        text += f"Descuento=${opportunity.discount:.2f} :"
        text += opportunity.deal.product_description[:10]+'... '
        text += opportunity.deal.url
        if DO_PUSH:
            self.push(text)
        self.log("El Agente Mensajero ha completado la tarea")
        
    
        