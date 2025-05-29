from transformers import pipeline

try:
    modelo_moderacao = pipeline(
        "sentiment-analysis", 
        model="nlptown/bert-base-multilingual-uncased-sentiment"
    )
    print("INFO: Modelo de moderação 'nlptown/bert-base-multilingual-uncased-sentiment' carregado.")

except Exception as e:
    print(f"ERRO ao carregar o modelo de moderação: {e}")
    print("AVISO: A moderação de comentários pode não funcionar como esperado. Usando fallback que aprova tudo.")
    modelo_moderacao = None # Fallback

def analisar_comentario(texto: str) -> bool:
    """
    Analisa o sentimento do texto do comentário.
    Retorna True se o sentimento for considerado negativo (potencialmente "tóxico" ou indesejado),
    False caso contrário (sentimento neutro ou positivo).
    """
    if not modelo_moderacao:
        print("AVISO: Modelo de moderação não carregado. Aprovando comentário por padrão (não tóxico/sentimento positivo).")
        return False # Failsafe: aprova (considera não "tóxico") se o modelo não carregou

    try:
        resultado = modelo_moderacao(texto)[0]
        print(f"DEBUG [analisar_comentario] - Texto: '{texto}', Resultado do modelo de sentimento: {resultado}")
        
        # O modelo 'nlptown/bert-base-multilingual-uncased-sentiment' retorna labels como:
        # '1 star', '2 stars', '3 stars', '4 stars', '5 stars'
        # Vamos considerar '1 star' ou '2 stars' como sentimento negativo (e, portanto, "tóxico" para nosso caso de uso)
        
        label_do_modelo = resultado['label'].lower() # ex: "1 star", "5 stars"
        score_do_modelo = resultado['score']

        # Consideramos tóxico se for 1 ou 2 estrelas.
        # Você pode ajustar este critério se achar muito ou pouco rigoroso.
        if label_do_modelo == "1 star" or label_do_modelo == "2 stars":
            # Poderia adicionar um critério de score aqui se quisesse ser mais granular
            # Ex: if (label_do_modelo == "1 star" and score_do_modelo > 0.7) or label_do_modelo == "2 stars":
            print(f"DEBUG [analisar_comentario] - Sentimento negativo detectado: {label_do_modelo}")
            return True # Considerado "tóxico" / não aprovado
        
        print(f"DEBUG [analisar_comentario] - Sentimento neutro/positivo detectado: {label_do_modelo}")
        return False # Considerado "não tóxico" / aprovado

    except Exception as e:
        print(f"ERRO durante a análise de sentimento do comentário: {e}")
        return False # Failsafe: aprova se a análise falhar