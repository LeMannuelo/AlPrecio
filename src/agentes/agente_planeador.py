from typing import Optional, List
from agentes.agente import Agente
from agentes.deals import Deal, Opportunity
from agentes.agente_scanner import AgenteScanner
from agentes.agente_ensamblador import AgenteEnsamblador
from agentes.agente_mensajero import AgenteMensajero


class AgentePlaneador(Agente):

    name = "Agente Planeador"
    color = Agente.GREEN
    DEAL_THRESHOLD = 50

    def __init__(self, collection):
        """
        Crea instancias de los 3 Agentes que este planificador coordina
        """
        self.log("El Agente Planeador se está inicializando")
        self.scanner = AgenteScanner()
        self.ensemble = AgenteEnsamblador(collection)
        self.messenger = AgenteMensajero()
        self.log("El Agente Planeador está listo")

    def run(self, deal: Deal) -> Opportunity:
        """
        Ejecuta el flujo de trabajo para una oferta específica
        :param deal: la oferta, resumida de un RSS scrape
        :returns: una oportunidad que incluye el descuento
        """
        self.log("El Agente Planeador está calculando el precio de una posible oferta")
        estimate = self.ensemble.price(deal.product_description)
        discount = estimate - deal.price
        self.log(f"El Agente Planeador ha procesado una oferta con descuento de ${discount:.2f}")
        return Opportunity(deal=deal, estimate=estimate, discount=discount)

    def plan(self, memory: List[str] = []) -> Optional[Opportunity]:
        """
        Ejecuta el flujo de trabajo completo:
        1. Usa el AgenteScanner para encontrar ofertas de feeds RSS
        2. Usa el AgenteEnsamblador para estimarlas
        3. Usa el AgenteMensajero para enviar notificaciones de ofertas
        :param memory: una lista de URLs que han sido encontradas en el pasado
        :return: una Oportunidad si se encontró una, si no, None
        """
        self.log("El Agente Planeador está iniciando una ejecución")
        selection = self.scanner.scan(memory=memory)
        if selection:
            opportunities = [self.run(deal) for deal in selection.deals[:5]]
            opportunities.sort(key=lambda opp: opp.discount, reverse=True)
            best = opportunities[0]
            self.log(f"El Agente Planeador ha identificado que la mejor oferta tiene un descuento de ${best.discount:.2f}")
            if best.discount > self.DEAL_THRESHOLD:
                self.messenger.alert(best)
            self.log("El Agente Planeador ha completado una ejecución")
            return best if best.discount > self.DEAL_THRESHOLD else None
        return None