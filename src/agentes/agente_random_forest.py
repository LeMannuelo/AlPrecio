from sentence_transformers import SentenceTransformer
import joblib
from agentes.agente import Agente



class AgenteRandomForest(Agente):

    name = "Agente Random Forest"
    color = Agente.MAGENTA

    def __init__(self):
        """
        Inicializa este objeto cargando los pesos del modelo guardado
        y el modelo de codificación vectorial SentenceTransformer
        """
        self.log("El Agente Random Forest se está inicializando")
        try:
            self.vectorizer = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2', device='cpu')
        except RuntimeError:
            self.vectorizer = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2').to('cpu')
        self.model = joblib.load('src/random_forest_model.pkl')
        self.log("El Agente Random Forest está listo")

    def price(self, description: str) -> float:
        """
        Usa un modelo Random Forest para estimar el precio del artículo descrito
        :param description: el producto a ser estimado
        :return: el precio como número decimal
        """        
        self.log("El Agente Random Forest está iniciando una predicción")
        vector = self.vectorizer.encode([description])
        result = max(0, self.model.predict(vector)[0])
        self.log(f"El Agente Random Forest ha completado - prediciendo ${result:.2f}")
        return result