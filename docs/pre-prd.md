# Radar de Estágio — Documento de Definição (Pré-PRD)

**Status:** em validação<br>
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

O Radar de Estágio reduz o esforço diário de estudantes que procuram o primeiro estágio. O sistema coleta vagas, elimina anúncios claramente incompatíveis, compara as oportunidades com o perfil do estudante e entrega pelo Telegram uma lista curta, ranqueada e explicada.

A prova técnica principal já existe: o projeto coletou vagas reais da Adzuna, aplicou pré-filtro, avaliou as oportunidades com Gemini e enviou cinco recomendações reais pelo Telegram. Portanto, a maior incerteza deixou de ser a integração básica entre as tecnologias.

As principais incertezas agora são de produto e operação:

- a Adzuna oferece volume suficiente de vagas relevantes?
- os estudantes confiam no ranking e nas justificativas?
- Telegram é um canal aceitável para o público?
- a cota disponível do Gemini suporta a frequência e a quantidade de análises?
- o benefício percebido é suficiente para gerar uso recorrente?

> **Veredito preliminar:** o projeto é tecnicamente viável como prova de ponta a ponta. A viabilidade como produto depende da cobertura das fontes, da confiança no matching, da aceitação do canal e da capacidade de operar dentro dos limites das APIs.

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
- justificativa curta e específica;
- requisitos atendidos e lacunas relevantes;
- alerta de possível inconsistência ou “pegadinha”;
- link para candidatura.

O Radar não se candidata em nome do usuário, não substitui os portais de vagas e não funciona como um chatbot genérico. Seu valor está na execução recorrente, no filtro, no ranking explicável e na entrega proativa.

### 5.2 Separação por fases

Para preservar a viabilidade, a visão completa não deve ser tratada como uma única entrega.

#### Fase 1 — Prova técnica de ponta a ponta

- Uma fonte oficial: Adzuna.
- Um perfil fixo.
- Pré-filtro determinístico.
- Matching com Gemini.
- Mensagem ranqueada no Telegram.
- Execução diária pelo GitHub Actions.
- Sem banco de dados.
- Sem cadastro web.
- Sem múltiplos usuários.
- Sem aprendizado por feedback.

#### Fase 2 — MVP de validação com usuários

- Cadastro estruturado do perfil.
- Persistência em PostgreSQL/Supabase.
- Vínculo seguro entre cadastro e Telegram.
- Suporte a vários usuários.
- Pausar, retomar e editar o perfil.
- Feedback simples sobre as recomendações.
- Métricas do funil e da qualidade das vagas.

#### Evoluções posteriores

- Mais fontes de vagas.
- Deduplicação entre fontes.
- Alertas instantâneos para oportunidades excepcionais.
- Aprendizado com histórico de feedback.
- Tendências do mercado e lacunas de competências.
- Outros cursos e níveis profissionais.

## 6. Evidências disponíveis

### 6.1 O que já foi comprovado

- O ambiente Python e as dependências funcionam localmente com `uv`.
- A API oficial da Adzuna pode ser consultada com as credenciais do grupo.
- A resposta da Adzuna pode ser convertida para o modelo de domínio do projeto.
- O pré-filtro elimina casos incompatíveis antes do uso de IA.
- O Gemini retorna avaliação estruturada com nota, motivo e alerta.
- O Telegram recebe mensagens formatadas e divididas quando necessário.
- O pipeline completo já enviou uma lista real com cinco vagas avaliadas.
- As integrações principais possuem testes automatizados sem chamadas reais de rede.

### 6.2 Limitações já observadas

- A camada gratuita disponível do modelo Gemini usado pelo projeto permite aproximadamente vinte avaliações por dia.
- Ao atingir a cota diária, novas tentativas imediatas não resolvem o problema.
- O número de vagas que pode ser analisado precisa ser controlado antes da chamada à IA.
- A cobertura real da Adzuna para estágios de tecnologia no Brasil ainda precisa ser medida durante vários dias.

### 6.3 Trabalho técnico restante na Fase 1

- Configurar a execução diária no GitHub Actions.
- Configurar os segredos no repositório.
- Criar o README operacional.
- Observar execuções automáticas por vários dias.
- Registrar volume coletado, volume filtrado, avaliações realizadas e falhas.

## 7. Hipóteses e testes de baixo custo

Os limites abaixo são propostas iniciais. O grupo deve confirmá-los antes da validação.

| Hipótese | Como testar | Sinal inicial de aprovação |
| --- | --- | --- |
| H1 — Estudantes preferem receber vagas selecionadas a fazer toda a busca manualmente. | Entrevistar de 15 a 20 estudantes e oferecer uma demonstração. | Pelo menos 60% afirmam que usariam o serviço semanalmente. |
| H2 — O matching é confiável o suficiente para orientar a triagem. | Separar 20 vagas reais; três integrantes avaliam relevância sem ver a nota da IA; depois comparar. | Concordância entre classificação humana e sistema em pelo menos 75% dos casos. |
| H3 — A Adzuna possui cobertura útil para o nicho inicial. | Executar a coleta diariamente por sete dias e classificar os resultados. | Volume suficiente para entregar recomendações relevantes na maioria dos dias úteis. |
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
| Cadastro curto do perfil | Permite validar o produto com usuários diferentes | Essencial | 2 | A discutir |
| Vínculo seguro cadastro → Telegram | Associa o perfil ao chat correto | Essencial | 2 | A discutir |
| Pausar e retomar entregas | Dá controle ao usuário | Importante | 2 | A discutir |
| Editar perfil | Evita recomendações baseadas em dados antigos | Importante | 2 | A discutir |
| Feedback Gostei / Não gostei / Candidatei-me | Mede utilidade e pode orientar melhorias | Importante | 2 | A discutir |
| Mais fontes de vagas | Aumenta cobertura e reduz dependência | Importante | Posterior | A discutir |
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
| Baixa cobertura da Adzuna para o nicho | Alto | Média | Não medida | Executar por sete dias, medir vagas úteis e definir critério para adicionar outra fonte. |
| Cota diária do Gemini | Alto | Alta | Comprovada | Pré-filtrar, limitar avaliações, interromper ao receber cota excedida e estimar alternativa paga. |
| Match Score incorreto | Alto | Média | Não validada | Comparação cega com avaliação humana, justificativa explícita e coleta de feedback. |
| Vagas falsas, expiradas ou enganosas | Alto | Média | Não medida | Mostrar fonte e data, sinalizar inconsistências e permitir que o usuário reporte problemas. |
| Falha silenciosa de coleta | Alto | Média | Parcialmente tratada | Logs, falha visível no GitHub Actions e alerta operacional ao grupo. |
| Dependência de um único provedor de vagas | Médio | Alta | Aceita na Fase 1 | Tratar como limite consciente; adicionar fonte somente se H3 falhar. |
| Dependência do Telegram | Médio | Média | Aceita inicialmente | Validar aceitação e manter a camada de notificação isolada. |
| Perda de usuários entre site e Telegram | Médio | Alta | Fase 2 | Deep link com token seguro, poucas etapas e medição do funil. |
| Exposição de perfil e identificador do Telegram | Alto | Baixa/média | Fase 2 | Coleta mínima, controle de acesso, exclusão de dados e política clara de finalidade. |
| Token previsível ou reutilizável no deep link | Alto | Baixa/média | Fase 2 | Token aleatório, expirável, de uso único e invalidado após o vínculo. |
| Aumento de escopo durante o semestre | Alto | Alta | Risco atual | Separar fases e impedir que oportunidades futuras entrem automaticamente no MVP. |
| Limites gratuitos ou preços mudarem | Médio | Média | Permanente | Registrar data e premissas de custo; recalcular antes do PRD e da apresentação. |
| GitHub Actions atrasar ou falhar | Médio | Baixa/média | Ainda não testada | Execução manual, logs, alertas e observação por sete dias. |

## 10. Oportunidades

Oportunidades são caminhos de expansão, não compromissos do MVP.

### Curto prazo

- **Early Alert:** antecipar vagas com compatibilidade muito alta.
- **Explicabilidade:** tornar os fatores do Match Score mais claros.
- **Métricas reais:** mostrar coleta, filtragem, avaliações, cliques e candidaturas na apresentação.
- **Parcerias acadêmicas:** testar o Radar com colegas e centrais de carreira.

### Médio prazo

- **Learning Loop:** usar feedback para melhorar recomendações futuras.
- **Career Gap:** mostrar habilidades recorrentes que faltam ao perfil.
- **Radar do mercado:** resumir tecnologias e áreas mais solicitadas.
- **Novas fontes:** aumentar cobertura quando houver evidência de necessidade.

### Longo prazo

- Outros cursos e níveis profissionais.
- Rastreamento de candidaturas.
- Integração com e-mail ou aplicativo próprio.
- Relacionamento com empresas e recrutadores, condicionado à validação do lado do estudante.

## 11. Análise de viabilidade

### 11.1 Viabilidade técnica

**Avaliação: demonstrada parcialmente e favorável.**

As integrações centrais já funcionaram juntas em uma execução real. Nenhuma parte da Fase 1 exige tecnologia experimental. O principal risco técnico conhecido é a cota diária da IA, que limita quantas vagas podem ser avaliadas e exige disciplina no pré-filtro.

Para concluir a demonstração técnica, o sistema ainda precisa executar automaticamente e de forma estável pelo GitHub Actions durante vários dias.

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

A execução pode ser automatizada, mas “rodar sozinho” não significa ausência de manutenção. O grupo precisará acompanhar:

- falhas de coleta e autenticação;
- mudanças nas APIs;
- cota da IA;
- links expirados;
- qualidade das recomendações;
- rotação e proteção de credenciais.

A operação da Fase 1 é simples porque usa uma fonte, um perfil e uma entrega diária. A complexidade cresce de forma relevante quando entram banco, múltiplos usuários, feedback e mais fontes.

### 11.4 Viabilidade de prazo

**Avaliação: favorável para a Fase 1; indefinida para a visão completa.**

O núcleo da Fase 1 está implementado. Restam automação, documentação e observação de estabilidade. Cadastro web, Supabase, vínculo com Telegram e multiusuário devem receber uma estimativa separada antes de serem tratados como compromisso.

### 11.5 Viabilidade de produto

**Avaliação: principal incerteza.**

Ainda não foi comprovado que estudantes usarão o Radar de forma recorrente, confiarão nas notas ou aceitarão Telegram como canal. Essas questões não são resolvidas com mais código; exigem entrevistas, demonstrações e observação do comportamento.

### Síntese

| Dimensão | Avaliação atual | Evidência faltante |
| --- | --- | --- |
| Técnica | Favorável | Execução automática estável por vários dias |
| Financeira | Favorável em baixo volume | Memória de cálculo e cenário pago |
| Operacional | Favorável para a Fase 1 | Monitoramento de execuções reais |
| Prazo | Favorável para a Fase 1 | Estimativa separada da Fase 2 |
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

- Qual volume de vagas relevantes torna a Adzuna suficiente para a Fase 1?
- Quando a baixa cobertura justifica adicionar uma segunda fonte?
- Quais fontes possuem uso permitido e estabilidade aceitável?
- Como detectar duplicatas quando houver mais de uma fonte?

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
- a execução automática tiver funcionado durante o período de observação definido;
- a cobertura da Adzuna tiver sido medida;
- o teste de concordância do matching tiver sido executado;
- o grupo tiver realizado entrevistas com estudantes do público inicial;
- os limites de aprovação de H1 a H6 estiverem definidos antes da análise dos resultados;
- as características “A discutir” da Fase 2 estiverem priorizadas;
- os dados obrigatórios e a política de exclusão estiverem definidos;
- a memória de cálculo de custo estiver registrada;
- o professor tiver confirmado os critérios acadêmicos da entrega.

## 14. Perguntas prioritárias para a próxima reunião

1. Estamos validando apenas a prova técnica ou também o cadastro com usuários externos neste semestre?
2. Qual resultado mínimo da coleta torna a Adzuna suficiente?
3. Qual regra inicial torna o Match Score explicável?
4. Qual concordância mínima entre avaliação humana e sistema consideramos aceitável?
5. Quantas vagas devem ser enviadas e qual comportamento usar em dias sem recomendação?
6. Telegram será validado como hipótese ou assumido como decisão do projeto acadêmico?
7. Quais três métricas serão apresentadas como evidência de que o projeto funcionou?
8. Quais características da Fase 2 são necessárias para o teste e quais podem ser simuladas manualmente?

## 15. Próximos passos sugeridos

1. Finalizar GitHub Actions e README da Fase 1.
2. Observar sete dias de execução e registrar volume e falhas.
3. Avaliar manualmente vinte vagas e comparar com o sistema.
4. Entrevistar de 15 a 20 estudantes de tecnologia.
5. Consolidar as respostas da próxima reunião.
6. Revisar o veredito de viabilidade com as evidências obtidas.
7. Elaborar o PRD somente para a fase aprovada.

---

**Status do documento:** EM VALIDAÇÃO — o projeto possui prova técnica favorável, mas ainda precisa comprovar cobertura, confiança e uso recorrente antes de assumir a viabilidade completa do produto.
