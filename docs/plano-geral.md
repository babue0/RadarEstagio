# Plano geral

**Data:** 05/09/2026

O que existe, o que falta e em que ordem. Os detalhes de cada frente moram nos documentos
apontados na seção 6; aqui é o mapa que amarra os três planos que hoje vivem separados.

## 1. Onde estamos

O código dos sprints 0 e 1 e de quase todo o 3 está no `main`. **Quase nada disso está no ar.**

| | Estado |
|---|---|
| Job diário | funcionando; entrega vaga todo dia às 07:23 |
| Custo de IA | resolvido para coorte homogênea: a mesma vaga não é reextraída. Perfil de cidade ou área nova **amplia o conjunto elegível** — medir antes do piloto |
| Landing | **não hospedada em lugar nenhum** |
| Edge Function `telegram-webhook` | publicada em 29/08; a versão com feedback **não foi republicada** |
| Edge Function `ir` | escrita, **nunca publicada** |
| Webhook do Telegram | `allowed_updates` já inclui `callback_query`, corrigido em 04/09 |
| Painel da conta | no ar no `main`; a `0013` **foi aplicada em 05/09** |
| Exclusão em duas etapas | pronta e aplicada: marca, para de entregar, apaga em 60 dias |
| Domínio | **comprado** (Cloudflare Registrar), ainda não apontado para lugar nenhum |
| Confirmação de e-mail | remetente ainda é o do Supabase; **não sustenta 10 a 20 cadastros no mesmo dia** |

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
| `vaga_irrelevante` | webhook | **não** — falta republicar a função com o feedback |
| `vaga_util` | ninguém | **não existe emissor** |
| `candidatura_iniciada` | ninguém | **não existe emissor** |

## 3. O buraco: a North Star segue incomputável

A North Star é *"percentual de estudantes ativados que encontram ao menos uma vaga útil por
semana"*. Vaga útil é definida em `CONTEXT.md` como recomendação com **feedback positivo** ou que
**gera candidatura**.

Nenhum dos dois eventos é gravado por linha nenhuma do código.

**Nenhum commit alcançável jamais gravou os dois.** Não é regressão: é lacuna que atravessou o
sprint inteiro sem ninguém notar, porque o catálogo da `0005` já previa os nomes e a instrumentação
parecia completa.

O que o código faz hoje, e dá para conferir: o teclado numerado só oferece recusa e "Todas
serviram", e o "Todas serviram" apenas apaga a mensagem, sem gravar evento. O "Candidatei-me" foi
deliberadamente deixado de fora do teclado diário, para a pergunta do dia seguinte — que ainda não
existe.

Duas saídas foram consideradas, e nenhuma delas foi a escolhida:

- **"Todas serviram" passa a gravar `vaga_util`** para as vagas do dia. Barato, mas sinal fraco:
  não reclamar não é o mesmo que ter servido.
- **A pergunta do dia seguinte**, só para as vagas que a pessoa abriu. Sinal forte, mas depende de
  `vaga_aberta` estar no ar e acrescenta uma segunda notificação por dia.

**Decidido em 05/09: o feedback é por vaga, dentro da própria mensagem.** Os números deixam de
significar recusa e passam a abrir o feedback daquela vaga. A mensagem diária termina em "Deixe seu
feedback 👇" com um número por recomendação, e o clique abre uma segunda mensagem, com a vaga e
seis opções:

| Botão | O que grava |
|---|---|
| 👍 Essa serviu | `vaga_util` |
| 👎 A nota não fez sentido | `vaga_irrelevante` · `motivo_nota` |
| 👎 Não é da minha área | `vaga_irrelevante` · `motivo_area` |
| 👎 Pedem demais | `vaga_irrelevante` · `motivo_exigencia` |
| 👎 Local ou modalidade | `vaga_irrelevante` · `motivo_logistica` |
| 👎 Já vi essa | `vaga_irrelevante` · `motivo_repetida` |

**Não precisa de migration**: `vaga_util` já está no enum da `0005` e o motivo vai em
`propriedades`, que é `jsonb` sem restrição de conteúdo. É mudança só de código, na
`telegram-webhook` e no formatador da mensagem.

`motivo_nota` não existia em nenhuma das duas saídas descartadas e é o ganho menos óbvio da
escolha. Ele é o sinal que a seção 7 da `auditoria-rcd.md` exige para mexer nos pesos do ranking:
a recusa de hoje não distingue "a vaga não serve para mim" de "a vaga serve, a nota é que está
errada", e só a segunda justifica ajustar peso.

**`candidatura_iniciada` fica sem emissor, e isso é deliberado.** O botão "Já me candidatei" saiu
do teclado porque quem se candidata também acha que a vaga serviu — o 👍 cobre a North Star
sozinho. O custo é que **Candidatura atribuída**, definida no `CONTEXT.md`, deixa de ser medível, e
a definição de vaga útil lá ("feedback positivo **ou** início de candidatura") passa a valer só
pela primeira metade. Alinhar o `CONTEXT.md` a isso, ou recuperar a captura junto da pergunta do
dia seguinte, se o piloto mostrar que faz falta.

## 4. O que falta, em ordem

### Fase A — destravar (tudo depende disto)

**O domínio não trava a medição.** O Cloudflare Pages publica em `*.pages.dev`, e a função `ir`
exige apenas que `URL_DA_LANDING` aponte para algum lugar — não para um domínio próprio. Dá para
destravar `vaga_aberta` hoje, sem comprar nada.

O domínio trava outra coisa: o **e-mail**. Sem ele não há endereço de contato para a política de
privacidade nem remetente próprio para o Resend.

```
publicar no *.pages.dev ── URL_DA_LANDING ── deploy da ir ── vaga_aberta
domínio ─┬─ contato@ ───── política de privacidade completa
         └─ Resend ─────── remetente próprio da confirmação
```

1. Publicar a landing no Cloudflare Pages, no endereço provisório
2. Registrar esse endereço em **Site URL e Redirect URLs** do Supabase Auth — sem isso o
   `emailRedirectTo` da confirmação não volta para a página publicada
3. Criar `URL_DA_LANDING` no Supabase e `URL_DE_RASTREIO` nos secrets do GitHub
4. Publicar a função `ir` e **republicar** a `telegram-webhook` com o feedback
5. ~~Comprar o domínio~~ — feito em 05/09. Publicar direto no domínio próprio dispensa refazer os
   passos 2 e 3 depois

Nada disso é código. A migration `0013` **saiu desta fase**: foi reescrita com os 60 dias,
revisada, corrigida e aplicada em 05/09.

**O domínio mudou o peso do e-mail.** Enquanto o plano supunha o endereço provisório, o remetente
do Supabase era ruim mas tolerável. Agora que o cadastro pode ir ao ar num domínio próprio, o
limite de poucos e-mails por hora do remetente compartilhado passa a ser o que separa o piloto de
funcionar: numa tarde com 10 a 20 estudantes se cadastrando, a maioria não recebe a confirmação.
Entrar é imune — `signInWithPassword` não passa por e-mail nem por redirect —, mas ninguém entra
antes de se cadastrar.

### Fase B — cadastro, consentimento e documentos

Detalhado em `plano-cadastro-e-privacidade.md`. **Esta fase começou pelo fim**: a exclusão em duas
etapas, o apagamento diário e os textos do painel saíram em 05/09 e estão aplicados. O que sobrou é
o bloco do consentimento — os dois documentos, as colunas de aceite, os checkboxes, o gatilho que
cria o perfil na confirmação, a tela de reenvio, o Turnstile, baixar os dados e recuperar a senha.

### Fase C — fechar a medição

7. Decidir entre as duas saídas da seção 3 e implementar o emissor
8. Corrigir o `python -m radar metricas`, que hoje **não fecha o funil**: a consulta começa nos
   perfis criados e ignora visita, etapas do cadastro e confirmação; conta utilidade e candidatura
   separadamente, sem formar a união que define vaga útil; e não recorta por semana, que a North
   Star exige. Implementar os emissores não conserta isso sozinho.

   Mais duas correções, achadas em 05/09 na revisão contra as skills:

   - **`vagas_abertas` conta cliques, não vagas.** É `count(*)` sobre os eventos, e o próprio
     `metricas.md` diz que clique repetido gera linha repetida de propósito. Uma pessoa abrindo a
     mesma vaga três vezes vira três.
   - **O critério de mexer no ranking não tem denominador.** A seção 7 da auditoria reage a
     `vaga_irrelevante` concentrado em anúncio raso, mas a consulta não conta quantas recomendações
     de cada grupo foram entregues — uma categoria concentra recusa por concentrar entrega. Sem o
     denominador, a evidência não sustenta a decisão que ela deveria destravar.
9. Rodar com dado real e conferir

Sem a fase C o piloto roda e não mede o que importa.

### Fase D — entrega imediata (sprint 2)

**Decidido em 05/09: o sprint 2 entra antes do piloto.** A auditoria trata a demora até a primeira
entrega — hoje até 24 horas, contra a meta de 15 minutos — como bloqueador, e o
`plano-melhorias-rcd.md` exige que os limites sejam aprovados antes de começar. Dispensar o
bloqueador em silêncio era a pior das saídas possíveis.

A regra acordada: **quem vincula o Telegram recebe a primeira mensagem na hora.** O gatilho é o
clique no botão do Telegram, não o cadastro nem o login — antes dele não existe `chat_id` para onde
enviar. A exceção é quem vincula na hora anterior ao disparo diário, entre **06:23 e 07:23** de
Brasília: esse espera o job das 07:23, para não receber duas mensagens na mesma manhã.

10. Fazer a `telegram-webhook` disparar a execução ao gravar o `chat_id`, respeitando a janela
11. Rodar o pipeline para um perfil só, sem afetar a execução diária dos demais

O trabalho não está em `radar/` e não é trivial: hoje **nada roda sob demanda**, o job é um cron no
GitHub Actions. Quem descobre o vínculo é a Edge Function `telegram-webhook`, então é ela que
precisa disparar um `repository_dispatch` no Actions — o que exige um token com permissão de
escrita, o mesmo obstáculo que devolveu 403 na rotina da nuvem.

### Fase E — piloto

Descrito no sprint 4 de `auditoria-rcd.md`: 10 a 20 estudantes, duas semanas, cinco entrevistas,
canais identificados. Só faz sentido depois das fases C e D.

## 5. Decisões em aberto

| Assunto | Situação |
|---|---|
| Viés do ranking: anúncio raso tira nota maior | decidido esperar dado do piloto; evidência já registrada na seção 7 da auditoria |
| Dados pessoais no histórico do git | trocar o arquivo não apagou o histórico; reescrever quebra os clones — decisão do grupo |
| Apagar conta abandonada | fora do escopo agora; revisitar depois do piloto |
| Sprint 2 (busca imediata após o vínculo) | **decidido em 05/09: entra antes do piloto**, com a janela de 06:23 a 07:23 como exceção. Virou a fase D |
| Remetente do e-mail | **decidido em 05/09: o Resend entra antes do piloto.** Sem remetente próprio o cadastro não sustenta 10 a 20 pessoas na mesma tarde |

## 6. Onde está cada coisa

| Documento | Para quê |
|---|---|
| `auditoria-rcd.md` | os catorze achados com situação, os sprints e o viés do ranking |
| `plano-cadastro-e-privacidade.md` | as sete decisões de cadastro, consentimento e LGPD |
| `plano-melhorias-rcd.md` | a estratégia RCD original, de onde tudo saiu |
| `metricas.md` | as consultas do funil e as definições |
| `arquitetura.md` | as camadas e as decisões técnicas |
| `CONTEXT.md` | o vocabulário: o que conta como ativação, vaga útil, candidatura |
