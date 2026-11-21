from django.db import models

class Categoria(models.Model):
    nombre = models.CharField(max_length=50, unique=True)
    orden = models.PositiveIntegerField(default=0)
    activa = models.BooleanField(default=True)

    class Meta:
        ordering = ['orden', 'nombre']
        verbose_name = 'Categoría'
        verbose_name_plural = 'Categorías'

    def save(self, *args, **kwargs):
        self.nombre = self.nombre.strip().upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nombre


class Producto(models.Model):
    ETIQUETAS = [
        ('NEW IN', 'New In'),
        ('STOCK', 'Stock'),
        ('OFERTA', 'Oferta'),
        ('AGOTADO', 'Agotado'),
    ]

    nombre = models.CharField(max_length=150)
    categoria = models.ForeignKey(
        Categoria,
        on_delete=models.PROTECT,
        related_name='productos'
    )
    etiqueta = models.CharField(max_length=20, choices=ETIQUETAS, default='NEW IN')
    precio = models.DecimalField(max_digits=8, decimal_places=2)
    precio_anterior = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    stock = models.PositiveIntegerField(default=1)
    tallas = models.CharField(
        max_length=50,
        default='S, M, L',
        help_text='Separa las tallas por coma. Ej: S, M, L o 30, 32, 34'
    )
    imagen = models.ImageField(upload_to='prendas/')
    descripcion = models.TextField(blank=True)
    activo = models.BooleanField(default=True, verbose_name='Visible en catálogo')
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-creado']
        verbose_name = 'Prenda'
        verbose_name_plural = 'Prendas'

    def __str__(self):
        return f"{self.nombre} ({self.categoria.nombre})"

    def lista_tallas(self):
        return [t.strip().upper() for t in self.tallas.split(',') if t.strip()]


class Pedido(models.Model):
    ESTADOS = [
        ('PENDIENTE', 'Pendiente'),
        ('EMPACADO', 'Listo / Empacado'),
        ('ENTREGADO', 'Entregado'),
        ('CANCELADO', 'Cancelado'),
    ]

    METODOS_PAGO = [
        ('YAPE / PLIN', 'Yape / Plin'),
        ('TRANSFERENCIA', 'Transferencia'),
        ('CONTRAENTREGA', 'Contraentrega / Efectivo'),
    ]

    cliente_nombre = models.CharField(max_length=120)
    cliente_telefono = models.CharField(max_length=30, blank=True)
    tipo_entrega = models.CharField(max_length=40, default='Delivery')
    direccion = models.TextField(blank=True)
    metodo_pago = models.CharField(max_length=30, choices=METODOS_PAGO, default='YAPE / PLIN')
    notas = models.TextField(blank=True)
    costo_envio = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    pagado = models.BooleanField(default=False)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='PENDIENTE')
    stock_descontado = models.BooleanField(default=False)
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-creado']
        verbose_name = 'Pedido'
        verbose_name_plural = 'Pedidos'

    @property
    def codigo(self):
        return f"DS-{self.id:04d}"

    @property
    def subtotal_prendas(self):
        return max(0, self.total - self.costo_envio)

    def __str__(self):
        return f"{self.codigo} - {self.cliente_nombre}"


class DetallePedido(models.Model):
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name='items')
    producto = models.ForeignKey(Producto, on_delete=models.SET_NULL, null=True, blank=True)
    nombre_producto = models.CharField(max_length=150)
    talla = models.CharField(max_length=20)
    cantidad = models.PositiveIntegerField(default=1)
    precio_unitario = models.DecimalField(max_digits=8, decimal_places=2)

    @property
    def subtotal(self):
        return self.cantidad * self.precio_unitario

    def __str__(self):
        return f"{self.cantidad}x {self.nombre_producto} ({self.talla})"