from django.db import models
from django.contrib.auth.models import User


# ========================
# GESTIÓN DE USUARIOS
# ========================

class UnidadHabitacional(models.Model):
    """
    Modelo que representa un departamento o casa dentro del condominio.
    
    Relaciones:
        - Referenciado por: Residente
    """
    numero = models.CharField(max_length=20, unique=True, help_text="Identificador único (ej: A-101)")
    torre = models.CharField(max_length=50, blank=True, null=True)
    area_m2 = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    activo = models.BooleanField(default=True, help_text="Indica si la unidad está ocupable")
    
    class Meta:
        verbose_name_plural = "Unidades Habitacionales"
        ordering = ['torre', 'numero']  # Mejora de ordenamiento para el admin
    
    def __str__(self):
        return f"{self.torre} - {self.numero}" if self.torre else self.numero


class Administrador(models.Model):
    """
    Perfil extendido para usuarios con rol de Administrador.
    Gestiona el sistema pero no necesariamente vive en el condominio.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil_administrador')
    telefono = models.CharField(max_length=20, blank=True, null=True)
    fecha_contratacion = models.DateField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = "Administradores"
    
    def __str__(self):
        return f"Admin: {self.user.get_full_name() or self.user.username}"


class Seguridad(models.Model):
    """
    Perfil para personal de seguridad.
    Encargado de validar accesos (QR, Placas) y gestionar alertas.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil_seguridad')
    telefono = models.CharField(max_length=20, blank=True, null=True)
    turno = models.CharField(max_length=50, blank=True, null=True, help_text="Ej: Mañana, Tarde, Noche")
    fecha_contratacion = models.DateField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = "Personal de Seguridad"
    
    def __str__(self):
        return f"Seguridad: {self.user.get_full_name() or self.user.username}"


class PersonalMantenimiento(models.Model):
    """
    Perfil para técnicos de mantenimiento.
    Se les asignan tickets para resolver problemas en unidades o áreas comunes.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil_mantenimiento')
    telefono = models.CharField(max_length=20, blank=True, null=True)
    especialidad = models.CharField(max_length=100, blank=True, null=True, help_text="Ej: Plomería, Electricidad")
    fecha_contratacion = models.DateField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = "Personal de Mantenimiento"
    
    def __str__(self):
        return f"Mantenimiento: {self.user.get_full_name() or self.user.username} ({self.especialidad})"


class Residente(models.Model):
    """
    Perfil principal del usuario final.
    
    IMPORTANTE:
        - Vinculado a una Unidad Habitacional.
        - Contiene `score_morosidad_ia` poblando externamente.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil_residente')
    unidad_habitacional = models.ForeignKey(UnidadHabitacional, on_delete=models.CASCADE, related_name='residentes')
    telefono = models.CharField(max_length=20, blank=True, null=True)
    es_propietario = models.BooleanField(default=True)
    
    # Campo calculado por IA externa (Predicción de riesgo)
    score_morosidad_ia = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        blank=True, 
        null=True,
        help_text="Puntaje (0-100) calculado por IA externa que indica probabilidad de impago."
    )
    
    # Nuevo: Foto para Reconocimiento Facial
    foto_perfil = models.ImageField(upload_to='residentes/fotos/', blank=True, null=True)
    
    class Meta:
        verbose_name_plural = "Residentes"
    
    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} - {self.unidad_habitacional}"


# ========================
# FINANZAS
# ========================

class Cuota(models.Model):
    """
    Registro de deuda mensual (expensas).
    Puede estar en estado pendiente, pagada o vencida.
    """
    ESTADOS = [
        ('pendiente', 'Pendiente'),
        ('pagada', 'Pagada'),
        ('vencida', 'Vencida'),
    ]
    
    residente = models.ForeignKey(Residente, on_delete=models.CASCADE, related_name='cuotas')
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    mes = models.CharField(max_length=20, help_text="Ej: Enero 2024")
    fecha_vencimiento = models.DateField()
    estado = models.CharField(max_length=20, choices=ESTADOS, default='pendiente')
    descripcion = models.TextField(blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = "Cuotas"
        ordering = ['-fecha_vencimiento']
    
    def __str__(self):
        return f"Cuota {self.mes} - {self.residente.user.username} ({self.get_estado_display()})"


class Pago(models.Model):
    """
    Registro transaccional de un pago realizado.
    Vinculado a una Cuota específica.
    """
    cuota = models.ForeignKey(Cuota, on_delete=models.CASCADE, related_name='pagos')
    monto_pagado = models.DecimalField(max_digits=10, decimal_places=2)
    fecha_pago = models.DateTimeField(auto_now_add=True)
    metodo_pago = models.CharField(max_length=50, blank=True, null=True)
    referencia_comprobante = models.CharField(max_length=100, blank=True, null=True)
    notas = models.TextField(blank=True, null=True)
    
    class Meta:
        verbose_name_plural = "Pagos"
        ordering = ['-fecha_pago']
    
    def __str__(self):
        return f"Pago ${self.monto_pagado} - {self.cuota}"


# ========================
# ÁREAS COMUNES Y RESERVAS
# ========================

class AreaComun(models.Model):
    """
    Espacios compartidos susceptibles de reserva.
    """
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, null=True)
    capacidad_personas = models.IntegerField(blank=True, null=True)
    costo_reserva = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    disponible = models.BooleanField(default=True)
    
    class Meta:
        verbose_name_plural = "Áreas Comunes"
    
    def __str__(self):
        return self.nombre


class Reserva(models.Model):
    """
    Solicitud de uso de un Área Común en un horario específico.
    """
    ESTADOS = [
        ('pendiente', 'Pendiente'),
        ('confirmada', 'Confirmada'),
        ('cancelada', 'Cancelada'),
        ('completada', 'Completada'),
    ]
    
    area_comun = models.ForeignKey(AreaComun, on_delete=models.CASCADE, related_name='reservas')
    residente = models.ForeignKey(Residente, on_delete=models.CASCADE, related_name='reservas')
    fecha_reserva = models.DateField()
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()
    estado = models.CharField(max_length=20, choices=ESTADOS, default='pendiente')
    cantidad_personas = models.IntegerField(default=1)
    notas = models.TextField(blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = "Reservas"
        ordering = ['-fecha_reserva', '-hora_inicio']
    
    def __str__(self):
        return f"Reserva: {self.area_comun.nombre} - {self.fecha_reserva}"


# ========================
# MANTENIMIENTO
# ========================

class TicketMantenimiento(models.Model):
    """
    Reporte de incidencias o solicitudes de reparación.
    """
    ESTADOS = [
        ('abierto', 'Abierto'),
        ('en_proceso', 'En Proceso'),
        ('resuelto', 'Resuelto'),
        ('cerrado', 'Cerrado'),
    ]
    
    PRIORIDADES = [
        ('baja', 'Baja'),
        ('media', 'Media'),
        ('alta', 'Alta'),
        ('urgente', 'Urgente'),
    ]
    
    residente = models.ForeignKey(Residente, on_delete=models.CASCADE, related_name='tickets_mantenimiento')
    asignado_a = models.ForeignKey(
        PersonalMantenimiento, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='tickets_asignados',
        help_text="Técnico encargado de la incidencia"
    )
    titulo = models.CharField(max_length=200)
    descripcion = models.TextField()
    prioridad = models.CharField(max_length=20, choices=PRIORIDADES, default='media')
    estado = models.CharField(max_length=20, choices=ESTADOS, default='abierto')
    costo_estimado = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    costo_real = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_resolucion = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        verbose_name_plural = "Tickets de Mantenimiento"
        ordering = ['-fecha_creacion']
    
    def __str__(self):
        return f"Ticket #{self.id} ({self.get_estado_display()}) - {self.titulo}"


# ========================
# SEGURIDAD Y CONTROL DE ACCESO
# ========================

class Visita(models.Model):
    """
    Registro de visitantes externos.
    
    LÓGICA ABSTRAÍDA:
        - `codigo_qr_acceso`: Token único generado por backend.
        - No se procesa imagen QR, se valida solo el string.
    """
    residente = models.ForeignKey(Residente, on_delete=models.CASCADE, related_name='visitas')
    nombre_visitante = models.CharField(max_length=200)
    documento_visitante = models.CharField(max_length=50, blank=True, null=True)
    fecha_visita = models.DateField()
    hora_entrada_esperada = models.TimeField()
    hora_salida_esperada = models.TimeField(blank=True, null=True)
    
    codigo_qr_acceso = models.CharField(max_length=100, unique=True, blank=True, null=True)
    
    hora_entrada_real = models.DateTimeField(blank=True, null=True)
    hora_salida_real = models.DateTimeField(blank=True, null=True)
    autorizado_por_seguridad = models.ForeignKey(
        Seguridad, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='visitas_autorizadas'
    )
    notas = models.TextField(blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = "Visitas"
        ordering = ['-fecha_visita', '-hora_entrada_esperada']
    
    def __str__(self):
        return f"Visita: {self.nombre_visitante} -> {self.residente}"


class VehiculoAutorizado(models.Model):
    """
    Vehículos permitidos para ingreso automático.
    
    LÓGICA OCR:
        - `placa`: String que se compara con el resultado del OCR externo.
    """
    residente = models.ForeignKey(Residente, on_delete=models.CASCADE, related_name='vehiculos')
    placa = models.CharField(max_length=20, unique=True, help_text="Placa sin guiones ni espacios para mejor validación")
    
    marca = models.CharField(max_length=50, blank=True, null=True)
    modelo = models.CharField(max_length=50, blank=True, null=True)
    color = models.CharField(max_length=30, blank=True, null=True)
    tipo_vehiculo = models.CharField(max_length=50, blank=True, null=True)
    autorizado = models.BooleanField(default=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = "Vehículos Autorizados"
    
    def save(self, *args, **kwargs):
        # Normalización: Guardar placa siempre en mayúsculas y sin espacios
        if self.placa:
            self.placa = self.placa.upper().replace(" ", "").replace("-", "")
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.placa} ({self.modelo})"


class AlertaSeguridad(models.Model):
    """
    Incidencias de seguridad detectadas automáticamente o reportadas.
    
    LÓGICA IA:
        - Recibe eventos de sistemas externos (cámaras con IA).
        - Guarda URL de evidencia en lugar de archivo binario.
    """
    TIPOS_ALERTA = [
        ('intruso', 'Intruso Detectado'),
        ('perro_suelto', 'Perro Suelto'),
        ('vehiculo_sospechoso', 'Vehículo Sospechoso'),
        ('actividad_inusual', 'Actividad Inusual'),
        ('otro', 'Otro'),
    ]
    
    tipo_alerta = models.CharField(max_length=50, choices=TIPOS_ALERTA)
    descripcion = models.TextField()
    fecha_hora = models.DateTimeField(auto_now_add=True)
    
    url_evidencia = models.URLField(
        blank=True, 
        null=True, 
        help_text="Link a la evidencia (S3/Cloudinary) generado por la IA externa"
    )
    
    residente_relacionado = models.ForeignKey(
        Residente, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='alertas_relacionadas'
    )
    atendido_por = models.ForeignKey(
        Seguridad, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='alertas_atendidas'
    )
    resuelto = models.BooleanField(default=False)
    notas_resolucion = models.TextField(blank=True, null=True)
    
    class Meta:
        verbose_name_plural = "Alertas de Seguridad"
        ordering = ['-fecha_hora']
    
    def __str__(self):
        return f"🚨 Alerta: {self.get_tipo_alerta_display()} ({self.fecha_hora.strftime('%Y-%m-%d %H:%M')})"
