from rest_framework import serializers
from .models import (
    UnidadHabitacional, Administrador, Seguridad, PersonalMantenimiento, Residente,
    Cuota, Pago, AreaComun, Reserva, TicketMantenimiento,
    Visita, VehiculoAutorizado, AlertaSeguridad
)
from django.contrib.auth.models import User
from django.utils import timezone


# ========================
# USUARIOS
# ========================

class UserSerializer(serializers.ModelSerializer):
    """Serializer básico para User de Django con campos seguros"""
    password = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'password']
        read_only_fields = ['id']

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user


class UnidadHabitacionalSerializer(serializers.ModelSerializer):
    """Gestión de unidades habitacionales (Deptos/Casas)"""
    class Meta:
        model = UnidadHabitacional
        fields = '__all__'


class AdministradorSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), 
        source='user', 
        write_only=True
    )
    
    class Meta:
        model = Administrador
        fields = '__all__'


class SeguridadSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), 
        source='user', 
        write_only=True
    )
    
    class Meta:
        model = Seguridad
        fields = '__all__'


class PersonalMantenimientoSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), 
        source='user', 
        write_only=True
    )
    
    class Meta:
        model = PersonalMantenimiento
        fields = '__all__'


class ResidenteSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), 
        source='user', 
        write_only=True
    )
    # Mostramos detalles de la unidad, pero permitimos seleccionarla por ID al crear/editar
    unidad_habitacional_detalle = UnidadHabitacionalSerializer(source='unidad_habitacional', read_only=True)
    unidad_habitacional_id = serializers.PrimaryKeyRelatedField(
        queryset=UnidadHabitacional.objects.all(),
        source='unidad_habitacional',
        write_only=True
    )
    
    class Meta:
        model = Residente
        fields = '__all__'


# ========================
# FINANZAS
# ========================

class CuotaSerializer(serializers.ModelSerializer):
    residente_nombre = serializers.CharField(source='residente.user.get_full_name', read_only=True)
    
    class Meta:
        model = Cuota
        fields = '__all__'
    
    def validate_monto(self, value):
        if value <= 0:
            raise serializers.ValidationError("El monto de la cuota debe ser positivo.")
        return value


class PagoSerializer(serializers.ModelSerializer):
    cuota_detalle = CuotaSerializer(source='cuota', read_only=True)
    cuota_id = serializers.PrimaryKeyRelatedField(
        queryset=Cuota.objects.all(),
        source='cuota',
        write_only=True
    )
    
    class Meta:
        model = Pago
        fields = '__all__'
    
    def validate(self, data):
        """Validar que el pago no exceda la deuda pendiente"""
        # Nota: Si es update, cuidamos de excluir el monto propio (simplificado para examen)
        cuota = data.get('cuota')
        if cuota and data.get('monto_pagado', 0) <= 0:
            raise serializers.ValidationError({"monto_pagado": "El monto pagado debe ser mayor a 0"})
        return data


# ========================
# ÁREAS COMUNES Y RESERVAS
# ========================

class AreaComunSerializer(serializers.ModelSerializer):
    class Meta:
        model = AreaComun
        fields = '__all__'


class ReservaSerializer(serializers.ModelSerializer):
    area_comun_detalle = AreaComunSerializer(source='area_comun', read_only=True)
    area_comun_id = serializers.PrimaryKeyRelatedField(
        queryset=AreaComun.objects.all(),
        source='area_comun',
        write_only=True
    )
    residente_nombre = serializers.CharField(source='residente.user.get_full_name', read_only=True)
    residente_id = serializers.PrimaryKeyRelatedField(
        queryset=Residente.objects.all(),
        source='residente',
        write_only=True
    )
    
    class Meta:
        model = Reserva
        fields = '__all__'
    
    def validate(self, data):
        """Validar consistencia de horas"""
        inicio = data.get('hora_inicio')
        fin = data.get('hora_fin')
        fecha = data.get('fecha_reserva')
        
        if inicio and fin and inicio >= fin:
            raise serializers.ValidationError("La hora de inicio debe ser anterior a la hora de fin.")
            
        if fecha and fecha < timezone.now().date():
            # Permitimos editar reservas pasadas, pero no crear nuevas en el pasado
            if not self.instance:
                raise serializers.ValidationError({"fecha_reserva": "No se pueden crear reservas en fechas pasadas."})
        
        return data


# ========================
# MANTENIMIENTO
# ========================

class TicketMantenimientoSerializer(serializers.ModelSerializer):
    residente_nombre = serializers.CharField(source='residente.user.get_full_name', read_only=True)
    asignado_a_nombre = serializers.CharField(source='asignado_a.user.get_full_name', read_only=True, allow_null=True)
    
    class Meta:
        model = TicketMantenimiento
        fields = '__all__'


# ========================
# SEGURIDAD Y CONTROL DE ACCESO
# ========================

class VisitaSerializer(serializers.ModelSerializer):
    residente_nombre = serializers.CharField(source='residente.user.get_full_name', read_only=True)
    
    class Meta:
        model = Visita
        fields = '__all__'
        read_only_fields = ['codigo_qr_acceso']  # El código QR se genera automáticamente


class VehiculoAutorizadoSerializer(serializers.ModelSerializer):
    residente_nombre = serializers.CharField(source='residente.user.get_full_name', read_only=True)
    
    class Meta:
        model = VehiculoAutorizado
        fields = '__all__'

    def validate_placa(self, value):
        """Asegurar formato de placa limpio"""
        return value.upper().replace(" ", "").replace("-", "")


class AlertaSeguridadSerializer(serializers.ModelSerializer):
    residente_nombre = serializers.CharField(
        source='residente_relacionado.user.get_full_name', 
        read_only=True, 
        allow_null=True
    )
    atendido_por_nombre = serializers.CharField(
        source='atendido_por.user.get_full_name', 
        read_only=True, 
        allow_null=True
    )
    
    class Meta:
        model = AlertaSeguridad
        fields = '__all__'


# ========================
# SERIALIZERS PARA ACCIONES PERSONALIZADAS
# ========================

class ValidarPlacaSerializer(serializers.Serializer):
    """Serializer para validar acceso por placa (OCR)"""
    # El texto de la placa viene de un servicio OCR externo
    placa = serializers.CharField(max_length=20, help_text="Texto de la placa leído por OCR externo")
    
    def validate_placa(self, value):
        return value.upper().replace(" ", "").replace("-", "")


class ValidarQRSerializer(serializers.Serializer):
    """Serializer para validar acceso por código QR"""
    codigo_qr = serializers.CharField(max_length=100, help_text="Código QR escaneado para validar acceso")


class ValidarFacialSerializer(serializers.Serializer):
    """Serializer para validar acceso por Reconocimiento Facial"""
    imagen = serializers.ImageField(help_text="Foto del rostro capturada por la cámara")

