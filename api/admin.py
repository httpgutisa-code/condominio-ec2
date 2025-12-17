from django.contrib import admin
from .models import (
    UnidadHabitacional, Administrador, Seguridad, PersonalMantenimiento, Residente,
    Cuota, Pago, AreaComun, Reserva, TicketMantenimiento,
    Visita, VehiculoAutorizado, AlertaSeguridad
)


@admin.register(UnidadHabitacional)
class UnidadHabitacionalAdmin(admin.ModelAdmin):
    list_display = ['numero', 'torre', 'area_m2', 'activo']
    list_filter = ['activo', 'torre']
    search_fields = ['numero', 'torre']


@admin.register(Administrador)
class AdministradorAdmin(admin.ModelAdmin):
    list_display = ['user', 'telefono', 'fecha_contratacion']
    search_fields = ['user__username', 'user__email']


@admin.register(Seguridad)
class SeguridadAdmin(admin.ModelAdmin):
    list_display = ['user', 'telefono', 'turno', 'fecha_contratacion']
    list_filter = ['turno']
    search_fields = ['user__username', 'user__email']


@admin.register(PersonalMantenimiento)
class PersonalMantenimientoAdmin(admin.ModelAdmin):
    list_display = ['user', 'telefono', 'especialidad', 'fecha_contratacion']
    list_filter = ['especialidad']
    search_fields = ['user__username', 'user__email']


@admin.register(Residente)
class ResidenteAdmin(admin.ModelAdmin):
    list_display = ['user', 'unidad_habitacional', 'telefono', 'es_propietario', 'score_morosidad_ia']
    list_filter = ['es_propietario', 'unidad_habitacional']
    search_fields = ['user__username', 'user__email', 'unidad_habitacional__numero']


@admin.register(Cuota)
class CuotaAdmin(admin.ModelAdmin):
    list_display = ['residente', 'mes', 'monto', 'fecha_vencimiento', 'estado']
    list_filter = ['estado', 'fecha_vencimiento']
    search_fields = ['residente__user__username', 'mes']


@admin.register(Pago)
class PagoAdmin(admin.ModelAdmin):
    list_display = ['cuota', 'monto_pagado', 'fecha_pago', 'metodo_pago', 'referencia_comprobante']
    list_filter = ['metodo_pago', 'fecha_pago']
    search_fields = ['referencia_comprobante']


@admin.register(AreaComun)
class AreaComunAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'capacidad_personas', 'costo_reserva', 'disponible']
    list_filter = ['disponible']
    search_fields = ['nombre']


@admin.register(Reserva)
class ReservaAdmin(admin.ModelAdmin):
    list_display = ['area_comun', 'residente', 'fecha_reserva', 'hora_inicio', 'hora_fin', 'estado']
    list_filter = ['estado', 'fecha_reserva']
    search_fields = ['residente__user__username', 'area_comun__nombre']


@admin.register(TicketMantenimiento)
class TicketMantenimientoAdmin(admin.ModelAdmin):
    list_display = ['id', 'titulo', 'residente', 'asignado_a', 'prioridad', 'estado', 'fecha_creacion']
    list_filter = ['estado', 'prioridad', 'fecha_creacion']
    search_fields = ['titulo', 'descripcion', 'residente__user__username']


@admin.register(Visita)
class VisitaAdmin(admin.ModelAdmin):
    list_display = ['nombre_visitante', 'residente', 'fecha_visita', 'hora_entrada_real', 'codigo_qr_acceso']
    list_filter = ['fecha_visita']
    search_fields = ['nombre_visitante', 'documento_visitante', 'codigo_qr_acceso', 'residente__user__username']


@admin.register(VehiculoAutorizado)
class VehiculoAutorizadoAdmin(admin.ModelAdmin):
    list_display = ['placa', 'residente', 'marca', 'modelo', 'tipo_vehiculo', 'autorizado']
    list_filter = ['autorizado', 'tipo_vehiculo']
    search_fields = ['placa', 'residente__user__username', 'marca', 'modelo']


@admin.register(AlertaSeguridad)
class AlertaSeguridadAdmin(admin.ModelAdmin):
    list_display = ['tipo_alerta', 'fecha_hora', 'residente_relacionado', 'atendido_por', 'resuelto']
    list_filter = ['tipo_alerta', 'resuelto', 'fecha_hora']
    search_fields = ['descripcion', 'tipo_alerta']
