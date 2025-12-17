from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    api_root,
    UserViewSet, UnidadHabitacionalViewSet, AdministradorViewSet, SeguridadViewSet,
    PersonalMantenimientoViewSet, ResidenteViewSet, CuotaViewSet, PagoViewSet,
    AreaComunViewSet, ReservaViewSet, TicketMantenimientoViewSet,
    VisitaViewSet, VehiculoAutorizadoViewSet, AlertaSeguridadViewSet,
    DashBoardView, ObtenerTokenView, ReporteViewSet
)

# Crear router
router = DefaultRouter()

# Registrar ViewSets
# Usuarios
router.register(r'users', UserViewSet, basename='user')
router.register(r'unidades-habitacionales', UnidadHabitacionalViewSet, basename='unidad-habitacional')
router.register(r'administradores', AdministradorViewSet, basename='administrador')
router.register(r'seguridad', SeguridadViewSet, basename='seguridad')
router.register(r'personal-mantenimiento', PersonalMantenimientoViewSet, basename='personal-mantenimiento')
router.register(r'residentes', ResidenteViewSet, basename='residente')

# Finanzas
router.register(r'cuotas', CuotaViewSet, basename='cuota')
router.register(r'pagos', PagoViewSet, basename='pago')

# Áreas Comunes
router.register(r'areas-comunes', AreaComunViewSet, basename='area-comun')
router.register(r'reservas', ReservaViewSet, basename='reserva')

# Mantenimiento
router.register(r'tickets-mantenimiento', TicketMantenimientoViewSet, basename='ticket-mantenimiento')

# Seguridad y Control de Acceso
router.register(r'visitas', VisitaViewSet, basename='visita')
router.register(r'vehiculos-autorizados', VehiculoAutorizadoViewSet, basename='vehiculo-autorizado')
router.register(r'alertas-seguridad', AlertaSeguridadViewSet, basename='alerta-seguridad')
router.register(r'reportes', ReporteViewSet, basename='reportes')

# URLs
urlpatterns = [
    path('', api_root, name='api-root'),  # Vista de bienvenida
    path('dashboard/admin/', DashBoardView, name='dashboard-admin'),  # Endpoint para KPIs
    path('token/', ObtenerTokenView.as_view(), name='token_obtain_pair'), # Endpoint Auth (Simulado)
    path('', include(router.urls)),
]
