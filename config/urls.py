from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from catalogo import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.inicio, name='inicio'),
    path('api/pedido/', views.crear_pedido, name='crear_pedido'),
    path('panel/', views.panel_lista, name='panel_lista'),
    path('panel/pedidos/', views.panel_pedidos, name='panel_pedidos'),
    path('panel/pedidos/<int:pk>/pago/', views.panel_pedido_pago, name='panel_pedido_pago'),
    path('panel/pedidos/<int:pk>/<str:nuevo_estado>/', views.panel_pedido_estado, name='panel_pedido_estado'),
    path('panel/categorias/', views.panel_categorias, name='panel_categorias'),
    path('panel/nueva/', views.panel_crear, name='panel_crear'),
    path('panel/editar/<int:pk>/', views.panel_editar, name='panel_editar'),
    path('panel/stock/<int:pk>/<str:accion>/', views.panel_stock_rapido, name='panel_stock_rapido'),
    path('panel/eliminar/<int:pk>/', views.panel_eliminar, name='panel_eliminar'),
    path('panel/recorte-masivo/', views.panel_recorte_masivo, name='panel_recorte_masivo'),
    path('panel/recorte-masivo/<int:pk>/', views.panel_actualizar_imagen_lote, name='panel_actualizar_imagen_lote'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)