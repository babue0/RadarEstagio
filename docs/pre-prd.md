# Radar de Estágio — Documento de Definição (Pré-PRD)

**Status:** base técnica viável; Fase 2 em validação de produto e operação

**Atualizado em:** 31/08/2026

**Entrega prevista:** 02/09/2026

**Disciplina:** Métodos e Aplicações de IA (IBM3116), turma 8001

**Professor:** Alvaro Riz

**Integrantes:** Igor Costa, Ian Dias e Miguel Esteves

## 1. Objetivo do documento

Este documento antecede o PRD. Seu objetivo não é transformar toda ideia em requisito, mas
permitir que o grupo decida, com base em evidências, se o Radar de Estágio é viável e qual
produto merece ser especificado depois da validação.

Ele deve servir para:

- tirar dúvidas sobre problema, público, solução, matching, canal e operação;
- separar fatos comprovados de hipóteses e decisões ainda abertas;
- tornar vulnerabilidades visíveis antes que gerem custo ou invalidem a proposta;
- listar oportunidades sem incorporá-las automaticamente ao escopo;
- pedir a priorização das características realmente pertinentes ao problema;
- avaliar viabilidade técnica, financeira, operacional, de prazo, privacidade e produto;
- definir quais evidências autorizam o avanço para um PRD completo.

### 1.1 Como interpretar as afirmações

| Classificação | Significado |
| --- | --- |
| **Comprovado** | Existe código, teste automatizado, execução real ou dado observável. |
| **Parcialmente comprovado** | A base existe, mas falta repetição, volume ou usuário externo. |
| **Hipótese** | É uma expectativa que ainda precisa de teste. |
| **Decisão aberta** | O grupo precisa escolher uma regra antes de medir ou desenvolver. |

O princípio central é **prova antes de promessa**: cadastro, quantidade de funcionalidades e
volume coletado não demonstram valor sozinhos. O valor inicial ocorre quando o estudante recebe
uma recomendação relevante; a utilidade só se confirma quando ele abre, aprova ou se candidata à
vaga.

## 2. Resumo executivo e veredito

O Radar de Estágio reduz o trabalho diário de estudantes que procuram o primeiro estágio. O
sistema coleta vagas da Adzuna e da Gupy, elimina duplicatas e incompatibilidades evidentes,
compara as oportunidades com o perfil do estudante e entrega pelo Telegram uma lista curta,
ranqueada e explicada.

A prova técnica funciona de ponta a ponta. O projeto possui cadastro web, múltiplos usuários,
vínculo com Telegram, persistência no Supabase, histórico entre execuções, matching estruturado,
nota determinística, entrega e instrumentação do funil até a primeira recomendação. Em
31/08/2026, a suíte possui **284 testes passando e 4 integrações ignoradas** sem um PostgreSQL de
teste. As cinco migrações estão aplicadas no banco remoto.

Uma coleta real em 30/08/2026, usando Adzuna e Gupy para dois perfis presenciais no Rio de
Janeiro, produziu **703 vagas únicas e 55 candidatas após o pré-filtro**. O agendamento externo
executou o workflow com sucesso às 07:23 BRT do mesmo dia. A execução posterior do commit de
instrumentação foi cancelada, portanto o estado mais recente ainda precisa de uma execução
completa no GitHub Actions.

### Veredito atual

> **O Radar é viável como MVP acadêmico e piloto técnico controlado. Ainda não está comprovado
> como produto de uso recorrente.**

É recomendado continuar a validação, sem ampliar fontes ou escopo agora. A elaboração de um PRD
completo deve depender de quatro provas ainda ausentes:

1. cobertura útil das fontes durante vários dias;
2. concordância aceitável entre o ranking e avaliações humanas;
3. ativação de usuários externos até a primeira recomendação;
4. ação útil após a entrega, como abertura da vaga ou candidatura.

## 3. Problema, público e limite da proposta

### 3.1 Problema

Procurar estágio exige acompanhamento frequente de diferentes portais. Muitos anúncios não
combinam com curso, período, habilidades, localização ou modalidade do estudante, e as melhores
oportunidades podem fechar rapidamente.

O estudante repete três trabalhos:

1. procurar vagas em fontes diferentes;
2. eliminar anúncios irrelevantes;
3. interpretar requisitos para escolher onde investir atenção.

As consequências esperadas são tempo perdido, candidaturas tardias e abandono da rotina de
busca. A frequência e a intensidade dessas dores ainda precisam ser confirmadas com estudantes
externos ao grupo.

### 3.2 Público inicial

- universitários de tecnologia no Brasil;
- em busca do primeiro estágio;
- com perfil mínimo de curso, período, habilidades, cidade e modalidade;
- dispostos a testar o Telegram como canal de entrega.

O próprio grupo é útil para verificar funcionamento, mas não comprova demanda. Outros cursos,
trainee, vagas júnior, bolsas, expansão internacional e recrutadores estão fora da validação
inicial.

### 3.3 Trabalho que o produto pretende resolver

> “Mostre, sem eu precisar procurar todos os dias, quais vagas recentes merecem minha atenção e
> explique por quê.”

O Radar não se candidata pelo estudante, não garante contratação, não substitui os portais e não
é um chatbot genérico. Sua proposta de valor é a combinação de recorrência, filtro, ranking
explicável e entrega proativa.

## 4. Hipótese central e promessas

Se um estudante informar seu perfil uma vez e o Radar monitorar vagas, remover oportunidades
incompatíveis, explicar a compatibilidade e notificá-lo proativamente, então ele gastará menos
tempo procurando e poderá se candidatar mais cedo às vagas relevantes.

| Promessa | O que precisa ser observado | Situação atual |
| --- | --- | --- |
| Economia de tempo | Tempo de busca antes e depois ou relato consistente de redução | Hipótese |
| Relevância | Proporção de recomendações julgadas úteis | Não mensurada |
| Velocidade | Intervalo entre publicação, entrega e abertura | Parcialmente mensurável |
| Confiança | Compreensão da nota e concordância com a justificativa | Não validada externamente |
| Recorrência | Retorno ou permanência no serviço após a primeira entrega | Não mensurada |

## 5. Solução definida para o MVP

### 5.1 Experiência desejada

O usuário cria uma conta, informa seu perfil e vincula o Telegram. O Radar executa diariamente e
entrega até cinco vagas novas com nota igual ou superior ao limite configurado. Cada vaga contém:

- título, empresa, localização, fonte e data;
- nota de compatibilidade de 0 a 100;
- até três fatos a favor e três requisitos ou incompatibilidades contra;
- alerta de possível inconsistência quando aplicável;
- link direto para a oportunidade.

O padrão atual envia até **5 vagas** com nota mínima **40**, ambos configuráveis.

### 5.2 Jornada e definição de ativação

```text
landing → cadastro → perfil → confirmação de e-mail → Telegram vinculado
        → primeira recomendação entregue → vaga aberta → ação útil
```

A ativação é a **primeira entrega bem-sucedida no Telegram contendo ao menos uma vaga
recomendada**. Conta criada, formulário concluído e Telegram vinculado são etapas necessárias,
mas não representam valor entregue.

O funil está instrumentado até a ativação. Os eventos `vaga_aberta`, `vaga_util`,
`vaga_irrelevante` e `candidatura_iniciada` estão reservados no banco, mas ainda não são emitidos
porque o produto não possui link rastreado nem feedback. A definição e as consultas estão em
[`metricas.md`](metricas.md).

### 5.3 Escopo implementado

- coleta combinada de Adzuna e Gupy, tolerando falha parcial;
- deduplicação dentro da coleta e histórico entre execuções;
- pré-filtro determinístico antes do uso de IA;
- Gemini API no CI e AGY em testes locais;
- fatores estruturados extraídos pela IA e nota calculada no Python;
- avaliação em lotes, reaproveitamento de avaliações e tratamento de cota;
- mensagem ranqueada no Telegram;
- cadastro web, autenticação, perfil e vínculo seguro com Telegram;
- Supabase com perfis, vagas, avaliações, envios e eventos de produto;
- múltiplos usuários;
- evento de ativação e funil da landing à primeira recomendação;
- execução diária disparada externamente no GitHub Actions.

### 5.4 Ainda não disponível

- edição e exclusão do perfil pelo usuário;
- pausa e retomada das entregas pela interface;
- feedback “útil”, “irrelevante” ou “candidatei-me”;
- rastreamento de abertura da vaga;
- painel ou histórico para o estudante;
- fontes além de Adzuna e Gupy.

## 6. Definição do matching

Gemini ou AGY interpreta a descrição e devolve fatores estruturados. A IA não escolhe livremente
a nota final. O Python aplica a seguinte fórmula:

\[
N = 50H + 15C + 10A + 15P + 10L
\]

Em que cada fator varia de 0 a 1:

- **H — habilidades:** cobertura das habilidades explícitas da vaga;
- **C — curso:** incompatível, parcial ou compatível;
- **A — área:** incompatível, parcial ou compatível;
- **P — período/experiência:** incompatível, parcial ou compatível;
- **L — logística:** média de localização e modalidade.

Regras atuais:

- habilidades valem 50% da nota porque são o principal sinal de capacidade prática;
- quando existem requisitos obrigatórios e desejáveis, eles representam 80% e 20% do fator de
  habilidades, respectivamente;
- a cobertura é suavizada, `(1+atendidas)/(1+exigidas)`: requisito ausente do perfil conta
  como incerteza, não como veto, e não há travas de nota por habilidade ausente;
- idiomas e pacote Office não entram na cobertura, mas seguem visíveis na lista de requisitos;
- Java e JavaScript são comparados como tecnologias diferentes;
- quando a vaga não explicita habilidades, o fator de habilidades recebe cobertura neutra de 0,35 (17,5/50);
- modalidade não informada recebe compatibilidade parcial apenas dentro de logística e não limita
  globalmente a nota;
- vaga presencial ou híbrida para um perfil que exige remoto tem nota limitada a 30;
- fatores semânticos parciais recebem metade do respectivo peso.

A versão anterior concedia 50/50 quando a vaga omitia habilidades. Em 31/08/2026, a análise das
98 vagas já enviadas confirmou o efeito colateral: os anúncios genéricos, sem stack declarada,
ocupavam o topo com nota 98, acima de vagas que citavam exatamente as habilidades do perfil
(notas 78 a 85). A cobertura passou a ser neutra e, em 31/08/2026 à noite, o teste com vinte vagas reais
revelou o efeito inverso: as travas de 60/70 pontos e requisitos como inglês e Excel derrubavam
toda vaga que declarava stack, devolvendo o topo aos anúncios genéricos. A régua atual usa
cobertura suavizada sem travas, ignora idiomas e Office na nota e rebaixa a cobertura neutra
para 0,35; no reteste das vinte vagas, as detalhadas e parcialmente compatíveis assumiram o topo.

## 7. Arquitetura e operação atuais

| Componente | Uso | Evidência ou ressalva |
| --- | --- | --- |
| Python e uv | Pipeline, regras e ambiente reproduzível | Comprovado localmente e no CI |
| Adzuna | Fonte oficial de vagas | API documentada e autenticada |
| Gupy | Segunda fonte | Endpoint público interno, sem garantia contratual |
| Gemini API | Extração de fatores no Actions | Funciona, sujeito a cota variável |
| AGY | Extração local para desenvolvimento | Não está disponível no Actions |
| Telegram Bot API | Entrega proativa | Envios reais comprovados |
| PostgreSQL/Supabase | Perfis, vagas, avaliações, envios e eventos | Migrações `0001` a `0005` aplicadas |
| GitHub Actions | Execução do pipeline | Workflow apenas com `workflow_dispatch` |
| cron-job.org | Disparo diário às 07:23 BRT | Sucesso observado; dependência externa |
| pytest e Ruff | Regressão e qualidade | 284 testes passando, 4 ignorados |

O workflow tem limite de quinze minutos. O disparo automático é externo porque o agendamento
nativo do GitHub deixou de executar durante dois dias. Isso resolve o disparo inicial, mas aumenta
a dependência operacional e precisa de observação contínua.

## 8. Evidências e lacunas

### 8.1 Comprovado

- Adzuna e Gupy podem ser convertidas para o mesmo modelo e combinadas;
- se uma fonte falha, a outra ainda pode fornecer vagas;
- duplicatas são removidas e vagas já enviadas não são reenviadas com Supabase;
- avaliações persistidas podem ser reutilizadas;
- o pré-filtro reduz vagas antes da IA;
- a nota é determinística a partir dos fatores estruturados;
- o Telegram recebe mensagens formatadas e divididas quando necessário;
- o pipeline já enviou uma lista real com cinco vagas;
- uma execução automática ocorreu em 29/08 e outra em 30/08 às 07:23 BRT;
- cadastro, vínculo Telegram e múltiplos usuários estão implementados;
- eventos de ativação e funil foram implantados no banco;
- 284 testes passam e 4 integrações dependem de PostgreSQL de teste.

### 8.2 Parcialmente comprovado

- volume inicial de 703 vagas únicas e 55 candidatas em uma coleta no Rio de Janeiro;
- operação automática em dias recentes, ainda sem uma janela contínua longa;
- funcionamento com vários perfis, mas sem piloto externo suficiente;
- explicabilidade técnica da nota, ainda sem evidência de confiança do estudante.

### 8.3 Ainda não comprovado

- que o problema é frequente e importante para estudantes externos ao grupo;
- que Adzuna e Gupy entregam vagas relevantes na maioria dos dias;
- que a nota concorda com avaliadores humanos em diferentes áreas de tecnologia;
- que o Telegram é aceito como canal de uso recorrente;
- que usuários concluem cadastro e vínculo sem ajuda;
- que recomendações geram abertura ou candidatura;
- que o custo e a cota permanecem adequados com crescimento de usuários.

## 9. Hipóteses e testes de baixo custo

Os limites abaixo são propostas. O grupo deve aprová-los **antes** da coleta para evitar escolher
um critério conveniente depois do resultado. Como o volume inicial é pequeno, entrevistas e
sessões observadas produzem sinal melhor do que testes A/B sem amostra suficiente.

| Hipótese | Teste mínimo | Sinal inicial proposto |
| --- | --- | --- |
| H1 — A busca manual é uma dor relevante | 5 entrevistas moderadas com estudantes do público; ampliar se os padrões forem inconclusivos | Pelo menos 4 relatam busca repetitiva e demonstram interesse em delegar a triagem |
| H2 — O matching orienta a triagem | 20 vagas, 3 avaliadores sem ver a nota do sistema | Concordância de pelo menos 75% entre sistema e decisão majoritária |
| H3 — As fontes têm cobertura útil | Executar por 7 dias e classificar vagas enviáveis | Ao menos 1 recomendação relevante em 5 dos 7 dias para a maioria dos perfis-piloto |
| H4 — Telegram é um canal aceitável | Participantes vinculam o bot e recebem uma entrega | Pelo menos 4 de 5 concluem sem considerar o canal uma barreira |
| H5 — A entrega gera ação útil | Pilotar por 2 semanas com link rastreado e feedback | Pelo menos metade abre uma vaga e 30% sinalizam utilidade ou candidatura |
| H6 — A operação cabe nos limites | Medir duração, chamadas, falhas e cota por execução | 6 de 7 execuções automáticas concluem sem falha permanente e dentro de 15 minutos |

Os percentuais de H1, H4 e H5 são sinais direcionais, não conclusões estatísticas. Resultados
qualitativos devem registrar comportamento observado e justificativa, não apenas respostas “sim”.

## 10. Dúvidas e decisões

### 10.1 Já respondidas pela implementação

| Dúvida | Resposta atual |
| --- | --- |
| Quantas vagas são entregues? | Até 5 por execução. |
| Existe nota mínima? | Sim, 40 por padrão e configurável. |
| Como a nota é calculada? | Fórmula determinística 50/15/10/15/10. |
| Qual é a ativação? | Primeira recomendação relevante entregue no Telegram. |
| Como evitar repetição entre dias? | Histórico de envios no Supabase. |
| Qual é o horário atual? | 07:23 BRT, disparado externamente. |
| O cadastro suporta vários usuários? | Sim. |
| A ausência de modalidade limita a nota? | Não globalmente; reduz apenas parte da logística. |
| Vaga sem stack declarada ganha nota cheia? | Não; recebe cobertura neutra de 0,35 desde 31/08, atrás de vaga detalhada e meio compatível. |

### 10.2 Decisões ainda abertas

1. Em dias sem vaga adequada, enviar uma mensagem ou permanecer em silêncio?
2. A nota mínima 40 é adequada para o piloto ou permite recomendações fracas?
3. A mesma régua funciona para desenvolvimento, dados, produto, suporte e infraestrutura?
4. Qual volume diário torna Adzuna e Gupy suficientes?
5. Feedback e clique rastreado entram antes da entrega ou serão simulados manualmente?
6. Qual política permite editar, pausar e excluir os dados do usuário?
7. Qual comportamento invalida o Telegram como canal inicial?
8. O professor espera prioritariamente arquitetura, demonstração, documentação ou métricas?

## 11. Vulnerabilidades e riscos

| Vulnerabilidade | Impacto | Situação | Mitigação ou decisão necessária |
| --- | --- | --- | --- |
| Cobertura baixa ou irregular | Alto | Uma coleta promissora, sem série suficiente | Executar H3 antes de adicionar fonte |
| Match Score incorreto | Alto | Não validado externamente | Comparação cega, justificativa e feedback |
| Vaga sem stack ganhar nota alta | Alto | Mitigada em 31/08 com cobertura neutra, após confirmação nos envios reais | Conferir a régua nova no teste humano das vinte vagas |
| Mudança no endpoint da Gupy | Alto | Risco permanente | Isolar coletor, alertar falha e continuar com Adzuna |
| Cota variável do Gemini | Alto | HTTP 429 já observado | Pré-filtro, lotes, interrupção segura e cenário pago |
| Job exceder 15 minutos | Alto | Execução de 30/08 ficou próxima do limite | Medir duração e reduzir volume por execução |
| Falha ou cancelamento do agendamento | Médio/alto | Sucessos recentes e um cancelamento posterior | Monitorar e executar o commit atual com sucesso |
| Falha silenciosa de coleta | Alto | Parcialmente tratada | Logs, job vermelho e alerta operacional |
| Não medir ação após a mensagem | Alto | Eventos reservados, sem emissão | Link rastreado ou feedback manual antes de H5 |
| Telegram não ser aceito | Médio | Conveniente para o grupo, não validado | Testar vínculo e entrega com usuários externos |
| Abandono entre site e Telegram | Alto | Funil instrumentado | Medir cada etapa e observar 5 sessões reais |
| Vagas falsas, expiradas ou enganosas | Alto | Não medido | Mostrar fonte/data, alertar inconsistência e receber reporte |
| Token reutilizável ou dados sem exclusão | Alto | Token aleatório; expiração e exclusão pendentes | Uso único/expiração e política de exclusão |
| Dependência de serviços gratuitos | Médio | Adequado ao piloto | Memória de cálculo com data e cenário pago |
| Crescimento de escopo | Alto | Risco atual | Aplicar o filtro de características da seção 12 |

## 12. Oportunidades e características pertinentes

Toda característica nova gera custo de manutenção, suporte, documentação, privacidade e carga
cognitiva. Antes de aprová-la, o grupo deve responder:

1. Ela reforça diretamente a promessa de encontrar vagas relevantes mais cedo?
2. Ela reduz uma incerteza importante do Pré-PRD?
3. Existe um teste manual ou menor que produza a mesma evidência?
4. Qual é o custo permanente, além do desenvolvimento inicial?
5. Qual item atual pode ser adiado para abrir espaço?

Para cada linha abaixo, o grupo deve escolher **aprovar agora**, **simular manualmente**,
**adiar** ou **rejeitar**.

| Característica | Problema ou hipótese atendida | Menor versão útil | Recomendação atual |
| --- | --- | --- | --- |
| Link rastreado para a vaga | Mede ação após a entrega | Redirecionamento que registra `vaga_aberta` | Aprovar agora ou simular no piloto |
| Feedback útil/irrelevante/candidatei-me | Valida relevância e H5 | Três ações simples ligadas à vaga | Aprovar agora ou coletar manualmente |
| Mensagem de dia sem vagas | Reduz incerteza sobre falha do serviço | Uma mensagem curta de estado | Decisão aberta |
| Editar perfil | Evita recomendações com dados antigos | Reabrir formulário existente | Aprovar após a entrega |
| Pausar e retomar | Dá controle e reduz rejeição ao canal | Um estado ativo/inativo | Aprovar após a entrega |
| Excluir conta e dados | Atende controle e privacidade | Fluxo autenticado de exclusão | Necessária antes de ampliar o piloto |
| Explicação detalhada da nota | Pode elevar confiança | Link ou detalhe opcional, sem alongar Telegram | Testar compreensão primeiro |
| Histórico de vagas | Ajuda a recuperar oportunidades | Lista simples das últimas recomendações | Adiar até H5 |
| Nova fonte de vagas | Pode aumentar cobertura | Um coletor adicional | Somente se H3 falhar |
| Alertas instantâneos | Pode reduzir tempo até candidatura | Regra para notas muito altas | Adiar |
| Lacunas de competências | Ajuda planejamento de estudos | Resumo de skills recorrentes ausentes | Adiar |
| Aplicação automática | Remove decisão e amplia riscos | Não há versão segura necessária ao MVP | Rejeitar |
| Scraping do LinkedIn | Aumentaria volume com risco de restrição | Não aplicável | Rejeitar |

## 13. Análise de viabilidade

| Dimensão | Avaliação | Evidência | Condição restante |
| --- | --- | --- | --- |
| Técnica | **Favorável** | Pipeline, fontes, IA, banco, Telegram, eventos e testes funcionando | Executar com sucesso o commit atual no Actions |
| Financeira | **Favorável no piloto acadêmico** | Serviços gratuitos suportam o volume atual | Registrar chamadas e cenário pago |
| Operacional | **Favorável com ressalvas** | Automação e persistência existem | Observar 7 dias, duração, cota e alertas |
| Prazo | **Favorável para a entrega técnica** | Núcleo e parte da Fase 2 concluídos | Não incluir novas expansões antes de 02/09 |
| Privacidade | **Parcialmente favorável** | Coleta mínima, RLS e token aleatório | Expiração, uso único e exclusão dos dados |
| Produto | **Inconclusiva** | Proposta coerente e prova técnica real | Entrevistas, matching humano, ativação e ação útil |

### 13.1 Decisão de continuidade

O projeto deve continuar como **piloto controlado**, porque a base técnica reduz risco suficiente
para testar a proposta com baixo custo. Não deve ser declarado produto validado nem receber
expansões relevantes antes das provas de produto.

### 13.2 Critérios para avançar ao PRD

O grupo pode avançar ao PRD quando:

- o commit atual executar com sucesso no GitHub Actions;
- a automação for observada durante a janela definida;
- H1 a H6 tiverem limites aprovados antes da análise;
- a cobertura conjunta for medida por sete dias;
- o teste humano de vinte vagas for concluído;
- pelo menos cinco estudantes externos forem observados ou entrevistados;
- as características da seção 12 forem classificadas;
- campos obrigatórios, expiração de token e exclusão de dados forem decididos;
- a memória de cálculo de custo for registrada;
- os critérios acadêmicos forem confirmados.

Se cobertura, confiança ou ativação falharem, o resultado não é “construir tudo”: o grupo deve
identificar a causa, testar a menor correção possível e reavaliar a viabilidade.

## 14. Próximos passos até a entrega

1. **30/08:** atualizar o Pré-PRD e aprovar dúvidas, limites e critérios de viabilidade.
2. **30–31/08:** executar no Actions a versão atual e registrar duração, coleta, filtro,
   avaliações, envios e falhas.
3. **Até 31/08:** realizar a comparação humana de vinte vagas, incluindo anúncios sem stack.
4. **Até 01/09:** consolidar a observação do cron e separar prova técnica de hipótese de produto.
5. **Até 01/09:** decidir se clique e feedback serão implementados ou simulados manualmente.
6. **Em 01/09:** congelar escopo, selecionar evidências e ensaiar demonstração.
7. **Em 02/09:** entregar a prova técnica e declarar explicitamente as hipóteses não validadas.
8. **Depois da entrega:** entrevistar e observar cinco estudantes, medir ativação e ação útil e
   elaborar o PRD apenas para a fase aprovada.

## 15. Perguntas prioritárias para a próxima reunião

1. A conclusão “viável como piloto, produto ainda não validado” representa o entendimento do grupo?
2. Os limites propostos para H1 a H6 serão aprovados ou alterados antes dos testes?
3. A cobertura neutra para habilidades ausentes se sustenta no teste das vinte vagas?
4. Clique rastreado e feedback entram agora ou serão coletados manualmente?
5. Qual é o comportamento em dias sem recomendação?
6. Qual risco impediria a apresentação ou a continuidade para o PRD?
7. Quais três evidências serão mostradas para comprovar viabilidade?
8. Quais características serão aprovadas, simuladas, adiadas ou rejeitadas?

---

**Síntese final:** a implementação demonstra viabilidade técnica e de prazo para um MVP acadêmico.
A decisão de produto permanece condicionada à cobertura recorrente, à confiança no matching, à
ativação de usuários externos e à observação de uma ação útil após a recomendação.
