# Política de Privacidade — Radar de Estágio

**Rascunho para revisão de Igor e Ian. Não publicado e ainda sem vigência.**

Este texto descreve a versão prevista para o piloto. As condições para publicá-lo estão em
[revisão dos documentos](revisao-cadastro-e-privacidade.md).

## 1. Responsáveis e contato

Igor Costa, Ian Dias e Miguel Esteves são os responsáveis pelas decisões sobre o tratamento
dos dados pessoais no projeto acadêmico Radar de Estágio.

Site: https://radarestagio.com.
Para assuntos de privacidade e pedidos sobre seus dados: [contato@radarestagio.com](mailto:contato@radarestagio.com).

## 2. Dados utilizados

| Dados | Para que são usados |
|---|---|
| E-mail e dados de autenticação | Criar a conta, confirmar o endereço, permitir acesso e recuperar a senha. A autenticação é gerenciada pelo Supabase, que armazena um hash da senha |
| Curso, período, habilidades, cidade, modalidade e áreas de interesse | Selecionar vagas e calcular a compatibilidade |
| Identificador do chat do Telegram | Vincular a conta e entregar mensagens |
| Recomendações, notas, explicações e histórico de envio | Entregar oportunidades, evitar repetições e verificar o funcionamento |
| Aberturas dos links e feedback sobre vagas | Medir o uso e a utilidade das recomendações e identificar problemas na seleção |
| Identificador de sessão e eventos de navegação e cadastro | Entender o percurso entre a visita ao site, o cadastro e o uso do Radar |
| Registro de aceite dos termos e preferência por e-mails | Registrar a versão aceita e respeitar sua escolha de comunicação |
| Datas de criação, atualização, ativação, pausa e pedido de exclusão, além de falhas de entrega | Operar a conta e executar seus controles |

O identificador de sessão não contém seu nome, mas pode ser associado à conta ao longo do
cadastro. Por isso, não tratamos esse histórico como informação irreversivelmente anônima.
As propriedades dos eventos são destinadas a informações sobre o uso do produto, sem campos
de texto livre para dados pessoais.

O navegador guarda dados da sessão de acesso e um identificador local usado nas métricas.
O fluxo de cadastro também pode manter temporariamente um perfil pendente no dispositivo.
Provedores de hospedagem, autenticação e proteção contra abuso processam dados técnicos das
requisições, como endereço IP e informações do navegador, conforme a configuração de cada
serviço.

## 3. Finalidades e escolhas

Usamos os dados necessários à conta e às recomendações para prestar o serviço solicitado.
O cadastro exige os dados indicados no formulário; sem um Telegram vinculado, não há entrega
de recomendações por esse canal.

O envio de e-mails ocasionais depende de uma escolha separada, inicialmente desmarcada.
Recusar ou revogar essa escolha não impede o uso do Radar. Você pode alterá-la no painel.
Confirmação de e-mail e recuperação de senha são comunicações necessárias à conta.

As métricas ajudam a identificar abandono do cadastro, falhas de entrega e recomendações que
não serviram. A justificativa e a base legal desse tratamento devem ser documentadas pelos
responsáveis antes da publicação desta política.

## 4. Serviços envolvidos

| Serviço | Dados envolvidos e finalidade |
|---|---|
| Supabase | Conta, perfil e histórico do produto, para autenticação e armazenamento |
| Telegram | Identificador do chat, mensagens de recomendação e interações com o bot |
| Google Gemini | Texto e informações dos anúncios, para extração de requisitos; o Radar não inclui o perfil do estudante nesse processamento |
| Adzuna e Gupy | Termos de busca, incluindo a cidade de perfis presenciais ou híbridos, sem identificador individual do estudante |
| GitHub Actions | Perfil, identificador do chat e dados de recomendações, processados durante a execução automatizada |
| Cloudflare | Tráfego do site e dados técnicos da verificação contra abuso pelo Turnstile |
| Resend | Endereço de e-mail e conteúdo das mensagens de conta, para envio pelo remetente do Radar |

O banco ativo do projeto está configurado na região de São Paulo. Isso não significa que todos
os fornecedores processem dados exclusivamente no Brasil. As condições de processamento
internacional e retenção dos fornecedores precisam ser confirmadas antes da publicação.

Ao abrir uma vaga, você é redirecionado ao site da fonte. O tratamento feito por esse site,
inclusive dos dados da candidatura, segue as regras dele.

## 5. Seleção automatizada

A inteligência artificial extrai informações dos anúncios. O código do Radar compara essas
informações com seu perfil para produzir a nota e a explicação. O Radar não toma decisões de
contratação. Você pode corrigir seu perfil, dar feedback por vaga e pedir esclarecimentos aos
responsáveis sobre uma recomendação.

## 6. Retenção e exclusão

Os dados associados à conta são mantidos enquanto ela existir. Pausar as entregas ou
desvincular o Telegram não elimina o perfil nem o histórico.

O pedido de exclusão no painel marca a conta e remove seu vínculo com o Telegram. O prazo de
60 dias permite cancelar o pedido. Ao terminar esse prazo, a rotina diária apaga a conta,
o perfil, as avaliações, os envios e os eventos ligados à conta. Também apaga os eventos sem
dono das sessões identificadas como associadas à conta, sem apagar eventos pertencentes a
outras contas que usaram o mesmo navegador.

Anúncios públicos de vagas podem permanecer no catálogo. Mensagens já recebidas no Telegram
e dados enviados aos sites de candidatura não são removidos por essa rotina. O apagamento do
banco também não limpa automaticamente o armazenamento local dos seus outros dispositivos.

Não há rotina de exclusão automática de contas apenas por inatividade. Prazos de logs e cópias
de segurança dos fornecedores serão registrados após conferência das configurações; este
rascunho não promete eliminação imediata dessas cópias.

## 7. Seus direitos e controles

O painel permite corrigir o perfil, controlar as entregas, revogar e-mails opcionais, baixar
uma cópia dos dados e solicitar ou cancelar a exclusão no prazo indicado.

Você também pode solicitar confirmação do tratamento, acesso, correção, informações sobre
compartilhamento, portabilidade nos termos aplicáveis e exclusão ou bloqueio quando cabíveis.
Pedidos sobre decisões automatizadas podem ser enviados pelo mesmo canal. Esses direitos
decorrem da [LGPD](https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709compilado.htm),
especialmente dos artigos 18 a 20.

Envie seu pedido a [contato@radarestagio.com](mailto:contato@radarestagio.com). Podemos precisar confirmar sua identidade para
evitar entregar seus dados a outra pessoa. O download do painel não inclui senhas, hashes,
tokens de acesso ou credenciais dos serviços.

## 8. Atualizações

A versão publicada terá data de vigência. Alterações relevantes serão informadas no site.
Novas finalidades que exijam consentimento terão uma escolha específica apresentada antes
do início desse uso.
