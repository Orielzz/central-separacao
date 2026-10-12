from collections import defaultdict
from datetime import datetime

DIMENSIONS = {'marketplace':'Marketplace','shop':'Loja / conta','deadline':'Prazo (data e hora)',
              'category':'Tipo de peça','ref':'Referência','color':'Cor','size':'Tamanho'}
FILTERS = set(DIMENSIONS) | {'status','mark','reconciliation','sku','order'}


def filter_rows(rows, filters=None):
    filters=filters or {}
    if set(filters)-FILTERS-{'deadline_from','deadline_to'}:
        raise ValueError('Filtro desconhecido')
    result=[]
    for row in rows:
        if any(values and row.get(key) not in values for key,values in filters.items() if key in FILTERS):
            continue
        if filters.get('deadline_from') or filters.get('deadline_to'):
            if not row['deadline']: continue
            dt=datetime.fromisoformat(row['deadline'])
            if filters.get('deadline_from') and dt<datetime.fromisoformat(filters['deadline_from']): continue
            if filters.get('deadline_to') and dt>datetime.fromisoformat(filters['deadline_to']): continue
        result.append(row)
    return result


def sort_rows(rows, key='deadline', descending=False):
    if key not in DIMENSIONS and key not in ('order','quantity'):
        raise ValueError('Ordenação desconhecida')
    known=[r for r in rows if r.get(key) is not None]
    unknown=[r for r in rows if r.get(key) is None]
    return sorted(known,key=lambda r:r[key],reverse=descending)+unknown


def totals(rows):
    return {'orders':len({r['order_id'] for r in rows}),'items':len(rows),
            'confirmed':sum(r['confirmed'] for r in rows),'pending':sum(r['pending'] for r in rows),
            'invalid_quantity':sum(r['quantity'] is None for r in rows),
            'resolved':sum(r['reconciliation']=='resolved' for r in rows)}


def group_rows(rows, dimensions, sort='deadline', descending=False):
    if len(dimensions)!=len(set(dimensions)) or any(d not in DIMENSIONS for d in dimensions):
        raise ValueError('Dimensões inválidas ou repetidas')
    ordered=sort_rows(rows,sort,descending)
    def build(items,depth,path):
        node={'path':path,'totals':totals(items),'children':[],'rows':[]}
        if depth==len(dimensions):
            node['rows']=items
            return node
        buckets=defaultdict(list)
        dim=dimensions[depth]
        for r in items: buckets[r.get(dim) or 'Não informado'].append(r)
        for value in sorted(buckets,key=str):
            node['children'].append(build(buckets[value],depth+1,path+[(dim,value)]))
        return node
    return build(ordered,0,[])


def leaves(tree):
    if not tree['children']:
        yield tree
    for child in tree['children']:
        yield from leaves(child)
