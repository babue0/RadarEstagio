# Radar de Estágio — Proposta de Projeto

_Agosto de 2026_

> O agente de IA que garimpa os sites de vagas todos os dias e entrega, no Telegram,
> apenas as oportunidades que combinam com o seu perfil — ranqueadas e explicadas.

## 1. O Problema

Procurar estágio é um segundo emprego não remunerado. As vagas estão espalhadas em
vários sites, e cada um despeja centenas de anúncios em que 90% não servem: outro
curso, outra cidade, ou "estágio" exigindo dois anos de experiência. As vagas boas
fecham rápido — quem aplica nos primeiros dias tem vantagem enorme — mas encontrá-las
exige garimpo diário.

O resultado: ou o estudante gasta uma hora por dia rolando feeds, ou cansa, para de
acompanhar, e a vaga perfeita passa sem que ele saiba que ela existiu.

## 2. A Solução

O Radar de Estágio é um assistente que trabalha sozinho. O usuário conversa uma única
vez com ele, no Telegram, contando quem é: curso, período, habilidades, cidade e
preferência por remoto ou presencial. A partir daí, não faz mais nada.

Todo dia de manhã chega uma mensagem curta com as 3 a 5 vagas novas que realmente valem
o tempo dele, em ordem de prioridade. Cada vaga vem com:

- Nota de compatibilidade (0–100) calculada pela IA a partir do perfil;
- O motivo em uma frase — "você cumpre 8 dos 9 requisitos; falta só nuvem, que é
  desejável";
- Alerta de pegadinha — ex.: vaga de "estágio" exigindo experiência de profissional
  pleno;
- Link direto para aplicar.

Trinta segundos de leitura no café da manhã. E o sistema aprende: a cada sugestão o
usuário pode curtir ou descartar, e o Radar fica mais certeiro semana após semana.

Em uma frase: é um amigo recrutador que vasculha os sites o dia inteiro por você e só
chama quando encontra algo que combina com o seu perfil — explicando o porquê.

## 3. Público-Alvo

Universitários de tecnologia em busca do primeiro estágio — começando pelo nosso
próprio grupo, que é o usuário número 1 do produto (construímos porque precisamos, e
testamos no nosso dia a dia). A mesma máquina depois se expande para qualquer curso,
área ou nível de senioridade: basta trocar o perfil e as fontes de vagas.

## 4. Diferencial — por que não é "mais do mesmo"

- **Alertas dos sites são burros:** filtram por palavra-chave e despejam tudo que tem
  "estágio" no título, sem considerar quem recebe. O Radar julga cada vaga como um
  recrutador humano julgaria — compara os requisitos com o perfil do usuário e mostra
  o raciocínio.
- **Cada site só avisa das próprias vagas.** O Radar cobre várias fontes de uma vez,
  num canal só.
- **Tem memória:** nunca repete vaga, aprende com o feedback e enxerga tendências do
  mercado ("essa semana abriram muitas vagas pedindo análise de dados").
- **Não é um "wrapper de chat":** o valor está na coleta contínua, na execução
  automática e na entrega proativa — coisas que nenhuma conversa avulsa com IA faz.

## 5. Como Vamos Fazer

Todo dia às 8h, sem ninguém pedir, o sistema executa cinco etapas:

1. **Coleta** — busca vagas novas de estágio em tecnologia nas fontes configuradas;
2. **Dedupe** — descarta o que já foi visto, comparando com o histórico no banco;
3. **Pré-filtro** — regras simples eliminam anúncios claramente irrelevantes antes de
   gastar IA;
4. **Matching com IA** — cada vaga é comparada ao perfil do usuário e recebe nota 0–100
   com justificativa;
5. **Entrega** — as melhores viram uma mensagem ranqueada no Telegram, com links
   diretos.

O cadastro dispensa formulário: o usuário dá `/start` no bot e conta seu perfil
conversando; a IA extrai os dados sozinha. Cada membro do grupo cadastra o próprio
perfil — o projeto já nasce multiusuário, com usuários reais para apresentar.

## 6. Tecnologias, APIs e Custos

### 6.1 Coleta de vagas — quais APIs?

Gupy, Vagas.com e afins não oferecem API pública oficial para desenvolvedores
externos. Usaremos três caminhos, todos gratuitos:

- **Adzuna (API oficial e gratuita):** agregador internacional de vagas que cobre o
  Brasil. Cadastro instantâneo em developer.adzuna.com gera App ID e App Key; o plano
  grátis dá cerca de 1.000 chamadas/mês — precisamos de ~30 (uma busca por dia).
  Limitação: descrição resumida, com link para a vaga completa.
- **Gupy (API interna do portal):** o portal de vagas da Gupy carrega tudo por uma API
  interna em JSON — grátis e sem cadastro, porém não oficial (pode mudar sem aviso). A
  chamada é descoberta pela aba Network do DevTools.
- **Vagas.com / InfoJobs:** leitura direta das páginas com Python (requests +
  BeautifulSoup).

LinkedIn fica de fora: bloqueia coleta automatizada e a proíbe nos termos de uso.
Excluí-lo é uma decisão de escopo consciente e declarada.

### 6.2 Inteligência Artificial — qual IA usar?

- **Opção custo zero — Google Gemini (modelos Flash):** camada gratuita sem cartão de
  crédito, com limites de centenas a ~1.500 requisições por dia — folgado para nossas
  dezenas de análises diárias. Os limites mudam com o tempo e, no plano grátis, o
  Google pode usar os dados enviados para treino (irrelevante aqui: vaga de emprego é
  dado público).
- **Opção premium — Claude Haiku 4.5 (Anthropic):** pago por uso, sem mensalidade:
  US$ 1 por milhão de tokens de entrada e US$ 5 por milhão de saída. No nosso volume
  (~50 vagas/dia), a conta fecha em US$ 3–5/mês (~R$ 20–30).

Estratégia: começar no Gemini grátis; se a qualidade da análise pedir, migrar para o
Claude é trocar meia dúzia de linhas de código.

### 6.3 Bot do Telegram — a entrega

A Bot API oficial do Telegram é 100% gratuita e sem limite prático para o nosso
volume. O bot é criado em 2 minutos com o @BotFather, e enviar mensagem é uma
requisição HTTP simples. O WhatsApp foi descartado: a API oficial da Meta é paga por
conversa e exige empresa verificada — inviável para projeto acadêmico.

### 6.4 Roda sozinho — o agendamento

GitHub Actions, o agendador do próprio GitHub, executa o sistema todo dia no horário
marcado. Gratuito em repositório público (e o plano grátis dá 2.000 minutos/mês em
privado; usaremos ~150). Sem servidor, sem deploy, sem cartão. O gatilho manual do
Actions é o botão da demonstração ao vivo: um clique e a mensagem chega no Telegram na
frente da banca.

### 6.5 Memória do sistema — o banco de dados

SQLite: um banco de dados em arquivo, dentro do próprio projeto — grátis e com zero
configuração. Guarda as vagas já vistas (dedupe), os perfis dos usuários, as notas
atribuídas e o feedback (curtir/descartar). Na fase multiusuário com painel web, o
Supabase (banco na nuvem) tem plano gratuito suficiente.

### 6.6 A conta final

| Peça                    | Ferramenta / API                          | Custo                               |
| ------------------------ | ------------------------------------------ | ------------------------------------ |
| Coleta de vagas          | Adzuna (oficial) + Gupy + Vagas.com        | R$ 0                                 |
| Inteligência artificial  | Gemini Flash (ou Claude Haiku 4.5)         | R$ 0 (ou ~R$ 25/mês)                 |
| Notificação              | Bot API do Telegram                        | R$ 0                                 |
| Agendamento              | GitHub Actions (cron diário)               | R$ 0                                 |
| Banco de dados           | SQLite (Supabase na fase 3)                | R$ 0                                 |
| **TOTAL**                |                                             | **R$ 0,00/mês (premium: ~R$ 25)**    |

A única cobrança possível do sistema inteiro é a IA — e mesmo ela tem alternativa
gratuita que atende o projeto.

## 7. Roadmap em 3 Fases

- **Fase 1 — MVP (1 fim de semana):** uma fonte de vagas, perfil fixo, matching com
  IA, mensagem no Telegram e agendamento diário. O sistema funcionando de ponta a
  ponta.
- **Fase 2 — Produto:** mais fontes, banco com histórico e dedupe, cadastro
  conversacional no bot e suporte a vários usuários.
- **Fase 3 — Polimento:** comando `/hoje` para resumo sob demanda, feedback
  curtir/descartar que refina o matching e painel web com estatísticas do mercado.
