import pandas as pd
import joblib

from agentes.agente import Agente
from agentes.agente_especialista import AgenteEspecialista
from agentes.agente_frontera import AgenteFrontera
from agentes.agente_random_forest import AgenteRandomForest


class AgenteEnsamblador(Agente):

    name = "Agente Ensamblador"
    color = Agente.YELLOW
    
    def __init__(self, collection):
        """
        Crea una instancia del ensamblador (ensemble) creando cada uno de los modelos
        y cargando los pesos del ensemble.
        """
        self.log("Iniciando el Agente Ensamblador")
        self.specialist = AgenteEspecialista()
        self.frontier = AgenteFrontera(collection)
        self.random_forest = AgenteRandomForest()
        self.model = joblib.load('src/ensemble_model.pkl')
        self.log("El Agente Ensamblador está listo")

    def price(self, description: str) -> float:
        """
        Ejecuta este modelo ensemble.
        Solicita a cada uno de los modelos que estimen el precio del producto
        y luego usa el modelo de regresión lineal para devolver el precio ponderado.
        :param description: la descripción de un producto
        :return: una estimación de su precio
        """
        self.log("Ejecutando el Agente Ensamblador - colaborando con especialista, frontier y random forest")
        specialist = self.specialist.price(description)
        frontier = self.frontier.price(description)
        random_forest = self.random_forest.price(description)
        X = pd.DataFrame({
            'Specialist': [specialist],
            'Frontier': [frontier],
            'RandomForest': [random_forest],
            'Min': [min(specialist, frontier, random_forest)],
            'Max': [max(specialist, frontier, random_forest)],
        })
        y = max(0, self.model.predict(X)[0])
        self.log(f"El Agente Ensamblador ha completado - devolviendo ${y:.2f}")
        return y