import io
from datetime import datetime
from html import escape
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, Flowable

from central.core import ZONE
from central.reports import DIMENSIONS, group_rows, leaves, totals


class CheckBox(Flowable):
    def __init__(self):
        super().__init__()
        self.width=10
        self.height=10

    def draw(self):
        self.canv.setStrokeColor(colors.HexColor('#444444'))
        self.canv.rect(1,1,8,8,fill=0)


def fmt_date(value):
    if not value: return 'Não informado'
    try: return datetime.fromisoformat(value).astimezone(ZONE).strftime('%d/%m/%Y %H:%M:%S')
    except ValueError: return str(value)


def generate_pdf(rows, config=None):
    config=config or {}
    data=io.BytesIO()
    styles=getSampleStyleSheet()
    body=ParagraphStyle('Cell',fontName='Helvetica',fontSize=8,leading=10,wordWrap='CJK')
    heading=ParagraphStyle('Header',parent=body,textColor=colors.white,fontName='Helvetica-Bold')
    note=ParagraphStyle('Note',parent=body,textColor=colors.HexColor('#666666'))
    p=lambda value,style=body:Paragraph(escape(str(value or 'Não informado')).replace('\n','<br/>'),style)
    doc=SimpleDocTemplate(data,pagesize=A4,leftMargin=30,rightMargin=30,topMargin=30,bottomMargin=34)
    story=[Paragraph('Central de Separação e Produção',styles['Title']),
           p('AnnaLiv e DonaMora · Unidades comerciais · America/Sao_Paulo'),
           p('Emitido em '+datetime.now(ZONE).strftime('%d/%m/%Y %H:%M:%S'),note),
           p('Agrupamentos: '+(' > '.join(DIMENSIONS[d] for d in config.get('groups',[])) or 'Sem agrupamento'),note),
           p('Filtros explícitos: '+(str(config.get('filters')) if config.get('filters') else 'Nenhum; todos os itens incluídos'),note),
           p('Quantidades pendentes não são adicionadas ao total confirmado. Vínculos não revisados são sinalizados. Nenhum status exclui itens automaticamente.',note),Spacer(1,12)]
    tree=group_rows(rows,config.get('groups',[]),config.get('sort','deadline'),config.get('descending',False))
    # Duas colunas compostas conservam todos os campos obrigatórios sem reduzir excessivamente a fonte.
    widths=[22,106,126,149,68,64]
    for leaf in leaves(tree):
        group_title=None
        if leaf['path']:
            title=' > '.join(f'{DIMENSIONS[k]}: {fmt_date(v) if k=="deadline" else v}' for k,v in leaf['path'])
            group_title=p(title,ParagraphStyle('Group',parent=body,fontName='Helvetica-Bold',fontSize=10,leading=13))
        table_rows=[[p('OK',heading),p('Marketplace / Loja',heading),p('Pedido / Prazo',heading),p('Referência / Produto',heading),p('Cor / Tamanho',heading),p('Quantidade',heading)]]
        header_row=0
        if group_title:
            table_rows.insert(0,[group_title,'','','','',''])
            header_row=1
        for r in leaf['rows']:
            product=f"{r['ref']}\n{r['name']}\nSKU: {r['sku']}"
            if r['ref']=='Não validada' and r.get('candidate_ref'):
                product+='\nREF candidata: '+r['candidate_ref']+' (revisar)'
            detail=[p(product)]
            if config.get('labels'):
                detail.append(p('; '.join(r['labels'])+'; '+r['mark'],note))
            if r['reconciliation']=='pending':
                detail.append(p('Identidade/quantidade pendente de reconciliação',note))
            if r['reconciliation']=='resolved':
                detail.append(p('Observação reconciliada; não somada novamente',note))
            if config.get('photos'):
                photo=Path(r['photo']) if r.get('photo') else None
                if photo and photo.is_file():
                    try:
                        img=Image(str(photo));img._restrictSize(85,68);detail.append(img)
                    except Exception:
                        detail.append(p('Foto indisponível',note))
                else: detail.append(p('Sem foto cadastrada',note))
            quantity=f"{r['quantity'] if r['quantity'] is not None else '?'}\n"
            quantity+=('Confirmada' if r['reconciliation']=='confirmed' else 'Pendente' if r['reconciliation']=='pending' else 'Reconciliada: 0 no total')
            variant=r['color']+'\n'+r['size']
            if r['color']=='Não validada' or r['size']=='Não validado':
                variant+='\nOrigem: '+r.get('variation','')
            deadline_text=fmt_date(r['deadline'])
            if len(r.get('deadline_observations',[]))>1:
                deadline_text+='\nPrazos divergentes:\n'+'\n'.join(fmt_date(v) for v in r['deadline_observations'])
            table_rows.append([CheckBox(),p(r['marketplace']+'\n'+r['shop']),p(r['order']+'\n'+deadline_text),detail,p(variant),p(quantity)])
        total=leaf['totals']
        table_rows.append(['',p('Subtotal'),'',p(f"{total['confirmed']} confirmadas; {total['pending']} pendentes"),'',p(f"{total['invalid_quantity']} sem qtd.") if total['invalid_quantity'] else ''])
        table=Table(table_rows,colWidths=widths,repeatRows=header_row+1,hAlign='LEFT',splitInRow=1)
        rules=[('BACKGROUND',(0,header_row),(-1,header_row),colors.HexColor('#66394F')),
            ('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),4),('RIGHTPADDING',(0,0),(-1,-1),4),
            ('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6),
            ('LINEBELOW',(0,header_row),(-1,header_row),0.5,colors.HexColor('#66394F')),
            ('LINEBELOW',(0,header_row+1),(-1,-2),0.25,colors.HexColor('#DDDDDD')),
            ('BACKGROUND',(0,-1),(-1,-1),colors.HexColor('#F0E8EC'))]
        if group_title:
            rules.extend([('SPAN',(0,0),(-1,0)),('BACKGROUND',(0,0),(-1,0),colors.HexColor('#F6F2F4'))])
        table.setStyle(TableStyle(rules))
        story.extend([table,Spacer(1,10)])
    t=totals(rows)
    story.append(p(f"TOTAL GERAL: {t['orders']} pedidos distintos; {t['items']} registros; {t['confirmed']} unidades confirmadas; {t['pending']} unidades pendentes; {t['invalid_quantity']} registros sem quantidade válida; {t['resolved']} observações reconciliadas.",ParagraphStyle('Total',parent=body,fontName='Helvetica-Bold',fontSize=10,leading=13)))
    def footer(canvas,document):
        canvas.setFont('Helvetica',8)
        canvas.setFillColor(colors.HexColor('#666666'))
        canvas.drawString(30,20,'Central local · Conferência pelos operadores')
        canvas.drawRightString(A4[0]-30,20,f'Página {document.page}')
    doc.build(story,onFirstPage=footer,onLaterPages=footer)
    return data.getvalue()
