import io
from django.http import HttpResponse
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from openpyxl import Workbook
from .models import Cuota, Pago, AlertaSeguridad

def generar_reporte_finanzas_excel():
    """Genera un archivo Excel con el reporte financiero actual"""
    wb = Workbook()
    ws = wb.active
    ws.title = "Reporte Financiero"
    
    # Headers
    headers = ["ID Cuota", "Residente", "Unidad", "Mes", "Monto", "Estado", "Total Pagado"]
    ws.append(headers)
    
    # Data
    cuotas = Cuota.objects.select_related('residente__user', 'residente__unidad_habitacional').all()
    
    for c in cuotas:
        total_pagado = sum(p.monto_pagado for p in c.pagos.all())
        ws.append([
            c.id,
            c.residente.user.get_full_name(),
            str(c.residente.unidad_habitacional),
            c.mes,
            c.monto,
            c.estado,
            total_pagado
        ])
    
    # Output buffer
    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return buffer

def generar_reporte_seguridad_pdf():
    """Genera un PDF con las alertas de seguridad recientes"""
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    
    # Header
    p.setFont("Helvetica-Bold", 18)
    p.drawString(1 * inch, height - 1 * inch, "Reporte de Seguridad - Smart Condominium")
    
    p.setFont("Helvetica", 12)
    y = height - 1.5 * inch
    
    # Data
    alertas = AlertaSeguridad.objects.select_related('residente_relacionado__user').all().order_by('-fecha_hora')[:20]
    
    for alerta in alertas:
        if y < 1 * inch: # Nueva página si se acaba el espacio
            p.showPage()
            y = height - 1 * inch
            
        texto = f"[{alerta.get_tipo_alerta_display()}] {alerta.descripcion} - {alerta.fecha_hora.strftime('%Y-%m-%d %H:%M')}"
        p.drawString(1 * inch, y, texto)
        y -= 0.25 * inch
        
        if alerta.residente_relacionado:
            residente = f"Residente: {alerta.residente_relacionado.user.get_full_name()}"
            p.drawString(1.2 * inch, y, residente)
            y -= 0.25 * inch
            
        estado = f"Estado: {'Resuelto' if alerta.resuelto else 'PENDIENTE'}"
        p.drawString(1.2 * inch, y, estado)
        y -= 0.4 * inch # Espacio entre items
        
    p.showPage()
    p.save()
    
    buffer.seek(0)
    return buffer
