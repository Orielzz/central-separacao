# Central de Separação e Produção

MVP local para AnnaLiv e DonaMora. Python, Streamlit, SQLite, pandas/openpyxl e ReportLab. Interface em português, horário operacional America/Sao_Paulo e PDFs A4. O sistema não usa API de IA e não envia planilhas a serviços externos.

## Regra operacional

Todos os pedidos e itens importados ficam disponíveis por padrão, incluindo pedidos em Retirada, etiquetas impressas, marcações Não necessita ação e registros que precisam de revisão. Somente filtros escolhidos pelo operador restringem consultas e PDFs. Não existe decisão automática sobre o que fabricar ou separar, nem integração de estoque.

As quantidades representam **unidades comerciais**, que podem incluir kits. Quantidades confirmadas, quantidades pendentes e registros sem quantidade válida são separados. A falta de vínculo SKU não apaga unidades comerciais. “Confirmada” na quantidade significa identidade reconciliada, não produto fabricado ou vínculo de catálogo aprovado.

## Instalar e iniciar no Windows

1. Para uma instalação nova, instale Python 3.12, incluindo o Python Launcher (`py`).
2. Execute `instalar.bat`. O download inicial das dependências requer internet; nenhuma planilha é enviada.
3. Execute `iniciar.bat`. A aplicação abre no navegador em `http://127.0.0.1:8501`.
4. Mantenha a janela do terminal aberta durante o uso. Para encerrar, pressione Ctrl+C nessa janela.

O ambiente `.venv` desta máquina já está preparado. O banco é criado automaticamente em `dados/central.sqlite3`. Se o CSV de amostra estiver presente e o catálogo estiver vazio, as 87 referências são carregadas na primeira abertura. As exportações de pedidos **não são importadas automaticamente**: selecione-as na tela Importação.

Se preferir o terminal:

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py --server.address 127.0.0.1 --server.port 8501 --browser.gatherUsageStats false
```

## Importar os arquivos

Abra **Importação**, selecione vários `.xlsx` e clique em **Importar arquivos**. Pode misturar lojas, marketplaces, etapas e datas. Não é necessário informar a etapa do arquivo.

O resumo apresenta as linhas de cada arquivo e o destino de cada linha. Arquivo repetido por hash gera um registro de nova identificação no histórico, mas não cria itens adicionais. Arquivo inválido gera erro visível; os demais arquivos do lote continuam sendo processados. Não trate a soma de quantidades observadas em snapshots repetidos como total operacional.

Os Excel de referência possuem dimensão A1 incorreta. O leitor ignora essa dimensão e percorre as linhas reais. Cabeçalhos são reconhecidos por nomes normalizados e aliases, sem depender de posição. Novos formatos desconhecidos ficam sinalizados; novos aliases exigem ajuste do mapeamento em `central/core.py` nesta versão.

## Consultar, conferir e marcar

A interface dispõe de temas claro e escuro. Use o menu `⋮` no canto superior direito e selecione **Light**, **Dark** ou **System** em **Theme**. A preferência fica no navegador e inclui formulários, tabelas, gráficos e barra lateral. Após atualizar a configuração de tema, encerre a execução anterior e reabra `iniciar.bat` para carregar as novas cores.

- **Dashboard:** quantidades gerais e prioridades por marketplace e prazo completo.
- **Pedidos e itens:** filtros, detalhes de origem, estado bruto, data original do pedido e histórico de importações.
- **Marcação manual:** Pendente, Em produção, Produzido, Separado, Conferido e Não necessita ação. A marcação é aplicada ao pedido inteiro e permanece após reimportação. Não exclui nenhuma linha.
- **Histórico e pendências:** erros de arquivo, destino de cada linha, decisões auditadas e reconciliação manual de itens.

“Dias desde importação” conta desde a primeira importação imutável. “Pendente há X dias” aparece apenas após a marcação manual Pendente. Etiqueta impressa só aparece com data de impressão interpretável; campo vazio significa impressão não informada. Estados brutos são preservados; etapa UpSeller e status nativo do marketplace permanecem desconhecidos quando sua interpretação não foi confirmada.

## Cadastro e vínculo SKU

Em **Produtos e vínculos SKU**, importe o CSV com `REF;PRODUTO;CUSTO_TOTAL`, ou revise/cadastre uma referência. Campos adicionais do CSV são ignorados. Um cadastro revisado não é sobrescrito pelo próximo CSV.

O prefixo numérico do SKU é uma **sugestão**, nunca um vínculo aceito automaticamente. Selecione marketplace, conta e SKU, confira a descrição original e escolha a referência, cor e tamanho. Marque a confirmação de revisão e salve. A ausência de REF 857 e o conflito envolvendo SKU 875-Preto-M aparecem nas pendências enquanto não houver decisão revisada.

Fotografias: informe um caminho de arquivo local no cadastro do produto. Não são baixadas imagens remotas. Foto ausente ou inválida aparece como indisponível no PDF com fotos. Cadastros avançados de variações e composição de kits possuem estrutura inicial no banco, mas ainda não têm fluxo de edição nesta interface.

## Configurar e imprimir

1. Abra **Relatórios**. Sem filtros, a população contém todos os itens, inclusive pendentes, marcados e observações reconciliadas.
2. Escolha filtros explícitos. Para uma lista do Mercado Livre, selecione `Mercado Libre`, conforme o valor da exportação.
3. Selecione os níveis na ordem desejada, por exemplo Marketplace → Prazo → Cor → Referência. Para consolidar unidades entre plataformas, use Referência → Cor → Tamanho e deixe o filtro de marketplace vazio. Cada grupo tem seu subtotal e preserva as linhas de origem.
4. Configure ordenação dos itens e colunas de consulta independentemente dos agrupamentos. O prazo usa data e hora completas. Prazo desconhecido continua visível quando não existe filtro de intervalo.
5. Escolha etiquetas e fotos. Salve um nome para reutilizar a configuração como favorito.
6. Clique em **Gerar PDF A4**, depois em **Baixar PDF para imprimir**. Abra o PDF e imprima em papel A4, escala 100% ou tamanho real.

O PDF sempre inclui marketplace, loja, pedido, prazo, referência, produto, cor, tamanho, quantidade, caixas de conferência, subtotais e total geral. Colunas ocultas da consulta não removem esses campos obrigatórios. Sem vínculo validado, a descrição e variação comerciais permanecem legíveis; a REF candidata é identificada como sugestão. Em prazos conflitantes, todos os prazos observados são apresentados, com o menor usado para atenção.

Pendências de identidade não são somadas às quantidades confirmadas. Uma observação reconhecida manualmente como repetida permanece visível, identificada como reconciliada e com contribuição zero no total. A emissão do PDF não marca pedidos como preparados. Cada emissão registra configuração, snapshot operacional e hash no banco.

## Reconciliação e limitações

Uma assinatura por pedido, subpedido, anúncio, variante, SKU e variação ajuda a reconhecer observações repetidas inequívocas. ID de anúncio e variante não são tratados isoladamente como IDs de item transacional. Linhas semelhantes dentro do mesmo arquivo são preservadas e sinalizadas, sem escolha automática entre duplicidade e multiplicidade legítima. Quantidade alterada ou identidade divergente gera pendência.

Se um pedido já observado chega com uma assinatura de item nova, o acréscimo fica pendente: pode ser produto adicional legítimo ou correção. Repetições da mesma coleção de assinaturas e quantidades preservam a multiplicidade e se tornam novas observações dos registros existentes; não multiplicam quantidades pendentes por simples reexportação.

Na tela de pendências, compare as origens e decida: item distinto, observação do mesmo item ou substituição dos dados/quantidade de um item confirmado. As observações originais e o histórico não são apagados. Quantidade inválida requer correção na fonte e nova importação; a observação inválida anterior continua visível.

Ainda precisam ser refinados: formatos adicionais de exportação e mapeamento pela interface, IDs transacionais confirmados por marketplace, amostras reais sobrepostas em várias etapas, vínculos por anúncio/vigência de SKU reaproveitado, marcações parciais por item, composições de kits, biblioteca avançada de fotos e estoque. Esta versão não expande kits em peças físicas e não calcula necessidade líquida de fabricação.

## Backup e privacidade

Em **Histórico e pendências**, use **Criar backup local do banco**. A cópia consistente é salva em `dados/backups`. Para restaurar, encerre o sistema, preserve o banco atual e coloque o backup escolhido no lugar de `dados/central.sqlite3`. Reabra e confira os totais, vínculos e marcações.

Não use o mesmo SQLite em pasta de rede com várias máquinas ou sincronização simultânea. O MVP é local. Fotos ficam em arquivos separados e também precisam ser copiadas para um backup completo.

O banco retém somente os campos operacionais necessários. Nome, documento, endereço, telefone e ID do comprador não são importados. Os originais não são alterados. `dados`, `amostras`, ambiente e PDFs estão no `.gitignore`; não publique os dados operacionais nem os arquivos de clientes.

## Testes

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Os testes usam bancos temporários e as amostras reais em modo de leitura. A verificação de PDF usa `pypdf` e Pillow, disponíveis no ambiente de validação. Para rodar em instalação nova, instale também `requirements-dev.txt`.

As amostras privadas não fazem parte do repositório. Sem elas, os testes sintéticos continuam executando e os testes que dependem das amostras são identificados como ignorados. Para carregar um catálogo em uma instalação nova sem amostras, use **Produtos e vínculos SKU** e selecione o CSV local.

Controles de referência: 163 pedidos, 179 linhas legítimas, 180 unidades comerciais e 87 referências. Esses números são asserções dos testes das amostras, não valores fixos do aplicativo. A suíte cobre importação múltipla, deduplicação, multiplicidade, histórico, marcações, divergências, agrupamentos, prazos por hora, ausência de omissão, proteção de revisões, privacidade, backup, PDF com/sem fotos e fluxos da interface.
