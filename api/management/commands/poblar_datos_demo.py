"""
Comando de Django para poblar la base de datos con datos DEMO para presentación.
Uso: python manage.py poblar_datos_demo
"""
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
    help = 'Pobla la base de datos con usuarios GOLDEN para demo y datos de relleno'

    def __init__(self):
        super().__init__()
        self.fake = Faker('es_ES')
        Faker.seed(999)
        random.seed(999)

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING(f'⚠️  INICIANDO POBLACIÓN DEMO - Borrando datos antiguos...'))
        self.stdout.write(f'🌍 Timezone activo: {timezone.get_current_timezone_name()}')
        
        self.limpiar_datos()
        
        # 1. Crear Estructura Base (Torres/Deptos)
        self.stdout.write('🏢 Creando estructura y unidades...')
        unidades = self.crear_unidades()
        
        # 2. Usuarios Golden (Los que vas a usar para probar)
        self.stdout.write('🔑 Creando usuarios GOLDEN (admin, guardia, residente)...')
        golden_users = self.crear_usuarios_golden(unidades)
        
        # 3. Datos de Relleno (Para que se vea vivo)
        self.stdout.write('👥 Poblando con residentes extra y actividad...')
        self.poblar_relleno(unidades, golden_users)
        
        self.stdout.write(self.style.SUCCESS('\n✅ ¡Demo lista! Usuarios creados:'))
        self.stdout.write('   - Admin:     admin / admin')
        self.stdout.write('   - Guardia:   guardia / guardia123')
        self.stdout.write('   - Residente: residente / residente123 (Torre A-101)')
        self.stdout.write('   - Moroso:    moroso / residente123 (Torre A-102)')
        self.stdout.write('   - Técnico:   tecnico / tecnico123')

    def limpiar_datos(self):
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
            # Borrar usuario admin explícitamente para recrearlo sin errores
            User.objects.filter(username='admin').delete()
            User.objects.filter(is_superuser=False).delete()

    def crear_unidades(self):
        unidades = []
        # Torre A y B, 10 pisos, 4 deptos
        for torre in ['Torre A', 'Torre B']:
            for piso in range(1, 6): # Solo 5 pisos para demo
                for num in range(1, 5):
                    u = UnidadHabitacional.objects.create(
                        numero=f"{torre[-1]}-{piso}0{num}",
                        torre=torre,
                        area_m2=random.choice([80, 100, 120]),
                        activo=True
                    )
                    unidades.append(u)
        return unidades

    def crear_usuarios_golden(self, unidades):
        users = {}
        
        # 1. ADMIN
        admin_user = User.objects.create_superuser('admin', 'admin@demo.com', 'admin')
        admin_user.first_name = "Administrador"
        admin_user.last_name = "Principal"
        admin_user.save()
        Administrador.objects.create(user=admin_user, telefono="+56912345678")
        users['admin'] = admin_user
        
        # 2. GUARDIA
        guardia_user = User.objects.create_user('guardia', 'guardia@demo.com', 'guardia123')
        guardia_user.first_name = "Juan"
        guardia_user.last_name = "Segura"
        guardia_user.save()
        seg = Seguridad.objects.create(user=guardia_user, turno="Mañana", telefono="+56987654321")
        users['guardia'] = seg
        
        # 3. TÉCNICO
        tecnico_user = User.objects.create_user('tecnico', 'tecnico@demo.com', 'tecnico123')
        tecnico_user.first_name = "Pedro"
        tecnico_user.last_name = "Reparador"
        tecnico_user.save()
        mant = PersonalMantenimiento.objects.create(user=tecnico_user, especialidad="Electricidad", telefono="+56911223344")
        users['tecnico'] = mant
        
        # 4. RESIDENTE (Bueno)
        res_user = User.objects.create_user('residente', 'residente@demo.com', 'residente123')
        res_user.first_name = "Ana"
        res_user.last_name = "García"
        res_user.save()
        # Asignar A-101
        unidad_buena = unidades[0] # A-101
        res = Residente.objects.create(
            user=res_user, 
            unidad_habitacional=unidad_buena,
            telefono="+56999887766",
            es_propietario=True,
            score_morosidad_ia=98.5
        )
        users['residente'] = res
        
        # 5. RESIDENTE (Moroso)
        moroso_user = User.objects.create_user('moroso', 'moroso@demo.com', 'residente123')
        moroso_user.first_name = "Carlos"
        moroso_user.last_name = "Deudor"
        moroso_user.save()
        # Asignar A-102
        unidad_mala = unidades[1] # A-102
        moroso = Residente.objects.create(
            user=moroso_user, 
            unidad_habitacional=unidad_mala,
            telefono="+56944556677",
            es_propietario=True,
            score_morosidad_ia=35.0 # Riesgo alto
        )
        users['moroso'] = moroso
        
        return users

    def poblar_relleno(self, unidades, golden):
        # --- Áreas Comunes ---
        areas = [
            AreaComun.objects.create(nombre="Quincho Panorámico", capacidad_personas=20, costo_reserva=20000),
            AreaComun.objects.create(nombre="Piscina", capacidad_personas=50, costo_reserva=0),
            AreaComun.objects.create(nombre="Sala Multiuso", capacidad_personas=30, costo_reserva=15000),
        ]
        
        # --- Residentes Extra (Relleno) ---
        residentes_extra = []
        for i in range(15):
            u_extra = User.objects.create_user(f'vecino{i}', self.fake.email(), 'vecino123')
            u_extra.first_name = self.fake.first_name()
            u_extra.last_name = self.fake.last_name()
            u_extra.save()
            
            # Unidades desde la 3ra en adelante
            if i + 2 < len(unidades):
                unidad = unidades[i+2]
                r = Residente.objects.create(
                    user=u_extra,
                    unidad_habitacional=unidad,
                    telefono=self.fake.phone_number(),
                    es_propietario=random.choice([True, False]),
                    score_morosidad_ia=random.uniform(50, 99)
                )
                residentes_extra.append(r)

        todos_residentes = [golden['residente'], golden['moroso']] + residentes_extra

        # --- Finanzas (Historial 6 meses) ---
        meses = ['Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
        for res in todos_residentes:
            for i, mes in enumerate(meses):
                estado = 'pagada'
                
                # El Moroso debe los últimos 2 meses
                if res == golden['moroso'] and i >= 4:
                    estado = 'vencida'
                
                # Algunos random deben el último mes
                if res in residentes_extra and i == 5 and random.random() > 0.8:
                    estado = 'pendiente'

                c = Cuota.objects.create(
                    residente=res,
                    monto=random.choice([50000, 75000, 100000]),
                    mes=f"{mes} 2024",
                    fecha_vencimiento=timezone.now().date().replace(day=5), # Simplificado
                    estado=estado,
                    descripcion=f"Gastos Comunes {mes}"
                )
                
                if estado == 'pagada':
                    Pago.objects.create(
                        cuota=c, 
                        monto_pagado=c.monto,
                        metodo_pago=random.choice(['Transferencia', 'Webpay'])
                    )

        # --- Seguridad: Visitas y Alertas ---
        
        # 1. Visita para HOY (Para probar QR)
        Visita.objects.create(
            residente=golden['residente'],
            nombre_visitante="Visita de Prueba",
            documento_visitante="12345678-9",
            fecha_visita=timezone.now().date(),
            hora_entrada_esperada=timezone.now().time(),
            codigo_qr_acceso=str(uuid.uuid4()) # Un QR válido
        )
        
        # 2. Alertas
        AlertaSeguridad.objects.create(
            tipo_alerta='perro_suelto',
            descripcion="Perro golden retriever sin correa en la piscina",
            fecha_hora=timezone.now() - timedelta(hours=2),
            resuelto=False,
            url_evidencia="https://images.unsplash.com/photo-1552053831-71594a27632d?auto=format&fit=crop&w=500&q=60"
        )
        
        AlertaSeguridad.objects.create(
            tipo_alerta='vehiculo_sospechoso',
            descripcion="Auto desconocido bloqueando portón",
            fecha_hora=timezone.now() - timedelta(days=2),
            resuelto=True,
            atendido_por=golden['guardia'],
            notas_resolucion="Era uber esperando pasajero, se retiró."
        )

        # --- Vehículos ---
        VehiculoAutorizado.objects.create(
            residente=golden['residente'],
            placa="ABCD12",
            marca="Toyota",
            modelo="Corolla",
            color="Gris",
            autorizado=True
        )

