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

O Radar de Estágio é um assistente que trabalha sozinho. O usuário cria uma conta no site,
preenche uma vez seu perfil — curso, período, habilidades, cidade e preferência de modalidade —
e vincula o Telegram. A partir daí, recebe as recomendações no Telegram.

Em cada execução diária chega uma mensagem curta com as 3 a 5 vagas novas que realmente valem
o tempo dele, em ordem de prioridade. Cada vaga vem com:

- Nota de compatibilidade (0–100) calculada pela IA a partir do perfil;
- O motivo em uma frase — "você cumpre 8 dos 9 requisitos; falta só nuvem, que é
  desejável";
- Alerta de pegadinha — ex.: vaga de "estágio" exigindo experiência de profissional
  pleno;
- Link direto para aplicar.

Trinta segundos de leitura no café da manhã. O Radar ainda não aprende com feedback: curtir,
descartar e personalizar automaticamente as recomendações permanecem como evoluções futuras.

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
- **Evita repetição:** com o banco configurado, não envia novamente vagas já entregues ao
  mesmo perfil; personalização por feedback e tendências de mercado ainda não fazem parte da
  versão atual.
- **Não é um "wrapper de chat":** o valor está na coleta contínua, na execução
  automática e na entrega proativa — coisas que nenhuma conversa avulsa com IA faz.

## 5. Como Vamos Fazer

Em cada execução diária, sem ninguém pedir, o sistema executa cinco etapas:

1. **Coleta** — busca vagas novas de estágio em tecnologia nas fontes configuradas;
2. **Dedupe** — descarta o que já foi visto, comparando com o histórico no banco;
3. **Pré-filtro** — regras simples eliminam anúncios claramente irrelevantes antes de
   gastar IA;
4. **Matching com IA** — cada vaga é comparada ao perfil do usuário e recebe nota 0–100
   com justificativa;
5. **Entrega** — as melhores viram uma mensagem ranqueada no Telegram, com links
   diretos.

O cadastro é feito no site: o usuário cria uma conta, preenche o perfil (curso, período,
habilidades, cidade e modalidade) e clica em um botão que abre o bot no Telegram já vinculado à
sua conta. O bot só entrega mensagens; edição, pausa e retomada do perfil ainda estão previstas
para uma fase posterior. O projeto já suporta um perfil por conta.

## 6. Tecnologias, APIs e Custos

### 6.1 Coleta de vagas — quais APIs?

O MVP usa duas fontes com contratos diferentes:

- **Adzuna (API oficial):** agregador internacional de vagas que cobre o Brasil. Exige App ID e
  App Key e pode devolver descrições resumidas, posteriormente enriquecidas quando possível.
- **Gupy (API interna do portal):** o portal de vagas da Gupy carrega tudo por uma API
  interna em JSON, sem chave, porém não oficial e sujeita a mudança sem aviso.

Novas fontes só devem entrar se a validação de sete dias comprovar cobertura insuficiente nas
fontes atuais.

LinkedIn fica de fora: bloqueia coleta automatizada e a proíbe nos termos de uso.
Excluí-lo é uma decisão de escopo consciente e declarada.

### 6.2 Inteligência Artificial — qual IA usar?

- **GitHub Actions:** Gemini Developer API com modelo Flash configurável.
- **Desenvolvimento local:** Gemini Developer API ou AGY, ambos atrás da mesma interface.

O projeto usa lotes, pré-filtro e reaproveitamento de avaliações para reduzir chamadas. Cotas e
preços mudam por modelo e plano; por isso o custo deve ser medido por execução e por usuário, sem
assumir que a camada gratuita sustentará crescimento.

### 6.3 Bot do Telegram — a entrega

A Bot API oficial do Telegram é 100% gratuita e sem limite prático para o nosso
volume. O bot é criado em 2 minutos com o @BotFather, e enviar mensagem é uma
requisição HTTP simples. O WhatsApp foi descartado: a API oficial da Meta é paga por
conversa e exige empresa verificada — inviável para projeto acadêmico.

### 6.4 Roda sozinho — o agendamento

O GitHub Actions executa um workflow com `workflow_dispatch`. O disparo diário às 07:23 BRT é
feito pelo cron-job.org porque o `schedule` nativo deixou de disparar durante a validação. O
gatilho manual continua disponível para testes e demonstrações.

### 6.5 Memória do sistema — o banco de dados

PostgreSQL no Supabase guarda as vagas já vistas, os perfis dos usuários, as notas atribuídas
e os envios. O banco já está integrado ao job e ao cadastro web. Feedback, histórico de
preferências e tendências continuam fora do escopo atual.

### 6.6 A conta final

| Peça                    | Ferramenta / API                          | Custo                               |
| ------------------------ | ------------------------------------------ | ------------------------------------ |
| Coleta de vagas          | Adzuna + Gupy                               | camada gratuita no piloto; medir limites |
| Inteligência artificial  | Gemini Flash                               | variável por chamadas e tokens            |
| Notificação              | Bot API do Telegram                        | sem custo observado no piloto              |
| Agendamento              | GitHub Actions + cron-job.org              | sem custo observado no piloto              |
| Banco e contas           | Supabase (PostgreSQL + Auth)               | camada gratuita no piloto; medir limites   |

O piloto opera nas camadas gratuitas, mas isso não constitui unit economics. Antes de monetizar,
é necessário registrar chamadas de IA, duração, armazenamento, suporte e custo por usuário com
ativação operacional.

## 7. Roadmap em 3 Fases

- **Fase 1 — Prova técnica:** coleta, matching com IA, mensagem no Telegram e agendamento
  diário. Concluída.
- **Fase 2 — MVP de validação com usuários:** mais fontes, banco com histórico e dedupe, site
  com conta e cadastro do perfil, vínculo com o Telegram por botão, suporte a vários usuários e
  métricas de ativação operacional. Parcialmente implementada; faltam a ativação de produto e a
  validação de uso com estudantes.
- **Fase 3 — Retenção e controle:** editar, pausar e retomar o perfil, feedback simples e
  personalização baseada em volume suficiente de interações.
