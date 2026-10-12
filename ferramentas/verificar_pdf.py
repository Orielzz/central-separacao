"""Gera amostras locais para QA visual, sem alterar o banco operacional."""
import sys
import tempfile
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from PIL import Image
from central.core import Store
from central.pdf import generate_pdf
from central.reports import filter_rows

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'tmp/pdfs'
OUT.mkdir(parents=True,exist_ok=True)
with tempfile.TemporaryDirectory() as folder:
    store=Store(Path(folder)/'qa.sqlite3')
    store.import_catalog((ROOT/'amostras/catalogo/catalogo_base_validada_2026-10-12.csv').read_bytes())
    store.import_files([(p.name,p.read_bytes()) for p in sorted((ROOT/'amostras/upseller').glob('*.xlsx'))])
    all_rows=store.rows()
    config={'groups':['marketplace','deadline'],'labels':True,'photos':False,'filters':{}}
    output=ROOT/'output/pdf'
    output.mkdir(parents=True,exist_ok=True)
    (output/'relatorio-amostras.pdf').write_bytes(generate_pdf(all_rows,config))
    # Foto sintética local: testa proporção e paginação, não é foto de produto validada.
    image=OUT/'foto-teste.png'
    Image.new('RGB',(200,320),'#773C58').save(image)
    photo_rows=filter_rows(all_rows,{'marketplace':['Kwai']})
    for row in photo_rows:row['photo']=str(image)
    (OUT/'com-fotos.pdf').write_bytes(generate_pdf(photo_rows,{'groups':['marketplace'],'photos':True,'labels':True}))
    store.close()
print('PDFs de QA gerados localmente.')
