"""Apresentação: cores nativas claro/escuro e estilos sem interferir nos dados."""
from html import escape
import streamlit as st

PAGES = {
    'Dashboard': ('space_dashboard','Visão geral da operação','Acompanhe os pedidos, seus prazos e o que precisa de atenção.'),
    'Importação': ('upload_file','Novos arquivos, uma só operação','Reúna as exportações das suas lojas em um lugar.'),
    'Pedidos e itens': ('inventory_2','Cada pedido, cada detalhe','Consulte os produtos, confira a origem e registre o andamento.'),
    'Produtos e vínculos SKU': ('sell','Um catálogo para suas lojas','Organize referências e valide como cada SKU se conecta ao produto.'),
    'Relatórios': ('print','Organize. Confira. Imprima.','Monte sua lista com a combinação de filtros e grupos que funciona para você.'),
    'Histórico e pendências': ('history','Uma operação rastreável','Acompanhe importações, revise divergências e consulte as decisões.'),
}


def styles():
    # currentColor acompanha o tema nativo instantaneamente, inclusive sem rerun.
    st.html('''<style>
    .stMainBlockContainer {max-width: 1500px; padding-top: 4.4rem; padding-bottom: 3rem;}
    [data-testid="stAppDeployButton"] {display:none;}
    [data-testid="stSidebar"] {min-width: 270px; max-width: 290px;}
    [data-testid="stSidebarUserContent"] {padding-top: 1.7rem;}
    .cs-brand {display:flex;align-items:center;gap:12px;margin:0 0 28px;}
    .cs-logo {display:grid;place-items:center;width:44px;height:44px;border-radius:14px;background:linear-gradient(145deg,#635bff,#a077ed);color:#fff;font-weight:800;font-size:18px;box-shadow:0 6px 20px #635bff26;}
    .cs-brand strong {font-size:18px;letter-spacing:-.5px;}
    .cs-brand small {display:block;font-size:11px;opacity:.6;letter-spacing:1.5px;margin-top:2px;text-transform:uppercase;}
    [data-testid="stSidebar"] [role="radiogroup"] {gap:5px;}
    [data-testid="stSidebar"] [data-baseweb="radio"] {padding:10px 12px;margin:0;width:100%;border-radius:11px;transition:background .15s;}
    [data-testid="stSidebar"] [data-baseweb="radio"]:hover {background:color-mix(in srgb,currentColor 5%,transparent);}
    [data-testid="stSidebar"] [data-baseweb="radio"]:has(input:checked) {background:#635bff19;box-shadow:inset 3px 0 #8276ff;}
    [data-testid="stSidebar"] [data-baseweb="radio"] > div:first-child {display:none;}
    [data-testid="stSidebar"] [data-baseweb="radio"] p {font-size:13px;font-weight:550;}
    .cs-kicker {font-size:11px;font-weight:700;letter-spacing:1.6px;text-transform:uppercase;opacity:.55;}
    .cs-hero {padding:5px 0 22px;margin-bottom:18px;border-bottom:1px solid color-mix(in srgb,currentColor 10%,transparent);}
    .cs-hero h1 {font-size:clamp(25px,3vw,36px);font-weight:750;letter-spacing:-1.3px;line-height:1.2;margin:10px 0;}
    .cs-hero p {font-size:14px;opacity:.65;margin:0;line-height:1.6;}
    .cs-status {display:inline-flex;align-items:center;gap:7px;padding:5px 10px;background:#10b98114;color:#10a780;border:1px solid #10b98128;border-radius:100px;font-size:11px;font-weight:650;}
    .cs-status:before {content:'';width:6px;height:6px;border-radius:50%;background:#10b981;}
    .cs-hero-top {display:flex;align-items:center;justify-content:space-between;gap:12px;}
    [data-testid="stMetric"] {padding:20px 23px;border:1px solid color-mix(in srgb,currentColor 10%,transparent);border-radius:16px;background:color-mix(in srgb,currentColor 2%,transparent);box-shadow:0 3px 12px #00000004;}
    [data-testid="stMetricLabel"] {font-size:12px;opacity:.65;min-height:36px;}
    [data-testid="stMetricLabel"] p {white-space:normal !important;overflow:visible !important;text-overflow:unset !important;}
    [data-testid="stMetricValue"] {font-size:34px;letter-spacing:-1px;font-weight:750;}
    [data-testid="stExpander"] {border-radius:14px;}
    [data-testid="stDataFrame"] {border-radius:12px;overflow:hidden;}
    [data-testid="stFileUploader"] {border-radius:16px;}
    [data-testid="stFileUploaderDropzone"] {padding:35px 22px;border:1px dashed #9389df;}
    .stButton button,.stDownloadButton button {font-weight:650;min-height:40px;transition:transform .12s;}
    .stButton button:hover,.stDownloadButton button:hover {transform:translateY(-1px);}
    h2,h3 {letter-spacing:-.5px;}
    h3 {font-size:19px !important;}
    .cs-empty {text-align:center;padding:48px 24px;border:1px dashed color-mix(in srgb,currentColor 15%,transparent);border-radius:18px;background:linear-gradient(130deg,#635bff09,transparent);margin:16px 0;}
    .cs-empty strong {font-size:21px;display:block;letter-spacing:-.5px;margin:12px 0;}
    .cs-empty p {font-size:14px;opacity:.6;max-width:450px;margin:auto;line-height:1.7;}
    .cs-empty-icon {font-size:28px;color:#9389df;}
    @media(max-width:1100px) {[data-testid="stHorizontalBlock"]:has([data-testid="stVegaLiteChart"]) {flex-direction:column;} [data-testid="stHorizontalBlock"]:has([data-testid="stVegaLiteChart"]) > [data-testid="stColumn"] {width:100%;flex:1 1 100%;}}
    @media(max-width:700px) {.stMainBlockContainer {padding:4rem 1rem 1.4rem;} .cs-hero h1{font-size:27px;} [data-testid="stMetric"]{padding:12px;} .cs-status {font-size:10px;}}
    </style>''')


def sidebar():
    st.sidebar.html('<div class="cs-brand"><div class="cs-logo">CS</div><div><strong>Central</strong><small>Separação & Produção</small></div></div>')
    page=st.sidebar.radio('Área de trabalho',list(PAGES),key='navigation',
        format_func=lambda p: f':material/{PAGES[p][0]}:  {p}',label_visibility='collapsed')
    st.sidebar.divider()
    st.sidebar.caption('SUAS LOJAS')
    st.sidebar.markdown('**AnnaLiv** &nbsp; **DonaMora**',unsafe_allow_html=True)
    st.sidebar.caption('Horário de São Paulo · Operação local')
    with st.sidebar.expander(':material/contrast: Aparência'):
        st.caption('Use o menu ⋮ no canto superior direito. Em Theme, escolha Light (claro), Dark (escuro) ou System (seguir o computador). A escolha fica salva neste navegador.')
    with st.sidebar.expander(':material/visibility: Todos os pedidos visíveis'):
        st.caption('Status e marcações não ocultam pedidos. Apenas os filtros escolhidos por você restringem a consulta e impressão.')
    return page


def hero(page):
    _,title,description=PAGES[page]
    st.html(f'<section class="cs-hero"><div class="cs-hero-top"><span class="cs-kicker">Central / {escape(page)}</span><span class="cs-status">Operação local</span></div><h1>{escape(title)}</h1><p>{escape(description)}</p></section>')


def empty_state():
    st.html('<div class="cs-empty"><div class="cs-empty-icon">↥</div><strong>Sua operação começa aqui</strong><p>Importe as exportações do UpSeller para acompanhar pedidos, organizar prioridades e preparar suas listas de conferência.</p></div>')
    st.button('Importar meus primeiros arquivos',icon=':material/upload_file:',type='primary',
        on_click=lambda:st.session_state.update(navigation='Importação'))
