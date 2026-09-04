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
| 3 | Retenção | Enquanto a conta existir. Excluir apaga tudo em cascata |
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
   ↓  imediato e visível
ativo = false             para de entregar na hora
telegram_chat_id = null   nada mais chega no Telegram
excluida_em = now()
   ↓  60 dias
auth.users apagado; a cascata leva perfil, avaliações, envios e eventos
```

A primeira etapa é o que a pessoa pediu: parar de processar. A segunda é o apagamento definitivo.
Entre as duas ela pode entrar e cancelar.

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

**Com quem são compartilhados**

| Quem | O que recebe |
|---|---|
| Supabase | tudo — é onde o banco e as contas moram |
| Telegram | o `chat_id` e o conteúdo das mensagens |
| Google Gemini | **apenas o texto dos anúncios de vaga** |
| Adzuna e Gupy | nada do usuário; só a busca sai |
| Cloudflare | tráfego do site e o Turnstile |

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

Do 3 em diante, um commit por decisão e suíte verde em comando separado, como manda o `CLAUDE.md`.

A migration `0013` ainda **não foi aplicada** em banco nenhum, então o passo 3 a edita no lugar em
vez de empilhar uma correção por cima. Como ela já passou por revisão, pedir uma segunda depois da
mudança.

## 5. Dependências externas

| O quê | Trava o quê |
|---|---|
| Domínio | contato na política, hospedagem, remetente do e-mail |
| Resend | o e-mail sair com remetente próprio e sem limite por hora |
| Chaves do Turnstile | pública no `web/config.js`, secreta no Supabase |

Os passos 8 e 9 ficam prontos e inertes até as chaves existirem — mesma situação da Edge Function
`ir` hoje.

## 6. Fora do escopo, e por quê

- **Apagar conta abandonada automaticamente.** O rigoroso seria remover perfil sem interação por
  12 meses, mas isso exige rotina que ninguém escreveu, e prometer no documento o que não está
  implementado é o defeito que a auditoria persegue. Revisitar depois do piloto.
- **Termos e política revisados por advogado.** O rascunho descreve o sistema com honestidade; não
  substitui revisão jurídica se o projeto sair do contexto acadêmico.
- **Link de descadastro no e-mail.** Enquanto nenhum e-mail opcional for enviado, o checkbox no
  painel cumpre o papel.
