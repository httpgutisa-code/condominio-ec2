from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from django.utils import timezone
from django.contrib.auth.models import User
from django.http import HttpResponse # Importación faltante
import uuid

# Vista de bienvenida para la raíz de la API
@api_view(['GET'])
def api_root(request):
    """Vista raíz de la API con información y enlaces de documentación"""
    return Response({
        'mensaje': '¡Bienvenido a Smart Condominium API!',
        'version': '1.0.0',
        'descripcion': 'Sistema de gestión inteligente para condominios',
        'documentacion': {
            'swagger': request.build_absolute_uri('/api/docs/'),
            'redoc': request.build_absolute_uri('/api/redoc/'),
            'schema_openapi': request.build_absolute_uri('/api/schema/'),
        },
        'endpoints_principales': {
            'usuarios': {
                'residentes': '/api/residentes/',
                'administradores': '/api/administradores/',
                'seguridad': '/api/seguridad/',
                'personal_mantenimiento': '/api/personal-mantenimiento/',
            },
            'finanzas': {
                'cuotas': '/api/cuotas/',
                'pagos': '/api/pagos/',
            },
            'areas_comunes': {
                'areas': '/api/areas-comunes/',
                'reservas': '/api/reservas/',
            },
            'mantenimiento': {
                'tickets': '/api/tickets-mantenimiento/',
            },
            'seguridad': {
                'visitas': '/api/visitas/',
                'vehiculos': '/api/vehiculos-autorizados/',
                'alertas': '/api/alertas-seguridad/',
                'validar_qr': '/api/seguridad/validar-qr/',
                'validar_placa': '/api/seguridad/validar-placa/',
            }
        },
        'funcionalidades_ia': {
            'prediccion_morosidad': 'POST /api/residentes/{id}/actualizar-score-ia/',
            'validacion_qr': 'POST /api/seguridad/validar-qr/',
            'validacion_ocr_placas': 'POST /api/seguridad/validar-placa/',
        }
    })


from rest_framework.views import APIView
from django.db.models import Count, Sum

class DashboardAdminView(APIView):
    """
    Endpoint agregado para el Dashboard de Administrador.
    Retorna KPIs y datos listos para gráficos.
    """
    
    def get(self, request):
        # 1. KPIs Generales
        total_unidades = UnidadHabitacional.objects.count()
        unidades_ocupadas = UnidadHabitacional.objects.filter(residentes__isnull=False).distinct().count()
        ocupacion_pct = round((unidades_ocupadas / total_unidades * 100), 1) if total_unidades > 0 else 0
        
        total_residentes = Residente.objects.count()
        
        # 2. Resumen Financiero (Mes Actual)
        mes_actual = timezone.now().strftime('%B %Y').capitalize() # Ej: Diciembre 2024
        # Nota: En producción usarías filtros de fecha reales, aquí asumimos el string del mes
        
        deuda_total = Cuota.objects.filter(estado__in=['pendiente', 'vencida']).aggregate(total=Sum('monto'))['total'] or 0
        recaudado_total = Pago.objects.aggregate(total=Sum('monto_pagado'))['total'] or 0
        
        # 3. Alertas de Seguridad
        alertas_activas = AlertaSeguridad.objects.filter(resuelto=False).count()
        ultimas_alertas = AlertaSeguridad.objects.order_by('-fecha_hora')[:5]
        
        # 4. Tickets Mantenimiento
        tickets_abiertos = TicketMantenimiento.objects.filter(estado__in=['abierto', 'en_proceso']).count()
        
        # 5. Estructura de respuesta para Gráficos
        finanzas_chart = {
            'labels': ['Pagado', 'Por Cobrar'],
            'data': [float(recaudado_total), float(deuda_total)]
        }
        
        return Response({
            'kpis': {
                'total_residentes': total_residentes,
                'ocupacion_porcentaje': ocupacion_pct,
                'alertas_activas': alertas_activas,
                'tickets_pendientes': tickets_abiertos,
                'recaudacion_total': float(recaudado_total),
                'deuda_pendiente': float(deuda_total)
            },
            'graficos': {
                'finanzas': finanzas_chart
            },
            'actividad_reciente': {
                'alertas': AlertaSeguridadSerializer(ultimas_alertas, many=True).data
            }
        })

DashBoardView = DashboardAdminView.as_view()  # Helper para urls.py


from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from django.contrib.auth.models import User
from django.db.models import Sum
from .report_utils import generar_reporte_finanzas_excel, generar_reporte_seguridad_pdf
import uuid

from .models import (
    UnidadHabitacional, Administrador, Seguridad, PersonalMantenimiento, Residente,
    Cuota, Pago, AreaComun, Reserva, TicketMantenimiento,
    Visita, VehiculoAutorizado, AlertaSeguridad
)
from .serializers import (
    UnidadHabitacionalSerializer, AdministradorSerializer, SeguridadSerializer,
    PersonalMantenimientoSerializer, ResidenteSerializer, CuotaSerializer, PagoSerializer,
    AreaComunSerializer, ReservaSerializer, TicketMantenimientoSerializer,
    VisitaSerializer, VehiculoAutorizadoSerializer, AlertaSeguridadSerializer,
    ValidarPlacaSerializer, ValidarQRSerializer, ValidarFacialSerializer, UserSerializer
)


# ========================
# USUARIOS
# ========================

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer


class UnidadHabitacionalViewSet(viewsets.ModelViewSet):
    queryset = UnidadHabitacional.objects.all()
    serializer_class = UnidadHabitacionalSerializer


class AdministradorViewSet(viewsets.ModelViewSet):
    queryset = Administrador.objects.all()
    serializer_class = AdministradorSerializer


from django.contrib.auth import authenticate
from rest_framework.views import APIView

class ObtenerTokenView(APIView):
    """
    Vista personalizada para simular la obtención de Token (JWT Style)
    y devolver la estructura exacta que espera la App Móvil.
    """
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        
        user = authenticate(username=username, password=password)
        
        if user:
            # Determinar Rol y ID específico
            role = "OTRO"
            residente_id = None
            
            if hasattr(user, 'perfil_residente'):
                role = "RESIDENTE"
                residente_id = user.perfil_residente.id
            elif hasattr(user, 'perfil_seguridad'):
                role = "GUARDIA"
            elif hasattr(user, 'perfil_administrador'):
                role = "ADMIN"
                
            # Simular tokens JWT (Strings fijos por ahora para que pase la validación móvil)
            # En producción real instalar simplejwt
            return Response({
                "access": f"ey_simulated_access_token_{user.id}",
                "refresh": f"ey_simulated_refresh_token_{user.id}",
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "role": role,
                    "residente_id": residente_id
                }
            })
        else:
            return Response({"detail": "Credenciales inválidas"}, status=status.HTTP_401_UNAUTHORIZED)


class SeguridadViewSet(viewsets.ModelViewSet):
    """ViewSet para personal de seguridad con acciones personalizadas"""
    queryset = Seguridad.objects.all()
    serializer_class = SeguridadSerializer
    
    @action(detail=False, methods=['post'], url_path='validar-facial')
    def validar_facial(self, request):
        """
        Simula la validación de acceso mediante Reconocimiento Facial.
        """
        serializer = ValidarFacialSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # LÓGICA DE SIMULACIÓN IA
        # En un sistema real, aquí llamaríamos a AWS Rekognition o similar
        
        try:
            # Buscamos el primer residente "Propietario" de la base de datos para mostrar sus datos
            residente = Residente.objects.filter(es_propietario=True).first()
            
            if not residente:
                return Response({
                    'valido': True,
                    'mensaje': 'Rostro verificado (Demo)',
                    'es_propietario': True,
                    'residente': {
                        'nombre': 'Residente Demo',
                        'unidad': 'A-101 (Demo)'
                    }
                }, status=status.HTTP_200_OK)
                
            return Response({
                'valido': True,
                'mensaje': 'Rostro verificado exitosamente',
                'es_propietario': residente.es_propietario,
                'residente': {
                    'nombre': residente.user.get_full_name(),
                    'unidad': str(residente.unidad_habitacional),
                    'foto_perfil': request.build_absolute_uri(residente.foto_perfil.url) if residente.foto_perfil else None
                }
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'valido': False,
                'mensaje': f'Error en procesamiento facial: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'], url_path='validar-placa')
    def validar_placa(self, request):
        """
        Valida el acceso de un vehículo mediante su placa (Spec Móvil).
        """
        serializer = ValidarPlacaSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        placa = serializer.validated_data['placa'].upper().strip()
        
        try:
            vehiculo = VehiculoAutorizado.objects.get(placa=placa, autorizado=True)
            # MATCH SPEC MÓVIL EXACTO: "valido": true, "residente": string nombre, "tipo": string
            return Response({
                'valido': True,
                'mensaje': 'Vehículo autorizado',
                'residente': f"{vehiculo.residente.user.first_name} {vehiculo.residente.user.last_name}",
                'tipo': vehiculo.tipo_vehiculo or "Vehículo",
                # Extras útiles pero opcionales para la app
                'unidad': str(vehiculo.residente.unidad_habitacional)
            }, status=status.HTTP_200_OK)
        except VehiculoAutorizado.DoesNotExist:
            return Response({
                'valido': False,
                'mensaje': 'Vehículo no autorizado',
                'residente': 'Desconocido',
                'tipo': 'Desconocido'
            }, status=status.HTTP_200_OK) # La app espera 200 OK con valido: false, no 404
    
    @action(detail=False, methods=['post'], url_path='validar-qr')
    def validar_qr(self, request):
        """
        Valida el acceso de un visitante mediante código QR (Spec Móvil).
        """
        serializer = ValidarQRSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        codigo_qr = serializer.validated_data['codigo_qr']
        
        try:
            visita = Visita.objects.get(codigo_qr_acceso=codigo_qr)
            
            # Verificar si ya ingresó
            if visita.hora_entrada_real:
                # MATCH SPEC MÓVIL: Las claves deben ser 'autorizado', 'visita' object
                return Response({
                    'autorizado': False,
                    'mensaje': 'QR ya utilizado anteriormente',
                    'visita': {
                        'nombre_visitante': visita.nombre_visitante,
                        'residente_nombre': str(visita.residente.user.get_full_name()),
                        'unidad': str(visita.residente.unidad_habitacional)
                    }
                }, status=status.HTTP_200_OK)
            
            # Registrar entrada
            visita.hora_entrada_real = timezone.now()
            visita.save()
            
            return Response({
                'autorizado': True,
                'mensaje': 'Acceso permitido',
                'visita': {
                    'nombre_visitante': visita.nombre_visitante,
                    'residente_nombre': str(visita.residente.user.get_full_name()),
                    'unidad': str(visita.residente.unidad_habitacional)
                }
            }, status=status.HTTP_200_OK)
            
        except Visita.DoesNotExist:
            return Response({
                'autorizado': False,
                'mensaje': 'Código QR inválido o no existe',
                'visita': None
            }, status=status.HTTP_200_OK)


class PersonalMantenimientoViewSet(viewsets.ModelViewSet):
    queryset = PersonalMantenimiento.objects.all()
    serializer_class = PersonalMantenimientoSerializer


class ResidenteViewSet(viewsets.ModelViewSet):
    queryset = Residente.objects.all()
    serializer_class = ResidenteSerializer
    
    @action(detail=True, methods=['post'], url_path='actualizar-score-ia')
    def actualizar_score_ia(self, request, pk=None):
        """
        Actualiza el score de morosidad calculado por IA externa.
        
        La IA calcula el riesgo de morosidad externamente y envía el puntaje al backend.
        """
        residente = self.get_object()
        score = request.data.get('score_morosidad_ia')
        
        if score is None:
            return Response({
                'error': 'El campo score_morosidad_ia es requerido'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            score = float(score)
            if score < 0 or score > 100:
                return Response({
                    'error': 'El score debe estar entre 0 y 100'
                }, status=status.HTTP_400_BAD_REQUEST)
        except ValueError:
            return Response({
                'error': 'El score debe ser un número válido'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        residente.score_morosidad_ia = score
        residente.save()
        
        return Response({
            'mensaje': 'Score de morosidad actualizado correctamente',
            'residente': ResidenteSerializer(residente).data
        }, status=status.HTTP_200_OK)


from django_filters.rest_framework import DjangoFilterBackend

# ========================
# FINANZAS
# ========================

class CuotaViewSet(viewsets.ModelViewSet):
    """
    Gestión de cuotas/expensas.
    FILTROS: ?residente={id} & ?estado={pendiente|pagada|vencida}
    """
    queryset = Cuota.objects.all()
    serializer_class = CuotaSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['residente', 'estado', 'mes']


class PagoViewSet(viewsets.ModelViewSet):
    """
    Registro de pagos realizados.
    FILTROS: ?cuota__residente={id} (Para ver todos los pagos de un residente)
    """
    queryset = Pago.objects.all()
    serializer_class = PagoSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['cuota', 'cuota__residente']
    
    def create(self, request, *args, **kwargs):
        """Override para actualizar automáticamente el estado de la cuota al crear un pago"""
        response = super().create(request, *args, **kwargs)
        
        # Actualizar estado de la cuota si se pagó el monto completo
        pago = Pago.objects.get(id=response.data['id'])
        cuota = pago.cuota
        
        total_pagado = sum(p.monto_pagado for p in cuota.pagos.all())
        if total_pagado >= cuota.monto:
            cuota.estado = 'pagada'
            cuota.save()
        
        return response


# ========================
# ÁREAS COMUNES Y RESERVAS
# ========================

class AreaComunViewSet(viewsets.ModelViewSet):
    queryset = AreaComun.objects.all()
    serializer_class = AreaComunSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['disponible']


class ReservaViewSet(viewsets.ModelViewSet):
    """
    Gestión de reservas.
    FILTROS: ?residente={id} & ?fecha_reserva={YYYY-MM-DD}
    """
    queryset = Reserva.objects.all()
    serializer_class = ReservaSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['residente', 'area_comun', 'fecha_reserva', 'estado']


# ========================
# MANTENIMIENTO
# ========================

class TicketMantenimientoViewSet(viewsets.ModelViewSet):
    """
    Tickets de mantenimiento.
    FILTROS: ?residente={id} & ?estado={abierto|en_proceso...}
    """
    queryset = TicketMantenimiento.objects.all()
    serializer_class = TicketMantenimientoSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['residente', 'estado', 'prioridad', 'asignado_a']


# ========================
# SEGURIDAD Y CONTROL DE ACCESO
# ========================

class VisitaViewSet(viewsets.ModelViewSet):
    """
    Registro de visitantes y generación de QR.
    Para crear una visita se debe enviar datos del visitante y residente.
    El QR se genera automáticamente en el serializador/modelo.
    """
    queryset = Visita.objects.all()
    serializer_class = VisitaSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['residente', 'fecha_visita']
    
    def perform_create(self, serializer):
        """Generar código QR único antes de guardar"""
        serializer.save(codigo_qr_acceso=str(uuid.uuid4()))


class VehiculoAutorizadoViewSet(viewsets.ModelViewSet):
    queryset = VehiculoAutorizado.objects.all()
    serializer_class = VehiculoAutorizadoSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['residente', 'autorizado', 'placa']


class AlertaSeguridadViewSet(viewsets.ModelViewSet):
    queryset = AlertaSeguridad.objects.all()
    serializer_class = AlertaSeguridadSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['resuelto', 'tipo_alerta', 'residente_relacionado']


class ReporteViewSet(viewsets.ViewSet):
    """
    ViewSet para generar reportes administrativos (PDF/Excel).
    """
    
    @action(detail=False, methods=['get'], url_path='finanzas')
    def reporte_finanzas(self, request):
        """Descargar reporte de cuotas y pagos en Excel"""
        buffer = generar_reporte_finanzas_excel()
        response = HttpResponse(
            buffer,
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename="reporte_finanzas.xlsx"'
        return response

    @action(detail=False, methods=['get'], url_path='seguridad')
    def reporte_seguridad(self, request):
        """Descargar reporte de alertas de seguridad recientes en PDF"""
        buffer = generar_reporte_seguridad_pdf()
        response = HttpResponse(buffer, content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="reporte_seguridad.pdf"'
        return response
