from __future__ import annotations

import csv
import hashlib
import io
import json
import re
import sqlite3
import unicodedata
from collections import Counter, defaultdict
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from zoneinfo import ZoneInfo

import openpyxl

ZONE = ZoneInfo('America/Sao_Paulo')
MARKS = ['Pendente', 'Em produção', 'Produzido', 'Separado', 'Conferido', 'Não necessita ação']
FIELDS = {
    'order': ['Nº de Pedido da Plataforma'], 'suborder': ['Nº do Subpedido'],
    'erp_order': ['Nº de Pedido'], 'marketplace': ['Plataformas', 'Marketplace'],
    'shop': ['Nome da Loja no UpSeller'], 'status': ['Estado do Pedido'],
    'third_status': ['3PL Status'], 'ordered': ['Hora do Pedido'],
    'printed': ['Impressão da Etiqueta'], 'sent': ['Enviado'],
    'deadline': ['Prazo de Envio'], 'sent_at': ['Hora de Envio'],
    'pickup': ['Horário da Retirada'], 'listing_name': ['Nome do Anúncio'],
    'listing_id': ['ID do Anúncio'], 'sku': ['SKU'], 'variation': ['Variação'],
    'variant_id': ['ID da Variante'], 'quantity': ['Qtd. do Produto'],
    'cancellation': ['Pós-venda/Cancelado/Devolvido'],
}


def now():
    return datetime.now(timezone.utc).isoformat()


def norm(value):
    value = unicodedata.normalize('NFKD', str(value or ''))
    return re.sub(r'[^a-z0-9]', '', ''.join(c for c in value if not unicodedata.combining(c)).lower())


def dumps(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)


def text(value):
    return '' if value is None else str(value).strip()


def date_value(value):
    if not value:
        return None
    if isinstance(value, datetime):
        dt = value
    else:
        dt = None
        for fmt in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S', '%d/%m/%Y %H:%M:%S', '%Y-%m-%d', '%d/%m/%Y'):
            try:
                dt = datetime.strptime(str(value).strip(), fmt)
                break
            except ValueError:
                pass
        if dt is None:
            raise ValueError('Data inválida: ' + str(value))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=ZONE)
    return dt.isoformat()


def quantity_value(value):
    try:
        q = Decimal(str(value).strip().replace(',', '.'))
        if not q.is_finite() or q <= 0 or q > 9223372036854775807 or q != q.to_integral_value():
            raise ValueError()
        return int(q)
    except (InvalidOperation, ValueError):
        raise ValueError('Quantidade deve ser um inteiro positivo')


def read_excel(content):
    """Todas as linhas não vazias viram observações, mesmo sob esquema desconhecido."""
    workbook = openpyxl.load_workbook(io.BytesIO(content), read_only=True, data_only=False)
    records, layouts = [], []
    try:
        for sheet in workbook:
            declared = sheet.calculate_dimension()
            sheet.reset_dimensions()
            header = None
            indices = {}
            for line, cells in enumerate(sheet.iter_rows(), 1):
                vals = [c.value for c in cells]
                if not any(v not in (None, '') for v in vals):
                    continue
                if header is None:
                    # Procurar cabeçalho sem transformar títulos de pré-âmbulo em pedidos.
                    keys = defaultdict(list)
                    for i, v in enumerate(vals):
                        keys[norm(v)].append(i)
                    possible = {k: [i for alias in aliases for i in keys[norm(alias)]] for k, aliases in FIELDS.items()}
                    if sum(bool(v) for v in possible.values()) < 2:
                        records.append({'sheet': sheet.title, 'line': line, 'raw': {}, 'quantity': None,
                                        'issues': ['Linha sem cabeçalho reconhecido; conteúdo não operacional não retido']})
                        continue
                    header = vals
                    indices = {k: v[0] for k, v in possible.items() if len(v) == 1}
                    layouts.append({'sheet': sheet.title, 'declared': declared, 'columns': len(header),
                                    'header_line': line, 'mapped': list(indices),
                                    'missing': [k for k in ('order', 'marketplace', 'shop', 'sku', 'quantity') if k not in indices],
                                    'ambiguous': [k for k, v in possible.items() if len(v) > 1]})
                    continue
                raw, issues = {}, []
                for k, i in indices.items():
                    v = vals[i] if i < len(vals) else None
                    raw[k] = text(v)
                    if isinstance(v, str) and v.startswith('='):
                        issues.append('Fórmula não avaliada em ' + k)
                    if k in ('order', 'suborder', 'erp_order', 'listing_id', 'variant_id', 'sku') and v not in (None, '') and not isinstance(v, str):
                        issues.append('Identificador numérico pode ter perdido precisão: ' + k)
                for k in ('order', 'marketplace', 'shop', 'sku'):
                    if not raw.get(k):
                        issues.append('Campo ausente: ' + k)
                try:
                    q = quantity_value(raw.get('quantity'))
                except ValueError as e:
                    q = None
                    issues.append(str(e))
                deadline = None
                try:
                    deadline = date_value(raw.get('deadline'))
                except ValueError:
                    issues.append('Prazo inválido')
                if not raw.get('deadline'):
                    issues.append('Prazo não informado')
                for k in ('printed', 'ordered', 'sent_at'):
                    if raw.get(k):
                        try:
                            date_value(raw[k])
                        except ValueError:
                            issues.append('Data inválida em ' + k)
                records.append({'sheet': sheet.title, 'line': line, 'raw': raw,
                                'quantity': q, 'deadline': deadline, 'issues': issues})
    finally:
        workbook.close()
    return records, layouts


SCHEMA = """
PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS batches(id INTEGER PRIMARY KEY, imported_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS files(id INTEGER PRIMARY KEY, hash TEXT UNIQUE NOT NULL, name TEXT, layouts TEXT);
CREATE TABLE IF NOT EXISTS attempts(id INTEGER PRIMARY KEY, batch_id INTEGER REFERENCES batches,
 file_id INTEGER REFERENCES files, name TEXT, duplicate INTEGER DEFAULT 0, error TEXT, rows INTEGER DEFAULT 0);
CREATE TABLE IF NOT EXISTS orders(id INTEGER PRIMARY KEY, identity TEXT UNIQUE NOT NULL,
 marketplace TEXT, shop TEXT, external_id TEXT, first_seen TEXT, last_seen TEXT,
 manual_mark TEXT, manual_since TEXT);
CREATE TABLE IF NOT EXISTS items(id INTEGER PRIMARY KEY, order_id INTEGER REFERENCES orders,
 signature TEXT, raw TEXT, quantity INTEGER, deadline TEXT,
 reconciliation TEXT NOT NULL, related_id INTEGER REFERENCES items, issue TEXT);
CREATE INDEX IF NOT EXISTS item_identity ON items(order_id,signature);
CREATE TABLE IF NOT EXISTS observations(id INTEGER PRIMARY KEY, attempt_id INTEGER REFERENCES attempts,
 sheet TEXT, line INTEGER, order_id INTEGER REFERENCES orders, item_id INTEGER REFERENCES items,
 raw TEXT, quantity INTEGER, deadline TEXT, issues TEXT, outcome TEXT);
CREATE TABLE IF NOT EXISTS products(ref TEXT PRIMARY KEY, name TEXT NOT NULL, cost TEXT,
 category TEXT DEFAULT '', photo TEXT DEFAULT '', reviewed INTEGER DEFAULT 0);
CREATE TABLE IF NOT EXISTS links(id INTEGER PRIMARY KEY, marketplace TEXT, shop TEXT, sku TEXT,
 ref TEXT REFERENCES products, color TEXT, size TEXT, reviewed_at TEXT,
 UNIQUE(marketplace,shop,sku));
CREATE TABLE IF NOT EXISTS favorites(name TEXT PRIMARY KEY, config TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS audit(id INTEGER PRIMARY KEY, happened_at TEXT, entity TEXT, entity_id TEXT,
 action TEXT, detail TEXT);
CREATE TABLE IF NOT EXISTS variants(id INTEGER PRIMARY KEY, ref TEXT REFERENCES products,
 color TEXT, size TEXT, attributes TEXT);
CREATE TABLE IF NOT EXISTS kit_components(id INTEGER PRIMARY KEY, parent_ref TEXT REFERENCES products,
 component_ref TEXT REFERENCES products, quantity INTEGER CHECK(quantity>0), reviewed INTEGER DEFAULT 0);
CREATE TABLE IF NOT EXISTS reports(id INTEGER PRIMARY KEY, created_at TEXT, config TEXT, snapshot TEXT, pdf_hash TEXT);
PRAGMA user_version=1;
"""


class Store:
    def __init__(self, path='dados/central.sqlite3'):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(self.path)
        self.db.row_factory = sqlite3.Row
        self.db.executescript(SCHEMA)

    def close(self):
        self.db.close()

    def audit(self, entity, entity_id, action, detail):
        self.db.execute('INSERT INTO audit(happened_at,entity,entity_id,action,detail) VALUES(?,?,?,?,?)',
                        (now(), entity, str(entity_id), action, dumps(detail)))

    def import_catalog(self, content):
        rows = list(csv.DictReader(io.StringIO(content.decode('utf-8-sig')), delimiter=';'))
        if not rows or not {'REF', 'PRODUTO', 'CUSTO_TOTAL'} <= set(rows[0]):
            raise ValueError('CSV precisa de REF, PRODUTO e CUSTO_TOTAL, separados por ponto e vírgula')
        counts = Counter(text(r['REF']) for r in rows)
        errors, inserted, protected = [], 0, 0
        with self.db:
            for n, r in enumerate(rows, 2):
                ref, name = text(r['REF']), text(r['PRODUTO'])
                try:
                    cost = Decimal(r['CUSTO_TOTAL'].replace(',', '.'))
                    if not ref or not name or counts[ref] > 1 or not cost.is_finite() or cost < 0:
                        raise ValueError()
                except (ValueError, InvalidOperation):
                    errors.append(f'Linha {n}: referência, produto ou custo inválido/duplicado')
                    continue
                old = self.db.execute('SELECT * FROM products WHERE ref=?', (ref,)).fetchone()
                if old and old['reviewed']:
                    protected += 1
                    continue
                self.db.execute('INSERT INTO products(ref,name,cost) VALUES(?,?,?) ON CONFLICT(ref) DO UPDATE SET name=excluded.name,cost=excluded.cost', (ref, name, str(cost)))
                inserted += 1
            self.audit('catalog', '', 'importação', {'accepted': inserted, 'protected': protected, 'errors': errors})
        return {'accepted': inserted, 'protected': protected, 'errors': errors}

    def import_files(self, files, timestamp=None):
        timestamp = timestamp or now()
        summaries = []
        with self.db:
            batch = self.db.execute('INSERT INTO batches(imported_at) VALUES(?)', (timestamp,)).lastrowid
            for name, content in files:
                # Savepoint: falha de arquivo não deixa pedidos parcialmente gravados.
                self.db.execute('SAVEPOINT file_import')
                try:
                    digest = hashlib.sha256(content).hexdigest()
                    existing = self.db.execute('SELECT * FROM files WHERE hash=?', (digest,)).fetchone()
                    if existing:
                        fid = existing['id']
                        attempt = self.db.execute('INSERT INTO attempts(batch_id,file_id,name,duplicate) VALUES(?,?,?,1)', (batch, fid, name)).lastrowid
                        source = self.db.execute('SELECT o.* FROM observations o JOIN attempts a ON a.id=o.attempt_id WHERE a.file_id=? ORDER BY o.id', (fid,)).fetchall()
                        source = [r for r in source if r['attempt_id'] == source[0]['attempt_id']] if source else []
                        for r in source:
                            self.db.execute('INSERT INTO observations(attempt_id,sheet,line,order_id,item_id,raw,quantity,deadline,issues,outcome) VALUES(?,?,?,?,?,?,?,?,?,?)',
                                (attempt,r['sheet'],r['line'],r['order_id'],r['item_id'],r['raw'],r['quantity'],r['deadline'],r['issues'],'arquivo duplicado'))
                            self.db.execute('UPDATE orders SET last_seen=MAX(last_seen,?) WHERE id=?', (timestamp,r['order_id']))
                        self.db.execute('UPDATE attempts SET rows=? WHERE id=?', (len(source),attempt))
                        summaries.append({'file': name, 'attempt':attempt,'rows':len(source),'duplicate':True})
                    else:
                        records, layouts = read_excel(content)
                        fid = self.db.execute('INSERT INTO files(hash,name,layouts) VALUES(?,?,?)', (digest,name,dumps(layouts))).lastrowid
                        attempt = self.db.execute('INSERT INTO attempts(batch_id,file_id,name,rows) VALUES(?,?,?,?)', (batch,fid,name,len(records))).lastrowid
                        signatures = []
                        for r in records:
                            raw = r['raw']
                            identity = [raw.get(k,'') for k in ('marketplace','shop','order')]
                            good = all(identity) and not any('Identificador numérico' in e for e in r['issues'])
                            key = dumps(identity) if good else dumps(['incerto',digest,r['sheet'],r['line']])
                            sig = dumps([raw.get(k,'') for k in ('suborder','listing_id','variant_id','sku','variation')])
                            signatures.append((key,sig,good))
                        counts = Counter((key,sig) for key,sig,_ in signatures)
                        quantity_counts = Counter((key,sig,r['quantity']) for r,(key,sig,_) in zip(records,signatures))
                        match_cursor = Counter()
                        # Candidatos anteriores ao arquivo: multiplicidade dentro do arquivo não é deduplicada.
                        previous = defaultdict(list)
                        for item in self.db.execute("SELECT * FROM items WHERE reconciliation!='resolved'"):
                            previous[(item['order_id'],item['signature'])].append(item)
                        for r,(key,sig,good) in zip(records,signatures):
                            raw = r['raw']
                            order = self.db.execute('SELECT * FROM orders WHERE identity=?',(key,)).fetchone()
                            if order:
                                oid = order['id']
                                self.db.execute('UPDATE orders SET last_seen=MAX(last_seen,?) WHERE id=?',(timestamp,oid))
                            else:
                                oid = self.db.execute('INSERT INTO orders(identity,marketplace,shop,external_id,first_seen,last_seen) VALUES(?,?,?,?,?,?)',
                                    (key,raw.get('marketplace',''),raw.get('shop',''),raw.get('order',''),timestamp,timestamp)).lastrowid
                            matches = previous[(oid,sig)]
                            exact_matches = [m for m in matches if m['quantity']==r['quantity']]
                            ambiguous = not good or r['quantity'] is None or counts[(key,sig)] > 1 or any('Fórmula' in e for e in r['issues'])
                            if not raw.get('sku'):
                                ambiguous=True
                            related = None
                            reason = ''
                            stable_multiset = (good and bool(raw.get('sku')) and r['quantity'] is not None
                                and not any('Fórmula' in e for e in r['issues'])
                                and len(exact_matches)==quantity_counts[(key,sig,r['quantity'])])
                            if stable_multiset and exact_matches:
                                cursor_key=(oid,sig,r['quantity'])
                                matched=exact_matches[match_cursor[cursor_key]]
                                match_cursor[cursor_key]+=1
                                iid = matched['id']
                                outcome = 'reobservado' if matched['reconciliation']=='confirmed' else 'pendente reobservado'
                            else:
                                if matches:
                                    ambiguous = True
                                    related = matches[0]['id'] if len(matches)==1 else None
                                    reason = 'Possível reexportação/alteração de item; reconciliar quantidade e identidade'
                                if counts[(key,sig)]>1:
                                    reason = 'Linhas semelhantes preservadas; confirmar multiplicidade'
                                if not good:
                                    reason = 'Identidade do pedido incompleta ou numérica; confirmar antes de somar'
                                if not raw.get('sku'):
                                    reason = 'SKU ausente; identidade do item precisa de revisão'
                                # Variante/SKU alterado do mesmo anúncio exige conferência, não novo total automático.
                                if not matches:
                                    alternatives = self.db.execute('SELECT * FROM items WHERE order_id=?',(oid,)).fetchall()
                                    alternatives = [i for i in alternatives if any(p['id']==i['id'] for p in previous.get((oid,i['signature']),[]))]
                                    if alternatives:
                                        ambiguous=True
                                        related=alternatives[0]['id'] if len(alternatives)==1 else None
                                        reason='Novo identificador de item em pedido já observado; confirmar acréscimo ou correção'
                                state = 'pending' if ambiguous else 'confirmed'
                                iid = self.db.execute('INSERT INTO items(order_id,signature,raw,quantity,deadline,reconciliation,related_id,issue) VALUES(?,?,?,?,?,?,?,?)',
                                    (oid,sig,dumps(raw),r['quantity'],r.get('deadline'),state,related,reason)).lastrowid
                                outcome = 'pendente' if ambiguous else 'novo item'
                            self.db.execute('INSERT INTO observations(attempt_id,sheet,line,order_id,item_id,raw,quantity,deadline,issues,outcome) VALUES(?,?,?,?,?,?,?,?,?,?)',
                                (attempt,r['sheet'],r['line'],oid,iid,dumps(raw),r['quantity'],r.get('deadline'),dumps(r['issues']),outcome))
                        summaries.append({'file':name,'attempt':attempt,'rows':len(records),'duplicate':False})
                    self.db.execute('RELEASE file_import')
                except Exception as e:
                    self.db.execute('ROLLBACK TO file_import')
                    self.db.execute('RELEASE file_import')
                    message = f'{type(e).__name__}: {e}'
                    self.db.execute('INSERT INTO attempts(batch_id,name,error) VALUES(?,?,?)',(batch,name,message))
                    summaries.append({'file':name,'error':message})
        return {'batch':batch,'files':summaries}

    def set_mark(self, order_id, mark, timestamp=None):
        if mark not in MARKS + ['']:
            raise ValueError('Marcação inválida')
        timestamp = timestamp or now()
        with self.db:
            old = self.db.execute('SELECT * FROM orders WHERE id=?',(order_id,)).fetchone()
            if not old:
                raise ValueError('Pedido inexistente')
            since = old['manual_since'] if old['manual_mark']==mark else (timestamp if mark else None)
            self.db.execute('UPDATE orders SET manual_mark=?,manual_since=? WHERE id=?',(mark,since,order_id))
            self.audit('order',order_id,'marcação manual',{'before':old['manual_mark'],'after':mark,'since':since})

    def resolve(self, item_id, action, target_id=None):
        with self.db:
            item = self.db.execute('SELECT * FROM items WHERE id=?',(item_id,)).fetchone()
            if not item or item['reconciliation']!='pending':
                raise ValueError('Item não está pendente')
            if action=='distinct':
                if item['quantity'] is None:
                    raise ValueError('Quantidade inválida: corrigir a fonte e reimportar; não assumir zero')
                self.db.execute("UPDATE items SET reconciliation='confirmed',issue='' WHERE id=?",(item_id,))
            elif action in ('duplicate','replace') and (target_id or item['related_id']):
                target = self.db.execute('SELECT * FROM items WHERE id=?',(target_id or item['related_id'],)).fetchone()
                if not target or target['reconciliation']!='confirmed' or target['order_id']!=item['order_id']:
                    raise ValueError('Destino precisa ser um item confirmado')
                if action=='replace':
                    if item['quantity'] is None:
                        raise ValueError('Quantidade inválida')
                    self.db.execute('UPDATE items SET raw=?,quantity=?,deadline=?,signature=? WHERE id=?',
                                    (item['raw'],item['quantity'],item['deadline'],item['signature'],target['id']))
                self.db.execute("UPDATE items SET reconciliation='resolved',related_id=?,issue=? WHERE id=?",(target['id'],'Reconciliado manualmente: '+action,item_id))
            else:
                raise ValueError('Ação exige correspondência inequívoca; confirme itens distintos quando apropriado')
            self.audit('item',item_id,'reconciliação',action)

    def save_product(self, ref, name, cost, category='', photo=''):
        c = Decimal(str(cost).replace(',','.'))
        if not ref.strip() or not name.strip() or not c.is_finite() or c<0:
            raise ValueError('Referência, nome e custo válido são obrigatórios')
        with self.db:
            self.db.execute('INSERT INTO products(ref,name,cost,category,photo,reviewed) VALUES(?,?,?,?,?,1) ON CONFLICT(ref) DO UPDATE SET name=excluded.name,cost=excluded.cost,category=excluded.category,photo=excluded.photo,reviewed=1', (ref.strip(),name.strip(),str(c),category,photo))
            self.audit('product',ref,'revisão manual',{'name':name,'cost':str(c),'category':category})

    def save_link(self, marketplace, shop, sku, ref, color, size):
        if not sku or not self.db.execute('SELECT 1 FROM products WHERE ref=?',(ref,)).fetchone():
            raise ValueError('SKU e referência existente são obrigatórios')
        with self.db:
            self.db.execute('INSERT INTO links(marketplace,shop,sku,ref,color,size,reviewed_at) VALUES(?,?,?,?,?,?,?) ON CONFLICT(marketplace,shop,sku) DO UPDATE SET ref=excluded.ref,color=excluded.color,size=excluded.size,reviewed_at=excluded.reviewed_at', (marketplace,shop,sku,ref,color,size,now()))
            self.audit('sku',dumps([marketplace,shop,sku]),'vínculo revisado',{'ref':ref,'color':color,'size':size})

    def save_favorite(self, name, config):
        if not name.strip():
            raise ValueError('Informe um nome')
        with self.db:
            self.db.execute('INSERT INTO favorites VALUES(?,?) ON CONFLICT(name) DO UPDATE SET config=excluded.config',(name.strip(),dumps(config)))

    def history(self, order_id):
        return [dict(r) for r in self.db.execute('SELECT o.sheet,o.line,o.raw,o.quantity,o.outcome,a.name,b.imported_at FROM observations o JOIN attempts a ON a.id=o.attempt_id JOIN batches b ON b.id=a.batch_id WHERE o.order_id=? ORDER BY b.imported_at,o.id',(order_id,))]

    def ledger(self, attempt_id):
        result=[]
        for row in self.db.execute('SELECT o.sheet,o.line,o.item_id,o.quantity,o.outcome,o.issues,i.reconciliation FROM observations o JOIN items i ON i.id=o.item_id WHERE o.attempt_id=? ORDER BY o.id',(attempt_id,)):
            r=dict(row)
            r['confirmed_at_import']=(r['quantity'] or 0) if r['outcome']=='novo item' else 0
            r['pending_at_import']=(r['quantity'] or 0) if r['outcome']=='pendente' else 0
            result.append(r)
        return result

    def rows(self, at=None):
        at = datetime.fromisoformat(at or now())
        products = {r['ref']:dict(r) for r in self.db.execute('SELECT * FROM products')}
        links = {(r['marketplace'],r['shop'],r['sku']):dict(r) for r in self.db.execute('SELECT * FROM links')}
        observations = defaultdict(list)
        for r in self.db.execute('SELECT o.*,a.name,a.batch_id,b.imported_at FROM observations o JOIN attempts a ON a.id=o.attempt_id JOIN batches b ON b.id=a.batch_id ORDER BY b.imported_at,o.id'):
            observations[r['item_id']].append(r)
        results=[]
        for i in self.db.execute('SELECT i.*,o.marketplace,o.shop,o.external_id,o.first_seen,o.last_seen,o.manual_mark,o.manual_since FROM items i JOIN orders o ON o.id=i.order_id ORDER BY i.id'):
            raw=json.loads(i['raw']); obs=observations[i['id']]
            latest=json.loads(obs[-1]['raw']) if obs else raw
            issues = sorted(set(e for ob in obs for e in json.loads(ob['issues'])))
            if i['issue']: issues.append(i['issue'])
            sku=raw.get('sku','')
            link=links.get((i['marketplace'],i['shop'],sku))
            prefix=re.match(r'^(\d+)[.\-]',sku)
            candidate=prefix.group(1) if prefix else ''
            product=products.get(link['ref']) if link else None
            if not link:
                issues.append('SKU sem vínculo revisado' + ('; REF candidata '+candidate+(' ausente no catálogo' if candidate not in products else '') if candidate else ''))
            if sku=='875-Preto-M' and not link:
                issues.append('Conflito REF 875: anúncio de camisola versus blusa de tule + cropped')
            deadlines=sorted(set(ob['deadline'] for ob in obs if ob['deadline']))
            if len(deadlines)>1: issues.append('Prazos divergentes; exibido o menor para atenção')
            deadline = min(deadlines) if deadlines else i['deadline']
            ordered_dates=list(dict.fromkeys(json.loads(ob['raw']).get('ordered') for ob in obs if json.loads(ob['raw']).get('ordered')))
            if len(ordered_dates)>1: issues.append('Datas originais do pedido divergentes; consultar histórico')
            labels=[]
            batches={ob['batch_id'] for ob in obs}
            labels.append('Já importado' if len(batches)>1 else 'Novo no sistema')
            age=max(0,(at.astimezone(ZONE).date()-datetime.fromisoformat(i['first_seen']).astimezone(ZONE).date()).days)
            printed=[]
            for ob in obs:
                v=json.loads(ob['raw']).get('printed')
                try:
                    if date_value(v): printed.append(v)
                except ValueError: pass
            labels.append('Etiqueta impressa' if printed else 'Impressão não informada')
            if latest.get('status') not in ('Pendente Revisão','Em Processo','Retirada'):
                labels.append('Status desconhecido')
            operational_days=None
            if i['manual_mark']=='Pendente' and i['manual_since']:
                operational_days=max(0,(at.astimezone(ZONE).date()-datetime.fromisoformat(i['manual_since']).astimezone(ZONE).date()).days)
                labels.append(f'Pendente há {operational_days} dias (marcação manual)')
            if issues: labels.append('Dados precisam de revisão')
            state=i['reconciliation']
            results.append({'item_id':i['id'],'order_id':i['order_id'],'order':i['external_id'] or 'Identidade não informada',
                'marketplace':i['marketplace'] or 'Não informado','shop':i['shop'] or 'Não informado',
                'deadline':deadline,'ref':link['ref'] if link else 'Não validada', 'candidate_ref':candidate,
                'name':product['name'] if product else raw.get('listing_name') or 'Não informado',
                'category':product['category'] or 'Não informado' if product else 'Não informado',
                'color':link['color'] or 'Não informado' if link else 'Não validada',
                'size':link['size'] or 'Não informado' if link else 'Não validado',
                'sku':sku,'variation':raw.get('variation',''),'quantity':i['quantity'],
                'confirmed':i['quantity'] if state=='confirmed' and i['quantity'] is not None else 0,
                'pending':i['quantity'] if state=='pending' and i['quantity'] is not None else 0,
                'reconciliation':state,'related_id':i['related_id'],'status':latest.get('status') or 'Não informado',
                'erp_stage':'Desconhecida','marketplace_status':'Desconhecido',
                'mark':i['manual_mark'] or 'Sem marcação','first_seen':i['first_seen'],'last_seen':i['last_seen'],
                'ordered':ordered_dates[0] if ordered_dates else '', 'deadline_observations':deadlines,
                'age_days':age,'operational_days':operational_days,
                'labels':labels,'issues':issues,'sources':[f"{ob['name']} / {ob['sheet']} / linha {ob['line']}" for ob in obs],
                'photo':product['photo'] if product else ''})
        return results

    def backup(self, destination):
        target=sqlite3.connect(destination)
        try:
            self.db.backup(target)
        finally:
            target.close()
