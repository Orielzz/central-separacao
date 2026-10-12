import hashlib
import json
import os
from datetime import datetime, time
from pathlib import Path

import pandas as pd
import streamlit as st
import altair as alt

from central.core import Store, MARKS, ZONE, now, dumps
from central.pdf import generate_pdf, fmt_date
from central.reports import DIMENSIONS, filter_rows, group_rows, leaves, totals
from central.ui import styles, sidebar, hero, empty_state

ROOT=Path(__file__).resolve().parent
st.set_page_config(page_title='Central de Separação',layout='wide')
styles()


@st.cache_resource
def bootstrap_catalog(db_path):
    store=Store(db_path)
    try:
        if not store.db.execute('SELECT 1 FROM products LIMIT 1').fetchone():
            catalog=ROOT/'amostras/catalogo/catalogo_base_validada_2026-10-12.csv'
            if catalog.exists(): store.import_catalog(catalog.read_bytes())
    finally: store.close()


db_path=os.environ.get('CENTRAL_DB',str(ROOT/'dados/central.sqlite3'))
bootstrap_catalog(db_path)
store=Store(db_path)
page=sidebar()
rows=store.rows()
LABELS={'order':'Pedido','marketplace':'Marketplace','shop':'Loja / conta','deadline':'Prazo de envio','ref':'Referência',
        'candidate_ref':'REF candidata','name':'Produto / descrição','color':'Cor','size':'Tamanho','sku':'SKU',
        'variation':'Variação original','quantity':'Qtd. comercial','confirmed':'Qtd. confirmada','pending':'Qtd. pendente',
        'reconciliation':'Reconciliação','status':'Estado bruto','mark':'Marcação manual','first_seen':'Primeira importação',
        'last_seen':'Última identificação','age_days':'Dias desde importação','labels':'Etiquetas','issues':'Revisão',
        'item_id':'ID do item','category':'Tipo','erp_stage':'Etapa UpSeller','marketplace_status':'Status marketplace'}
DEFAULT_COLUMNS=['order','marketplace','shop','deadline','ref','name','color','size','quantity','confirmed','pending','status','mark','labels']


def show_rows(selected, columns=None):
    columns=DEFAULT_COLUMNS if columns is None else columns
    if not columns:
        st.caption(f'{len(selected)} registros selecionados. Selecione colunas para ver os detalhes; o PDF mantém os campos obrigatórios.')
        return
    table=[]
    for row in selected:
        record={}
        for col in columns:
            value=row.get(col)
            if isinstance(value,list): value='; '.join(value)
            if col=='deadline': value=fmt_date(value)
            record[LABELS.get(col,col)]=value
        table.append(record)
    st.dataframe(pd.DataFrame(table),hide_index=True,width='stretch')


def metrics(selected):
    t=totals(selected)
    columns=st.columns(4)
    for col,key,label in zip(columns,['orders','items','confirmed','pending'],['Pedidos distintos','Registros de itens','Unidades confirmadas','Unidades pendentes']):
        col.metric(label,t[key])
    if t['invalid_quantity']: st.warning(f"{t['invalid_quantity']} registros sem quantidade válida continuam visíveis.")
    st.caption('Unidades comerciais. As pendentes podem ser observações repetidas e não são somadas às confirmadas. Vínculo de produto pendente não apaga a quantidade comercial.')


def filter_controls(prefix, initial=None):
    initial=initial or {}
    result={}
    with st.expander('Filtros explícitos',expanded=bool(initial)):
        cols=st.columns(3)
        for n,key in enumerate(['marketplace','shop','ref','category','color','size','status','mark','reconciliation','sku']):
            opts=sorted({r[key] for r in rows if r[key] is not None})
            values=cols[n%3].multiselect(LABELS.get(key,key),opts,default=[v for v in initial.get(key,[]) if v in opts],key=prefix+key)
            if values: result[key]=values
        enable=st.checkbox('Filtrar por intervalo de prazo (inclui horários)',value=bool(initial.get('deadline_from')),key=prefix+'enable')
        if enable:
            defaults=[datetime.fromisoformat(initial[k]).astimezone(ZONE) if initial.get(k) else datetime.now(ZONE) for k in ['deadline_from','deadline_to']]
            a,b=st.columns(2)
            start_day=a.date_input('Data inicial',value=defaults[0].date(),key=prefix+'fromday')
            start_time=a.time_input('Hora inicial',value=defaults[0].time().replace(tzinfo=None) if initial.get('deadline_from') else time(0,0),key=prefix+'fromtime',step=1)
            end_day=b.date_input('Data final',value=defaults[1].date(),key=prefix+'today')
            end_time=b.time_input('Hora final',value=defaults[1].time().replace(tzinfo=None) if initial.get('deadline_to') else time(23,59,59),key=prefix+'totime',step=1)
            result['deadline_from']=datetime.combine(start_day,start_time,tzinfo=ZONE).isoformat()
            result['deadline_to']=datetime.combine(end_day,end_time,tzinfo=ZONE).isoformat()
            if result['deadline_from']>result['deadline_to']: st.error('Intervalo invertido: nenhum resultado será incluído.')
    return result


hero(page)
try:
    if page=='Dashboard':
        metrics(rows)
        if not rows: empty_state()
        groups=group_rows(rows,['marketplace','deadline'])
        overview=[]
        for leaf in leaves(groups):
            path=dict(leaf['path']);t=leaf['totals']
            overview.append({'Marketplace':path['marketplace'],'Prazo':fmt_date(path['deadline']),
                             'Pedidos distintos':t['orders'],'Confirmadas':t['confirmed'],'Pendentes':t['pending']})
        if rows:
            left,right=st.columns([1.5,1],gap='large')
            with left:
                st.subheader('Prazos por marketplace')
                st.dataframe(pd.DataFrame(overview),hide_index=True,width='stretch')
            with right:
                st.subheader('Demanda comercial')
                demand=pd.DataFrame([{'Marketplace':r['marketplace'],'Confirmadas':r['confirmed'],'Pendentes':r['pending']} for r in rows]).groupby('Marketplace').sum()
                chart_data=demand.reset_index().melt(id_vars='Marketplace',var_name='Situação',value_name='Unidades')
                chart_data=chart_data[chart_data['Unidades']>0]
                if not chart_data.empty:
                    chart=alt.Chart(chart_data).mark_bar(cornerRadiusEnd=4).encode(
                        x=alt.X('Unidades:Q',title=None,stack=None),y=alt.Y('Marketplace:N',title=None,sort='-x'),
                        yOffset=alt.YOffset('Situação:N'),
                        color=alt.Color('Situação:N',scale=alt.Scale(domain=['Confirmadas','Pendentes'],range=['#8276FF','#E8A04B']),
                                        legend=alt.Legend(orient='bottom',columns=1)),
                        tooltip=['Marketplace','Situação','Unidades']).properties(height=300).configure_view(stroke=None)
                    st.altair_chart(chart,width='stretch')
                else:st.caption('Quantidades válidas aparecerão aqui após a conferência dos registros.')
        st.subheader('Itens por prioridade')
        from central.reports import sort_rows
        show_rows(sort_rows(rows))
    elif page=='Importação':
        st.write('Selecione um ou vários Excel de qualquer loja, marketplace ou etapa. Os originais não serão modificados.')
        files=st.file_uploader('Exportações UpSeller',type=['xlsx'],accept_multiple_files=True)
        if st.button('Importar arquivos',disabled=not files,type='primary',icon=':material/upload_file:'):
            result=store.import_files([(f.name,f.getvalue()) for f in files])
            st.session_state['last_import']=result
            st.rerun()
        result=st.session_state.get('last_import')
        if result:
            st.subheader(f"Conciliação do lote {result['batch']}")
            for f in result['files']:
                if f.get('error'): st.error(f"{f['file']}: {f['error']}");continue
                ledger=store.ledger(f['attempt'])
                st.write(f"**{f['file']}** — {f['rows']} linhas; "+('arquivo duplicado, sem adicionar itens' if f['duplicate'] else 'arquivo processado'))
                outcomes=pd.DataFrame(ledger)
                if not outcomes.empty:
                    st.dataframe(outcomes.groupby('outcome',dropna=False).agg(linhas=('line','count'),quantidade_observada=('quantity','sum'),
                        novas_confirmadas_na_importacao=('confirmed_at_import','sum'),novas_pendentes_na_importacao=('pending_at_import','sum')),width='stretch')
                    st.caption('Quantidade observada neste arquivo não deve ser adicionada aos totais de outros snapshots. Consulte confirmadas e pendentes no dashboard.')
                    st.caption('As contribuições acima representam a decisão no momento da importação. Revisões posteriores aparecem na coluna de reconciliação atual e na auditoria.')
                    with st.expander('Destino de cada linha original'): st.dataframe(outcomes,hide_index=True,width='stretch')
    elif page=='Pedidos e itens':
        selected=filter_rows(rows,filter_controls('query'))
        metrics(selected);show_rows(selected)
        orders=sorted({r['order_id'] for r in selected})
        if orders:
            oid=st.selectbox('Pedido para conferir / marcar',orders,format_func=lambda v:next(f"{r['order']} · {r['marketplace']} · {r['shop']}" for r in selected if r['order_id']==v))
            current=next(r for r in selected if r['order_id']==oid)
            mark=st.selectbox('Marcação manual',['Sem marcação']+MARKS,index=(['Sem marcação']+MARKS).index(current['mark']))
            if st.button('Salvar marcação'):
                store.set_mark(oid,'' if mark=='Sem marcação' else mark);st.rerun()
            st.caption(f"Primeira importação: {fmt_date(current['first_seen'])}. Última identificação: {fmt_date(current['last_seen'])}. Antiguidade no sistema: {current['age_days']} dias. Antiguidade operacional só é contada desde uma marcação manual Pendente.")
            for r in [r for r in selected if r['order_id']==oid]:
                with st.expander(f"Item {r['item_id']} · {r['sku']} · dados e fontes"):
                    st.write('Variação original: '+r['variation'])
                    st.write('Estado exportado: '+r['status']+' · Etapa UpSeller: desconhecida · Status marketplace: desconhecido')
                    st.write('Data original do pedido: '+(r['ordered'] or 'Não informada'))
                    st.write('Prazos observados: '+('; '.join(fmt_date(v) for v in r['deadline_observations']) or 'Não informado'))
                    st.write('Etiquetas: '+'; '.join(r['labels']))
                    st.write('Revisão: '+'; '.join(r['issues']))
                    st.write('Origens:');st.write(r['sources'])
            st.subheader('Histórico das importações')
            history=store.history(oid)
            st.dataframe(pd.DataFrame([{'Arquivo':h['name'],'Importação':fmt_date(h['imported_at']),'Linha':h['line'],
                'Estado observado':json.loads(h['raw']).get('status',''),'Prazo original':json.loads(h['raw']).get('deadline',''),
                'Qtd. observada':h['quantity'],'Destino':h['outcome']} for h in history]),hide_index=True,width='stretch')
    elif page=='Produtos e vínculos SKU':
        products=[dict(r) for r in store.db.execute('SELECT * FROM products ORDER BY ref')]
        st.caption('Somente REF, PRODUTO e CUSTO_TOTAL são importados do CSV. Nenhum prefixo de SKU vira vínculo automaticamente.')
        csvfile=st.file_uploader('Importar / atualizar catálogo CSV',type=['csv'])
        if st.button('Importar catálogo',disabled=not csvfile):
            st.session_state['catalog_result']=store.import_catalog(csvfile.getvalue());st.rerun()
        if st.session_state.get('catalog_result'): st.write(st.session_state['catalog_result'])
        st.dataframe(pd.DataFrame(products),hide_index=True,width='stretch')
        refs=[p['ref'] for p in products]
        chosen=st.selectbox('Editar referência existente ou cadastrar',['Nova referência']+refs)
        existing=next((p for p in products if p['ref']==chosen),{})
        with st.form('product'):
            ref=st.text_input('REF',value=existing.get('ref',''),disabled=chosen!='Nova referência')
            name=st.text_input('Nome interno',value=existing.get('name',''))
            cost=st.text_input('Custo-base informado',value=existing.get('cost',''))
            category=st.text_input('Categoria / tipo',value=existing.get('category',''))
            photo=st.text_input('Caminho de foto local (opcional)',value=existing.get('photo',''))
            if st.form_submit_button('Salvar produto revisado'):
                store.save_product(ref,name,cost,category,photo);st.rerun()
        st.subheader('Validar vínculo SKU')
        choices=sorted({(r['marketplace'],r['shop'],r['sku']) for r in rows})
        if choices and refs:
            choice=st.selectbox('SKU por marketplace e conta',choices,format_func=lambda v:' · '.join(v))
            sample=next(r for r in rows if (r['marketplace'],r['shop'],r['sku'])==choice)
            st.write('Descrição comercial e variação: '+sample['name']+' / '+sample['variation'])
            st.write('Referência candidata (não validada): '+(sample['candidate_ref'] or 'Nenhuma'))
            for issue in sample['issues']: st.warning(issue)
            old=store.db.execute('SELECT * FROM links WHERE marketplace=? AND shop=? AND sku=?',choice).fetchone()
            with st.form('link'):
                target=st.selectbox('Referência revisada',refs,index=refs.index(old['ref']) if old else 0,format_func=lambda v:v+' · '+next(p['name'] for p in products if p['ref']==v))
                color=st.text_input('Cor validada',value=old['color'] if old else '')
                size=st.text_input('Tamanho validado',value=old['size'] if old else '')
                confirm=st.checkbox('Conferi o anúncio e confirmo este vínculo, cor e tamanho')
                if st.form_submit_button('Salvar vínculo revisado'):
                    if not confirm: st.error('A confirmação de revisão é necessária para aceitar o vínculo.')
                    else: store.save_link(*choice,target,color,size);st.rerun()
        st.subheader('Vínculos revisados')
        st.dataframe(pd.DataFrame([dict(r) for r in store.db.execute('SELECT * FROM links')]),hide_index=True,width='stretch')
    elif page=='Relatórios':
        favorites={r['name']:json.loads(r['config']) for r in store.db.execute('SELECT * FROM favorites')}
        favorite=st.selectbox('Modelo favorito',['Configuração livre']+list(favorites))
        initial=favorites.get(favorite,{})
        prefix='report_'+favorite
        filters=filter_controls(prefix,initial.get('filters'))
        st.caption('Selecione os níveis na ordem desejada. Filtros, ordem dos níveis, ordenação dos itens e colunas são independentes.')
        groups=st.multiselect('Níveis de agrupamento (ordem de seleção)',list(DIMENSIONS),default=initial.get('groups',['marketplace','deadline']),format_func=DIMENSIONS.get,key=prefix+'groups')
        sort=st.selectbox('Ordenar itens por',list(DIMENSIONS)+['order','quantity'],index=(list(DIMENSIONS)+['order','quantity']).index(initial.get('sort','deadline')),format_func=lambda v:LABELS.get(v,DIMENSIONS.get(v,v)),key=prefix+'sort')
        descending=st.checkbox('Ordem decrescente',value=initial.get('descending',False),key=prefix+'desc')
        columns=st.multiselect('Colunas da consulta',list(LABELS),default=initial.get('columns',DEFAULT_COLUMNS),format_func=LABELS.get,key=prefix+'cols')
        labels=st.checkbox('Incluir etiquetas informativas no PDF',value=initial.get('labels',True),key=prefix+'labels')
        photos=st.checkbox('Incluir fotos locais cadastradas',value=initial.get('photos',False),key=prefix+'photos')
        config={'version':1,'filters':filters,'groups':groups,'sort':sort,'descending':descending,'columns':columns,'labels':labels,'photos':photos}
        selected=filter_rows(rows,filters)
        metrics(selected)
        tree=group_rows(selected,groups,sort,descending)
        for leaf in leaves(tree):
            st.write(' > '.join(f"{DIMENSIONS[k]}: {fmt_date(v) if k=='deadline' else v}" for k,v in leaf['path']) or 'Todos os itens')
            show_rows(leaf['rows'],columns)
            st.caption(f"Subtotal: {leaf['totals']['confirmed']} confirmadas / {leaf['totals']['pending']} pendentes")
        name=st.text_input('Nome para salvar esta configuração')
        if st.button('Salvar favorito'):
            store.save_favorite(name,config);st.success('Favorito salvo.')
        st.caption('O PDF mantém sempre os campos operacionais obrigatórios, inclusive marketplace, loja, pedido e prazo, independentemente das colunas da consulta.')
        if st.button('Gerar PDF A4',type='primary',icon=':material/print:'):
            pdf=generate_pdf(selected,config)
            with store.db:
                rid=store.db.execute('INSERT INTO reports(created_at,config,snapshot,pdf_hash) VALUES(?,?,?,?)',(now(),dumps(config),dumps(selected),hashlib.sha256(pdf).hexdigest())).lastrowid
            st.session_state['pdf']={'bytes':pdf,'config':dumps(config),'rows':dumps(selected),'name':f'central-relatorio-{rid}.pdf'}
        generated=st.session_state.get('pdf')
        if generated and generated['config']==dumps(config) and generated['rows']==dumps(selected):
            st.download_button('Baixar PDF para imprimir',generated['bytes'],file_name=generated['name'],mime='application/pdf')
    else:
        st.subheader('Dados que precisam de revisão (continuam nos relatórios)')
        pending=[r for r in rows if r['issues']]
        show_rows(pending,['item_id','order','marketplace','shop','sku','quantity','confirmed','pending','issues'])
        uncertain=[r for r in rows if r['reconciliation']=='pending']
        if uncertain:
            iid=st.selectbox('Item para reconciliar',[r['item_id'] for r in uncertain])
            item=next(r for r in uncertain if r['item_id']==iid)
            st.write(item['issues'])
            targets=[r['item_id'] for r in rows if r['order_id']==item['order_id'] and r['reconciliation']=='confirmed']
            action=st.selectbox('Decisão',['Confirmar como item distinto','Mesma observação de item existente','Substituir quantidade/dados do item existente'])
            target=st.selectbox('Item existente para comparação',[None]+targets,format_func=lambda v:'Nenhum' if v is None else str(v))
            if target:
                show_rows([r for r in rows if r['item_id'] in [iid,target]])
            confirm=st.checkbox('Conferi as linhas originais e confirmo a decisão de reconciliação')
            if st.button('Aplicar reconciliação',disabled=not confirm):
                codes={'Confirmar como item distinto':'distinct','Mesma observação de item existente':'duplicate','Substituir quantidade/dados do item existente':'replace'}
                store.resolve(iid,codes[action],target);st.rerun()
        st.subheader('Importações e erros')
        st.dataframe(pd.DataFrame([dict(r) for r in store.db.execute('SELECT a.*,b.imported_at FROM attempts a JOIN batches b ON b.id=a.batch_id ORDER BY a.id DESC')]),hide_index=True,width='stretch')
        attempt_ids=[r[0] for r in store.db.execute('SELECT id FROM attempts ORDER BY id DESC')]
        if attempt_ids:
            aid=st.selectbox('Ver conciliação por linha do arquivo',attempt_ids)
            st.dataframe(pd.DataFrame(store.ledger(aid)),hide_index=True,width='stretch')
        with st.expander('Mapeamento de colunas observado'):
            for f in store.db.execute('SELECT name,layouts FROM files'):
                st.write(f['name']);st.json(json.loads(f['layouts']))
        with st.expander('Auditoria das alterações manuais'):
            st.dataframe(pd.DataFrame([dict(r) for r in store.db.execute('SELECT * FROM audit ORDER BY id DESC')]),hide_index=True,width='stretch')
        if st.button('Criar backup local do banco'):
            backup=Path(db_path).parent/'backups'/('central-'+datetime.now(ZONE).strftime('%Y%m%d-%H%M%S')+'.sqlite3')
            backup.parent.mkdir(parents=True,exist_ok=True)
            store.backup(str(backup));st.success('Backup criado: '+str(backup))
except Exception as error:
    st.error(str(error))
finally:
    store.close()
