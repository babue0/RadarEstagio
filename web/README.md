# Landing page — Radar de Estágio

Landing page responsiva do projeto, com apresentação da proposta e fluxo de cadastro do perfil.

`termos.html` e `privacidade.html` estão disponíveis no rodapé, como versões para revisão e
sem vigência. O aviso permanece até a revisão dos textos, a ativação do contato e a entrega
das funcionalidades descritas. Essas páginas não carregam autenticação ou métricas.

As configurações externas estão no [guia de publicação e piloto](../docs/guia-publicacao-e-piloto.md).

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
- persiste o perfil no Supabase e abre o vínculo com o Telegram por token aleatório;
- reconhece quando o webhook concluiu o vínculo;
- registra os eventos do funil sem bloquear o cadastro quando a telemetria falha;
- diz, no rodapé e no cadastro, quais dados guarda e para que servem;
- dá ao dono da conta um painel para editar o perfil, pausar e retomar as entregas, desvincular o
  Telegram e excluir a conta;
- na exclusão, mostra a data do apagamento definitivo e oferece cancelar enquanto o prazo corre.

O cadastro exige aceite dos documentos e oferece e-mails opcionais, inicialmente desmarcados.
O perfil segue nos metadados do cadastro e o banco guarda uma cópia protegida até a confirmação.
O gatilho cria o perfil com a versão aceita e a sessão de origem, inclusive quando a confirmação
acontece em outro aparelho. Novos cadastros não guardam o perfil no `localStorage`.

Há reenvio com endereço editável e espera de 60 segundos, recuperação de senha, exportação JSON
e controle de e-mails no painel. A exportação inclui dados associados à conta; eventos anônimos
de um navegador compartilhado não são atribuídos automaticamente ao dono do download.

## Configuração

Preencha `supabasePublishableKey` em `web/config.js` com a chave publicável ou `anon` do projeto.
Essa chave é própria para uso no navegador; o acesso aos dados continua limitado pelas policies
RLS e pelas permissões de coluna das migrations. Nunca use a chave `service_role` no frontend.

No Supabase Auth, adicione a URL publicada do site e `http://localhost:8000` à lista de Redirect
URLs. A confirmação de e-mail retorna ao site, que conclui a criação do perfil automaticamente.

Antes de publicar, revise e aplique em ordem as migrations até `0016`. As novas `0014` a `0016`
foram testadas localmente, mas não aplicadas no projeto remoto nesta etapa. A `0005` instrumenta
o funil, a `0006` adiciona áreas de interesse ao perfil, a `0007` persiste os requisitos técnicos
extraídos das vagas, a `0011` dá a cada envio o token do link rastreável, a `0012` remove as
colunas de preferências múltiplas, que nunca tiveram quem lesse ou escrevesse, e a `0013` entrega
as funções do painel da conta e a exclusão em duas etapas. A `0014` entrega consentimento e
criação do perfil na confirmação, a `0015` exportação e a `0016` proteção das interações após
pausa, exclusão ou desvínculo. A `0013` aplicada não foi alterada.

Inclua também os retornos de recuperação `http://localhost:8000/?fluxo=recuperar` e
`https://radarestagio.com/?fluxo=recuperar` na configuração do Auth quando usados.
`turnstileSiteKey` fica vazio até configurar o widget e a verificação no Supabase. A chave
secreta do Turnstile e a chave do Resend pertencem ao servidor, nunca a este arquivo.

Os textos ainda são rascunhos. Antes de liberar cadastros públicos, finalize os documentos e
alinhe sua versão com `VERSAO_DOS_TERMOS` e a validação da migration de consentimento.

Excluir a conta **não apaga na hora**: marca a data, para a entrega e solta o Telegram. O
apagamento definitivo é feito pelo job diário depois de 60 dias, e até lá a pessoa pode entrar e
cancelar — precisando vincular o Telegram outra vez.

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
- O site usa Supabase Auth; cria perfis por gatilho ou RPC autenticada e edita campos permitidos
  em `perfis`. Não existe API Python entre os dois componentes.
- A sessão de eventos é um UUID aleatório no `localStorage`; propriedades não recebem e-mail,
  curso, cidade ou outros campos livres do perfil.
- O front não pedirá `@username` nem `chat_id` do Telegram.
- Após salvar o perfil, o site lê `token_vinculo` e abre o bot. O comando `/start` vincula o
  usuário real do Telegram ao perfil cadastrado.
- React, Next.js, Astro, roteador e biblioteca de estado só serão reconsiderados se o escopo do
  frontend crescer de forma concreta.

## Testes locais

`deno task --config tests/web/deno.json test` executa os fluxos de tela com JSDOM e todas as
migrations em PostgreSQL isolado via PGlite. Não usa o banco real nem dispara e-mails. A suíte
Python continua em `uv run pytest -q`. A conferência visual e a entrega real de e-mails são
etapas separadas do guia de publicação.
