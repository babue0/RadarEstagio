# Landing page — Radar de Estágio

Landing page responsiva do projeto, com apresentação da proposta e fluxo de cadastro do perfil.

## Experiência

- comunica o problema e a promessa do Radar na primeira dobra;
- demonstra como uma recomendação chega no Telegram;
- explica coleta, matching e entrega em três passos;
- explicita que modalidade ausente não é inferida pela localização;
- oferece um único CTA para cadastro;
- coleta nome, e-mail, curso, período, habilidades, cidade e modalidade em duas etapas.

Enquanto a API de perfis não existe, o cadastro é salvo apenas no `localStorage` do navegador,
na chave `radar-perfil`. Nenhum dado é enviado pela rede.

## Como abrir

```bash
uv run python -m http.server 8000 -d web
```

Acesse <http://localhost:8000>. Também é possível abrir `index.html` diretamente no navegador.

O protótipo usa apenas HTML, CSS e JavaScript. Ele não escolhe nem exige a stack do produto final.

## Decisões de frontend

- O escopo atual é uma landing page com cadastro, não um dashboard.
- A implementação usa HTML, CSS e JavaScript, sem framework, build ou dependências.
- O formulário será conectado ao backend Python por HTTP quando existir persistência de perfis.
- O front não pedirá `@username` nem `chat_id` do Telegram.
- Após salvar o perfil, o backend deverá devolver um link do bot com token temporário. Ao abrir
  esse link, o comando `/start` vinculará o usuário real do Telegram ao perfil cadastrado.
- React, Next.js, Astro, roteador e biblioteca de estado só serão reconsiderados se o escopo do
  frontend crescer de forma concreta.
