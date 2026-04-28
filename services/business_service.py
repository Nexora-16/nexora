from services.storage_service import obtener_productos_db

def analizar_negocio(producto, stock, costo, venta, user_id):
    margen = venta - costo
    porcentaje = (margen / costo) * 100 if costo > 0 else 0

    productos = obtener_productos_db(user_id)

    respuesta = f"{producto}\nMargen: {porcentaje:.1f}%\n\n"

    # 🔥 ANÁLISIS INDIVIDUAL
    if margen < 0:
        respuesta += "⚠️ Estás perdiendo dinero\n"
    elif porcentaje < 30:
        respuesta += "Margen bajo\n"
    else:
        respuesta += "Buen margen\n"

    # 🔥 ANÁLISIS GLOBAL
    if productos:
        stock_total = sum(p["stock"] for p in productos)
        ganancia_total = sum((p["venta"] - p["costo"]) * p["stock"] for p in productos)

        respuesta += f"\n📊 Stock total: {stock_total}"
        respuesta += f"\n💰 Ganancia potencial: ${ganancia_total}"

        # 🔥 PRODUCTOS CRÍTICOS
        criticos = [p for p in productos if p["stock"] < 5]
        if criticos:
            respuesta += f"\n⚠️ Productos con poco stock: {len(criticos)}"

    # 🤖 RECOMENDACIONES
    if porcentaje < 20:
        respuesta += "\n👉 Recomendación: subir precio o bajar costos"

    return respuesta