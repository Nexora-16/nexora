from services.storage_service import obtener_productos_db, obtener_recursos_db
from models.insumo import Insumo


def construir_contexto(user_id, mensaje):
    productos = obtener_productos_db(user_id)
    recursos  = obtener_recursos_db(user_id)
    insumos   = Insumo.query.filter_by(user_id=user_id).all()

    contexto = "NEGOCIO (panadería):\n"

    for p in productos:
        contexto += f"- {p['producto']} | stock: {p['stock']} | costo: ${p['costo']:.2f} | venta: ${p['venta']:.2f}\n"

    if insumos:
        contexto += "\nINSUMOS (materias primas):\n"
        for i in insumos:
            contexto += f"- {i.nombre} | stock: {i.stock} {i.unidad} | costo: ${i.costo_unitario}/{i.unidad}\n"

    if recursos:
        contexto += "\nRECURSOS:\n"
        contexto += f"- Alquiler: {recursos.get('alquiler', 0)}\n"
        contexto += f"- Empleados: {recursos.get('empleados', 0)}\n"
        contexto += f"- Ubicación: {recursos.get('ubicacion', 'No definida')}\n"

    return contexto