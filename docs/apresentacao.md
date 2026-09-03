# Roteiro da apresentação — Radar de Estágio

**Status:** preparado em 30/08/2026 e revisado em 02/09/2026
**Uso:** alinhamento técnico e de produto do MVP  
**Público assumido:** equipe, professor e avaliadores do projeto

## Mensagem central

O Radar já comprova tecnicamente o fluxo de coleta, filtragem, avaliação e entrega de vagas.
Ainda não comprova que estudantes confiam nas recomendações, aceitam o Telegram ou recebem
valor rápido o suficiente para continuar usando o produto. A próxima decisão deve ser tomada
com base em ativação operacional, ativação de produto e um piloto com usuários.

## Sequência sugerida

| Bloco | Mensagem principal | O que precisa ficar claro |
| --- | --- | --- |
| 1. Contexto | A busca manual consome tempo e espalha a atenção por vários portais. | O problema é recorrente e tem um custo concreto para o estudante. |
| 2. Prova técnica | O fluxo principal funciona de ponta a ponta. | A implementação existe; isso não é ainda prova de utilidade. |
| 3. Hipóteses | A aceitação do produto ainda precisa ser observada. | Confiança, canal, cobertura, ação e custo continuam em aberto. |
| 4. Ativação | A entrega confirma o fluxo; a abertura confirma o primeiro interesse. | Ativação operacional e ativação de produto são marcos diferentes. |
| 5. Tempo até o valor | O maior risco de produto é o usuário esperar demais pelo primeiro resultado. | A primeira entrega precisa acontecer em minutos e gerar interação. |
| 6. Validação | Cada incerteza terá um teste curto e um sinal de decisão. | O próximo passo é medir comportamento real, não adicionar escopo. |
| 7. Decisão | Avançar depende de ativação de produto e utilidade observadas. | Resultados negativos orientam correção ou redução de escopo. |

## 1. Contexto e promessa

### Texto da apresentação

> O Radar coleta oportunidades de estágio, elimina anúncios claramente incompatíveis,
> compara cada vaga com o perfil do estudante e entrega uma lista curta, ranqueada e explicada
> pelo Telegram.

### Limite da promessa

O Radar reduz a busca e a triagem manual, mas não se candidata pelo estudante. O produto atual
também não promete aprender com feedback nem oferecer edição do perfil antes de essas
capacidades existirem na interface.

Fonte: [`docs/pre-prd.md`](pre-prd.md) e [`README.md`](../README.md).

## 2. O que foi tecnicamente comprovado

### Fluxo implementado

```text
Adzuna + Gupy
  → deduplicação
  → pré-filtro por regras
  → avaliação em lotes com nota de 0 a 100
  → ranking
  → mensagem com justificativa no Telegram
```

O sistema também possui cadastro web, persistência do perfil no Supabase, múltiplos usuários,
vínculo por token aleatório entre perfil e chat do Telegram e registro da ativação operacional.

### Evidências disponíveis

- Em 30/08/2026, uma coleta real com dois perfis presenciais no Rio produziu **703 vagas únicas**:
  356 da Adzuna e 347 da Gupy.
- O filtro geográfico encontrou **210 vagas no Rio** e o pré-filtro deixou **55 candidatas**
  para avaliação, contra 2 antes do ajuste de cobertura.
- A mensagem real do Telegram contém localização, modalidade, fonte, data, nota, justificativa,
  pontos a favor e contra, alerta opcional e link original.
- A suíte local possui **318 testes passando**; 4 testes de integração dependem de um PostgreSQL
  de teste.

### O que ainda é uma verificação técnica pendente

- Confirmar a execução da versão atual no GitHub Actions depois da inclusão da Gupy.
- Observar o agendamento automático por vários dias.
- Registrar volume coletado, filtrado, avaliado, enviado e eventuais falhas.

Fontes: [`docs/pre-prd.md`](pre-prd.md), [`docs/passos-realizados.md`](passos-realizados.md) e
[`README.md`](../README.md).

## 3. O que ainda é hipótese de produto

| Hipótese | Pergunta que precisa de resposta | Teste planejado |
| --- | --- | --- |
| H1 — Seleção economiza esforço | Estudantes preferem receber uma lista filtrada a procurar tudo manualmente? | Entrevistas com 15–20 estudantes. |
| H2 — O matching orienta a triagem | A nota e a justificativa são confiáveis o bastante para decidir onde olhar primeiro? | Comparação cega de 20 vagas com avaliações humanas. |
| H3 — Há cobertura suficiente | Adzuna e Gupy produzem oportunidades úteis para o nicho inicial? | Coleta diária durante 7 dias. |
| H4 — Telegram é aceitável | O canal facilita a rotina ou cria uma barreira? | Entrevistas e teste da entrega. |
| H5 — A entrega gera ação | Uma recomendação faz o estudante abrir, salvar ou iniciar candidatura? | Piloto com recomendações durante 2 semanas. |
| H6 — A operação cabe no limite | A frequência de coleta e avaliação cabe na cota e no custo disponíveis? | Medição por execução e por usuário com ativação operacional. |

Ainda não há resultado de usuários para declarar essas hipóteses como confirmadas. Feedback,
edição e pausa de entregas são recursos posteriores; portanto, não devem aparecer como prova da
experiência atual.

Fonte: [`docs/pre-prd.md`](pre-prd.md), seção “Hipóteses e testes de baixo custo”.

## 4. Marcos de ativação

### Definição

> **Ativação operacional = primeira recomendação entregue com sucesso no Telegram.**
>
> **Ativação de produto = primeira abertura de uma vaga recomendada.**

### O que não conta como ativação

- criar a conta;
- concluir o cadastro;
- confirmar o e-mail;
- vincular o Telegram;
- receber uma mensagem dizendo que nenhuma vaga foi encontrada.

A fonte de verdade da ativação operacional é `perfis.ativado_em`. O campo é preenchido somente
depois que o Telegram aceita a entrega e junto do registro em `envios`; ele não é sobrescrito em
reprocessamentos. A ativação de produto ainda depende da emissão de `vaga_aberta`.

### Métricas para acompanhar

- **Taxa de ativação operacional em 7 dias:** perfis que receberam a primeira recomendação dentro da
  janela, entre as coortes maduras.
- **Tempo até a primeira entrega:** mediana de horas entre `criado_em` e `ativado_em`.
- **Tempo até o valor:** mediana entre `criado_em` e o primeiro `vaga_aberta`, quando o evento
  estiver implementado.
- **Funil:** perfil salvo → Telegram vinculado → primeira recomendação → vaga aberta → ação útil
  ou candidatura iniciada.

Fonte: [`docs/metricas.md`](metricas.md).

## 5. Risco: tempo até o primeiro valor

O produto promete que o estudante informa o perfil uma vez e recebe oportunidades compatíveis.
Se a pessoa precisa esperar a próxima execução diária, ou recebe apenas uma confirmação sem uma
vaga útil, o benefício ainda não foi experimentado. Isso pode causar abandono entre o vínculo do
Telegram e a primeira recomendação.

### Direção de mitigação

Após o vínculo, a jornada desejada é:

```text
Telegram vinculado → busca específica → recomendação entregue → vaga aberta → ação útil
```

### Metas iniciais — ainda não são resultados

- tempo mediano até a primeira entrega abaixo de **15 minutos**;
- evolução posterior para menos de **5 minutos**;
- pelo menos **80% dos usuários vinculados** recebendo uma recomendação em até 24 horas.

Quando não houver uma vaga adequada, o perfil não deve ser ativado. A mensagem precisa explicar
que nenhuma oportunidade segura foi encontrada e informar a próxima busca, sem empurrar uma vaga
ruim apenas para gerar o evento.

Fonte: [`docs/plano-melhorias-rcd.md`](plano-melhorias-rcd.md), Fase 2, e
[`docs/metricas.md`](metricas.md).

## 6. Plano de validação com usuários

### Preparação do funil

Instrumentar a sequência `landing_visualizada → conta_criada → perfil_salvo → telegram_vinculado
→ primeira_recomendacao_enviada → vaga_aberta → vaga_util → candidatura_iniciada`. Em cada etapa,
registrar quantidade, falhas e tempo decorrido.

### Testes de baixo custo

| Ordem | Participantes/período | Evidência observada | Sinal inicial de aprovação |
| --- | --- | --- | --- |
| 1. Entrevistas | 15–20 estudantes | Como procuram, o que consideram relevante e se aceitam Telegram. | Pelo menos 60% relatam intenção de uso recorrente e não veem o canal como barreira. |
| 2. Matching | 20 vagas reais, avaliadas por 3 pessoas sem ver a nota da IA | Concordância entre a classificação humana e o sistema. | Pelo menos 75% de concordância. |
| 3. Cobertura | Adzuna e Gupy por 7 dias | Vagas coletadas, únicas, filtradas, relevantes e falhas por fonte. | Vagas relevantes na maioria dos dias úteis; o limite numérico deve ser definido antes do teste. |
| 4. Primeira entrega | Usuários vinculados no piloto | Tempo até a entrega, ativação operacional em 24h/7d e perdas entre perfil e Telegram. | Maioria com recomendação em 24h e tempo dentro da meta aprovada. |
| 5. Utilidade | Grupo piloto por 2 semanas | Aberturas, salvamentos, “faz sentido”, problemas e candidaturas iniciadas. | Ações úteis observáveis; o limite numérico deve ser definido antes do teste. |
| 6. Operação | Cada execução | Chamadas de IA, cota, custo, duração e erros de coleta/envio. | Permanecer dentro do limite operacional definido. |

O piloto principal deve incluir **10–20 estudantes de tecnologia**, buscando o primeiro estágio
e dispostos a usar o Telegram por duas semanas. Cada participante deve ser acompanhado desde a
landing até a primeira candidatura ou até o motivo de abandono ficar registrado.

## 7. Decisão ao final do piloto

Avançar para retenção e monetização somente se houver evidência conjunta de:

- funil sem falhas bloqueantes;
- recomendação entregue em até 24 horas para a maioria dos usuários vinculados;
- tempo mediano até a primeira entrega dentro do limite aprovado;
- recomendações consideradas úteis ou capazes de gerar ação;
- operação dentro das cotas e com falhas observáveis.

Se a ativação operacional falhar, a prioridade é reduzir o tempo até a entrega, corrigir o vínculo
ou melhorar cobertura. Se a entrega estiver rápida, mas a ativação de produto ou a utilidade
falhar, a prioridade é revisar pré-filtro, matching e explicação.
Novos recursos não devem entrar antes de responder a essas incertezas.

## Demonstração ao vivo

1. Mostrar a promessa atual da landing.
2. Preencher um perfil de teste válido.
3. Confirmar o vínculo com o Telegram.
4. Mostrar uma mensagem real com fonte, data, modalidade, localização, nota e justificativa.
5. Explicar que a mensagem demonstra o funcionamento técnico, enquanto ativação de produto,
   utilidade e retenção dependem do piloto.
