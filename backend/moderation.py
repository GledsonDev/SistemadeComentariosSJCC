from transformers import pipeline

modelo = pipeline("text-classification", model="unitary/toxic-bert")
def analisar_comentario(texto: str) -> bool:
    resultado = modelo(texto)[0]
    return resultado['label'].lower() == "toxic"