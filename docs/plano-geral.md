# Plano geral

**Consolidado em 09/09/2026.** A expansão para diferentes áreas foi autorizada em 08/09.
O registro de execução encerra as entregas locais de cadastro, landing, métricas e pausa
(O00–R03), com testes registrados. Não há uma fila de implementação desses IDs a reiniciar.
Publicação, validação com estudantes e decisões externas continuam pendentes de evidência.
Esta consolidação não consultou serviços externos nem repetiu os testes de implementação.

Este é o acompanhamento atual do projeto. O plano formal de piloto foi retirado por decisão
do Igor: não há obrigação de recrutar uma coorte, realizar cinco entrevistas, calcular D7
ou cumprir metas de pesquisa antes de divulgar. As métricas existentes continuam disponíveis.

## 1. O que já está feito

- **Expansão local concluída:** limite de sete recomendações, cadastro com perfil antes da
  conta, caminho explícito sem habilidades, sugestões conforme o curso, demonstração
  ilustrativa e FAQ, estados de vínculo sem promessa de busca já executada, participação no
  feedback, medianas observadas, utilidade por área e motivo opcional após a pausa.
  Contratos nas migrations `0017`–`0019`; presença no Git não comprova aplicação remota.

- **Cadastro e conta:** formulário em etapas, confirmação entre aparelhos, reenvio, recuperação
  de senha, edição de perfil, consentimento e preferência de e-mails.
- **Controle dos dados:** pausa, retomada, desvínculo, exportação, exclusão com carência de
  60 dias e cancelamento. Migrations até `0016` aplicadas; histórico reconciliado em 06/09.
- **Telegram:** vínculo por token de uso único, recomendações explicadas e feedback com seis
  opções. Funções `ir` e `telegram-webhook` publicadas e código comparado com o repositório
  em 06/09, conforme o registro no guia.
- **Primeira entrega:** dispatch por perfil, com exceção entre 06:23 e 07:23 de Brasília.
  Teste registrado de vínculo até mensagem em cerca de quatro minutos; não é garantia de prazo.
- **Concorrência:** trava por perfil e releitura do histórico, testadas com duas conexões.
  Telegram e banco continuam sendo operações separadas.
- **Coleta e ranking:** Adzuna por padrão (Gupy desligada pelos termos), extração de fatos compartilhada, nota em Python,
  deduplicação e personalização v1 por recusas. Jooble pronto, mas desligado por padrão.
- **Mensagens:** listas longas resumidas; desde 09/09, habilidades desejáveis ausentes aparecem
  como “Diferenciais que a vaga cita”, separadas dos requisitos a conferir e sem virar veto.
- **Métricas:** funil, vagas abertas distintas, utilidade semanal e recusas com denominadores.
  Abertura com token real e relatório foram conferidos; falta confirmar o teste de feedback do Igor.
- **Contato e e-mail:** `contato@radarestagio.com` com recebimento confirmado; Resend verificado
  e SMTP salvo. Confirmação e recuperação reais pelo site ainda precisam de teste registrado.

As evidências remotas acima são de 05–06/09 e estão no [guia](guia-publicacao-e-piloto.md).
Esta revisão não refez esses testes nem consultou o estado atual das contas externas.

## 2. O que falta antes de divulgar

### 1. Confirmar onde o site está publicado

- [x] Confirmado em 09/09 que `radarestagio.pages.dev` serve os arquivos do `main`
  ([guia](guia-publicacao-e-piloto.md)); falta a conta Cloudflare e a forma de publicação.
- [ ] Definir o endereço público final e conferir HTTPS, início, Termos e Privacidade.
      `radarestagio.com` ainda não resolve por HTTP: só tem MX, e os textos legais já apontam
      para ele.
- [ ] Confirmar se mudanças na `main` atualizam o frontend automaticamente.

A conversa sobre publicação no Pages não confirma que ela terminou. Por isso, o estado aqui
é **a confirmar**, e não “não hospedado em lugar nenhum”. O domínio continua na conta do Igor;
a transferência para `RadarEstagio/RadarEstagio` foi confirmada em 08/09 e o PR #21 foi
integrado à main. A configuração de cada automação ainda deve ser verificada. Combinar acesso e administração sem compartilhar senhas.

### 2. Conectar o endereço ao cadastro

- [x] Site URL corrigido para o endereço publicado em 09/09, depois do cadastro de ponta a
      ponta ter caído em `radarestagio.com` ([guia](guia-publicacao-e-piloto.md), seção 5).
- [ ] Trocar a `URL_DA_LANDING` provisória pelo endereço escolhido.
- [ ] Configurar Turnstile no frontend e no Supabase e testar o desafio; hoje
      `turnstileSiteKey` está vazio e o captcha do Auth está desligado.

Não reaplicar as migrations já registradas nem republicar funções só para repetir etapas
concluídas. Se o código ou o repositório mudar, atualizar as integrações afetadas.

### 3. Testar com uma conta da equipe

- [ ] Cadastro, confirmação, reenvio e recuperação de senha.
- [ ] Vínculo, entrega de recomendações, abertura e feedback positivo/negativo.
- [ ] Edição, pausa/retomada, exportação, exclusão e cancelamento.

Para feedback, usar envio persistido no banco: `testar-local` gera tokens que o webhook não
encontra. `rodar --perfil` recebe `perfis.id` e exige `DATABASE_URL` configurada para atender
um perfil real. Não colocar essa conexão no frontend. Anotar os erros encontrados e corrigir
os bloqueadores antes de convidar outras pessoas.

### 4. Concluir os textos e combinar a manutenção

- [ ] Igor, Ian e Miguel revisarem Termos e Política e resolverem as passagens pendentes.
- [ ] Definir versão/vigência e sincronizar Markdown e páginas HTML.
- [ ] Combinar quem responde ao contato, acompanha falhas e paga a renovação do domínio.

As páginas seguem como rascunhos até essa revisão; a implementação não aprova os textos.

### 5. Pedir para alguns colegas usarem

- [ ] Enviar o site quando o fluxo estiver funcionando.
- [ ] Perguntar onde travaram, se alguma vaga serviu e se as mensagens ficaram claras.
- [ ] Anotar problemas concretos e escolher o próximo ajuste com a equipe.

Sem quantidade mínima, roteiro obrigatório de entrevista, prazo de duas semanas ou metas
formais. Consultar as métricas quando ajudarem a entender um problema; não é necessário criar
um dashboard ou novas consultas para começar essa conversa.

## 2.1 Rodada de confiabilidade (10/09/2026)

Uma revisão externa apontou defeitos no núcleo do produto, e eles foram corrigidos com teste
que reproduz cada falha. O detalhe operacional está no [CLAUDE.md](../CLAUDE.md); a decisão de
arquitetura, em [arquitetura.md](arquitetura.md). Em resumo: fronteira de transação, identidade
da vaga por fonte e id, deduplicação que preserva cidade, prompt preservando o nível da
habilidade, recusa corrigida deixando de penalizar, negação no pré-filtro de experiência, falha
temporária de entrega não pausando conta, travessão no nome do curso, suítes rodando em pull
request e versão fixa do cliente supabase.

**Antes da próxima execução:** a mudança do prompt invalidou o cache de extração. A execução
seguinte reextrai as candidatas e gasta cota; ler o resumo das 07:23 e conferir "vagas sem
extração".

O que essa rodada deliberadamente não fez, e continua pendente:

- **Pesos da nota.** A regra de não recalibrar sem `vaga_irrelevante` real continua valendo. O
  que mudou foi a explicação: perfil sem habilidade cadastrada agora recebe um aviso na
  mensagem em vez de uma nota alta sem ressalva.
- **Detectar execução ausente.** Se o cron externo não disparar, nada avisa: o passo
  `if: failure()` do workflow só cobre execução que começou. Falta escolher onde esse alerta
  mora, e a opção mais simples é o próprio cron-job.org avisar por e-mail quando falhar.
- **Rotular os descartes.** `python -m radar descartes` já exporta a amostra com o motivo, mas
  ninguém preencheu `descarte_correto` ainda. Sem isso, continuamos medindo só a qualidade do
  que foi entregue.
- **Preencher o gabarito humano.** As 20 entregas de `docs/gabarito-2026-09-09.json` seguem com
  `relevante` nulo, então o juiz automático ainda não foi validado.
- **Frontend em um arquivo só.** `web/assets/app.js` passa de 1.500 linhas com estado
  compartilhado; a recomendação dessa revisão foi separar responsabilidades sem trocar de
  framework. Em 12/09, Igor solicitou um plano para React com JavaScript, ainda sem execução;
  ver a seção 2.3.

## 2.2 Auditoria do agendamento diário (10/09/2026)

A auditoria está em
[auditorias/2026-09-10-agendamento-diario.md](auditorias/2026-09-10-agendamento-diario.md), com
dez achados numerados e o histórico real das execuções. O disparo externo é confiável: 13 de 13
dias no horário desde 28/08. O risco está no que acontece depois dele, e estas são as pendências
que saíram de lá:

- **G01 e G07 — prazo da extração e timeouts do workflow.** É o único achado capaz de zerar as
  entregas de todos: a extração roda para todos antes de qualquer envio e só é gravada no fim,
  então um kill por timeout deixa a coorte sem mensagem e joga fora o que já foi pago ao Gemini.
  Em correção no PR #57.
- **G03 — não reenviar a quem já foi atendido no dia.** Sem essa marca não existe recuperação
  segura depois de uma falha parcial nem agendador de reserva, e quem vincula no fim da janela
  pode receber duas mensagens na mesma manhã. Exige migration.
- **G04 — detectar execução ausente**, o mesmo item da rodada de confiabilidade acima.
- **G06 — run por perfil coleta para a coorte inteira**: cada vínculo custa uma coleta completa
  na Adzuna, e esse custo cresce com o número de cidades.
- **G02 — registrar o fim de cada lote com a duração.** Fecha a margem do G01 e mede o efeito do
  raciocínio `low` na latência.

## 2.3 Migração do frontend para React (12/09/2026)

**Estado: planejamento em revisão; implementação não iniciada.** Igor solicitou registrar
a migração em PR, mantendo React com JavaScript, sem TypeScript e sem redesenhar a interface.
O [plano detalhado](plano-migracao-react.md) define arquitetura proposta, etapas, contratos,
transição dos testes, critérios de aceite, publicação e reversão.

As PRs [#60](https://github.com/RadarEstagio/RadarEstagio/pull/60) e
[#61](https://github.com/RadarEstagio/RadarEstagio/pull/61) já estão integradas à `main` na base
`0f0ca45`: preservar header/seções atuais, faixa de logos removida e selos da Adzuna.
Isso registra o estado do código, não uma conferência do site publicado.

Próximo passo: revisar o plano com Igor e obter autorização para implementar. Este registro
não instala dependências, altera o frontend ou autoriza mudanças remotas de publicação/Auth.

## 3. Limitações e decisões que continuam valendo

- **Candidatura:** acontece na fonte; o Radar não se candidata e não captura novas candidaturas.
- **Feedback:** última resposta conta nas métricas, mas pode haver eventos brutos repetidos e
  perguntas simultâneas. Mensagem enviada sem gravação pode deixar token órfão.
- **Histórico:** exclusões definitivas podem alterar métricas de semanas passadas.
- **Ranking:** a v1 usa repetição e recusas de área. Os outros motivos não mudam pesos
  automaticamente; investigar exemplos antes de recalibrar.
- **IA:** reuso reduz trabalho repetido; novos anúncios, cidades e áreas podem exigir extrações.
- **Fora do trabalho imediato:** cobrança, plano formal de pesquisa, D7, campanhas de e-mail
  e exclusão automática por abandono. Medianas de entrega e abertura já estão implementadas;
  são tempos observados, não promessa de prazo. Monetização permanece uma hipótese futura.
- **Jooble:** ativação opcional, com chave e configuração próprias; não bloqueia a divulgação.
- **Histórico Git e skills:** permanecem conforme decisões registradas em 05/09. Não há nova
  autorização para reescrever histórico ou remover recursos de terceiros.

## 4. Pendências externas da expansão

Os IDs abaixo são referências históricas. Atualizar o estado geral aqui e a evidência no
documento indicado; não manter uma segunda fila no antigo registro de execução.

| Frente | Estado e próximo passo | Documento responsável |
|---|---|---|
| E01 — publicação e jornada | Conferir versões, migrations, deploy automático, Auth, SMTP, CAPTCHA, cron e jornada com conta da equipe; inspecionar 375 px e 1280 px | [Guia](guia-publicacao-e-piloto.md) |
| E02 — cobertura | Escolher janela, acesso e responsável; coletar amostra e separar erro técnico, desconhecido e descarte legítimo | [Cobertura](cobertura-estagios.md) |
| E03 — aquisição | Após verificar a jornada, confirmar canal, URL, responsável e mensagem; obter autorização antes de divulgar relato | [Aquisição e prova](aquisicao-e-prova.md) |
| E04 — custos | Reunir faturas, uso e horas de suporte em uma janela comum; custos desconhecidos não são zero | [Custos](custos-operacao.md) |
| E05 — oferta | Após cobertura e custos, decidir oferta, pagador, preço, duração, renovação, cancelamento, aceite e provedor; checkout é tarefa posterior | [Hipótese comercial](hipotese-comercial.md) |
| D01 — formação | Usar casos de cobertura para decidir escala acadêmica, correlatos, aliases e cursos fora do catálogo; preservar contrato atual até decisão | [Contrato](contrato-front.md#elegibilidade-acadêmica--decisão-d01-em-aberto) |

Os responsáveis continuam a confirmar; a proposta de divisão está na seção 2 do guia.
E02–E05/D01 não criam metas formais nem impedem o piloto informal depois da conferência
operacional. Não há autorização de cobrança ou disparo de mensagens implícita nesta fila.

## 5. Onde consultar os detalhes

- [Funcionalidades](funcionalidades.md): o que usuários e desenvolvedores podem fazer.
- [Guia de publicação](guia-publicacao-e-piloto.md): configuração e evidências datadas.
- [Cadastro e privacidade](contrato-front.md): decisões dessa frente.
- [Revisão dos textos](guia-publicacao-e-piloto.md#2-revisar-os-documentos-e-combinar-a-manutenção): pendências dos responsáveis.
- [Métricas](metricas.md): definições e limites das consultas existentes.
- [Arquitetura](arquitetura.md) e [contrato frontend](contrato-front.md): implementação.
- [Índice](README.md): documentos mantidos. O histórico dos planos antigos está no Git.
