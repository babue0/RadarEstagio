# Radar de Estágio — Documento de Definição (Pré-PRD)

**Status:** Fase 2 parcialmente implementada; validação técnica e de produto em andamento<br>
**Atualizado em:** 30/08/2026<br>
**Entrega prevista:** 02/09/2026<br>
**Disciplina:** Métodos e Aplicações de IA (IBM3116), turma 8001<br>
**Professor:** Alvaro Riz<br>
**Integrantes:** Igor Costa, Ian Dias e Miguel Esteves<br>
**Objetivo:** avaliar a viabilidade do projeto antes da elaboração do PRD<br>
**Base:** visão do produto, plano do MVP e prova técnica já executada pelo grupo

## 1. Finalidade deste documento

Este Pré-PRD organiza o que já sabemos sobre o Radar de Estágio e o que ainda precisa ser validado. Ele não especifica todos os requisitos do produto final. Sua função é:

- esclarecer o problema e a hipótese central;
- separar fatos comprovados de premissas ainda não testadas;
- avaliar viabilidade técnica, financeira, operacional, de prazo e de produto;
- expor vulnerabilidades antes que elas se tornem custo de desenvolvimento;
- listar oportunidades sem transformá-las automaticamente em escopo;
- pedir ao grupo a priorização das características pertinentes ao problema;
- registrar as decisões necessárias para avançar ao PRD.

## 2. Resumo executivo

O Radar de Estágio reduz o esforço diário de estudantes que procuram o primeiro estágio. O sistema coleta vagas da Adzuna e da Gupy, remove duplicatas, elimina anúncios claramente incompatíveis, compara as oportunidades com o perfil do estudante e entrega pelo Telegram uma lista curta, ranqueada e explicada.

A prova técnica principal já existe: o projeto coleta vagas da Adzuna e da Gupy, aplica pré-filtro,
avalia as oportunidades com Gemini e envia recomendações pelo Telegram. Em 30/08/2026, uma coleta
real com dois perfis presenciais no Rio produziu 703 vagas únicas e 55 candidatas após o
pré-filtro. O fluxo também pode usar o AGY localmente para testes sem consumir a cota da API
direta. A suíte atual possui 268 testes passando e 4 integrações condicionadas a um PostgreSQL
de teste.

As principais incertezas agora são de produto e operação:

- Adzuna e Gupy oferecem volume suficiente de vagas relevantes?
- os estudantes confiam no ranking e nas justificativas?
- Telegram é um canal aceitável para o público?
- a versão atual executa de forma estável no agendamento diário?
- a cota disponível do Gemini suporta a frequência e a quantidade de análises no CI?
- o benefício percebido é suficiente para gerar uso recorrente?

> **Veredito preliminar:** a Fase 1 é tecnicamente viável e está implementada. A viabilidade como produto ainda depende da cobertura das fontes, da confiança no matching, da aceitação do canal e da operação contínua dentro dos limites das APIs.

## 3. Problema que queremos resolver

Procurar estágio exige acompanhamento frequente de diferentes portais. Grande parte dos anúncios não combina com o curso, período, habilidades, localização ou modalidade desejada pelo estudante. Ao mesmo tempo, boas oportunidades podem fechar rapidamente.

O estudante precisa repetir três trabalhos:

1. procurar vagas em fontes diferentes;
2. eliminar manualmente anúncios irrelevantes;
3. interpretar requisitos para decidir onde vale a pena se candidatar.

Quando esse processo depende apenas de disciplina diária, surgem três consequências:

- tempo perdido analisando vagas inadequadas;
- candidaturas tardias;
- abandono da rotina de busca.

### Público inicial

- Universitários de tecnologia.
- Em busca do primeiro estágio.
- Inicialmente no Brasil.
- Dispostos a receber oportunidades pelo Telegram.
- O próprio grupo atua como primeiro conjunto de usuários e avaliadores.

Outros cursos, trainee, vagas júnior, bolsas, programas universitários e expansão internacional não fazem parte da validação inicial.

## 4. Hipótese central

Se um estudante informar seu perfil uma vez e o Radar monitorar vagas, remover oportunidades incompatíveis, explicar o nível de compatibilidade e notificá-lo proativamente, então ele gastará menos tempo procurando e conseguirá se candidatar mais cedo às vagas relevantes.

Essa hipótese contém quatro promessas que precisam ser avaliadas separadamente:

- **economia de tempo:** menos esforço de busca e triagem;
- **relevância:** maior proporção de vagas adequadas ao perfil;
- **velocidade:** descoberta mais próxima da publicação da vaga;
- **confiança:** explicações suficientes para o usuário compreender a recomendação.

## 5. Solução proposta

### 5.1 Experiência desejada do produto

Na visão de produto, o usuário preenche um cadastro curto com curso, período, habilidades, cidade e preferência de modalidade. Em seguida, ativa seu Radar no Telegram. A partir daí, recebe periodicamente as melhores vagas novas, contendo:

- título, empresa e localização;
- nota de compatibilidade entre 0 e 100;
- até três pontos concretos a favor e três pontos contra;
- alerta de possível inconsistência ou “pegadinha”;
- link para candidatura.

O Radar não se candidata em nome do usuário, não substitui os portais de vagas e não funciona como um chatbot genérico. Seu valor está na execução recorrente, no filtro, no ranking explicável e na entrega proativa.

### 5.2 Separação por fases

Para preservar a viabilidade, a visão completa não deve ser tratada como uma única entrega.

#### Fase 1 — Prova técnica de ponta a ponta (implementada)

- Duas fontes: Adzuna, por API oficial, e Gupy, por endpoint público não oficial.
- Coleta combinada com tolerância à falha parcial e deduplicação por título e empresa.
- Um perfil fixo.
- Pré-filtro determinístico.
- Matching com Gemini API no CI ou AGY em testes locais.
- Avaliação em lotes e saída estruturada validada por schema.
- Mensagem ranqueada no Telegram.
- Execução diária pelo GitHub Actions.
- Sem banco de dados.
- Sem cadastro web.
- Sem múltiplos usuários.
- Sem aprendizado por feedback.

#### Fase 2 — MVP de validação com usuários (em andamento)

- Cadastro estruturado do perfil (implementado no site).
- Persistência de perfis, vagas e avaliações em PostgreSQL/Supabase (implementada).
- Reutilização da avaliação quando a mesma vaga reaparecer.
- Explicação mais detalhada da nota sem aumentar a mensagem principal no Telegram.
- Vínculo seguro entre cadastro e Telegram (implementado).
- Suporte a vários usuários (implementado).
- Métricas do funil e da qualidade das vagas (estrutura implementada).
- Pausar, retomar e editar o perfil (ainda não disponível).
- Feedback simples sobre as recomendações (ainda não disponível).

#### Evoluções posteriores

- Mais fontes de vagas.
- Deduplicação entre execuções e histórico de vagas já vistas.
- Alertas instantâneos para oportunidades excepcionais.
- Aprendizado com histórico de feedback.
- Tendências do mercado e lacunas de competências.
- Outros cursos e níveis profissionais.

### 5.3 Tecnologias escolhidas

| Tecnologia | Uso no projeto | Motivo da escolha |
| --- | --- | --- |
| Python | Implementação do pipeline e das regras | Permite integrar APIs e escrever regras com uma base de código pequena. |
| uv | Ambiente e dependências | Reproduz o ambiente local e o ambiente do GitHub Actions a partir do arquivo de lock. |
| Pydantic | Modelos, configurações e saída da IA | Valida dados de entrada, variáveis de ambiente e respostas estruturadas. |
| httpx | Comunicação HTTP | Atende às integrações externas síncronas usadas pelo MVP. |
| Adzuna | Fonte oficial de vagas | Possui API documentada e credenciais próprias para consulta. |
| Gupy | Segunda fonte de vagas | Aumenta a cobertura e fornece descrições e modalidade mais completas, embora o endpoint não seja oficial. |
| Gemini API | Matching no GitHub Actions | Oferece saída estruturada e camada gratuita suficiente para o volume inicial, com uso de lotes. |
| AGY | Matching em testes locais | Permite testar o mesmo fluxo localmente sem consumir a cota da API direta. |
| Telegram Bot API | Entrega das recomendações | Envia mensagens e links sem exigir o desenvolvimento de um aplicativo próprio. |
| GitHub Actions | Agendamento diário | Executa o pipeline sem servidor dedicado e também permite disparo manual. |
| pytest e Ruff | Testes e qualidade de código | Detectam regressões e verificam o padrão do código sem acessar serviços reais. |
| PostgreSQL/Supabase | Persistência da Fase 2 | Guarda perfis, vagas, avaliações e envios fora da máquina temporária do Actions. |

### 5.4 Alternativas consideradas

| Alternativa | Decisão |
| --- | --- |
| LinkedIn | Descartado porque a plataforma restringe coleta automatizada. |
| WhatsApp | Adiado por exigir uma integração mais cara e burocrática que o Telegram. |
| SQLite no GitHub Actions | Descartado porque o arquivo não sobrevive ao fim de cada execução. |
| Servidor próprio e framework web | Adiados porque o MVP funciona como uma tarefa diária e não precisa expor uma API HTTP. |
| Uma única fonte de vagas | Substituída pela combinação de Adzuna e Gupy para aumentar a cobertura. |

## 6. Evidências disponíveis

### 6.1 O que já foi comprovado

- O ambiente Python e as dependências funcionam localmente com `uv`.
- A API oficial da Adzuna pode ser consultada com as credenciais do grupo.
- A Gupy pode ser consultada sem credenciais pelo endpoint utilizado no portal.
- As respostas das duas fontes podem ser convertidas para o mesmo modelo de domínio.
- As fontes podem ser combinadas; se uma falhar, a outra ainda pode fornecer vagas.
- Duplicatas da mesma execução são removidas por título e empresa, preservando a versão com mais informações.
- O pré-filtro elimina casos incompatíveis antes do uso de IA.
- Gemini API e AGY retornam os mesmos fatores estruturados, pontos a favor, pontos contra e
  alerta; a nota é calculada deterministicamente no Python.
- A avaliação em lotes reduz o número de requisições e isola falhas de vagas específicas.
- O Telegram recebe mensagens formatadas e divididas quando necessário.
- O formatador limita a exibição a três pontos a favor e três contra sem invalidar a avaliação.
- O pipeline completo já enviou uma lista real com cinco vagas avaliadas.
- O GitHub Actions teve execuções manuais bem-sucedidas em 26 e 27/08/2026 na versão anterior à Gupy.
- O README documenta instalação, configuração, comandos locais e execução pelo Actions.
- Em 30/08/2026, 268 testes automatizados passam e 4 integrações são ignoradas sem PostgreSQL de teste.

### 6.2 Limitações já observadas

- A camada gratuita observada do Gemini permite aproximadamente vinte requisições por dia; o valor pode mudar.
- O uso de lotes reduz requisições, mas uma falha pode gerar novas tentativas e consumir cota adicional.
- Ao atingir a cota diária, novas tentativas imediatas não resolvem o problema.
- O AGY aumenta a capacidade de testes locais, mas não está disponível no GitHub Actions e não substitui a API no agendamento.
- A Gupy é acessada por um endpoint não oficial, que pode mudar sem aviso.
- No modo sem banco, a deduplicação ocorre apenas entre vagas da mesma execução e uma vaga pode
  reaparecer em dias diferentes; com Supabase, o histórico de envios é persistido.
- A cobertura conjunta de Adzuna e Gupy para estágios de tecnologia no Brasil ainda precisa ser medida durante vários dias.

### 6.3 Trabalho técnico e validação restantes

- Confirmar a execução da versão atual no GitHub Actions após a inclusão da Gupy.
- Observar a execução automática atual por vários dias.
- Registrar volume coletado, volume filtrado, avaliações realizadas e falhas.
- Comparar uma amostra de resultados com avaliações humanas.
- Validar o cadastro, o vínculo com o Telegram e o primeiro valor com usuários externos.

## 7. Hipóteses e testes de baixo custo

Os limites abaixo são propostas iniciais. O grupo deve confirmá-los antes da validação.

| Hipótese | Como testar | Sinal inicial de aprovação |
| --- | --- | --- |
| H1 — Estudantes preferem receber vagas selecionadas a fazer toda a busca manualmente. | Entrevistar de 15 a 20 estudantes e oferecer uma demonstração. | Pelo menos 60% afirmam que usariam o serviço semanalmente. |
| H2 — O matching é confiável o suficiente para orientar a triagem. | Separar 20 vagas reais; três integrantes avaliam relevância sem ver a nota da IA; depois comparar. | Concordância entre classificação humana e sistema em pelo menos 75% dos casos. |
| H3 — As fontes atuais possuem cobertura útil para o nicho inicial. | Executar Adzuna e Gupy diariamente por sete dias e classificar os resultados. | Volume suficiente para entregar recomendações relevantes na maioria dos dias úteis. |
| H4 — Telegram é um canal aceitável para o público inicial. | Incluir a pergunta nas entrevistas e permitir que os participantes testem a entrega. | Pelo menos 60% aceitam o canal sem considerar isso uma barreira. |
| H5 — A entrega gera uma ação útil. | Enviar recomendações durante duas semanas para o grupo e convidados. | Usuários abrem vagas, salvam oportunidades ou relatam candidatura. |
| H6 — O sistema opera dentro da cota e do custo disponíveis. | Medir vagas coletadas, descartadas e enviadas à IA em cada execução. | O pré-filtro mantém as avaliações diárias abaixo do limite operacional definido. |

Para H3 e H5, o grupo ainda precisa definir números mínimos antes de observar os resultados. O limite não deve ser escolhido depois do teste apenas para justificar uma conclusão positiva.

## 8. Características pertinentes ao problema

Esta lista serve para priorização. Uma característica só deve entrar no produto quando tiver relação direta com a promessa central.

| Característica | Problema atendido | Prioridade sugerida | Fase | Decisão |
| --- | --- | --- | --- | --- |
| Coleta automática de vagas | Evita busca manual diária | Essencial | 1 | Confirmada |
| Pré-filtro determinístico | Reduz anúncios obviamente inadequados e custo de IA | Essencial | 1 | Confirmada |
| Nota de compatibilidade | Ajuda a ordenar onde investir atenção | Essencial | 1 | Confirmada |
| Justificativa da nota | Aumenta compreensão e confiança | Essencial | 1 | Confirmada |
| Alerta de inconsistência | Sinaliza exigências incompatíveis com estágio | Importante | 1 | Confirmada |
| Entrega automática no Telegram | Evita que o usuário precise lembrar de consultar o sistema | Essencial | 1 | Confirmada |
| Link direto para a vaga | Encurta o caminho até a candidatura | Essencial | 1 | Confirmada |
| Cadastro curto do perfil | Permite validar o produto com usuários diferentes | Essencial | 2 | Implementada |
| Vínculo seguro cadastro → Telegram | Associa o perfil ao chat correto | Essencial | 2 | Implementada |
| Pausar e retomar entregas | Dá controle ao usuário | Importante | 3 | Pendente |
| Editar perfil | Evita recomendações baseadas em dados antigos | Importante | 3 | Pendente |
| Feedback Gostei / Não gostei / Candidatei-me | Mede utilidade e pode orientar melhorias | Importante | 3 | Pendente |
| Adzuna e Gupy | Aumentam cobertura e reduzem dependência de uma única fonte | Importante | 1 | Confirmada |
| Fontes além de Adzuna e Gupy | Podem ampliar a cobertura se as fontes atuais forem insuficientes | Importante | Posterior | A discutir |
| Alerta instantâneo | Reduz o tempo até vagas muito relevantes | Desejável | Posterior | Não priorizada |
| Tendências de habilidades | Ajuda no planejamento de estudos | Desejável | Posterior | Não priorizada |
| Aplicação automática | Retira a decisão do usuário e amplia riscos | Fora do escopo | — | Rejeitada |
| Scraping do LinkedIn | Viola restrições da plataforma e aumenta risco | Fora do escopo | — | Rejeitada |

### Pergunta de priorização

Para cada item marcado como “A discutir”, o grupo deve responder:

1. Sem essa característica, a promessa central deixa de funcionar?
2. Existe uma forma manual ou mais simples de testar a mesma hipótese?
3. Ela reduz uma incerteza importante ou apenas deixa a demonstração mais completa?
4. Seu custo inclui manutenção, suporte, privacidade e observabilidade?
5. Qual característica existente pode ser adiada para abrir espaço para ela?

## 9. Vulnerabilidades e riscos

| Vulnerabilidade | Impacto | Probabilidade | Situação | Mitigação proposta |
| --- | --- | --- | --- | --- |
| Baixa cobertura de Adzuna e Gupy para o nicho | Alto | Média | Não medida | Executar por sete dias, medir vagas úteis e definir critério para adicionar outra fonte. |
| Mudança no endpoint não oficial da Gupy | Alto | Média | Risco permanente | Isolar o coletor, registrar falhas e continuar com Adzuna quando a Gupy estiver indisponível. |
| Cota diária do Gemini | Alto | Alta | Comprovada | Pré-filtrar, avaliar em lotes, interromper ao receber cota excedida e estimar alternativa paga. |
| Match Score incorreto | Alto | Média | Não validada | Comparação cega com avaliação humana, justificativa explícita e coleta de feedback. |
| Notas diferentes para a mesma vaga | Médio | Média | Possível sem histórico | Persistir a avaliação e reutilizá-la quando a vaga reaparecer para o mesmo perfil. |
| Vagas falsas, expiradas ou enganosas | Alto | Média | Não medida | Mostrar fonte e data, sinalizar inconsistências e permitir que o usuário reporte problemas. |
| Falha silenciosa de coleta | Alto | Média | Parcialmente tratada | Logs, falha visível no GitHub Actions e alerta operacional ao grupo. |
| Dependência de poucos provedores de vagas | Médio | Média | Parcialmente reduzida | Medir cobertura conjunta e adicionar outra fonte somente se H3 falhar. |
| Dependência do Telegram | Médio | Média | Aceita inicialmente | Validar aceitação e manter a camada de notificação isolada. |
| Perda de usuários entre site e Telegram | Médio | Alta | Parcialmente tratada | Deep link com token seguro, poucas etapas e medição do funil. |
| Exposição de perfil e identificador do Telegram | Alto | Baixa/média | Mitigada na implementação | Coleta mínima, RLS, permissões de coluna e política clara de finalidade. |
| Token previsível ou reutilizável no deep link | Alto | Baixa/média | Parcialmente tratada | Token aleatório e único já implementado; expiração e uso único continuam pendentes. |
| Aumento de escopo durante o semestre | Alto | Alta | Risco atual | Separar fases e impedir que oportunidades futuras entrem automaticamente no MVP. |
| Limites gratuitos ou preços mudarem | Médio | Média | Permanente | Registrar data e premissas de custo; recalcular antes do PRD e da apresentação. |
| GitHub Actions atrasar ou falhar | Médio | Baixa/média | Disparo manual comprovado; cron pendente | Logs, alerta de job vermelho e observação do agendamento por vários dias. |

## 10. Oportunidades

Oportunidades são caminhos de expansão, não compromissos do MVP.

### Curto prazo

- **Early Alert:** antecipar vagas com compatibilidade muito alta.
- **Explicabilidade:** oferecer mais detalhes sobre a nota sem aumentar a mensagem principal no Telegram.
- **Métricas reais:** mostrar coleta, filtragem, avaliações, cliques e candidaturas na apresentação.
- **Parcerias acadêmicas:** testar o Radar com colegas e centrais de carreira.

### Médio prazo

- **Learning Loop:** usar feedback para melhorar recomendações futuras.
- **Career Gap:** mostrar habilidades recorrentes que faltam ao perfil.
- **Radar do mercado:** resumir tecnologias e áreas mais solicitadas.
- **Novas fontes adicionais:** aumentar cobertura se Adzuna e Gupy não forem suficientes.

### Longo prazo

- Outros cursos e níveis profissionais.
- Rastreamento de candidaturas.
- Integração com e-mail ou aplicativo próprio.
- Relacionamento com empresas e recrutadores, condicionado à validação do lado do estudante.

## 11. Análise de viabilidade

### 11.1 Viabilidade técnica

**Avaliação: favorável, com a base da Fase 1 e parte da Fase 2 implementadas.**

As integrações centrais já funcionaram juntas em execuções reais. O projeto possui coletores independentes, deduplicação, pré-filtro, dois adapters de IA, avaliação em lotes, saída estruturada, formatação e envio pelo Telegram. Nenhuma parte da Fase 1 exige tecnologia experimental. Os principais riscos técnicos conhecidos são a cota diária da IA e a dependência do endpoint não oficial da Gupy.

O Actions já funcionou sob disparo manual na versão anterior. Para concluir a demonstração da
versão atual, ainda é necessário confirmar a execução com Adzuna e Gupy no Actions e observar o
cron durante vários dias.

### 11.2 Viabilidade financeira

**Avaliação: favorável no volume acadêmico, condicionada aos limites gratuitos.**

O cenário atual usa serviços com camadas gratuitas adequadas a uma prova acadêmica de baixo volume. Isso não significa custo permanentemente zero. Preços, cotas e políticas podem mudar, e o custo cresce com:

- número de usuários;
- número de vagas por usuário;
- quantidade de avaliações feitas pela IA;
- novas fontes e infraestrutura de persistência.

Antes do PRD, o grupo deve registrar uma memória de cálculo com volume diário esperado, chamadas por serviço e um cenário alternativo pago. Valores devem incluir data da consulta e fonte.

### 11.3 Viabilidade operacional

**Avaliação: favorável para poucos usuários, ainda não comprovada em operação contínua.**

A execução já está automatizada, mas “rodar sozinho” não significa ausência de manutenção. O grupo precisará acompanhar:

- falhas de coleta e autenticação;
- mudanças nas APIs;
- cota da IA;
- links expirados;
- qualidade das recomendações;
- rotação e proteção de credenciais.

A operação atual usa duas fontes, banco, múltiplos usuários e uma entrega diária. A complexidade
cresce de forma relevante quando entrarem feedback, edição de perfil e novas fontes.

### 11.4 Viabilidade de prazo

**Avaliação: favorável para concluir a entrega técnica; indefinida para a visão completa.**

O núcleo da Fase 1, a automação, o Supabase, o cadastro web, o vínculo com Telegram e o suporte
a múltiplos usuários estão implementados. O foco imediato é confirmar a operação atual no Actions,
coletar evidências e validar o produto com estudantes; edição, pausa, retomada e feedback ficam
para a próxima etapa.

### 11.5 Viabilidade de produto

**Avaliação: principal incerteza.**

Ainda não foi comprovado que estudantes usarão o Radar de forma recorrente, confiarão nas notas ou aceitarão Telegram como canal. Essas questões não são resolvidas com mais código; exigem entrevistas, demonstrações e observação do comportamento.

### Síntese

| Dimensão | Avaliação atual | Evidência faltante |
| --- | --- | --- |
| Técnica | Favorável | Execução da versão atual no Actions e observação do cron |
| Financeira | Favorável em baixo volume | Memória de cálculo e cenário pago |
| Operacional | Favorável para a base atual | Monitoramento de execuções reais com vários usuários |
| Prazo | Favorável para a entrega técnica | Validação do escopo restante da Fase 2 |
| Produto | Incerta | Entrevistas, aceitação das recomendações e uso recorrente |

## 12. Dúvidas que precisam ser respondidas

### Produto

- Quem exatamente participa do primeiro teste externo?
- Quantas vagas devem chegar por entrega?
- Existe nota mínima ou sempre são enviadas as melhores disponíveis?
- Em dias sem vaga adequada, o Radar avisa ou permanece em silêncio?
- Qual horário de entrega será testado?
- O usuário precisa pausar, retomar ou pedir uma atualização manual?

### Matching

- O que torna uma vaga eliminatória antes da IA?
- Como a nota combina skills, curso, período, modalidade e experiência?
- Qual diferença entre “não recomendado” e uma nota apenas baixa?
- Como medir concordância entre o sistema e avaliadores humanos?
- A mesma régua funciona para desenvolvimento, dados, produto e suporte?

### Fontes

- Qual volume de vagas relevantes torna Adzuna e Gupy suficientes para a Fase 1?
- Quando a baixa cobertura justifica adicionar uma fonte além das duas atuais?
- Quais fontes possuem uso permitido e estabilidade aceitável?
- Como medir erros da deduplicação atual e evitar repetições entre dias sem banco?

### Canal e cadastro

- Telegram é aceito pelo público ou apenas conveniente para o grupo?
- Cadastro web é necessário para validar ou um formulário manual resolve o primeiro teste?
- Quais campos são realmente necessários para uma recomendação útil?
- Como o usuário edita ou exclui seus dados?

### Acadêmico

- O professor avaliará mais a demonstração, documentação, arquitetura ou métricas?
- Quais evidências precisam aparecer na apresentação?
- O objetivo do semestre é uma prova acadêmica ou validação com usuários externos?

## 13. Critérios para avançar ao PRD

O grupo deve avançar ao PRD quando:

- o escopo da Fase 1 estiver congelado;
- a versão atual tiver sido executada com sucesso no GitHub Actions;
- a execução automática tiver funcionado durante o período de observação definido;
- a cobertura conjunta de Adzuna e Gupy tiver sido medida;
- o teste de concordância do matching tiver sido executado;
- o grupo tiver realizado entrevistas com estudantes do público inicial;
- os limites de aprovação de H1 a H6 estiverem definidos antes da análise dos resultados;
- as características “A discutir” da Fase 2 estiverem priorizadas;
- os dados obrigatórios e a política de exclusão estiverem definidos;
- a memória de cálculo de custo estiver registrada;
- o professor tiver confirmado os critérios acadêmicos da entrega.

## 14. Perguntas prioritárias para a próxima reunião

1. Estamos validando apenas a prova técnica ou também o cadastro com usuários externos neste semestre?
2. Qual resultado mínimo da coleta torna Adzuna e Gupy suficientes?
3. Qual regra inicial torna o Match Score explicável?
4. Qual concordância mínima entre avaliação humana e sistema consideramos aceitável?
5. Quantas vagas devem ser enviadas e qual comportamento usar em dias sem recomendação?
6. Telegram será validado como hipótese ou assumido como decisão do projeto acadêmico?
7. Quais três métricas serão apresentadas como evidência de que o projeto funcionou?
8. Quais características da Fase 2 são necessárias para o teste e quais podem ser simuladas manualmente?

## 15. Próximos passos sugeridos

1. Até 28/08: executar manualmente no Actions a versão com Adzuna e Gupy e guardar a evidência.
2. De 28/08 a 01/09: observar o cron e registrar volume coletado, vagas únicas, vagas filtradas, avaliações, envios e falhas.
3. Até 31/08: avaliar manualmente uma amostra de vinte vagas e comparar com o sistema, se o grupo conseguir reunir os avaliadores.
4. Até 01/09: definir as três métricas e os prints ou logs que entrarão na apresentação.
5. Em 01/09: congelar o escopo, revisar o documento e ensaiar a demonstração.
6. Em 02/09: entregar a Fase 1 com as evidências obtidas e declarar como pendentes as hipóteses de produto ainda não testadas.
7. Após a entrega: projetar a explicação detalhada da nota e a persistência de vagas e avaliações.
8. Depois: entrevistar estudantes, concluir H1 a H6 e elaborar o PRD somente para a fase aprovada.

---

**Status do documento:** FASE 1 IMPLEMENTADA; FASE 2 EM ANDAMENTO — a base técnica é favorável,
mas cobertura, confiança, uso recorrente e validação com usuários continuam pendentes para
comprovar a viabilidade do produto.
