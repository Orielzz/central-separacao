# Plano de português brasileiro e uso simplificado

## Objetivo

Permitir que uma pessoa com pouca experiência em computadores consiga abrir o sistema, carregar pedidos, escolher uma lista e imprimir sem conhecer termos técnicos ou configurar agrupamentos.

Este documento é uma proposta. A interface existente ainda não foi alterada nesta etapa.

## O que precisa mudar

Hoje há controles em inglês pertencentes ao Streamlit: Theme, Light, Dark, seleção de arquivos, busca, download de tabelas e opções de menu. Algumas telas também exibem nomes internos de campos e estados do banco. Além disso, a tela de relatórios apresenta muitas escolhas simultaneamente, as fotos exigem digitar um caminho e a revisão de itens usa IDs numéricos.

Para garantir português brasileiro em todos os controles da aplicação, proponho uma interface web própria, mantendo os serviços Python de importação, reconciliação, catálogo, histórico e PDF e o banco SQLite. A interface será servida localmente no mesmo computador, sem publicação externa. O Streamlit pode continuar temporariamente disponível durante a transição. Não depender de alterações nos arquivos internos da biblioteca ou de substituições frágeis de texto no navegador.

Os menus do navegador, a janela de seleção de arquivos do Windows e o diálogo da impressora seguem o idioma do computador. A aplicação pode traduzir seus próprios controles e oferecer instruções em português; não deve alterar o idioma do Windows sem solicitação específica.

## Navegação proposta

Quatro destinos principais:

1. **Início:** resumo da operação e botões Carregar pedidos, Consultar pedidos e Preparar impressão.
2. **Pedidos:** busca por número do pedido, referência ou código do produto; filtros básicos de loja, canal de venda e prazo; detalhes e marcações manuais.
3. **Imprimir listas:** modelos prontos e um caminho curto até a impressão.
4. **Precisa de revisão:** quantidades com possíveis duplicidades, dados ausentes e produtos sem vínculo validado, com explicações distintas.

Produtos, histórico de importações, configurações e cópia de segurança ficarão em **Mais opções**. Isso organiza a navegação sem exigir contas, permissões ou senhas na primeira entrega.

Todos os pedidos permanecem na população geral. Revisar uma pendência, marcar um pedido ou trocar de modelo não pode ocultar registros automaticamente.

## Caminho para carregar pedidos

1. Clicar em **Carregar pedidos**.
2. Clicar em **Escolher arquivos**, permitindo selecionar vários Excel, ou arrastar os arquivos para a área indicada.
3. Conferir os nomes e clicar em **Carregar**.
4. Ver um resultado em linguagem comum e o próximo botão: **Ver pedidos** ou **Preparar impressão**.

Exemplos de mensagens:

- “Pedidos carregados. Você já pode consultar e imprimir as listas.”
- “Este arquivo já foi carregado. Os pedidos não foram contados novamente.”
- “Encontramos informações que precisam de conferência. Os registros continuam disponíveis.”
- “Não conseguimos abrir este arquivo. Os outros arquivos foram processados.”

Separar pedidos novos, pedidos já conhecidos, novos itens e observações repetidas no resumo. Não chamar o total de linhas de total de pedidos. Mostrar contagem incerta em separado. Detalhes por linha, arquivo e decisão continuam acessíveis em **Ver detalhes da importação**.

## Caminho para imprimir

1. Escolher um modelo:
   - **Separação por canal de venda**: pedidos e itens preservados por canal e prazo.
   - **Lista por produto**: referências, cores e tamanhos agrupados entre canais, com suas origens disponíveis.
   - **Conferência por pedido**: todos os produtos de cada pedido juntos.
2. Escolher lojas/canais e prazo. O padrão é **Todos**, sem restrição de data ou marcação.
3. Conferir uma prévia com quantidade contabilizada, quantidade a revisar e filtros ativos.
4. Clicar em **Abrir lista para imprimir**. Oferecer também **Salvar PDF**.

Usar **Lista por produto** como nome simples de um modelo de demanda. O documento não decide necessidade de fabricação e não converte kits em peças físicas sem composição validada.

Opções menos frequentes ficam em **Personalizar lista**: ordem dos grupos, ordenação dos itens, colunas, fotos e etiquetas. O motor genérico existente continuará sendo utilizado; não criar um relatório independente para cada modelo.

Permitir **Salvar como minha lista** e reaplicar um modelo favorito. Exibir filtros em etiquetas legíveis, por exemplo “Canal: Mercado Livre” ou “Prazo: até 13/10 às 12h”, e um botão **Mostrar todos os pedidos** que limpa as restrições.

## Linguagem e formato

| Atual | Proposto |
| --- | --- |
| Dashboard | Início |
| Marketplace | Canal de venda |
| Reconciliação | Conferência de possíveis duplicidades |
| Estado bruto | Situação informada pelo UpSeller |
| REF | Referência |
| SKU | Código do produto (SKU), com explicação curta quando necessário |
| Unidades confirmadas | Quantidade contabilizada |
| Unidades pendentes | Quantidade a revisar |
| Snapshot, IDs e nomes de campos internos | Tradução em linguagem comum; detalhes técnicos em área específica |

Formatar datas como 13/10/2026 e horários como 12:00. Nas prioridades, usar descrições como “Prazo hoje, às 12:00”, calculadas pelo prazo completo. Um pedido com prazo vencido não deve ser rotulado automaticamente como ainda pendente de envio: a data vencida é conhecida, mas a situação física pode ser desconhecida.

Custos seguem a formatação numérica brasileira, com vírgula decimal. Só apresentar símbolo de moeda quando ela estiver definida no cadastro/configuração; não inventar a moeda de um custo importado.

Mostrar “Mercado Livre” como nome de apresentação, preservando “Mercado Libre” nos dados originais e mantendo os filtros ligados ao valor correto. Preservar nomes de produtos e valores de origem, incluindo status que precisem ser apresentados exatamente como vieram do UpSeller.

## Revisão e cadastro mais fáceis

- Revisar uma pendência por vez, mostrando nome, código, cor/tamanho de origem, quantidade e motivo. Botões **Ver pedido** e **Ver origem** substituem a escolha por ID isolado.
- Para possíveis duplicidades, mostrar os dois registros lado a lado e opções claras: **São itens diferentes**, **É o mesmo item** ou **Usar a informação corrigida**. Explicar o efeito nas quantidades antes da confirmação.
- Para produtos sem vínculo, apresentar a referência candidata como sugestão e nunca aceitá-la sem revisão. Manter explícitos REF 857 ausente e conflito 875.
- Trocar o campo de caminho de foto por **Escolher foto**, prévia da imagem e **Salvar**. Manter os arquivos locais.
- Mostrar mensagens de erro com orientação prática; detalhes técnicos continuam disponíveis para diagnóstico.
- Preservar o histórico das decisões e permitir correção auditada de enganos. A função de desfazer deve ser definida por tipo de ação para não apagar trabalho posterior.

## Aparência e acessibilidade

- Botão direto **Tema claro / Tema escuro**, em português, com preferência salva no navegador.
- Texto legível, contraste suficiente e botões grandes com rótulos escritos. Ícones complementam os textos.
- Uma ação principal por etapa, com indicador Carregar → Conferir → Imprimir.
- Não transmitir informação somente por cor. Avisos devem ter texto e ícone.
- Navegação por teclado, foco visível, boa apresentação com zoom de 125%/150% e sem cortes nas telas menores.
- Cópia de segurança com botão **Fazer cópia de segurança**, resultado com data/hora e acesso claro ao local salvo.
- Atalho para abrir o sistema. Se já estiver em execução, abrir a página existente em vez de apresentar erro de porta ocupada. Avaliar o lançador separadamente, preservando as mensagens de diagnóstico acessíveis.

## Entrega por fases

1. **Textos e desenhos das telas:** revisar o vocabulário e criar prévias do Início, Carregar pedidos e Imprimir listas, nos dois temas.
2. **Interface local em português:** criar a camada visual e sua comunicação com os serviços existentes; manter os mesmos dados e rastreabilidade.
3. **Fluxo básico completo:** carregar vários arquivos, consultar, escolher modelo, conferir prévia e imprimir.
4. **Revisão, cadastros e opções avançadas:** migrar as funções restantes, incluindo favoritos, fotos e cópia de segurança.
5. **Validação com operadores:** testar tarefas sem orientação passo a passo, corrigir dificuldades e documentar um guia de uma página.

A mudança de interface não exige reconstruir o banco nem mudar as regras de importação. Novas funções, como desfazer ações e o lançador, serão implementadas e testadas explicitamente.

## Critérios para considerar pronto

- Nenhum texto em inglês criado pela aplicação nos caminhos principais, inclusive botões, tabelas, mensagens, filtros e controles de tema. Dados originais e nomes comerciais permanecem preservados.
- Carregar pedidos e imprimir um modelo pronto sem entrar nas opções avançadas.
- Uma pessoa que não participou do desenvolvimento consegue realizar o fluxo básico sem ajuda. Registrar onde ela hesitou ou errou, não apenas se concluiu.
- Os controles reais continuam em 163 pedidos, 179 linhas e 180 unidades comerciais, e as 87 referências são mantidas. Os totais da operação não são fixados nesses números.
- Reimportação, pendências, marcações, filtros, favoritos e PDFs mantêm as garantias já testadas. Sem exclusão por status ou alteração silenciosa de quantidade.
- Tema claro/escuro, acessibilidade básica e idioma conferidos no navegador real, além dos testes de serviços.

Prioridade recomendada: entregar primeiro **Carregar pedidos → Escolher lista → Imprimir**, com três modelos prontos, e deixar personalização e revisão detalhada disponíveis fora do caminho principal.
