def detectar_emocion(texto):
    texto = texto.lower()

    if any(palabra in texto for palabra in ["triste", "solo", "mal", "deprimido"]):
        return "tristeza"

    if any(palabra in texto for palabra in ["estres", "cansado", "agotado"]):
        return "estres"

    if any(palabra in texto for palabra in ["ansiedad", "nervioso", "preocupado"]):
        return "ansiedad"

    if any(palabra in texto for palabra in ["enojo", "bronca", "odio"]):
        return "enojo"

    return "neutral"