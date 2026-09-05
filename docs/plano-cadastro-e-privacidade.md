# Plano — cadastro, consentimento e privacidade

**Data:** 05/09/2026 (revisto)

**Escopo:** o cadastro de ponta a ponta, os dois documentos legais e o que a LGPD exige do
produto. Nasceu da conversa sobre o e-mail de confirmação parecer amador e cresceu para cobrir
tudo que fica entre a landing e a primeira vaga entregue.

## 1. Decisões tomadas

| # | Assunto | Decisão |
|---|---|---|
| 1 | Controlador dos dados | Os três integrantes do projeto |
| 2 | Canal de contato | Domínio comprado em 05/09; falta criar o endereço e preencher o espaço reservado |
| 3 | Retenção | Enquanto a conta existir. Excluir apaga em cascata o que está ligado à conta |
| 4 | Portabilidade | Botão de baixar os próprios dados, por função no banco |
| 5 | Menor de idade | Fora do escopo; o documento não trata |
| 6 | Confirmação de e-mail | **Mantida.** Sem ela o endereço nunca é verificado e a recuperação de conta fica apoiada em algo que ninguém provou existir |
| 7 | Exclusão de conta | Marca agora, apaga em 60 dias, com direito a arrependimento |

A decisão 6 contraria a recomendação inicial de remover a confirmação para encurtar o funil. O
argumento que venceu: o produto pretende enviar e-mail no futuro, e enviar para endereço não
verificado gera bounce, o que derruba a reputação do domínio e faz *todos* os e-mails caírem em
spam, inclusive os de confirmação. Deixa de ser preferência e vira requisito técnico.

## 2. O que muda para o estudante

### Cadastro

```
Etapa 1   curso e período
Etapa 2   habilidades
Etapa 3   áreas, cidade, modalidade, e-mail, senha (com olho para revelar)
          [ ] Aceito os Termos de Uso e a Política de Privacidade   ← bloqueia
          [ ] Quero receber e-mails ocasionais do Radar             ← opcional
          "Criar conta e continuar"  →  Turnstile
```

Dois checkboxes, não um. São coisas diferentes: aceitar os termos é porta jurídica e impede
seguir; consentir e-mail é opcional, começa desmarcado e tem que ser reversível no painel.

### Confirmação em qualquer aparelho

Hoje, entre criar a conta e confirmar o e-mail, o perfil vive só no `localStorage`. Quem se
cadastra no notebook e confirma no celular volta para um site que não sabe quem é — e o código
retorna calado, sem dizer nada.

O perfil passa a viajar com a conta: vai em `options.data` do `signUp`, chega em
`auth.users.raw_user_meta_data` sem passar por RLS, e um gatilho cria a linha em `perfis` quando
`email_confirmed_at` deixa de ser nulo. Mesmo padrão dos gatilhos que a `0005` já usa.

Ganho lateral: confirmar no celular vira o **melhor** caminho, porque o passo seguinte é vincular
o Telegram, que está no celular.

### Tela de reenvio

Três caminhos levam a ela: não recebeu, o link expirou, ou tentou entrar sem ter confirmado. O
campo de e-mail é editável e vem preenchido quando se sabe qual é — sem isso, quem clica num link
expirado em outro aparelho chega sem nenhum contexto.

O botão trava por um minuto depois do envio, porque o Supabase limita o reenvio e o botão pareceria
quebrado.

### Exclusão com arrependimento

**Implementado e aplicado em 05/09**, com uma diferença importante do que este plano previa:
`ativo` **não** é tocado.

```
clica em excluir
   ↓  imediato
excluida_em = now()       sai do where do job, que exige excluida_em is null
telegram_chat_id = null   nada mais chega no Telegram; token_vinculo roda junto
   ↓  60 dias
auth.users apagado; a cascata leva perfil, avaliações, envios e eventos ligados à conta
mais os eventos anônimos daquelas sessões, que cascata nenhuma alcança
```

**Por que `ativo` ficou de fora.** Ele já significava duas coisas — pausa pedida pelo dono e pausa
por falha de envio. Usá-lo também para exclusão fazia o gatilho da `0005` emitir `entregas_pausadas`
para quem saiu de vez, misturando churn definitivo com pausa temporária no funil; e o cancelamento,
que punha `ativo = true` sem saber o estado anterior, religava quem tinha pausado antes de excluir.

**Por que o chat é solto.** `telegram_chat_id` é `unique`. Segurá-lo durante a carência reservava o
Telegram da pessoa por 60 dias contra uma conta nova dela mesma, com "chat de outra conta" e sem
saída. O preço é que quem cancelar precisa vincular o Telegram de novo — decisão do Igor em 05/09.

A policy de update também passou a recusar escrita em perfil marcado: esconder botão é cortesia,
não é o que garante a regra.

A primeira etapa é o que a pessoa pediu: parar de processar. A segunda é o apagamento definitivo.
Entre as duas ela pode entrar e cancelar.

**O que "parar na hora" ainda não cobre.** A quarta já foi resolvida; as três primeiras seguem
abertas e foram reconfirmadas pela revisão de 05/09:

- O pipeline lê os usuários **antes** de coletar e guarda o `chat_id` em memória. Quem exclui
  durante a execução ainda recebe a mensagem daquele dia. Revalidar antes de enviar.
- A função `ir` registra clique de link antigo sem consultar `ativo` nem `excluida_em`. Durante os
  60 dias ela continuaria gravando `vaga_aberta` de quem pediu para sair.
- O mesmo vale para o `telegram-webhook`: `envioDoToken` e `registrarRecusa` gravam
  `vaga_irrelevante` e respondem no Telegram sem verificar exclusão, `ativo` ou se o `chat_id`
  ainda está vinculado. Clicar num botão antigo continuaria processando dado de quem pediu para
  sair.
- ~~Os eventos anteriores ao login têm só `sessao_id` e nenhuma cascata os alcança.~~ **Resolvido
  em 05/09.** A rotina apaga por `sessao_id`, mas **só os que estão sem dono**: o `sessao_id` mora
  no `localStorage` e sobrevive a logout, então duas contas no mesmo navegador dividem sessão, e a
  primeira versão levava junto o funil de quem emprestou o computador.

Os 60 dias precisam de justificativa perante a LGPD — guardar dado "por precaução" não basta.
Permitir o arrependimento é a justificativa, e vai escrita na política.

**Isso obriga alguém a apagar no 61º dia.** O passo entra no job diário, que já roda às 07:23 e já
tem `DATABASE_URL`. Sem isso o documento promete o que não acontece.

## 3. Os dois documentos

O que os torna diferentes de política copiada da internet é serem **verdadeiros**. O que o sistema
faz está todo lido:

**Dados coletados** — e-mail, senha (o Supabase guarda só o hash), curso, período, habilidades,
cidade, modalidade, áreas de interesse e o `chat_id` do Telegram. Mais eventos de funil, que usam
identificador de sessão anônimo e não guardam dado pessoal nas propriedades.

A cidade merece nota à parte: ela sai do sistema. O coletor monta a busca por cidade para os
perfis presenciais e híbridos, então Adzuna e Gupy recebem esse campo — sem saber de quem é. A
política precisa dizer isso; escrever "nada seu é enviado" seria falso.

**Com quem são compartilhados**

| Quem | O que recebe |
|---|---|
| Supabase | tudo — é onde o banco e as contas moram |
| Telegram | o `chat_id` e o conteúdo das mensagens |
| Google Gemini | **apenas o texto dos anúncios de vaga** |
| Adzuna e Gupy | **a cidade** dos perfis presenciais e híbridos, usada como termo de busca; nenhum identificador individual |
| Cloudflare | tráfego do site e o Turnstile |
| GitHub Actions | **todo o perfil**: o job diário roda em runner do GitHub com a `DATABASE_URL` e carrega curso, período, habilidades, cidade, modalidade, interesses e `chat_id` para a memória de lá |

A linha do Gemini é um ponto forte e verificável: desde a separação entre extração e pontuação, em
03/09/2026, o perfil deixou de ir no prompt. Antes seguiam curso, período e habilidades; hoje a IA
lê só o anúncio.

**Direitos** — correção e exclusão já existem no painel. Portabilidade entra com o botão de baixar
os dados. O documento não promete nada além disso.

## 4. Ordem de implementação

**A ordem foi quebrada na prática**: o bloco da exclusão saiu primeiro, porque era o que já tinha
migration escrita, e o bloco do consentimento não começou. O que está feito, feito, e o resto segue
a ordem original.

1. Escrever os dois documentos; Igor e Ian revisam antes de qualquer código
2. `web/termos.html` e `web/privacidade.html`, linkados no rodapé
3. Migration: `aceita_emails`, `termos_aceitos_em`, versão dos termos, `excluida_em`; a
   `excluir_minha_conta()` deixa de apagar e passa a marcar; função para cancelar a exclusão
   — **metade feita em 05/09**: `excluida_em`, marcar e cancelar estão na `0013`, aplicada. As três
   colunas de consentimento não existem
4. ~~Passo diário que apaga o que passou dos 60 dias~~ — **feito**
5. Cadastro: os dois checkboxes, o olho na senha, o perfil em `options.data`
6. Gatilho que cria o perfil na confirmação
7. Tela de reenvio
8. Turnstile
9. Botão de baixar os dados
10. **Recuperação de senha** — não existe hoje, nem tela nem chamada. Configurar o Resend não
    entrega isso sozinho: falta o link "esqueci minha senha", a chamada
    `resetPasswordForEmail`, e a tela que recebe a volta e define a senha nova
11. **Textos e controles do painel** — **metade feita em 05/09**: as frases "Não dá para desfazer"
    e "Seus dados foram apagados" saíram, entraram a data do apagamento definitivo e o botão de
    cancelar. Falta o **controle para revogar o consentimento de e-mail**, que depende da coluna do
    passo 3
12. **Retorno da confirmação** — o `resumeConfirmedSignup` desiste quando não acha perfil no
    navegador, antes de consultar sessão e banco. Com o gatilho criando o perfil, ele precisa
    consultar primeiro. E o `sessao_id` do aparelho onde a pessoa se cadastrou não viaja para o
    gatilho: confirmar no celular cria o perfil e deixa o começo do funil do notebook
    desconectado

Do 3 em diante, um commit por decisão e suíte verde em comando separado, como manda o `CLAUDE.md`.

A migration `0013` **foi aplicada em 05/09** e não pode mais ser editada no lugar: o que faltar do
passo 3 entra numa `0014`. Ela passou por duas revisões antes de subir; a segunda achou três
defeitos reais que a primeira não viu, o que vale repetir nas próximas.

## 5. Dependências externas

| O quê | Trava o quê |
|---|---|
| ~~Domínio~~ | **comprado em 05/09.** Falta criar o endereço de contato e apontar o DNS |
| Resend | **deixou de ser cosmético.** Com o domínio na mão, o remetente compartilhado do Supabase é o que impede o cadastro de sustentar 10 a 20 pessoas na mesma tarde: são poucos e-mails por hora e caem em spam. Entrar não depende de e-mail; cadastrar sim |
| Chaves do Turnstile | pública no `web/config.js`, secreta no Supabase |

O passo 8 fica pronto e inerte até as chaves do Turnstile existirem — mesma situação da Edge
Function `ir` hoje. O passo 9 não depende de chave nenhuma: é função no banco mais botão, e pode
ir junto com o resto.

Sobre o limite de envio: trocar para o Resend **não remove** a limitação por hora. O Supabase
mantém um limite próprio mesmo com SMTP personalizado — mais alto que o do servidor compartilhado
e configurável, mas existe. Conferir o valor no painel antes do piloto.

## 6. Fora do escopo, e por quê

- **Apagar conta abandonada automaticamente.** O rigoroso seria remover perfil sem interação por
  12 meses, mas isso exige rotina que ninguém escreveu, e prometer no documento o que não está
  implementado é o defeito que a auditoria persegue. Revisitar depois do piloto.
- **Termos e política revisados por advogado.** O rascunho descreve o sistema com honestidade; não
  substitui revisão jurídica se o projeto sair do contexto acadêmico.
- **Link de descadastro no e-mail.** Enquanto nenhum e-mail opcional for enviado, o checkbox no
  painel cumpre o papel.
