# Plano — cadastro, consentimento e privacidade

**Data:** 04/09/2026

**Escopo:** o cadastro de ponta a ponta, os dois documentos legais e o que a LGPD exige do
produto. Nasceu da conversa sobre o e-mail de confirmação parecer amador e cresceu para cobrir
tudo que fica entre a landing e a primeira vaga entregue.

## 1. Decisões tomadas

| # | Assunto | Decisão |
|---|---|---|
| 1 | Controlador dos dados | Os três integrantes do projeto |
| 2 | Canal de contato | Criado junto com o domínio; até lá o documento fica com espaço reservado |
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

```
clica em excluir
   ↓  imediato
ativo = false             sai do where ativo do job
telegram_chat_id = null   nada mais chega no Telegram
excluida_em = now()
   ↓  60 dias
auth.users apagado; a cascata leva perfil, avaliações, envios e eventos ligados à conta
```

A primeira etapa é o que a pessoa pediu: parar de processar. A segunda é o apagamento definitivo.
Entre as duas ela pode entrar e cancelar.

**Três coisas que "parar na hora" ainda não cobre**, e que precisam entrar junto:

- O pipeline lê os usuários **antes** de coletar e guarda o `chat_id` em memória. Quem exclui
  durante a execução ainda recebe a mensagem daquele dia. Revalidar antes de enviar.
- A função `ir` registra clique de link antigo sem consultar `ativo` nem `excluida_em`. Durante os
  60 dias ela continuaria gravando `vaga_aberta` de quem pediu para sair.
- O mesmo vale para o `telegram-webhook`: `envioDoToken` e `registrarRecusa` gravam
  `vaga_irrelevante` e respondem no Telegram sem verificar exclusão, `ativo` ou se o `chat_id`
  ainda está vinculado. Clicar num botão antigo continuaria processando dado de quem pediu para
  sair.
- Os eventos anteriores ao login têm só `sessao_id`, com `user_id` e `perfil_id` nulos. **Nenhuma
  cascata os alcança.** A rotina dos 60 dias precisa apagá-los pelo `sessao_id` das sessões
  ligadas àquela conta, senão "apagamos tudo" é falso.

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

1. Escrever os dois documentos; Igor e Ian revisam antes de qualquer código
2. `web/termos.html` e `web/privacidade.html`, linkados no rodapé
3. Migration: `aceita_emails`, `termos_aceitos_em`, versão dos termos, `excluida_em`; a
   `excluir_minha_conta()` deixa de apagar e passa a marcar; função para cancelar a exclusão
4. Passo diário que apaga o que passou dos 60 dias
5. Cadastro: os dois checkboxes, o olho na senha, o perfil em `options.data`
6. Gatilho que cria o perfil na confirmação
7. Tela de reenvio
8. Turnstile
9. Botão de baixar os dados
10. **Recuperação de senha** — não existe hoje, nem tela nem chamada. Configurar o Resend não
    entrega isso sozinho: falta o link "esqueci minha senha", a chamada
    `resetPasswordForEmail`, e a tela que recebe a volta e define a senha nova
11. **Textos e controles do painel** — hoje ele diz "Não dá para desfazer" e "Seus dados foram
    apagados". Com os 60 dias as duas frases ficam falsas; entram a data do apagamento definitivo
    e o botão de cancelar. Entra também o **controle para revogar o consentimento de e-mail**: a
    decisão 2 promete que é reversível e a seção 6 usa isso para dispensar o link de descadastro,
    mas a sequência só previa a coluna no banco e o checkbox no cadastro
12. **Retorno da confirmação** — o `resumeConfirmedSignup` desiste quando não acha perfil no
    navegador, antes de consultar sessão e banco. Com o gatilho criando o perfil, ele precisa
    consultar primeiro. E o `sessao_id` do aparelho onde a pessoa se cadastrou não viaja para o
    gatilho: confirmar no celular cria o perfil e deixa o começo do funil do notebook
    desconectado

Do 3 em diante, um commit por decisão e suíte verde em comando separado, como manda o `CLAUDE.md`.

A migration `0013` ainda **não foi aplicada** em banco nenhum, então o passo 3 a edita no lugar em
vez de empilhar uma correção por cima. Como ela já passou por revisão, pedir uma segunda depois da
mudança.

## 5. Dependências externas

| O quê | Trava o quê |
|---|---|
| Domínio | contato na política e remetente do e-mail. **Não trava a hospedagem**: o Cloudflare Pages publica em `*.pages.dev` |
| Resend | remetente próprio, em vez do domínio compartilhado do Supabase |
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
