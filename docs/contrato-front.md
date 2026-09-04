# Contrato entre o site e o radar

Este documento é para quem faz o site. A stack é livre. O site **não chama nenhuma API do
`radar/`** e o `radar/` não chama o site: os dois só conversam pelo banco do Supabase. Tudo
que o site precisa é o projeto do Supabase (Auth + tabela `perfis`) e um link do Telegram.

## O que o site faz

1. Cria a conta do usuário com **Supabase Auth** (e-mail e senha, ou provedor social).
2. Deixa o usuário **preencher o perfil**, gravado na tabela `perfis`.
3. Mostra um botão **"Vincular Telegram"** que abre
   `https://t.me/RadarEstagio_bot?start=<token_vinculo>` com o `token_vinculo` lido do perfil.
4. Mostra se o Telegram já está vinculado (`telegram_chat_id` preenchido).

Edição, pausa e retomada do perfil estão previstas para a Fase 3 e não fazem parte da interface
atual.

Tudo o resto — coletar vagas, avaliar, mandar a mensagem, gravar o `chat_id` — é do radar e
do webhook, e já está pronto. O site não precisa saber como funciona.

## Acesso ao Supabase

Use a **URL do projeto** e a **chave anônima** (`anon`), as duas em Project Settings → API.
A chave anônima pode ficar no código do front; ela só permite o que as policies deixam.

Com a sessão do Supabase Auth ativa, o usuário só enxerga e edita **a própria linha** de
`perfis` (RLS, `user_id = auth.uid()`). Sem sessão não lê nada. As outras tabelas (`vagas`,
`avaliacoes`, `envios`) não são acessíveis pelo site nesta fase.

## Tabela `perfis`

Uma linha por usuário. `user_id` é o `id` do usuário no Auth (`auth.users.id`).

| coluna             | tipo     | quem escreve   | regra                                                      |
|--------------------|----------|----------------|------------------------------------------------------------|
| `id`               | uuid     | banco          | gerado; não enviar                                         |
| `user_id`          | uuid     | site           | obrigatório, único; `= session.user.id`                    |
| `curso`            | text     | site           | obrigatório. Ex.: `Ciência da Computação`                  |
| `periodo`          | int      | site           | obrigatório, ≥ 1                                           |
| `habilidades`      | text[]   | site           | obrigatório, ao menos 1. Ex.: `{Python,SQL,Git}`            |
| `cidade`           | text     | site           | obrigatório. Ex.: `Rio de Janeiro`                         |
| `modalidade`       | text     | site           | um de `remoto`, `presencial`, `hibrido`, `indiferente`     |
| `telegram_chat_id` | text     | **webhook**    | só leitura no site; `null` = ainda não vinculou            |
| `token_vinculo`    | uuid     | banco/webhook  | gerado; só leitura, usado no link do Telegram; **rotaciona a cada vínculo** |
| `ativo`            | boolean  | sistema        | `true` recebe mensagens, `false` pausa; controle do site previsto para a Fase 3 |
| `criado_em`        | timestamptz | banco       | gerado                                                     |
| `atualizado_em`    | timestamptz | site        | atualizado quando um perfil existente é salvo novamente    |

O que o radar usa para escolher vagas: `curso`, `periodo`, `habilidades`, `cidade`,
`modalidade`. Quanto mais específicas as habilidades, melhor o ranqueamento.

Só entram no envio diário os perfis com `ativo = true` **e** `telegram_chat_id` preenchido.

## Exemplos com `@supabase/supabase-js`

Criar o perfil logo depois do cadastro:

```js
const { data: { user } } = await supabase.auth.getUser();
await supabase.from("perfis").insert({
  user_id: user.id,
  curso: "Ciência da Computação",
  periodo: 4,
  habilidades: ["Python", "SQL", "Git"],
  cidade: "Rio de Janeiro",
  modalidade: "hibrido",
});
```

Ler o perfil (vem só a linha do usuário logado):

```js
const { data: perfil } = await supabase.from("perfis").select("*").single();
```

### Edição futura (Fase 3)

Quando a interface de edição for disponibilizada:

```js
await supabase.from("perfis")
  .update({ habilidades: ["Python", "SQL", "Git", "Docker"], atualizado_em: new Date().toISOString() })
  .eq("user_id", user.id);
```

Botão do Telegram:

```js
const link = `https://t.me/RadarEstagio_bot?start=${perfil.token_vinculo}`;
```

Estado do vínculo: `perfil.telegram_chat_id !== null`. Como o `chat_id` é gravado pelo
webhook segundos depois do clique, basta recarregar o perfil ao voltar para a página (ou usar
Realtime do Supabase na linha, se quiser atualizar sozinho).

## O que acontece depois do clique

O Telegram abre o bot e manda `/start <token_vinculo>` automaticamente. O bot chama a Edge
Function `telegram-webhook`, que grava o `telegram_chat_id` no perfil daquele token e responde
"Telegram vinculado! Você vai receber as vagas compatíveis com o seu perfil todos os dias de
manhã." A partir da próxima execução (07:23, horário de Brasília) o usuário recebe a mensagem.

**O token é de uso único.** Na mesma atualização em que grava o `chat_id`, o webhook troca o
`token_vinculo` por um novo, de modo que um link vazado — print, histórico de conversa, celular
emprestado — não vincula o chat de outra pessoa ao perfil. Consequências para o site:

- o `token_vinculo` que a página leu antes do clique **deixa de valer** depois do vínculo. Ao
  recarregar o perfil, releia a coluna em vez de reaproveitar o valor em memória;
- quem clicar de novo com o link antigo recebe "Este link já foi usado ou expirou", ou, se aquele
  chat já for o chat vinculado, "Seu Telegram já está vinculado";
- um chat que já pertence a outra conta recebe recusa explícita, em vez de o webhook falhar calado.

## O que não fazer

- **Não criar nem alterar tabelas pelo painel.** Qualquer mudança de schema é uma migration
  em `supabase/migrations/`, combinada com quem mexe no `radar/`.
- Não escrever em `telegram_chat_id` nem em `token_vinculo`.
- Não usar a chave `service_role` no front: ela ignora as permissões.
- Não pedir `@username` do Telegram nem `chat_id` ao usuário: o vínculo é só pelo botão.

## Onde está cada coisa

- Schema completo: [`supabase/migrations/0001_tabelas_iniciais.sql`](../supabase/migrations/0001_tabelas_iniciais.sql)
- Webhook: [`supabase/functions/telegram-webhook/`](../supabase/functions/telegram-webhook/)
- Visão geral do sistema: [`docs/arquitetura.md`](arquitetura.md)
