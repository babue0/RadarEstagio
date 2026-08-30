# Landing page — Radar de Estágio

Landing page responsiva do projeto, com apresentação da proposta e fluxo de cadastro do perfil.

## Experiência

- comunica o problema e a promessa do Radar na primeira dobra;
- demonstra como uma recomendação chega no Telegram;
- explica coleta, matching e entrega em três passos;
- explicita que modalidade ausente não é inferida pela localização;
- oferece um único CTA para cadastro;
- cria ou acessa uma conta por e-mail e senha;
- coleta curso e período, habilidades e preferências em três etapas curtas;
- sugere cursos e habilidades comuns, mas mantém entrada livre para outros perfis;
- pede e-mail e senha somente depois que o usuário configura o radar;
- persiste o perfil no Supabase e abre o vínculo seguro com o Telegram;
- reconhece quando o webhook concluiu o vínculo.
- ainda não oferece edição, pausa ou retomada do perfil; essas ações ficam para a Fase 3.

Quando a confirmação de e-mail está ativa no Supabase, os campos do perfil ficam temporariamente
no `localStorage`, na chave `radar-perfil-pendente`, até o usuário voltar pelo link de confirmação.
A senha nunca é armazenada pelo site.

## Configuração

Preencha `supabasePublishableKey` em `web/config.js` com a chave publicável ou `anon` do projeto.
Essa chave é própria para uso no navegador; o acesso aos dados continua limitado pelas policies
RLS e pelas permissões de coluna das migrations. Nunca use a chave `service_role` no frontend.

No Supabase Auth, adicione a URL publicada do site e `http://localhost:8000` à lista de Redirect
URLs. A confirmação de e-mail retorna ao site, que conclui a criação do perfil automaticamente.

Antes de publicar, aplique também `supabase/migrations/0002_permissoes_frontend.sql` no projeto.

## Como abrir

```bash
uv run python -m http.server 8000 -d web
```

Acesse <http://localhost:8000>. O fluxo autenticado deve ser servido por HTTP e não abrindo o
`index.html` diretamente.

O protótipo usa apenas HTML, CSS e JavaScript. Ele não escolhe nem exige a stack do produto final.

## Decisões de frontend

- O escopo atual é uma landing page com cadastro, não um dashboard.
- A implementação usa HTML, CSS e JavaScript, sem framework, build ou dependências.
- O site usa Supabase Auth e escreve diretamente na tabela `perfis`; não existe API Python entre
  os dois componentes.
- O front não pedirá `@username` nem `chat_id` do Telegram.
- Após salvar o perfil, o site lê `token_vinculo` e abre o bot. O comando `/start` vincula o
  usuário real do Telegram ao perfil cadastrado.
- React, Next.js, Astro, roteador e biblioteca de estado só serão reconsiderados se o escopo do
  frontend crescer de forma concreta.
