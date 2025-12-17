"""
Comando de Django para poblar la base de datos con datos de prueba
Uso: python manage.py poblar_datos
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from faker import Faker
from datetime import timedelta, datetime
import random
import uuid

from api.models import (
    UnidadHabitacional, Administrador, Seguridad, PersonalMantenimiento, Residente,
    Cuota, Pago, AreaComun, Reserva, TicketMantenimiento,
    Visita, VehiculoAutorizado, AlertaSeguridad
)


class Command(BaseCommand):
    help = 'Pobla la base de datos con datos de prueba históricos'

    def __init__(self):
        super().__init__()
        self.fake = Faker('es_ES')  # Datos en español
        Faker.seed(42)  # Para reproducibilidad
        random.seed(42)

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS('🚀 Iniciando población de datos...'))
        
        # Limpiar datos existentes (opcional)
        self.stdout.write('🗑️  Limpiando datos existentes...')
        self.limpiar_datos()
        
        # Crear datos
        self.stdout.write('🏢 Creando unidades habitacionales...')
        unidades = self.crear_unidades_habitacionales()
        
        self.stdout.write('👥 Creando usuarios del sistema...')
        usuarios_sistema = self.crear_usuarios_sistema()
        
        self.stdout.write('🏠 Creando residentes...')
        residentes = self.crear_residentes(unidades)
        
        self.stdout.write('💰 Creando cuotas y pagos históricos...')
        self.crear_cuotas_y_pagos(residentes)
        
        self.stdout.write('🏊 Creando áreas comunes...')
        areas = self.crear_areas_comunes()
        
        self.stdout.write('📅 Creando reservas...')
        self.crear_reservas(residentes, areas)
        
        self.stdout.write('🔧 Creando tickets de mantenimiento...')
        self.crear_tickets_mantenimiento(residentes, usuarios_sistema['mantenimiento'])
        
        self.stdout.write('👋 Creando registro de visitas...')
        self.crear_visitas(residentes, usuarios_sistema['seguridad'])
        
        self.stdout.write('🚗 Creando vehículos autorizados...')
        self.crear_vehiculos(residentes)
        
        self.stdout.write('🚨 Creando alertas de seguridad...')
        self.crear_alertas_seguridad(residentes, usuarios_sistema['seguridad'])
        
        self.stdout.write(self.style.SUCCESS('✅ ¡Datos poblados exitosamente!'))
        self.mostrar_estadisticas()

    def limpiar_datos(self):
        """Limpia los datos existentes (excepto superusuarios)"""
        from django.db import transaction
        
        with transaction.atomic():
            # Eliminar en orden inverso a las dependencias
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
        
        self.stdout.write('   ✓ Limpieza completada')

    def crear_unidades_habitacionales(self):
        """Crea unidades habitacionales en diferentes torres"""
        unidades = []
        torres = {'A': 'Torre A', 'B': 'Torre B', 'C': 'Torre C', 'D': 'Torre D'}
        
        for letra, torre in torres.items():
            for piso in range(1, 11):  # 10 pisos
                for numero in range(1, 5):  # 4 departamentos por piso
                    # Número único: letra + piso + numero (ej: A-101, A-102, B-101, B-102)
                    numero_unidad = f"{letra}-{piso}{numero:02d}"
                    
                    unidad = UnidadHabitacional.objects.create(
                        numero=numero_unidad,
                        torre=torre,
                        area_m2=round(random.uniform(45.0, 150.0), 2),
                        activo=True
                    )
                    unidades.append(unidad)
        
        return unidades

    def crear_usuarios_sistema(self):
        """Crea administradores, seguridad y personal de mantenimiento"""
        usuarios = {
            'administradores': [],
            'seguridad': [],
            'mantenimiento': []
        }
        
        # Administradores (3)
        for i in range(3):
            user = User.objects.create_user(
                username=f'admin{i+1}',
                email=self.fake.email(),
                password='admin123',
                first_name=self.fake.first_name(),
                last_name=self.fake.last_name()
            )
            admin = Administrador.objects.create(
                user=user,
                telefono=self.fake.phone_number(),
                fecha_contratacion=self.fake.date_between(start_date='-3y', end_date='-1y')
            )
            usuarios['administradores'].append(admin)
        
        # Personal de Seguridad (6)
        turnos = ['Mañana', 'Tarde', 'Noche']
        for i in range(6):
            user = User.objects.create_user(
                username=f'seguridad{i+1}',
                email=self.fake.email(),
                password='seguridad123',
                first_name=self.fake.first_name(),
                last_name=self.fake.last_name()
            )
            seg = Seguridad.objects.create(
                user=user,
                telefono=self.fake.phone_number(),
                turno=turnos[i % 3],
                fecha_contratacion=self.fake.date_between(start_date='-2y', end_date='-6m')
            )
            usuarios['seguridad'].append(seg)
        
        # Personal de Mantenimiento (5)
        especialidades = ['Plomería', 'Electricidad', 'Carpintería', 'Pintura', 'Jardinería']
        for i, especialidad in enumerate(especialidades):
            user = User.objects.create_user(
                username=f'mantenimiento{i+1}',
                email=self.fake.email(),
                password='mantenimiento123',
                first_name=self.fake.first_name(),
                last_name=self.fake.last_name()
            )
            mant = PersonalMantenimiento.objects.create(
                user=user,
                telefono=self.fake.phone_number(),
                especialidad=especialidad,
                fecha_contratacion=self.fake.date_between(start_date='-2y', end_date='-3m')
            )
            usuarios['mantenimiento'].append(mant)
        
        return usuarios

    def crear_residentes(self, unidades):
        """Crea residentes vinculados a unidades habitacionales"""
        residentes = []
        
        # 80% de las unidades ocupadas
        unidades_ocupadas = random.sample(unidades, int(len(unidades) * 0.8))
        
        for unidad in unidades_ocupadas:
            user = User.objects.create_user(
                username=f'residente_{unidad.id}',
                email=self.fake.email(),
                password='residente123',
                first_name=self.fake.first_name(),
                last_name=self.fake.last_name()
            )
            
            # Score de morosidad aleatorio (simulado por IA)
            score_ia = round(random.uniform(10.0, 95.0), 2) if random.random() > 0.3 else None
            
            residente = Residente.objects.create(
                user=user,
                unidad_habitacional=unidad,
                telefono=self.fake.phone_number(),
                es_propietario=random.choice([True, True, False]),  # 66% propietarios
                score_morosidad_ia=score_ia
            )
            residentes.append(residente)
        
        return residentes

    def crear_cuotas_y_pagos(self, residentes):
        """Crea cuotas mensuales y pagos históricos (último año)"""
        meses = [
            'Enero 2024', 'Febrero 2024', 'Marzo 2024', 'Abril 2024',
            'Mayo 2024', 'Junio 2024', 'Julio 2024', 'Agosto 2024',
            'Septiembre 2024', 'Octubre 2024', 'Noviembre 2024', 'Diciembre 2024',
            'Enero 2025'
        ]
        
        for residente in residentes:
            for i, mes in enumerate(meses):
                # Fecha de vencimiento: día 10 de cada mes
                año, mes_num = (2024, i + 1) if i < 12 else (2025, 1)
                fecha_venc = datetime(año, mes_num, 10).date()
                
                monto = round(random.uniform(150.0, 350.0), 2)
                
                # 85% de cuotas pagadas
                estado = 'pagada' if random.random() < 0.85 else random.choice(['pendiente', 'vencida'])
                
                cuota = Cuota.objects.create(
                    residente=residente,
                    monto=monto,
                    mes=mes,
                    fecha_vencimiento=fecha_venc,
                    estado=estado,
                    descripcion=f"Cuota de mantenimiento {mes}"
                )
                
                # Si está pagada, crear el pago
                if estado == 'pagada':
                    fecha_pago = fecha_venc - timedelta(days=random.randint(1, 9))
                    Pago.objects.create(
                        cuota=cuota,
                        monto_pagado=monto,
                        fecha_pago=datetime.combine(fecha_pago, datetime.min.time()),
                        metodo_pago=random.choice(['Transferencia', 'Efectivo', 'Tarjeta', 'Depósito']),
                        referencia_comprobante=self.fake.bothify(text='REF-########'),
                        notas=self.fake.sentence() if random.random() > 0.7 else ''
                    )

    def crear_areas_comunes(self):
        """Crea áreas comunes del condominio"""
        areas_data = [
            ('Piscina', 'Piscina con área de recreación', 50, 0),
            ('Salón de Eventos', 'Salón para fiestas y eventos', 100, 150.00),
            ('Gimnasio', 'Gimnasio equipado', 30, 0),
            ('Cancha de Tenis', 'Cancha profesional', 4, 20.00),
            ('BBQ/Parrilla', 'Área de parrillas', 20, 30.00),
            ('Sala de Juegos', 'Mesa de billar y juegos de mesa', 15, 15.00),
            ('Coworking', 'Espacio de trabajo compartido', 12, 0),
        ]
        
        areas = []
        for nombre, desc, capacidad, costo in areas_data:
            area = AreaComun.objects.create(
                nombre=nombre,
                descripcion=desc,
                capacidad_personas=capacidad,
                costo_reserva=costo,
                disponible=True
            )
            areas.append(area)
        
        return areas

    def crear_reservas(self, residentes, areas):
        """Crea reservas históricas y futuras"""
        # Reservas de los últimos 3 meses y próximos 2 meses
        for _ in range(150):
            residente = random.choice(residentes)
            area = random.choice(areas)
            
            # Fecha aleatoria en el rango
            dias_offset = random.randint(-90, 60)
            fecha_reserva = (timezone.now() + timedelta(days=dias_offset)).date()
            
            hora_inicio = random.choice([9, 10, 14, 16, 18, 20])
            
            # Estado según la fecha
            if dias_offset < -7:
                estado = 'completada'
            elif dias_offset < 0:
                estado = random.choice(['completada', 'cancelada'])
            else:
                estado = random.choice(['confirmada', 'pendiente'])
            
            Reserva.objects.create(
                area_comun=area,
                residente=residente,
                fecha_reserva=fecha_reserva,
                hora_inicio=datetime.min.time().replace(hour=hora_inicio),
                hora_fin=datetime.min.time().replace(hour=hora_inicio + 2),
                estado=estado,
                cantidad_personas=random.randint(5, 30),
                notas=self.fake.sentence() if random.random() > 0.6 else ''
            )

    def crear_tickets_mantenimiento(self, residentes, personal_mant):
        """Crea tickets de mantenimiento históricos"""
        prioridades = ['baja', 'media', 'alta', 'urgente']
        estados = ['abierto', 'en_proceso', 'resuelto', 'cerrado']
        
        problemas = [
            'Fuga de agua en baño',
            'Problema eléctrico en cocina',
            'Puerta no cierra correctamente',
            'Grifo con goteo',
            'Luz del pasillo no funciona',
            'Aire acondicionado con ruidos',
            'Ventana rota',
            'Problema con el ascensor',
            'Humedad en pared',
            'Cerradura de puerta dañada'
        ]
        
        for _ in range(200):
            residente = random.choice(residentes)
            fecha_creacion = timezone.now() - timedelta(days=random.randint(1, 180))
            
            estado = random.choice(estados)
            asignado = random.choice(personal_mant) if estado != 'abierto' else None
            
            ticket = TicketMantenimiento.objects.create(
                residente=residente,
                asignado_a=asignado,
                titulo=random.choice(problemas),
                descripcion=self.fake.paragraph(),
                prioridad=random.choice(prioridades),
                estado=estado,
                costo_estimado=round(random.uniform(50, 500), 2) if estado != 'abierto' else None,
                costo_real=round(random.uniform(45, 550), 2) if estado in ['resuelto', 'cerrado'] else None,
                fecha_creacion=fecha_creacion,
                fecha_resolucion=fecha_creacion + timedelta(days=random.randint(1, 15)) if estado in ['resuelto', 'cerrado'] else None
            )

    def crear_visitas(self, residentes, personal_seg):
        """Crea registro de visitas con códigos QR"""
        for _ in range(300):
            residente = random.choice(residentes)
            dias_offset = random.randint(-60, 30)
            fecha_visita = (timezone.now() + timedelta(days=dias_offset)).date()
            
            hora_entrada_esperada = random.choice([9, 10, 14, 16, 18, 20])
            
            # Calcular hora de salida sin exceder 23
            horas_duracion = random.randint(2, 4)
            hora_salida = min(hora_entrada_esperada + horas_duracion, 22)
            
            # Código QR único
            codigo_qr = str(uuid.uuid4())
            
            # Si la visita fue en el pasado, tiene hora de entrada real
            entrada_real = None
            salida_real = None
            autorizado = None
            
            if dias_offset < 0:  # Visita pasada
                # Usar timezone.now() para fechas aware
                entrada_real = timezone.make_aware(
                    datetime.combine(
                        fecha_visita,
                        datetime.min.time().replace(hour=hora_entrada_esperada, minute=random.randint(0, 30))
                    )
                )
                
                if random.random() > 0.2:  # 80% tiene salida registrada
                    salida_real = entrada_real + timedelta(hours=random.randint(1, 5))
                
                autorizado = random.choice(personal_seg)
            
            Visita.objects.create(
                residente=residente,
                nombre_visitante=self.fake.name(),
                documento_visitante=self.fake.bothify(text='########'),
                fecha_visita=fecha_visita,
                hora_entrada_esperada=datetime.min.time().replace(hour=hora_entrada_esperada),
                hora_salida_esperada=datetime.min.time().replace(hour=hora_salida),
                codigo_qr_acceso=codigo_qr,
                hora_entrada_real=entrada_real,
                hora_salida_real=salida_real,
                autorizado_por_seguridad=autorizado,
                notas=self.fake.sentence() if random.random() > 0.7 else ''
            )

    def crear_vehiculos(self, residentes):
        """Crea vehículos autorizados"""
        marcas = ['Toyota', 'Honda', 'Nissan', 'Chevrolet', 'Ford', 'Mazda', 'Hyundai', 'Kia']
        colores = ['Blanco', 'Negro', 'Gris', 'Rojo', 'Azul', 'Plata']
        tipos = ['Auto', 'SUV', 'Camioneta', 'Moto']
        
        # 70% de residentes tienen vehículo
        residentes_con_vehiculo = random.sample(residentes, int(len(residentes) * 0.7))
        
        for residente in residentes_con_vehiculo:
            # Algunos tienen 2 vehículos
            num_vehiculos = 2 if random.random() > 0.8 else 1
            
            for _ in range(num_vehiculos):
                placa = self.fake.bothify(text='???-###').upper()
                
                VehiculoAutorizado.objects.create(
                    residente=residente,
                    placa=placa,
                    marca=random.choice(marcas),
                    modelo=self.fake.word().capitalize(),
                    color=random.choice(colores),
                    tipo_vehiculo=random.choice(tipos),
                    autorizado=random.choice([True, True, True, False])  # 75% autorizados
                )

    def crear_alertas_seguridad(self, residentes, personal_seg):
        """Crea alertas de seguridad"""
        tipos = ['intruso', 'perro_suelto', 'vehiculo_sospechoso', 'actividad_inusual', 'otro']
        
        descripciones = {
            'intruso': 'Persona no identificada merodeando en el área',
            'perro_suelto': 'Mascota sin supervisión en área común',
            'vehiculo_sospechoso': 'Vehículo desconocido estacionado por largo tiempo',
            'actividad_inusual': 'Actividad sospechosa reportada',
            'otro': 'Incidente reportado por residente'
        }
        
        for _ in range(80):
            tipo = random.choice(tipos)
            fecha_hora = timezone.now() - timedelta(days=random.randint(1, 90))
            
            resuelto = random.random() > 0.3  # 70% resueltas
            
            AlertaSeguridad.objects.create(
                tipo_alerta=tipo,
                descripcion=descripciones[tipo] + '. ' + self.fake.paragraph(),
                fecha_hora=fecha_hora,
                url_evidencia=f'https://storage.ejemplo.com/evidencia/{self.fake.uuid4()}.jpg' if random.random() > 0.5 else None,
                residente_relacionado=random.choice(residentes) if random.random() > 0.4 else None,
                atendido_por=random.choice(personal_seg) if resuelto else None,
                resuelto=resuelto,
                notas_resolucion=self.fake.paragraph() if resuelto else ''
            )

    def mostrar_estadisticas(self):
        """Muestra estadísticas de los datos creados"""
        self.stdout.write(self.style.SUCCESS('\n📊 Estadísticas de datos creados:'))
        self.stdout.write(f'  - Unidades Habitacionales: {UnidadHabitacional.objects.count()}')
        self.stdout.write(f'  - Usuarios totales: {User.objects.count()}')
        self.stdout.write(f'  - Residentes: {Residente.objects.count()}')
        self.stdout.write(f'  - Administradores: {Administrador.objects.count()}')
        self.stdout.write(f'  - Personal Seguridad: {Seguridad.objects.count()}')
        self.stdout.write(f'  - Personal Mantenimiento: {PersonalMantenimiento.objects.count()}')
        self.stdout.write(f'  - Cuotas: {Cuota.objects.count()}')
        self.stdout.write(f'  - Pagos: {Pago.objects.count()}')
        self.stdout.write(f'  - Áreas Comunes: {AreaComun.objects.count()}')
        self.stdout.write(f'  - Reservas: {Reserva.objects.count()}')
        self.stdout.write(f'  - Tickets Mantenimiento: {TicketMantenimiento.objects.count()}')
        self.stdout.write(f'  - Visitas: {Visita.objects.count()}')
        self.stdout.write(f'  - Vehículos: {VehiculoAutorizado.objects.count()}')
        self.stdout.write(f'  - Alertas Seguridad: {AlertaSeguridad.objects.count()}')
        self.stdout.write(self.style.SUCCESS('\n🎉 ¡Base de datos lista para usar!'))
