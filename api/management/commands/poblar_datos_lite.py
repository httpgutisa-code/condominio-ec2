from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from faker import Faker
from datetime import timedelta, datetime
import random
import uuid
from django.db import transaction

from api.models import (
    UnidadHabitacional, Administrador, Seguridad, PersonalMantenimiento, Residente,
    Cuota, Pago, AreaComun, Reserva, TicketMantenimiento,
    Visita, VehiculoAutorizado, AlertaSeguridad
)

class Command(BaseCommand):
    help = 'Pobla la base de datos con datos LIGEROS (Lite) para carga rápida'

    def __init__(self):
        super().__init__()
        self.fake = Faker('es_ES')
        Faker.seed(123)  # Nueva seed diferente
        random.seed(123)

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING('🚀 Iniciando población LITE (Rápida)...'))
        
        self.limpiar_datos()
        
        # 1. Unidades: Solo 1 Torre, 3 pisos, 2 deptos por piso = 6 unidades
        unidades = self.crear_unidades_lite()
        self.stdout.write(f'  - {len(unidades)} Unidades creadas')
        
        # 2. Usuarios Sistema: 1 Admin, 1 Guardia, 1 Mantenimiento
        usuarios_sys = self.crear_usuarios_lite()
        self.stdout.write('  - Usuarios de sistema creados')
        
        # 3. Residentes: Ocupar 5 de las 6 unidades
        residentes = self.crear_residentes_lite(unidades)
        self.stdout.write(f'  - {len(residentes)} Residentes creados')
        
        # 4. Datos transaccionales (pocos)
        self.crear_datos_transaccionales(residentes, usuarios_sys)
        
        self.stdout.write(self.style.SUCCESS('✅ ¡Datos LITE cargados en < 2 segundos!'))

    def limpiar_datos(self):
        """Limpia todo usando transacción atómica"""
        with transaction.atomic():
            AlertaSeguridad.objects.all().delete()
            VehiculoAutorizado.objects.all().delete()
            Visita.objects.all().delete()
            TicketMantenimiento.objects.all().delete()
            Reserva.objects.all().delete()
            AreaComun.objects.all().delete()
            Pago.objects.all().delete()
            Cuota.objects.all().delete()
            Residente.objects.all().delete()
            PersonalMantenimiento.objects.all().delete()
            Seguridad.objects.all().delete()
            Administrador.objects.all().delete()
            UnidadHabitacional.objects.all().delete()
            User.objects.filter(is_superuser=False).delete()

    def crear_unidades_lite(self):
        unidades = []
        # Solo Torre A
        for piso in range(1, 4):  # Pisos 1 a 3
            for num in range(1, 3):  # Deptos 1 y 2
                unidad = UnidadHabitacional.objects.create(
                    numero=f"A-{piso}0{num}",
                    torre="Torre A",
                    area_m2=80.0,
                    activo=True
                )
                unidades.append(unidad)
        return unidades

    def crear_usuarios_lite(self):
        # Admin
        u_admin, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@test.com',
                'first_name': 'Admin',
                'last_name': 'Principal'
            }
        )
        if created:
            u_admin.set_password('admin123')
            u_admin.save()
        
        # Crear perfil si no existe
        if not hasattr(u_admin, 'perfil_administrador'):
            Administrador.objects.create(user=u_admin, telefono='555-0001')
            
        profiles = {'seguridad': [], 'mantenimiento': []}
        
        # Seguridad
        u_seg, created = User.objects.get_or_create(
            username='guardia',
            defaults={
                'email': 'guardia@test.com',
                'first_name': 'Juan',
                'last_name': 'Guardia'
            }
        )
        if created:
            u_seg.set_password('guardia123')
            u_seg.save()
            
        if not hasattr(u_seg, 'perfil_seguridad'):
            seg = Seguridad.objects.create(user=u_seg, turno='Mañana', telefono='555-0002')
        else:
            seg = u_seg.perfil_seguridad
        profiles['seguridad'].append(seg)
        
        # Mant
        u_mant, created = User.objects.get_or_create(
            username='tecnico',
            defaults={
                'email': 'tecnico@test.com',
                'first_name': 'Pedro',
                'last_name': 'Técnico'
            }
        )
        if created:
            u_mant.set_password('tecnico123')
            u_mant.save()
            
        if not hasattr(u_mant, 'perfil_mantenimiento'):
            mant = PersonalMantenimiento.objects.create(user=u_mant, especialidad='General', telefono='555-0003')
        else:
            mant = u_mant.perfil_mantenimiento
        profiles['mantenimiento'].append(mant)
        
        return profiles

    def crear_residentes_lite(self, unidades):
        residentes = []
        # Usamos 5 de las 6 unidades
        for i, unidad in enumerate(unidades[:5]):
            user = User.objects.create_user(
                f'residente{i+1}', 
                f'res{i+1}@test.com', 
                'res123', 
                first_name=self.fake.first_name(), 
                last_name=self.fake.last_name()
            )
            # Simulamos score variado
            score = 95.0 if i < 3 else 45.0 # 3 buenos, 2 morosos
            
            res = Residente.objects.create(
                user=user,
                unidad_habitacional=unidad,
                telefono=self.fake.phone_number(),
                es_propietario=True,
                score_morosidad_ia=score
            )
            residentes.append(res)
        return residentes

    def crear_datos_transaccionales(self, residentes, usuarios_sys):
        # 1. Áreas Comunes (Solo 2)
        piscina = AreaComun.objects.create(nombre="Piscina", capacidad_personas=20)
        gym = AreaComun.objects.create(nombre="Gimnasio", capacidad_personas=10)
        
        # 2. Cuotas (Solo mes actual y anterior)
        meses = ['Noviembre 2024', 'Diciembre 2024']
        for res in residentes:
            for mes in meses:
                estado = 'pagada'
                # El residente 4 y 5 deben dinero
                if res.user.username in ['residente4', 'residente5'] and mes == 'Diciembre 2024':
                    estado = 'vencida'
                
                c = Cuota.objects.create(
                    residente=res,
                    monto=200.00,
                    mes=mes,
                    fecha_vencimiento=timezone.now().date(),
                    estado=estado,
                    descripcion=f"Expensa {mes}"
                )
                if estado == 'pagada':
                    Pago.objects.create(cuota=c, monto_pagado=200.00)

        # 3. Datos de Seguridad (Alertas y Visitas)
        seguridad = usuarios_sys['seguridad'][0]
        
        # Una alerta pendiente (importante para el dashboard)
        AlertaSeguridad.objects.create(
            tipo_alerta='perro_suelto',
            descripcion='Perro ladrando en pasillo Torre A',
            resuelto=False,
            url_evidencia='https://via.placeholder.com/300'
        )
        
        # Visita de hoy
        Visita.objects.create(
            residente=residentes[0],
            nombre_visitante='Visitante Prueba',
            fecha_visita=timezone.now().date(),
            hora_entrada_esperada=timezone.now().time(),
            codigo_qr_acceso=str(uuid.uuid4())
        )
