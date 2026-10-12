# Central de Separação e Produção — análise e plano técnico

Data da análise: 12/10/2026. Escopo: primeira etapa solicitada, sem implementação do sistema.

> Atualização da segunda etapa: este documento registra a análise original. O usuário aprovou o desenvolvimento com regras que prevalecem sobre as propostas abaixo: todos os pedidos e itens são operacionais por padrão; não há estoque integrado, exclusão por status ou decisão automática de fabricação/separação. Marcações são informativas e persistentes. O MVP implementado e suas limitações estão documentados em `README.md`.

Foram examinados integralmente os oito Excel em `amostras/upseller` e o CSV em `amostras/catalogo`. A leitura ocorreu localmente. Os arquivos originais não foram alterados. Seus hashes SHA-256 foram registrados e conferidos ao fim da análise. Não houve envio de planilhas ou dados de clientes a serviços externos ou repositórios remotos.

## 1. Estrutura encontrada

Cada Excel tem uma aba chamada `sheet`, cabeçalho na primeira linha e 81 colunas, de A a CC. Os oito arquivos têm a mesma sequência de cabeçalhos nesta amostra, mas isso não será tratado como garantia para futuras exportações.

| Arquivo | Conteúdo observado | Linhas de produtos | Pedidos distintos no arquivo | Soma de Qtd. do Produto |
| --- | --- | ---: | ---: | ---: |
| Export_Order20261012154117.xlsx | Mercado Libre / Annaliv / Pendente Revisão | 36 | 34 | 36 |
| Export_Order20261012154117 - Copia.xlsx | Cópia binária idêntica do arquivo anterior | 36 | 34 | 36 |
| Export_Order20261012154137.xlsx | Mercado Libre / ML - Donamora / Pendente Revisão | 39 | 33 | 39 |
| Export_Order20261012154137 - Copia.xlsx | Cópia binária idêntica do arquivo anterior | 39 | 33 | 39 |
| Export_Order20261012155154.xlsx | TikTok Shop e Shopee / contas AnnaLiv / Retirada | 24 | 23 | 24 |
| Export_Order20261012155209.xlsx | Shopee / Shopee- Annaliv / Em Processo | 1 | 1 | 1 |
| Export_Order20261012155254.xlsx | Shopee / SHP - Donamora / Em Processo | 1 | 1 | 1 |
| Export_Order20261012155305.xlsx | Shopee, Shein, Kwai e Mercado Libre / contas DonaMora / Retirada | 78 | 71 | 79 |

Os oito arquivos somam 254 linhas. Excluindo apenas as duas cópias comprovadas por hash, restam seis arquivos, 179 linhas, 163 pedidos e 180 unidades comerciais. Não foram encontradas linhas integralmente iguais dentro de cada arquivo, nem sobreposição de pedidos entre os seis conteúdos distintos, usando plataforma + conta + número do pedido da plataforma.

Há 14 pedidos com várias linhas legítimas, com até três linhas por pedido. Deduplicar apenas pelo pedido excluiria 16 linhas válidas nesta amostra. No último arquivo, a linha 49 contém `809-Vinho-G` com quantidade 2: contar linhas como quantidade perderia uma unidade.

| Plataforma e conta, como exportadas | Pedidos | Linhas | Unidades comerciais |
| --- | ---: | ---: | ---: |
| Mercado Libre / Annaliv | 34 | 36 | 36 |
| Mercado Libre / ML - Donamora | 34 | 41 | 41 |
| TikTok Shop / Tik Tok - AnnaLiv | 5 | 5 | 5 |
| Shopee / Shopee- Annaliv | 19 | 20 | 20 |
| Shopee / SHP - Donamora | 63 | 69 | 69 |
| Shein / SHN - Donamora | 5 | 5 | 5 |
| Kwai / KWA - Donamora | 3 | 3 | 4 |
| Total | 163 | 179 | 180 |

Problema confirmado no XML: todos os Excel declaram `dimension ref="A1"`, apesar de conterem registros até CC. A leitura inicial por dimensão retornaria somente um cabeçalho. A leitura foi refeita ignorando a dimensão declarada, e linhas e quantidades foram conferidas diretamente no XML. O importador deverá detectar e contornar essa condição sem regravar o original. Também existe aviso de ausência de estilo padrão, sem impedimento à leitura dos valores.

Há duas colunas chamadas `Lucro Estimado`, em Y e Z. O cabeçalho não pode ser convertido diretamente em um dicionário que sobrescreva colunas homônimas. Esses campos financeiros não são necessários para a operação inicial.

O catálogo é CSV UTF-8 com BOM, delimitado por ponto e vírgula. Contém exatamente `REF`, `PRODUTO` e `CUSTO_TOTAL`: 87 referências distintas, sem duplicatas nem campos vazios. Os custos informados variam de 6,15 a 48,80, com ponto decimal no arquivo. A moeda e a data de vigência do custo não estão explicitadas; não devem ser inventadas. Categoria, variações, fotos e vínculos comerciais não estão disponíveis no catálogo.

## 2. Mapeamento de colunas

As letras abaixo localizam as colunas atuais. O importador usará nomes e perfis versionados; não dependerá dessas posições.

| Campo do sistema | Coluna atual | Interpretação e tratamento |
| --- | --- | --- |
| Marketplace | D — Plataformas | Presente em todas as 179 linhas. Preservar valor bruto e manter alias configurável, por exemplo Mercado Libre para Mercado Livre. |
| Conta vendedora | E — Nome da Loja no UpSeller | Presente em todas. Existem sete contas. Vincular conta à marca AnnaLiv/DonaMora por cadastro revisado. |
| Pedido da plataforma | A — Nº de Pedido da Plataforma | Presente em todas, armazenado como texto. Identificador externo principal, dentro da conta e marketplace. |
| Subpedido | B — Nº do Subpedido | Preenchido nas 77 linhas do Mercado Libre; vazio nas outras 102. Há 77 valores distintos preenchidos. É candidato a identificar subpedidos, não prova de ID universal de item. |
| Pedido UpSeller | C — Nº de Pedido | Presente em todas. 163 valores distintos; relação um para um com os pedidos externos observados nesta amostra. Manter como identificador alternativo. |
| Item da transação | Não há coluna explicitamente identificada | Nenhum ID de linha de pedido foi comprovado. Não confundir anúncio ou variante com item transacional. |
| Nome comercial | AH — Nome do Anúncio | Preenchido em todas. Descrição de origem; não sobrescreve o nome interno revisado. |
| Anúncio | AI — ID do Anúncio | Preenchido em todas. Identifica anúncio, que pode aparecer em muitos pedidos. |
| SKU comercial | AJ — SKU | Preenchido em todas; 128 SKUs distintos. Preservar pontuação, caixa e valor original. |
| Variação bruta | AK — Variação | Preenchida em todas, mas conteúdo e ordem variam. Cor e tamanho precisam de parsing e validação. |
| Variante comercial | AL — ID da Variante | Preenchido em 103 linhas, com 83 valores distintos. Identifica variante, não linha de pedido. |
| Foto de origem | AM — Link da Imagem | Preenchido em todas. URL não comprova foto correta nem disponibilidade offline. Não baixar durante esta análise. |
| Quantidade comercial | AO — Qtd. do Produto | Números 1 ou 2 nesta amostra; fonte para unidades vendidas. Não equivale necessariamente a peças físicas. |
| Cadastro de armazém | AT — SKU (Armazém); AU — quantidade mapeada; AV — Quantidade de Produtos; AW — Nome do Produto | Todos vazios nesta amostra. Não usar como referência, quantidade ou nome de reserva automaticamente. |
| Referência mestre | Ausente como coluna própria | Candidato extraído do SKU e confrontado com REF; só se torna vínculo operacional após validação. |
| Prazo de envio | M — Prazo de Envio | Preenchido em todas, como texto com data e hora. Preservar hora. |
| Estado exportado | F — Estado do Pedido | Pendente Revisão, Em Processo e Retirada. Sem evidência suficiente para separar o status nativo do marketplace da etapa do UpSeller somente por esse campo. |
| Status de terceiro | G — 3PL Status | Vazio em todas. Guardar separado quando disponível. |
| Impressão de etiqueta | K — Impressão da Etiqueta | Datas e horas em 102 linhas; vazio em 77. Impressão não comprova fabricação, conferência ou envio. |
| Envio | L — Enviado; P — Hora de Envio | Vazios em todas. Ausência não prova que o pedido não saiu. |
| Outros horários | J — Horário Programado; N — Horário de Saída; O — Horário da Retirada | Preservar como campos independentes. Horário da Retirada tem valores passados e futuros; não comprova retirada efetiva. |
| Pós-venda/cancelamento | AD — Pós-venda/Cancelado/Devolvido; AE/AF — cancelamento | Vazios nesta amostra; suportar futuramente sem inferir que campo vazio significa ausência de cancelamento. |
| Dados mestre confiáveis | CSV: REF, PRODUTO, CUSTO_TOTAL | Únicos campos autorizados para importação inicial do catálogo. |

Datas da exportação não têm indicação de fuso. A aplicação poderá usar America/Sao_Paulo como configuração operacional explicitamente confirmada, preservando a data e hora brutas e registrando a interpretação. Os prazos vão de 13 a 16/10/2026. Dois itens vencem em 13/10 às 12:00, enquanto muitos outros vencem às 23:59:59. Agrupar por dia não pode eliminar a hora usada na prioridade.

Campos de destinatário, documento, telefone, endereço, ID do comprador e etiquetas não são necessários aos relatórios solicitados. Não serão copiados para o modelo operacional nem incluídos em logs ou PDFs. A rastreabilidade usará arquivo, aba e linha. Os originais locais continuarão sendo a fonte caso seja necessária uma inspeção autorizada.

## 3. Identificação e deduplicação seguras

**Separar arquivo, observação, pedido, subpedido e item.** Uma linha lida é uma observação de origem; só passa a representar um item consolidado quando sua identidade for resolvida.

1. Arquivo: calcular SHA-256 antes de importar. Um conteúdo já importado não entra novamente nos totais, mesmo com outro nome. Registrar a tentativa para auditoria. Conteúdos diferentes nunca são descartados apenas por semelhança do nome.
2. Pedido: usar ID interno do banco e chave externa `(marketplace_id, conta_id, pedido_plataforma_texto)`. Relacionar o número UpSeller como identidade alternativa. Se faltar plataforma, conta ou número, deixar pendente de resolução; não criar uma conta genérica compartilhada para fundir registros.
3. Subpedido: guardar B como entidade/identidade adicional. Os valores únicos observados no Mercado Livre são evidência útil, mas sua estabilidade entre etapas e sua relação com itens ainda precisam de amostras sobrepostas.
4. Item com ID transacional comprovado: usar pedido + ID de item, incluindo subpedido/remessa quando a semântica exigir. Não usar ID do anúncio ou da variante isoladamente.
5. Item sem esse ID: gerar assinatura candidata com pedido, subpedido disponível, anúncio, variante disponível, SKU e variação bruta. Quantidade, prazo, etapa e impressão são atributos de observação, não identidade. Uma alteração de quantidade não pode criar automaticamente um segundo item.
6. Reconciliar coleções de itens por pedido, preservando multiplicidade. Duas linhas com mesmo SKU podem ser dois itens válidos. Sem identidade suficiente, nem mesmo linhas inteiramente iguais dentro de um arquivo serão apagadas automaticamente. Comparar ocorrências entre exportações requer avaliar se o arquivo é completo, parcial ou tem expansão de componentes/armazém.
7. Reexportação em outra etapa: anexar nova observação ao mesmo item quando a correspondência for inequívoca, sem somar as quantidades dos snapshots. Não substituir o conjunto inteiro de itens quando a exportação puder ser parcial. Itens ausentes de um novo arquivo não são excluídos automaticamente.
8. Ambiguidade: criar pendência com linhas de origem, motivo e diferenças. Manter os registros, impedir que a parcela incerta seja somada como se fosse um total confirmado e apresentar quantidade confirmada e pendente separadamente. A revisão poderá decidir que são observações do mesmo item, itens distintos ou correções.

Preservar histórico de quantidade, prazo e estados. O horário da importação não é o horário de atualização do pedido. Os metadados dos Excel contêm data de criação, mas não comprovam a última atualização de cada registro. Uma exportação antiga importada depois não deve regredir automaticamente um estado. Aplicar precedência documentada por fonte e data confiável; conflitos sem evidência temporal suficiente exigem revisão. Para alertas, pode-se mostrar o menor prazo conflitante de forma conservadora, identificado como conflito, sem substituir silenciosamente o prazo confirmado.

As amostras validam cópias binárias e pedidos com vários itens. **Elas não validam estabilidade de identidade, alteração de quantidade nem transição do mesmo pedido entre exportações diferentes**, pois não há sobreposição entre os seis arquivos distintos. Os 163 pedidos são um controle observado da amostra, não uma garantia sobre todas as exportações futuras.

## 4. Vinculação SKU–referência, cor e tamanho

Regra candidata observada: sequência numérica inicial seguida de ponto ou hífen. Exemplos: `111.TERRACOTA.GG` e `116-Azul-marinho-G-Lisa`. Essa regra encontra uma REF existente para 126 dos 128 SKUs distintos, correspondentes a 176 das 179 linhas, cobrindo 32 referências do catálogo. Isso mede cobertura de candidatos, não vínculos validados.

Os SKUs `857.PRETO.GG` e `857.MARROM.GG` aparecem em três linhas e não têm REF 857 no catálogo. A referência deve ficar pendente; não criar custo ou cadastro confiável a partir do anúncio.

Conflito concreto: no arquivo `Export_Order20261012155154.xlsx`, aba `sheet`, linha 17, o SKU `875-Preto-M` está ligado a anúncio de camisola com renda e estampa. A REF 875 do catálogo é `Blusa(Manga Curta) de Tule + Cropped`. Portanto, nem um prefixo existente autoriza vínculo automático. Essa linha precisa de revisão para determinar se o SKU foi reaproveitado, digitado incorretamente ou se o anúncio está errado. Não corrigir por semelhança de texto.

Proposta de resolução:

- Buscar primeiro vínculo explícito já revisado, no escopo de marketplace + conta + SKU e, quando necessário, anúncio/variante. Guardar vigência e alertar se um SKU revisado aparecer com descrição incompatível.
- Sem vínculo, apresentar sugestão pelo prefixo e descrição lado a lado. Nomes comerciais são evidência secundária; não alteram o mestre.
- Registrar aprovação/rejeição, autor ou operador, data, origem e justificativa. Reimportação não sobrescreve produto, categoria, custo, cor ou tamanho revisados. Mudanças vindas do catálogo tornam-se propostas quando afetarem campos protegidos.
- Manter cor e tamanho originais e normalizados separados. Dicionários de aliases devem ser revisados: MARINHO/Azul-marinho pode ser candidato, mas Azul, Azul-bic e Azul-escuro não devem ser fundidos por suposição.
- Ler SKUs e variações com regras por família/perfil. `GG,Verde` tem ordem invertida; `867-G-Azul Marinho` usa tamanho antes da cor; hífens podem pertencer à cor ou à medida. Há variações incompletas, SKUs terminados em ponto e tamanho `10ANOS`. Não aplicar um único split posicional.
- Guardar tamanho comercial e faixa declarada, como `GG - 46` e `GG - 42/44`, sem presumir equivalência entre modelagens. Preservar atributos extras como Listras, Lisa e Tule. Dados ausentes aparecem como “Não informado” ou pendência, jamais como uma cor/tamanho inventado.
- Categoria/tipo de peça será cadastro manual, com sugestões opcionais explicitamente não validadas. Kits e conjuntos precisam de composição revisada antes de converter unidades comerciais em peças a fabricar.

Fotos: inicialmente permitir arquivos locais associados ao produto/variação. URLs importadas são sugestões de origem; eventual obtenção de fotos será uma etapa separada, sem envio de pedidos a terceiros. O PDF deve funcionar com as fotos locais ou com um espaço indicando ausência.

## 5. Banco de dados proposto

SQLite local, com chaves estrangeiras, migrações, transações e índices nas identidades e filtros. Identificadores externos serão texto para preservar zeros e números longos. Custos serão decimais convertidos a unidades inteiras de armazenamento com escala explícita; nenhuma aritmética monetária com float. Quantidades comerciais terão validação de unidade e domínio, sem arredondamento silencioso.

| Tabela ou conjunto | Responsabilidade e integridade |
| --- | --- |
| marketplaces, marcas, contas_vendedoras, aliases | Separar marca, conta e plataforma. Nome exportado é alias revisado, não chave permanente. |
| lotes_importacao, arquivos_importados, tentativas_importacao | Histórico de importação, hash único por conteúdo, origem, horário de criação observado, perfil usado e resultado. |
| perfis_importacao, mapeamentos_colunas | Versão de esquema, aliases de cabeçalhos, formatos de data/quantidade e decisões aprovadas pelo usuário. |
| observacoes_origem | Arquivo + aba + linha, campos operacionais brutos, tipo original e avisos. Não armazenar payload completo com dados pessoais. |
| pedidos, identidades_pedido, subpedidos | Pedido interno, chave externa por conta/plataforma e identificadores alternativos. |
| itens_pedido, identidades_item, observacoes_item | Item canônico e suas observações. Identidades comprovadas têm restrição única no escopo certo; assinatura candidata não terá unicidade que apague itens legítimos. |
| observacoes_estado, regras_estado | Estado bruto, marketplace, etapa ERP e etiqueta separados; cada regra guarda origem, versão e grau de confirmação semântico. |
| produtos, categorias, variacoes, atributos_variacao | Mestre compartilhado por REF, nome/custo confiáveis e categoria/variações revisadas. Campos guardam origem e proteção contra atualização automática. |
| vinculos_sku, historico_vinculos | Referência/variação, conta, SKU, anúncio/variante quando necessário, situação de revisão e vigência. Impedir vínculos ativos incompatíveis no mesmo escopo. |
| composicoes_produto | Kit ou conjunto e componentes, quantidades e variações revisadas. Evitar ciclos e impedir expansão sem composição validada. |
| fotos | Caminho relativo local, produto/variação, origem e validação. |
| pendencias, decisoes_revisao, auditoria | Conflitos de identidade, prazo, SKU, quantidade e cadastro; ações reversíveis e rastreáveis. |
| movimentacoes_operacionais, alocacoes, lotes_producao | Confirmações locais de separado, produzido, conferido e alocação de estoque, inclusive parcial, vinculadas ao item. Reimportação não apaga esse trabalho. |
| favoritos_relatorio | Configuração JSON versionada de filtros, agrupamentos ordenados, ordenação, colunas e modo de PDF. |
| emissoes_relatorio | Configuração, corte de dados, regras e vínculos usados, IDs/quantidades e caminho do PDF para reproduzir o documento. |

Separar estado importado de estado operacional confirmado. Nas amostras há 75 linhas em Pendente Revisão, 2 em Em Processo e 102 em Retirada. Todas as 102 em Retirada têm data de impressão, mas nenhuma linha tem Enviado ou Hora de Envio preenchidos. Isso não permite afirmar que Retirada significa pedido fisicamente preparado. Não chamar Estado do Pedido de status nativo do marketplace sem confirmação.

Ter telas/listas separadas para demanda comercial importada, demanda elegível para separação, preparação confirmada e necessidade de fabricação. Sem estoque/alocação e composição validada, só é possível apresentar demanda em unidades comerciais ou uma previsão de produção explicitamente condicionada. A necessidade física deve descontar alocações e trabalho já confirmado, evitando consumir a mesma disponibilidade em vários pedidos.

## 6. Arquitetura de filtros, agrupamentos e relatórios

Tecnologia proposta conforme a preferência inicial: Python, Streamlit, SQLite, pandas/openpyxl para leitura e tratamento, ReportLab para PDF. A lógica de negócio ficará independente do Streamlit, para poder testar importação, reconciliação e totais sem abrir a interface. Não é necessário serviço de IA ou API externa.

Camadas: leitura de arquivos e detecção de esquema; normalização e validação; reconciliação de identidades; catálogo e operação; consultas de relatório; interface e geração PDF. O parser poderá usar openpyxl com dimensão corrigida em memória, seguido de pandas sobre registros já extraídos. Não confiar em um caminho padrão de leitura que trunque as amostras.

Um registro de dimensões autorizadas definirá marketplace, marca/loja, conta, prazo/data, referência, tipo, cor e tamanho, com identificador estável, rótulo, tipo e tratamento de ausência. Consultas SQL serão parametrizadas; nomes de dimensões/colunas virão dessa lista permitida.

O fluxo será:

1. Selecionar finalidade e população: demanda, separação ou fabricação. Expor pendências e regras de elegibilidade utilizadas.
2. Aplicar filtros independentes por plataforma, loja/conta, intervalo de prazo, REF, tipo, cor e tamanho. Campo ausente terá opção própria de filtro. Intervalos por dia incluem a hora final corretamente.
3. Selecionar níveis de agrupamento em uma lista ordenada, sem repetir dimensão. A mudança de ordem altera a árvore do relatório, não a população filtrada nem o total.
4. Agregar quantidades no nível desejado. Mesmo agrupando só por prazo e cor, manter detalhe de REF, nome, tamanho e quantidade; não escolher arbitrariamente o primeiro valor de um grupo.
5. Configurar ordenação dos grupos e dos itens separadamente. Usar prazo real para urgência, preservando horário e evidência da origem. Prazo ausente terá lista própria de atenção.
6. Configurar colunas de tela separadamente. O PDF operacional sempre incluirá os campos mínimos solicitados e caixas de conferência.
7. Salvar favorito como configuração versionada. Favoritos aplicam-se aos dados atuais; a emissão de PDF registra um snapshot para reprodução histórica.

Separação por marketplace deve manter pedidos e seus itens identificáveis dentro dos agrupamentos; somar peças por cor não substitui a conferência de cada pedido. A produção pode consolidar componentes/referências entre marketplaces e continuar ligada a todos os itens de origem, suas quantidades e prazos. Não transformar um grupo com vários prazos em uma única data sem mostrar a composição.

PDF A4 com e sem fotos: cabeçalho com filtros, agrupamentos e data do corte; referência, nome, cor, tamanho, quantidade, prazo e marketplace; caixa de conferência por linha; subtotais que não sejam contados novamente no total geral; paginação, cabeçalhos repetidos e grupos legíveis. Quantidade de pedidos distinta não é aditiva entre grupos: um mesmo pedido com cores diferentes pode participar de mais de um grupo.

A emissão de uma lista não significa que a peça foi fabricada ou separada. Confirmações físicas serão ações explícitas, com suporte a conclusão parcial.

## 7. Riscos e limitações

- Dimensão A1 incorreta pode produzir importação vazia sem erro aparente. Deve haver reconciliação obrigatória de linhas lidas.
- Sem ID transacional de item comprovado, certas reexportações terão ambiguidades que nenhum algoritmo pode resolver com certeza usando apenas estas colunas.
- Ausência de sobreposição entre arquivos distintos limita a validação de atualizações e transições. Obter exemplos locais do mesmo pedido em mais de uma etapa será necessário para homologar essa parte.
- Conta renomeada e SKU reaproveitado podem mudar a identidade aparente. Usar aliases e vínculos com histórico, sem normalizações destrutivas.
- Prefixo de SKU é apenas sugestão. A REF 857 ausente e o conflito da REF 875 são pendências reais.
- Cor/tamanho nem sempre estão completos; delimitação varia e tamanhos comerciais iguais podem representar medidas diferentes.
- Etiqueta impressa, data de retirada e estado Retirada não comprovam fabricação, separação ou expedição. Regras de negócio precisam de confirmação semântica.
- Unidades comerciais incluem kits/conjuntos. Não há composição validada nem posição de estoque nas amostras. O total 180 não deve ser anunciado como 180 peças a fabricar.
- Exportações são snapshots que podem ficar desatualizados. Mostrar corte, origem e pendências; importar pedido novo não substitui uma consulta atual ao ERP.
- Fotos remotas podem mudar ou faltar. Priorizar biblioteca local validada para impressão offline.
- Aplicação inicial será para uso local em uma máquina. Não colocar o banco SQLite em pasta de rede ou sincronização concorrente; expansão para várias máquinas exige nova decisão de arquitetura.
- Banco e backups precisam permanecer locais e recuperar vínculos, revisões e confirmações. Os originais já contêm dados pessoais; excluir esses campos do sistema e dos PDFs reduz sua propagação.

## 8. Plano de implementação por fases

| Fase | Entrega | Critério para concluir |
| --- | --- | --- |
| 1 — Importação auditável | Estrutura do projeto, SQLite, perfis, seleção de múltiplos arquivos, validação e resumo por origem | Ler as oito amostras inteiras; distinguir cópias e reproduzir 163 pedidos, 179 linhas e 180 unidades comerciais sem apresentar isso como produção. |
| 2 — Identidade e revisão | Observações, pedidos/itens, reconciliação, histórico e tela de ambiguidades | Reimportar não altera totais; itens legítimos permanecem; cenários de sobreposição, alteração e arquivo parcial passam em testes e exemplos reais quando disponíveis. |
| 3 — Catálogo mestre | Importar apenas REF/PRODUTO/CUSTO_TOTAL, revisar SKU/cor/tamanho/tipo, fotos locais e proteção de campos | 87 referências importadas; 857 e conflito 875 expostos; nenhuma sugestão aceita silenciosamente e nenhuma revisão sobrescrita. |
| 4 — Operação e produção | Regras de elegibilidade confirmadas, separação parcial, composição de kits e alocação quando aplicável | Diferenciar demanda, preparado e necessidade física; evitar repetir trabalho confirmado ou descontar o mesmo estoque duas vezes. |
| 5 — Consultas dinâmicas | Filtros, níveis ordenados, ordenação, colunas e favoritos | As combinações solicitadas funcionam e mantêm os mesmos totais para a mesma população. Origem e prazos permanecem consultáveis. |
| 6 — Impressão | PDF A4 com/sem fotos e rastreabilidade da emissão | Todos os campos e subtotais corretos, nenhuma informação pessoal e revisão visual de documentos curtos e longos. |
| 7 — Homologação Windows | Inicialização local simples, versões fixadas, backup/restauração, documentação e piloto | Instalação e operação verificadas no Windows, funcionamento sem APIs externas e restauração testada preservando revisões e operação. |

Antes de liberar regras automáticas de preparação e reconciliação, confirmar o significado das etapas e reunir amostras locais sobrepostas do mesmo pedido. A falta delas não impede construir importação auditável e revisão, mas impede afirmar que todo o ciclo foi homologado.

## 9. Testes necessários

**Controles reais já verificados nesta análise:** leitura integral após ignorar a dimensão incorreta; contagens e soma de quantidades confrontadas com XML; hashes das duas cópias; 163 pedidos, 179 linhas e 180 unidades após deduplicação binária; 14 pedidos com múltiplas linhas; catálogo com 87 REF únicas; ausência de sobreposição entre conteúdos distintos; integridade dos hashes dos originais ao fim da análise. Os demais testes abaixo são propostos para o sistema futuro, não foram executados como se o sistema já existisse.

| Área | Cenários e resultado esperado |
| --- | --- |
| Leitura | A1 incorreto, dimensões corretas, aba vazia, cabeçalho deslocado, múltiplas abas, colunas reordenadas/renomeadas/duplicadas/ausentes, fórmulas sem cache e arquivo inválido. Nenhuma perda silenciosa; perfil novo requer validação. |
| Reimportação | Mesmo arquivo duas vezes, cópia renomeada, arquivo reexportado com metadados diferentes e carga interrompida. Totais estáveis, histórico registrado e transação consistente. |
| Pedido | Mesmo número externo em lojas/marketplaces diferentes, alias de conta, ID UpSeller conflitante e campo de identidade vazio. Não fundir pedidos sem confirmação. |
| Item | Pedido com três itens, dois itens de mesmo SKU, duas linhas idênticas sem ID, subpedido com vários itens, ID de variante reutilizado, quantidade alterada e exportação parcial. Preservar multiplicidade; conflito fica visível; snapshot não vira quantidade adicional. |
| Atualização | Mesmo pedido em etapas diferentes, carga em ordem inversa, campos vazios após preenchidos, prazo alterado e cancelamento. Sem regressão silenciosa ou exclusão pela ausência em arquivo parcial. |
| Números e datas | Quantidade 2 da amostra, zero, negativo, decimal incompatível, separador local, zeros iniciais e IDs com mais de 15 dígitos. Validar sem arredondar ou converter identificadores em números. Testar prazo ao meio-dia, limites de dia e data inválida/ausente. |
| Catálogo | Importar somente três campos autorizados, REF duplicada, custo inválido/zero/ausente, importação repetida e atualização após revisão manual. Campos revisados permanecem protegidos; custo ausente não vira zero. |
| Vínculos | 857 sem catálogo, 875 incompatível, SKU com prefixo existente mas produto errado, SKU reaproveitado, delimitadores variados, cor composta e tamanho infantil. Sugestões exigem revisão; aliases só se aplicam no escopo aprovado. |
| Operação | Etiqueta impressa sem separação, Retirada sem envio comprovado, confirmação parcial, reimportação após conferência e estoque compartilhado entre pedidos. Trabalho físico não é criado por inferência nem apagado pela carga. |
| Kits | Unidade vendida com dois ou mais componentes, composição ausente, componente sem variação e custo específico ausente. Produção expande apenas composição validada; lacunas aparecem como pendência. |
| Agrupamento | Todas as ordens exemplificadas no pedido, sem agrupamento, filtros combinados, ausências e alteração de colunas. Total filtrado permanece invariável sob reordenação dos níveis; subtotais não duplicam quantidades. |
| PDF | Com/sem fotos, foto ausente, nome longo, quebra de página, várias origens/prazos e favoritos. Conferir conteúdo e renderizar para inspeção visual; nenhuma informação pessoal. |
| Recuperação | Backup/restauração, falha durante gravação e reabertura. Preservar itens, decisões, favoritos, vínculos e confirmações sem cargas parciais. |

Na homologação, conferir manualmente uma seleção estratificada por marketplace e etapa, incluindo todos os pedidos com múltiplas linhas, a quantidade 2, a REF 857, o conflito 875 e os kits. Para as partes críticas, comparar conjuntos de identidades e quantidades por origem, não apenas um total geral que pode esconder erros compensados.

Conclusão da etapa: a tecnologia preferida é compatível com o escopo local proposto. O desenvolvimento deverá priorizar importação auditável, identidade e revisão antes de automatizar listas de fabricação. A implementação aguarda a próxima instrução do usuário.
