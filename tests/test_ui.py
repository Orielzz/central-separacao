import os
import tempfile
import unittest
from pathlib import Path

from streamlit.testing.v1 import AppTest

from central.core import Store

ROOT=Path(__file__).resolve().parents[1]


@unittest.skipUnless((ROOT/'amostras/upseller').exists() and (ROOT/'amostras/catalogo/catalogo_base_validada_2026-10-12.csv').exists(), 'Testes da interface com amostras privadas executados localmente')
class InterfaceTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.path=Path(self.tmp.name)/'ui.sqlite3'
        self.previous=os.environ.get('CENTRAL_DB')
        os.environ['CENTRAL_DB']=str(self.path)
        store=Store(self.path)
        store.import_catalog((ROOT/'amostras/catalogo/catalogo_base_validada_2026-10-12.csv').read_bytes())
        store.import_files([(p.name,p.read_bytes()) for p in sorted((ROOT/'amostras/upseller').glob('*.xlsx'))])
        store.close()
        self.app=AppTest.from_file(str(ROOT/'app.py'),default_timeout=20).run()

    def tearDown(self):
        if self.previous is None:os.environ.pop('CENTRAL_DB',None)
        else:os.environ['CENTRAL_DB']=self.previous
        self.tmp.cleanup()

    def assert_clean(self):
        self.assertEqual(len(self.app.exception),0,[e.message for e in self.app.exception])
        self.assertEqual(len(self.app.error),0,[e.value for e in self.app.error])

    def go(self,page):
        self.app.sidebar.radio[0].set_value(page).run()
        self.assert_clean()

    def test_all_six_screens_load(self):
        self.assert_clean()
        self.assertEqual([m.value for m in self.app.metric],['163','179','180','0'])
        for page in ['Importação','Pedidos e itens','Produtos e vínculos SKU','Relatórios','Histórico e pendências']:
            self.go(page)

    def test_manual_mark_ui_and_report_still_contains_all(self):
        self.go('Pedidos e itens')
        next(s for s in self.app.selectbox if s.label=='Marcação manual').set_value('Não necessita ação')
        next(b for b in self.app.button if b.label=='Salvar marcação').click().run()
        self.assert_clean()
        self.go('Relatórios')
        self.assertEqual([m.value for m in self.app.metric],['163','179','180','0'])

    def test_report_filter_group_favorite_and_pdf(self):
        self.go('Relatórios')
        next(m for m in self.app.multiselect if m.label=='Marketplace').set_value(['Mercado Libre']).run()
        self.assert_clean()
        self.assertEqual([m.value for m in self.app.metric],['68','77','77','0'])
        next(m for m in self.app.multiselect if m.label.startswith('Níveis')).set_value(['color','ref','size']).run()
        next(t for t in self.app.text_input if t.label.startswith('Nome para salvar')).set_value('Mercado Livre por cor')
        next(b for b in self.app.button if b.label=='Salvar favorito').click().run()
        self.assert_clean()
        next(b for b in self.app.button if b.label=='Gerar PDF A4').click().run()
        self.assert_clean()
        self.assertTrue(self.app.session_state['pdf']['bytes'].startswith(b'%PDF'))
        next(s for s in self.app.selectbox if s.label=='Modelo favorito').set_value('Mercado Livre por cor').run()
        self.assert_clean()
        self.assertEqual([m.value for m in self.app.metric],['68','77','77','0'])
        self.assertEqual(next(m for m in self.app.multiselect if m.label.startswith('Níveis')).value,['color','ref','size'])
        store=Store(self.path)
        try:
            self.assertEqual(store.db.execute('SELECT COUNT(*) FROM reports').fetchone()[0],1)
            self.assertEqual(store.db.execute('SELECT COUNT(*) FROM favorites').fetchone()[0],1)
        finally:store.close()

    def test_pending_resolution_interface(self):
        from test_core import excel
        store=Store(self.path)
        try:store.import_files([('duplicidade.xlsx',excel([{},{}]))])
        finally:store.close()
        self.go('Histórico e pendências')
        next(s for s in self.app.selectbox if s.label=='Decisão').set_value('Confirmar como item distinto')
        next(c for c in self.app.checkbox if c.label.startswith('Conferi as linhas')).check()
        next(b for b in self.app.button if b.label=='Aplicar reconciliação').click().run()
        self.assert_clean()
        store=Store(self.path)
        try:
            states=[r['reconciliation'] for r in store.rows() if r['order']=='00012345678901234567890']
            self.assertEqual(sorted(states),['confirmed','pending'])
        finally:store.close()

    def test_product_and_sku_review_form(self):
        self.go('Produtos e vínculos SKU')
        next(s for s in self.app.selectbox if s.label.startswith('Editar referência')).set_value('100').run()
        next(t for t in self.app.text_input if t.label=='Categoria / tipo').set_value('Body')
        next(b for b in self.app.button if b.label=='Salvar produto revisado').click().run()
        self.assert_clean()
        choices=next(s for s in self.app.selectbox if s.label=='SKU por marketplace e conta')
        # Escolha com REF 100 e guarde o escopo para verificar o vínculo.
        store=Store(self.path)
        try:choice=next((r['marketplace'],r['shop'],r['sku']) for r in store.rows() if r['candidate_ref']=='100')
        finally:store.close()
        choices.set_value(choice).run()
        next(s for s in self.app.selectbox if s.label=='Referência revisada').set_value('100')
        next(t for t in self.app.text_input if t.label=='Cor validada').set_value('Preto')
        next(t for t in self.app.text_input if t.label=='Tamanho validado').set_value('50')
        next(c for c in self.app.checkbox if c.label.startswith('Conferi o anúncio')).check()
        next(b for b in self.app.button if b.label=='Salvar vínculo revisado').click().run()
        self.assert_clean()
        store=Store(self.path)
        try:self.assertEqual(store.db.execute('SELECT ref FROM links WHERE marketplace=? AND shop=? AND sku=?',choice).fetchone()[0],'100')
        finally:store.close()


if __name__=='__main__':unittest.main()
