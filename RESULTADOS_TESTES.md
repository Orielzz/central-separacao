# Validação do MVP

Executada em 12/10/2026, no Windows desta máquina, usando o ambiente `.venv` do projeto.

## Resultado

**25 testes automatizados passaram**, em 5,579 segundos na execução final:

```text
python -m unittest discover -s tests -v
Ran 25 tests in 5.579s
OK
```

São 20 testes de serviços e 5 de interface Streamlit via AppTest. A verificação de dependências também passou: `pip check` retornou `No broken requirements found`. Os requisitos fixados foram conferidos com instalação `--no-index` contra o ambiente preparado.

## Evidências verificadas

- Os oito Excel reais foram lidos integralmente, ignorando a dimensão A1 incorreta.
- As 254 linhas dos oito arquivos têm observações e destinos registrados. Duas cópias binárias não criam itens adicionais.
- Após a reconciliação das amostras: 163 pedidos, 179 registros legítimos, 180 unidades comerciais confirmadas e zero unidades com identidade pendente. Há pendências de cadastro SKU, independentes da quantidade comercial.
- As 87 referências do CSV são carregadas sem vínculo automático de SKU. REF 857 ausente e conflito 875 permanecem sinalizados.
- A reimportação mantém os totais e a primeira importação; atualiza a última identificação e acrescenta histórico.
- Linhas semelhantes permanecem visíveis. Reexportar a mesma multiplicidade não aumenta quantidades pendentes.
- Alteração de quantidade e nova assinatura em pedido já conhecido exigem decisão explícita. Observações reconciliadas continuam acessíveis.
- Marcações manuais sobrevivem à importação e não excluem itens do relatório geral.
- Identificadores textuais longos e zeros iniciais são preservados; identificadores numéricos incertos e quantidade inválida aparecem sinalizados.
- Agrupamentos em 24 permutações e nas demais combinações solicitadas preservam os totais. Filtro temporal distingue meio-dia de 23:59:59.
- Todos os seis menus da aplicação abrem sem erros nos testes. Também foram exercitados marcação manual, revisão de produto/SKU, reconciliação de pendência, filtro do Mercado Livre, troca da ordem de grupos, salvamento/carregamento de favorito e geração de PDF.
- PDFs multipágina A4 com e sem imagens contêm os totais, horários, etiquetas e cabeçalhos esperados. Imagens são incorporadas localmente. Dados pessoais sintéticos de destinatário não aparecem no banco nem no PDF.
- Backup foi aberto em um segundo banco e preservou dados e favorito.
- Os hashes dos nove arquivos originais foram conferidos ao final e continuam iguais aos registrados na primeira análise.

## Verificação visual e inicialização

Foi gerado `output/pdf/relatorio-amostras.pdf` a partir de um banco temporário, com todas as amostras. O arquivo final tem 28 páginas A4. As páginas foram renderizadas por Poppler e inspecionadas em uma visão geral, com inspeção ampliada da primeira página e da versão com fotos sintéticas locais. Cabeçalhos de grupo repetem em continuações e não ficam isolados; tabelas, textos, caixas e totais não apresentaram cortes aparentes.

O servidor Streamlit iniciou em `127.0.0.1:8501`; o endpoint de saúde respondeu `ok` e a página respondeu HTTP 200. O servidor usado para validação foi encerrado, liberando a porta para `iniciar.bat`.

Os testes de pedidos usam bancos temporários. O banco operacional possui o catálogo inicial; pedidos não foram inseridos automaticamente nele. Use Importação para escolher os arquivos da operação.

## Limites da validação

Não houve teste em impressora física nem instalação do zero em uma segunda máquina. A integração e os fluxos da interface foram testados via AppTest; a seleção de arquivos pelo diálogo nativo do navegador não é automatizada por essa ferramenta, e a importação múltipla foi exercitada diretamente no mesmo serviço usado pela tela.

As amostras reais não contêm sobreposição entre exportações diferentes do mesmo pedido. As transições e divergências foram exercitadas com planilhas sintéticas. Ainda é necessário homologar esses cenários com exportações reais sobrepostas antes de ampliar a automação de reconciliação.

O MVP não calcula estoque, não determina necessidade de ação, não expande kits em peças físicas e não fornece edição avançada de composições. Regras de identidade, status e vínculo permanecem conservadoras, com revisão explícita quando faltam evidências.

## Validação após instalação independente do Python

A pedido do usuário, Python 3.12.10 foi instalado pelo winget a partir do instalador oficial python.org, no usuário do Windows. O projeto recebeu um novo `.venv` isolado, sem pacotes do runtime interno do Codex, com todas as dependências instaladas. `pip check` passou e os mesmos 25 testes passaram novamente, em 6,383 segundos. O ambiente anterior foi preservado em `.venv-codex-backup`.

## Renovação da interface e temas

A interface recebeu nova navegação, cartões, cabeçalhos, estado inicial e gráfico de demanda por marketplace, com temas nativos claros/escuros configurados também para a barra lateral. Ambos foram acionados e inspecionados no navegador local. A busca no console por `Invalid color` retornou vazia. As capturas estão em `output/interface/tema-claro.jpg` e `output/interface/tema-escuro.jpg`. Os testes de regressão continuam cobrindo os mesmos fluxos operacionais; nenhuma regra de seleção de pedidos foi alterada pelo redesenho.
