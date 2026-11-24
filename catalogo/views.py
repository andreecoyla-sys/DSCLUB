import json
from urllib.parse import quote
from decimal import Decimal, InvalidOperation
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.db.models.deletion import ProtectedError
from django.views.decorators.http import require_POST
from .models import Producto, Categoria, Pedido, DetallePedido

TALLAS_BASE = ['16', 'S', 'M', 'L', 'XL', '30', '32', '34', 'ÚNICA']
WHATSAPP_TIENDA = '51987532146'

TARIFA_DELIVERY = Decimal('0.00')
TARIFA_PROVINCIA = Decimal('0.00')

def asegurar_categorias_base():
    if not Categoria.objects.exists():
        for i, nombre in enumerate(['POLOS', 'SHORES', 'BUSOS', 'POLERAS', 'JEAN'], start=1):
            Categoria.objects.create(nombre=nombre, orden=i)

def _combinar_tallas(tallas_check, tallas_extra_raw):
    resultado = []
    for t in tallas_check:
        t_clean = t.strip().upper()
        if t_clean and t_clean not in resultado:
            resultado.append(t_clean)
    if tallas_extra_raw:
        for t in tallas_extra_raw.split(','):
            t_clean = t.strip().upper()
            if t_clean and t_clean not in resultado:
                resultado.append(t_clean)
    return ', '.join(resultado) if resultado else 'ÚNICA'

def inicio(request):
    asegurar_categorias_base()
    categorias = Categoria.objects.filter(activa=True)
    productos = Producto.objects.select_related('categoria').filter(
        activo=True,
        stock__gt=0,
        categoria__activa=True
    )

    tallas_en_stock = []
    data = []
    for p in productos:
        lista_t = p.lista_tallas()
        for t in lista_t:
            if t and t not in tallas_en_stock:
                tallas_en_stock.append(t)
        data.append({
            'id': p.id,
            'tag': p.etiqueta,
            'category': p.categoria.nombre,
            'name': p.nombre,
            'price': float(p.precio),
            'old_price': float(p.precio_anterior) if p.precio_anterior else None,
            'stock': p.stock,
            'sizes': lista_t,
            'image': p.imagen.url if p.imagen else '',
            'description': p.descripcion,
        })

    # Ordena primero las tallas base conocidas y luego cualquier talla nueva creada por el dueño
    tallas_filtro = [t for t in TALLAS_BASE if t in tallas_en_stock] + [
        t for t in tallas_en_stock if t not in TALLAS_BASE
    ]

    return render(request, 'catalogo/index.html', {
        'productos_data': data,
        'categorias': categorias,
        'tallas_filtro': tallas_filtro,
        'tarifa_delivery': float(TARIFA_DELIVERY),
        'tarifa_provincia': float(TARIFA_PROVINCIA),
    })

@require_POST
def crear_pedido(request):
    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'ok': False, 'error': 'Datos inválidos'}, status=400)

    cliente_nombre = payload.get('nombre', '').strip()
    cliente_telefono = payload.get('telefono', '').strip()
    tipo_entrega = payload.get('entrega', 'Delivery').strip()
    direccion = payload.get('direccion', '').strip()
    provincia = payload.get('provincia', '').strip()
    agencia = payload.get('agencia', '').strip()
    dni = payload.get('dni', '').strip()
    metodo_pago = payload.get('pago', 'YAPE / PLIN').strip()
    notas = payload.get('notas', '').strip()
    items = payload.get('items', [])

    if not cliente_nombre:
        return JsonResponse({'ok': False, 'error': 'Por favor ingresa tu nombre.'}, status=400)
    if not items:
        return JsonResponse({'ok': False, 'error': 'Tu carrito está vacío.'}, status=400)

    if tipo_entrega == 'Envío provincia':
        costo_envio = TARIFA_PROVINCIA
        partes_prov = []
        if provincia:
            partes_prov.append(f"Destino: {provincia}")
        if agencia:
            partes_prov.append(f"Agencia: {agencia}")
        if dni:
            partes_prov.append(f"DNI: {dni}")
        destino_final = " | ".join(partes_prov)
    elif tipo_entrega == 'Recojo en tienda':
        costo_envio = Decimal('0.00')
        destino_final = ""
    else:
        costo_envio = TARIFA_DELIVERY
        destino_final = direccion

    with transaction.atomic():
        pedido = Pedido.objects.create(
            cliente_nombre=cliente_nombre,
            cliente_telefono=cliente_telefono,
            tipo_entrega=tipo_entrega,
            direccion=destino_final,
            metodo_pago=metodo_pago,
            notas=notas,
            costo_envio=costo_envio,
        )

        subtotal_prendas = Decimal('0.00')
        lineas_wpp = []

        for item in items:
            prod = Producto.objects.filter(pk=item.get('id'), activo=True).first()
            cantidad = max(1, int(item.get('qty', 1)))
            talla = str(item.get('size', 'ÚNICA')).upper()

            if prod:
                nombre_prod = prod.nombre
                precio_unit = prod.precio
            else:
                nombre_prod = str(item.get('name', 'Prenda'))
                precio_unit = Decimal(str(item.get('price', 0)))

            subtotal = precio_unit * cantidad
            subtotal_prendas += subtotal

            DetallePedido.objects.create(
                pedido=pedido,
                producto=prod,
                nombre_producto=nombre_prod,
                talla=talla,
                cantidad=cantidad,
                precio_unitario=precio_unit,
            )

            lineas_wpp.append(f"• {cantidad}x {nombre_prod} | Talla: {talla} — S/ {subtotal:.2f}")

        total_final = subtotal_prendas + costo_envio
        pedido.total = total_final
        pedido.save()

    detalle_texto = "\n".join(lineas_wpp)
    bloque_tel = f"\n*Teléfono:* {cliente_telefono}" if cliente_telefono else ""
    bloque_notas = f"\n*Notas:* {notas}" if notas else ""

    if tipo_entrega == 'Envío provincia':
        bloque_destino = ""
        if provincia:
            bloque_destino += f"\n*Provincia / Destino:* {provincia}"
        if agencia:
            bloque_destino += f"\n*Agencia:* {agencia}"
        if dni:
            bloque_destino += f"\n*DNI Destinatario:* {dni}"
    elif destino_final:
        bloque_destino = f"\n*Dirección / Referencia:* {destino_final}"
    else:
        bloque_destino = ""

    aviso_comprobante = (
        "\n\n_Adjunto mi captura de pago aquí abajo para confirmar mi envío:_"
        if metodo_pago in {'YAPE / PLIN', 'TRANSFERENCIA'}
        else ""
    )

    mensaje = (
        f"*NUEVO PEDIDO DSCLUB ({pedido.codigo})*\n"
        f"--------------------------------\n"
        f"*Cliente:* {cliente_nombre}{bloque_tel}\n"
        f"*Entrega:* {tipo_entrega}{bloque_destino}\n"
        f"*Método de pago:* {metodo_pago}{bloque_notas}\n"
        f"--------------------------------\n"
        f"*PRENDAS:*\n"
        f"{detalle_texto}\n"
        f"--------------------------------\n"
        f"*TOTAL PRENDAS: S/ {total_final:.2f}*"
        f"{aviso_comprobante}"
    )

    whatsapp_url = f"https://wa.me/{WHATSAPP_TIENDA}?text={quote(mensaje)}"

    return JsonResponse({
        'ok': True,
        'codigo': pedido.codigo,
        'whatsapp_url': whatsapp_url,
    })

@login_required(login_url='/admin/login/')
def panel_lista(request):
    asegurar_categorias_base()
    cat_id = request.GET.get('cat', 'ALL')
    productos = Producto.objects.select_related('categoria').all()
    if cat_id != 'ALL' and cat_id.isdigit():
        productos = productos.filter(categoria_id=int(cat_id))

    return render(request, 'catalogo/panel_lista.html', {
        'productos': productos,
        'categoria_actual': cat_id,
        'categorias': Categoria.objects.all(),
        'total_activos': Producto.objects.filter(activo=True, stock__gt=0).count(),
        'total_prendas': Producto.objects.count(),
        'pedidos_pendientes': Pedido.objects.filter(estado__in=['PENDIENTE', 'EMPACADO']).count(),
    })

@login_required(login_url='/admin/login/')
def panel_pedidos(request):
    estado = request.GET.get('estado', 'ACTIVOS')
    pedidos = Pedido.objects.prefetch_related('items').all()

    if estado == 'ACTIVOS':
        pedidos = pedidos.filter(estado__in=['PENDIENTE', 'EMPACADO'])
    elif estado != 'ALL':
        pedidos = pedidos.filter(estado=estado)

    return render(request, 'catalogo/panel_pedidos.html', {
        'pedidos': pedidos,
        'estado_actual': estado,
        'activos_count': Pedido.objects.filter(estado__in=['PENDIENTE', 'EMPACADO']).count(),
        'pendientes_count': Pedido.objects.filter(estado='PENDIENTE').count(),
        'empacados_count': Pedido.objects.filter(estado='EMPACADO').count(),
        'entregados_count': Pedido.objects.filter(estado='ENTREGADO').count(),
        'cancelados_count': Pedido.objects.filter(estado='CANCELADO').count(),
    })

@login_required(login_url='/admin/login/')
@require_POST
def panel_pedido_pago(request, pk):
    pedido = get_object_or_404(Pedido, pk=pk)
    pedido.pagado = not pedido.pagado
    pedido.save()
    estado_txt = "PAGADO (Verificado)" if pedido.pagado else "POR VERIFICAR"
    messages.success(request, f'Pago de {pedido.codigo} marcado como {estado_txt}.')
    return redirect('panel_pedidos')

@login_required(login_url='/admin/login/')
@require_POST
def panel_pedido_estado(request, pk, nuevo_estado):
    pedido = get_object_or_404(Pedido, pk=pk)

    if nuevo_estado == 'ELIMINAR':
        codigo = pedido.codigo
        pedido.delete()
        messages.success(request, f'Pedido {codigo} eliminado del historial.')
        return redirect('panel_pedidos')

    estados_validos = {'PENDIENTE', 'EMPACADO', 'ENTREGADO', 'CANCELADO'}

    if nuevo_estado in estados_validos:
        with transaction.atomic():
            if nuevo_estado in {'EMPACADO', 'ENTREGADO'} and not pedido.stock_descontado:
                for item in pedido.items.select_related('producto').all():
                    if item.producto:
                        item.producto.stock = max(0, item.producto.stock - item.cantidad)
                        item.producto.save()
                pedido.stock_descontado = True

            elif nuevo_estado == 'CANCELADO' and pedido.stock_descontado:
                for item in pedido.items.select_related('producto').all():
                    if item.producto:
                        item.producto.stock += item.cantidad
                        item.producto.save()
                pedido.stock_descontado = False

            pedido.estado = nuevo_estado
            pedido.save()
            messages.success(request, f'Pedido {pedido.codigo} actualizado a {pedido.get_estado_display()}.')

    return redirect('panel_pedidos')

@login_required(login_url='/admin/login/')
def panel_categorias(request):
    asegurar_categorias_base()
    if request.method == 'POST':
        accion = request.POST.get('accion', 'crear')
        if accion == 'crear':
            nombre = request.POST.get('nombre', '').strip().upper()
            if not nombre:
                messages.error(request, 'Escribe el nombre de la categoría.')
            elif Categoria.objects.filter(nombre=nombre).exists():
                messages.error(request, f'La categoría "{nombre}" ya existe.')
            else:
                ultimo_orden = Categoria.objects.count() + 1
                Categoria.objects.create(nombre=nombre, orden=ultimo_orden)
                messages.success(request, f'Categoría "{nombre}" agregada.')
        elif accion == 'eliminar':
            cat = get_object_or_404(Categoria, pk=request.POST.get('cat_id'))
            try:
                nombre = cat.nombre
                cat.delete()
                messages.success(request, f'Categoría "{nombre}" eliminada.')
            except ProtectedError:
                messages.error(request, f'No puedes borrar "{cat.nombre}" porque tiene prendas asignadas. Cámbialas de categoría primero.')
        return redirect('panel_categorias')

    return render(request, 'catalogo/panel_categorias.html', {
        'categorias': Categoria.objects.all(),
    })

@login_required(login_url='/admin/login/')
def panel_crear(request):
    asegurar_categorias_base()
    categorias = Categoria.objects.filter(activa=True)

    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        categoria_id = request.POST.get('categoria')
        etiqueta = request.POST.get('etiqueta', 'NEW IN')
        precio_raw = request.POST.get('precio', '0')
        precio_ant_raw = request.POST.get('precio_anterior', '').strip()
        stock = int(request.POST.get('stock', 1) or 0)
        tallas_sel = request.POST.getlist('tallas')
        tallas_extra = request.POST.get('tallas_personalizadas', '')
        descripcion = request.POST.get('descripcion', '').strip()
        activo = request.POST.get('activo') == 'on'
        imagen = request.FILES.get('imagen')

        try:
            precio = Decimal(precio_raw)
        except InvalidOperation:
            precio = Decimal('0.00')

        precio_anterior = None
        if precio_ant_raw:
            try:
                precio_anterior = Decimal(precio_ant_raw)
            except InvalidOperation:
                precio_anterior = None

        categoria_obj = Categoria.objects.filter(pk=categoria_id).first()

        if not nombre or not imagen or not categoria_obj:
            messages.error(request, 'El nombre, categoría y foto de la prenda son obligatorios.')
        else:
            Producto.objects.create(
                nombre=nombre,
                categoria=categoria_obj,
                etiqueta=etiqueta,
                precio=precio,
                precio_anterior=precio_anterior,
                stock=max(0, stock),
                tallas=_combinar_tallas(tallas_sel, tallas_extra),
                imagen=imagen,
                descripcion=descripcion,
                activo=activo,
            )
            messages.success(request, f'Prenda "{nombre}" publicada en el catálogo.')
            return redirect('panel_lista')

    return render(request, 'catalogo/panel_form.html', {
        'producto': None,
        'categorias': categorias,
        'etiquetas': Producto.ETIQUETAS,
        'tallas_disponibles': TALLAS_BASE,
        'tallas_marcadas': ['S', 'M', 'L'],
        'tallas_personalizadas': '',
    })

@login_required(login_url='/admin/login/')
def panel_editar(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    categorias = Categoria.objects.filter(activa=True)

    if request.method == 'POST':
        producto.nombre = request.POST.get('nombre', producto.nombre).strip()
        cat_id = request.POST.get('categoria')
        if cat_id:
            producto.categoria_id = int(cat_id)
        producto.etiqueta = request.POST.get('etiqueta', producto.etiqueta)
        producto.stock = max(0, int(request.POST.get('stock', producto.stock) or 0))
        tallas_sel = request.POST.getlist('tallas')
        tallas_extra = request.POST.get('tallas_personalizadas', '')
        producto.tallas = _combinar_tallas(tallas_sel, tallas_extra)
        producto.descripcion = request.POST.get('descripcion', '').strip()
        producto.activo = request.POST.get('activo') == 'on'

        try:
            producto.precio = Decimal(request.POST.get('precio', producto.precio))
        except InvalidOperation:
            pass

        precio_ant_raw = request.POST.get('precio_anterior', '').strip()
        if precio_ant_raw:
            try:
                producto.precio_anterior = Decimal(precio_ant_raw)
            except InvalidOperation:
                pass
        else:
            producto.precio_anterior = None

        if request.FILES.get('imagen'):
            producto.imagen = request.FILES['imagen']

        producto.save()
        messages.success(request, f'Cambios guardados en "{producto.nombre}".')
        return redirect('panel_lista')

    tallas_actuales = producto.lista_tallas()
    tallas_custom = [t for t in tallas_actuales if t not in TALLAS_BASE]

    return render(request, 'catalogo/panel_form.html', {
        'producto': producto,
        'categorias': categorias,
        'etiquetas': Producto.ETIQUETAS,
        'tallas_disponibles': TALLAS_BASE,
        'tallas_marcadas': tallas_actuales,
        'tallas_personalizadas': ', '.join(tallas_custom),
    })

@login_required(login_url='/admin/login/')
def panel_stock_rapido(request, pk, accion):
    if request.method == 'POST':
        producto = get_object_or_404(Producto, pk=pk)
        if accion == 'sumar':
            producto.stock += 1
        elif accion == 'restar' and producto.stock > 0:
            producto.stock -= 1
        elif accion == 'toggle':
            producto.activo = not producto.activo
        producto.save()
    return redirect('panel_lista')

@login_required(login_url='/admin/login/')
def panel_eliminar(request, pk):
    if request.method == 'POST':
        producto = get_object_or_404(Producto, pk=pk)
        nombre = producto.nombre
        producto.delete()
        messages.success(request, f'Se eliminó "{nombre}".')
    return redirect('panel_lista')