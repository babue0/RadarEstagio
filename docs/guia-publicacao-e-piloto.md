# Guia de publicação e piloto

Deploy adiado por decisão do Igor em 05/09. O trabalho atual fica local; não houve aplicação
remota das migrations nem publicação das funções nesta etapa. Os documentos continuam como
rascunhos, sem vigência.

Estado das configurações feitas pelo Igor durante a orientação:

- Domínio comprado e Email Routing habilitado; regra de contato preparada. Falta confirmar o
  recebimento e a rotina de resposta com Ian e Miguel.
- Domínio verificado no Resend e SMTP personalizado salvo no Supabase. Falta testar entrega real.
- Site URL e retornos básicos configurados. Acrescentar o retorno de recuperação descrito abaixo.
- Hospedagem e integração GitHub adiadas. Organização compartilhada será retomada depois.
- Cadastro e privacidade implementados localmente nas migrations `0014` a `0016` e no frontend.
  Feedback individual, métricas e primeira entrega sob demanda ainda são próximas etapas.

Use sempre o projeto Supabase **`xrhvjwemmylwbqgluebc`**, da região de São Paulo. O projeto
`bnzogphdvpubtkcflcue` não é o banco do Radar.

## 1. Criar o contato — pode fazer agora

No Cloudflare, abra **Email Service → Email Routing**, selecione `radarestagio.com` e cadastre
o domínio. Adicione e verifique o e-mail pessoal de destino. Em **Routing Rules**, crie
`contato` → encaminhar para esse destino. Confira os registros DNS propostos antes de salvar.
Envie uma mensagem de outra conta para `contato@radarestagio.com`; confira a caixa e o spam.
[Instruções do Cloudflare](https://developers.cloudflare.com/email-service/get-started/route-emails/).

O encaminhamento resolve o recebimento. Combine com Ian e Miguel quem acompanhará e responderá
as mensagens. O envio automático da confirmação será configurado separadamente no Resend.

**Concluído quando:** a mensagem chega e vocês conseguem responder ao remetente.

## 2. Revisar os documentos e combinar a manutenção

Revise com Ian os [Termos](../web/termos.html) e a [Política](../web/privacidade.html).
Miguel também está identificado como responsável pelos dados. Registrem:

- Concordância com a descrição do serviço, dados, fornecedores e retenção de 60 dias.
- Bases legais por finalidade e condições de processamento internacional, logs e backups,
  conferidas nos serviços contratados; esses pontos ainda estão abertos nos rascunhos.
- Quem atenderá solicitações de dados e pedidos de eliminação sem aguardar arrependimento.
- Quem acompanha falhas do job e a rotina de apagamento.
- Quem paga a renovação do domínio, a data e o destino do domínio e das contas ao fim da disciplina.

Não retire o aviso de revisão antes de resolver as passagens pendentes e implementar as
promessas. Use a [lista de revisão](revisao-cadastro-e-privacidade.md).

**Concluído quando:** texto final revisado, contato ativo e responsabilidades registradas.

## 3. Configurar Resend e SMTP — pode preparar agora

No Resend, adicione `radarestagio.com` em **Domains**. Copie para o Cloudflare os registros
DNS apresentados, respeitando seus nomes. Preserve os MX de recebimento do contato.
Aguarde a verificação do domínio e crie uma chave de API para envio.

No Supabase, abra **Authentication → Email → SMTP Settings**, habilite SMTP personalizado:

| Campo | Valor |
|---|---|
| Sender name | `Radar de Estágio` |
| Sender email | `contato@radarestagio.com` |
| Host | `smtp.resend.com` |
| Port | `465` |
| Username | `resend` |
| Password | Chave de API do Resend |

Salve a chave diretamente nesse campo. Ela não entra no frontend nem no Git.
[Configuração oficial do Resend](https://resend.com/docs/send-with-supabase-smtp).

Confira os limites de envio tanto no Supabase Auth quanto na conta Resend para comportar
10 a 20 cadastros e seus reenvios. SMTP próprio continua sujeito a limites. Nos templates de
confirmação e recuperação, use português e o nome Radar de Estágio, preservando o link de
ação do Supabase. [SMTP no Supabase](https://supabase.com/docs/guides/auth/auth-smtp).

**Concluído quando:** uma confirmação real chega à conta de teste com o remetente correto.
A tela de recuperação está implementada localmente; falta conferir o fluxo com envio real.

## 4. Hospedar o site e associar o domínio

Quando as alterações estiverem no GitHub, abra **Workers & Pages → Create application →
Pages → Import an existing Git repository** e escolha o repositório do Radar:

| Campo | Valor |
|---|---|
| Production branch | `main` |
| Framework preset | Nenhum |
| Root directory | Raiz do repositório |
| Build command | `exit 0` |
| Build output directory | `web` |

Confira o endereço `*.pages.dev`. Publique somente a pasta `web`.
[HTML estático no Pages](https://developers.cloudflare.com/pages/framework-guides/deploy-anything/).

No projeto Pages, abra **Custom domains** e adicione `radarestagio.com`. Faça a associação
pelo Pages antes de criar registros manualmente. Aguarde domínio e HTTPS ativos. Se usar
`www`, associe-o também e configure seu redirecionamento ao domínio principal.
[Domínios no Pages](https://developers.cloudflare.com/pages/configuration/custom-domains/).

**Concluído quando:** início, Termos e Privacidade abrem em HTTPS, inclusive no celular.
Publicação para conferir não libera o piloto: os bloqueadores da seção 9 continuam valendo.

## 5. Configurar o retorno do Auth

Em **Authentication → URL Configuration**, preencha:

| Campo | Valor |
|---|---|
| Site URL | `https://radarestagio.com` |
| Redirect URLs | `https://radarestagio.com` e `https://radarestagio.com/` |
| Desenvolvimento local | `http://localhost:8000` e `http://localhost:8000/` |

Inclua o endereço provisório exato se testar confirmação nele. Mantenha confirmação de e-mail
habilitada. Inclua também `https://radarestagio.com/?fluxo=recuperar` e, para teste local,
`http://localhost:8000/?fluxo=recuperar`, usados pela recuperação implementada.
[URLs de retorno do Supabase](https://supabase.com/docs/guides/auth/redirect-urls).

**Concluído quando:** a confirmação volta ao domínio correto. O teste em outro aparelho
deve ser repetido após aplicar a `0014` e publicar o frontend atualizado.

## 6. Preparar Turnstile — ativar a exigência só depois do código

No Cloudflare Turnstile, crie um widget gerenciado para `radarestagio.com`. Adicione outros
hostnames apenas se usados nos testes. Guarde a **site key** pública para o frontend e a
**secret key** para **Authentication → Bot and Abuse Protection → CAPTCHA**, no Supabase.

**A integração está pronta localmente e inerte**, com `turnstileSiteKey` vazio. Preencha essa
chave pública e disponibilize o frontend atualizado antes de exigir CAPTCHA no Supabase.
Depois escolha Turnstile no Supabase, habilite e teste cadastro,
login, reenvio e recuperação, incluindo expiração do desafio.
[CAPTCHA no Supabase](https://supabase.com/docs/guides/auth/auth-captcha).

**Concluído quando:** os fluxos passam com token válido e o servidor recusa token inválido.

## 7. Configurar rastreamento e publicar funções

| Onde | Nome | Valor |
|---|---|---|
| Supabase → Edge Functions → Secrets | `URL_DA_LANDING` | `https://radarestagio.com` |
| GitHub → Settings → Secrets and variables → Actions | `URL_DE_RASTREIO` | `https://xrhvjwemmylwbqgluebc.supabase.co/functions/v1/ir` |

Preserve os secrets existentes `TELEGRAM_BOT_TOKEN` e `TELEGRAM_WEBHOOK_SECRET` das funções.
As credenciais de banco das funções são fornecidas pelo ambiente Supabase. Nenhum segredo
entra em `web/config.js`; ali só cabe a chave publicável do projeto.

Após as correções e testes de privacidade e feedback, publique `ir` e republique
`telegram-webhook` no projeto correto. `supabase/config.toml` já define `verify_jwt = false`
para ambas: o webhook verifica o segredo do Telegram, e `ir` atende os links do navegador.

Confira a configuração do webhook: URL da função, mesmo segredo e `allowed_updates` contendo
`message` e `callback_query`. O plano registra isso como corrigido; não precisa rotacionar
o segredo apenas para republicar.

**Concluído quando:** abrir vaga grava `vaga_aberta`, token inválido volta à landing e cada
feedback grava o evento correto. Links antigos de conta excluída não podem gerar novos eventos.

## 8. Preparar a primeira entrega após vínculo

O workflow atual só aceita `workflow_dispatch`. A execução sob demanda ainda precisa ser
implementada. Depois disso, crie um token GitHub restrito ao repositório do Radar, com
**Contents: write**, para `repository_dispatch`. Defina expiração e responsável pela renovação.
Guarde-o em secret da Edge Function, com o nome que a implementação passar a consumir; esse
nome ainda não existe no código. [Permissão do GitHub](https://docs.github.com/en/rest/repos/repos#create-a-repository-dispatch-event).

Preserve a autorização e o agendamento do cron-job.org às 07:23 de Brasília. O token do
dispatch sob demanda é separado; não adicione um segundo agendador diário.

**Concluído quando:** vínculo dispara apenas o perfil vinculado, repetição não duplica envio,
a janela de 06:23 a 07:23 aguarda o diário e os demais perfis continuam atendidos.

## 9. Código e validação antes do piloto

Implementado e testado localmente, ainda sem publicação:

- `0014`: consentimento, versão aceita e perfil criado na confirmação a partir de cópia protegida.
- Cadastro com checkboxes separados, revelar senha e sessão de origem preservada.
- Confirmação entre aparelhos e reenvio com e-mail editável e espera de um minuto.
- Turnstile opcional, recuperação de senha, `0015` para baixar dados e revogação de e-mails.
- Revalidação do destinatário no job e nas funções, com `0016` impedindo novos eventos de vaga
  para contas pausadas, excluídas ou desvinculadas.

Ainda falta implementar:
- Feedback individual com seis opções, incluindo positivo e motivo da nota incorreta.
- Funil completo, vagas distintas, utilidade semanal e denominadores das recusas.
- Pipeline por perfil e dispatch após vínculo, sem duplicar envios concorrentes.
- Alinhar vocabulário e métricas: candidatura continua sem emissor por decisão do plano.

A `0013` aplicada não será reescrita. Testar e revisar as novas migrations antes de aplicar
no banco remoto, sempre pelo histórico de migrations. Depois da integração e revisão final,
retirar os avisos de rascunho das páginas e registrar versão/data coerentes com o aceite.

## 10. Conferência final com conta de teste

Use dados sintéticos e seus próprios endereços e Telegram:

- Cadastro sem aceite é recusado; e-mails opcionais começam desmarcados.
- Cadastro no computador e confirmação no celular recuperam o perfil correto.
- Link expirado, reenvio e login antes da confirmação têm saídas claras.
- Recuperação troca a senha e permite entrar com a nova senha.
- Vínculo, primeira entrega, links e seis opções de feedback funcionam conforme os planos.
- Edição, pausa, retomada, desvínculo e preferência de e-mail persistem após novo login.
- Download contém só os dados do dono, sem credenciais.
- Exclusão interrompe novas entregas/eventos e libera o chat; cancelamento preserva a pausa.
- Apagamento após a carência passa em ambiente de teste com datas controladas, incluindo duas
  contas no mesmo navegador. Não envelheça contas reais para testar.
- Métricas refletem os eventos e não contam cliques repetidos como vagas diferentes.

**Concluído quando:** resultados registrados e falhas corrigidas. Identifique as contas e
sessões de teste para separá-las das métricas do piloto.

## 11. Conduzir o piloto

Convide 10 a 20 estudantes por canais identificados, acompanhe por duas semanas e faça cinco
entrevistas. Confira diariamente falhas de confirmação e entrega. Meça a proporção semanal
de estudantes ativados com feedback positivo em ao menos uma recomendação; abertura sozinha
não prova utilidade.

Meça extrações, duração e custo com a diversidade real de cidades e áreas, que pode ampliar
as vagas elegíveis. Para avaliar o ranking, compare recusas com entregas de cada grupo;
não ajuste pesos por contagens brutas. Candidatura não será medida nesta versão.

Apagar contas abandonadas, reescrever o histórico Git e remover as skills não são pendências
deste lançamento: os planos já adiaram ou encerraram essas decisões.
