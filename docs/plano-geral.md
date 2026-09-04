# Plano geral

**Data:** 04/09/2026

O que existe, o que falta e em que ordem. Os detalhes de cada frente moram nos documentos
apontados na seção 6; aqui é o mapa que amarra os três planos que hoje vivem separados.

## 1. Onde estamos

O código dos sprints 0 e 1 e de quase todo o 3 está no `main`. **Quase nada disso está no ar.**

| | Estado |
|---|---|
| Job diário | funcionando; entrega vaga todo dia às 07:23 |
| Custo de IA | resolvido; não cresce com o número de usuários |
| Landing | **não hospedada em lugar nenhum** |
| Edge Functions `ir` e `telegram-webhook` | escritas, **não publicadas** |
| Webhook do Telegram | registrado só com `message`; clique de botão não chega |
| Painel da conta | escrito na PR #9, migration não aplicada |

A distância entre "está no `main`" e "o estudante usa" é toda de infraestrutura, não de código.

## 2. O funil, evento por evento

| Evento | Quem grava | Funciona hoje |
|---|---|---|
| `landing_visualizada` | site | sim, mas ninguém visita: não há hospedagem |
| `cta_cadastro_aberto` | site | idem |
| `etapa_perfil_concluida` | site | idem |
| `etapa_habilidades_concluida` | site | idem |
| `etapa_preferencias_concluida` | site | idem |
| `conta_criada` | gatilho | sim |
| `email_confirmado` | gatilho | sim |
| `perfil_salvo` | gatilho e site | sim |
| `telegram_aberto` | site | idem à landing |
| `telegram_vinculado` | gatilho | sim |
| `primeira_recomendacao_enviada` | gatilho | sim |
| `vaga_aberta` | função `ir` | **não** — falta publicar e criar `URL_DE_RASTREIO` |
| `vaga_irrelevante` | webhook | **não** — falta publicar e registrar `callback_query` |
| `vaga_util` | ninguém | **não existe emissor** |
| `candidatura_iniciada` | ninguém | **não existe emissor** |

## 3. O buraco: a North Star segue incomputável

A North Star é *"percentual de estudantes ativados que encontram ao menos uma vaga útil por
semana"*. Vaga útil é definida em `CONTEXT.md` como recomendação com **feedback positivo** ou que
**gera candidatura**.

Nenhum dos dois eventos é gravado por linha nenhuma do código.

Como isso aconteceu: o formato original do feedback tinha 👍, 👎 e "Candidatei-me" por vaga, e
emitia os três eventos. Ao trocar por uma mensagem só com botões numerados — que resolveu a
poluição do chat — o "Candidatei-me" saiu do teclado e o "Todas serviram" ficou só apagando a
mensagem, sem gravar nada. A troca resolveu a cadência e removeu em silêncio os dois eventos que
mais importam.

Duas saídas, e a escolha muda o produto:

- **"Todas serviram" passa a gravar `vaga_util`** para as vagas do dia. Barato, mas é sinal fraco:
  não reclamar não é o mesmo que ter servido.
- **A pergunta do dia seguinte**, só para as vagas que a pessoa abriu: *"ontem você abriu X.
  Serviu?"* com 👍, 👎 e "já me candidatei". Sinal forte, porque só pergunta onde houve interesse
  real, e é onde o "Candidatei-me" faz sentido. Depende de `vaga_aberta` estar funcionando.

Recomendação: a segunda, aceitando que a North Star só fica medível depois que o link rastreável
estiver no ar. A primeira como paliativo se o piloto começar antes.

## 4. O que falta, em ordem

### Fase A — destravar (tudo depende disto)

O domínio é o gargalo único: ele libera três coisas de uma vez.

```
domínio ─┬─ hospedagem da landing ── URL_DA_LANDING ── deploy da função ir ── vaga_aberta
         ├─ contato@ ─────────────── política de privacidade completa
         └─ Resend ───────────────── confirmação decente + recuperação de senha
```

1. Comprar o domínio e decidir em nome de quem fica
2. Publicar a landing
3. Criar `URL_DA_LANDING` no Supabase e `URL_DE_RASTREIO` nos secrets do GitHub
4. Publicar as duas Edge Functions
5. Registrar o webhook com `allowed_updates` incluindo `callback_query`
6. Aplicar a migration `0013`, revisada com os 60 dias

Do 1 ao 5 nada é código. O 6 depende da revisão da PR #9.

### Fase B — cadastro, consentimento e documentos

Detalhado em `plano-cadastro-e-privacidade.md`. Resumo da ordem: escrever os dois documentos,
publicá-los, migration do consentimento e da exclusão em duas etapas, o passo diário que apaga
depois de 60 dias, o cadastro com os dois checkboxes e o olho na senha, o gatilho que cria o perfil
na confirmação, a tela de reenvio, o Turnstile e o botão de baixar os dados.

### Fase C — fechar a medição

7. Decidir entre as duas saídas da seção 3 e implementar
8. Rodar `python -m radar metricas` com dado real e conferir se o funil fecha de ponta a ponta

Sem a fase C o piloto roda e não mede o que importa.

### Fase D — piloto

Descrito no sprint 4 de `auditoria-rcd.md`: 10 a 20 estudantes, duas semanas, cinco entrevistas,
canais identificados. Só faz sentido depois da fase C.

## 5. Decisões em aberto

| Assunto | Situação |
|---|---|
| Viés do ranking: anúncio raso tira nota maior | decidido esperar dado do piloto; evidência já registrada na seção 7 da auditoria |
| Dados pessoais no histórico do git | trocar o arquivo não apagou o histórico; reescrever quebra os clones — decisão do grupo |
| Apagar conta abandonada | fora do escopo agora; revisitar depois do piloto |
| Sprint 2 (busca imediata após o vínculo) | não começou; meta de 15 minutos até a primeira entrega segue não atendida |

## 6. Onde está cada coisa

| Documento | Para quê |
|---|---|
| `auditoria-rcd.md` | os catorze achados com situação, os sprints e o viés do ranking |
| `plano-cadastro-e-privacidade.md` | as sete decisões de cadastro, consentimento e LGPD |
| `plano-melhorias-rcd.md` | a estratégia RCD original, de onde tudo saiu |
| `metricas.md` | as consultas do funil e as definições |
| `arquitetura.md` | as camadas e as decisões técnicas |
| `CONTEXT.md` | o vocabulário: o que conta como ativação, vaga útil, candidatura |
