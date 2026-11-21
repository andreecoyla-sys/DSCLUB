from django.contrib import admin
from django.utils.html import format_html
from unfold.admin import ModelAdmin
from .models import Producto

@admin.register(Producto)
class ProductoAdmin(ModelAdmin):
    list_display = ('miniatura', 'nombre', 'categoria', 'precio', 'stock', 'tallas', 'etiqueta', 'activo')
    list_editable = ('precio', 'stock', 'etiqueta', 'activo')
    list_filter = ('categoria', 'etiqueta', 'activo')
    search_fields = ('nombre', 'descripcion')

    def miniatura(self, obj):
        if obj.imagen:
            return format_html('<img src="{}" style="width:45px; height:55px; object-fit:cover; border-radius:4px;" />', obj.imagen.url)
        return "-"
    miniatura.short_description = "Foto"