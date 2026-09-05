# Revisão dos documentos e sequência de implementação

**Estado: rascunhos e páginas HTML preparados; revisão final de Igor e Ian pendente.**

Em 05/09, Igor autorizou continuar localmente sem deploy. Cadastro, consentimento, reenvio,
recuperação, exportação e proteção das interações foram implementados e testados com mocks
de autenticação e PostgreSQL isolado. As migrations `0014`–`0016` não foram aplicadas no
projeto remoto; os avisos de revisão permanecem nas páginas. A sequência abaixo registra o
plano original, com os passos 1 a 4 preparados localmente e os passos 5 a 7 ainda pendentes.

O usuário autorizou criar as páginas para prosseguir com a preparação. Elas estão em
`web/termos.html` e `web/privacidade.html`, com aviso de revisão, sem vigência e ainda sem
publicação remota. O [guia de publicação e piloto](guia-publicacao-e-piloto.md) reúne as ações
externas e as dependências de implementação.

O passo 1 da seção 4 do [plano de cadastro](plano-cadastro-e-privacidade.md) determina:
“Escrever os dois documentos; Igor e Ian revisam antes de qualquer código”. Os textos para
essa revisão são os [Termos de Uso](termos-de-uso.md) e a
[Política de Privacidade](politica-de-privacidade.md). Não são documentos publicados nem textos
em vigor. O usuário confirmou o domínio `radarestagio.com` e os responsáveis Igor Costa, Ian Dias e Miguel Esteves. O endereço escolhido para contato é `contato@radarestagio.com`; o recebimento foi testado e confirmado por Igor em 05/09.

## O que revisar agora

- Recebimento em `contato@radarestagio.com` confirmado; combinar a rotina de atendimento.
- Revisar a descrição do serviço, das recomendações e das limitações das fontes.
- Revisar a retenção de 60 dias para arrependimento e o tratamento de pedidos de eliminação
  que não desejem aguardar esse prazo. A existência do prazo no código não comprova, sozinha,
  sua adequação jurídica.
- Definir e registrar a base legal por finalidade, em particular para métricas associadas à
  conta. Aceitar a política não deve virar consentimento genérico para todo tratamento.
- Confirmar condições de transferência internacional, logs e backups dos fornecedores e
  preencher as passagens de revisão antes de publicar.

## Promessas que dependem de implementação

| Trecho dos rascunhos | Condição para publicar |
|---|---|
| Feedback positivo e sobre a nota | Trocar o teclado diário por feedback individual com as seis opções do plano geral |
| Primeira busca após o vínculo | Dispatch autenticado, pipeline por perfil e janela de 06:23 a 07:23 de Brasília |
| Preferência por e-mails e versão aceita | Implementadas localmente; aplicar `0014` com o frontend atualizado e a versão final dos documentos |
| Download dos dados | RPC `0015` e botão implementados; testar no ambiente integrado |
| Recuperação de senha | Implementada localmente; testar o e-mail real e o retorno autorizado |
| Cloudflare, Turnstile e Resend | Configurar e verificar os serviços antes de apresentá-los como ativos |
| Interrupção após exclusão | Implementada no job, nas funções e na `0016`; disponibilizar as três partes e validar a integração |

O banco e a rotina de exclusão foram conferidos no código, não no ambiente remoto. A migration
`0013` permanece intacta. O prazo de apagamento depende da execução diária; não se deve prometer
apagamento em um horário exato nem extensão desse apagamento a mensagens já no Telegram.

## Sequência após a revisão

1. Concluir os textos e criar `web/termos.html` e `web/privacidade.html`, com links no rodapé.
2. Criar a migration `0014` para consentimento e criação de perfil após confirmação, preservando
   a sessão de origem do funil. Validar dados de metadata no banco e impedir alteração do aceite
   histórico por update direto do cliente.
3. Integrar cadastro, confirmação entre aparelhos, reenvio com espera de um minuto, revelação
   de senha e Turnstile; depois recuperação de senha, exportação e revogação no painel.
4. Fechar as três lacunas de processamento após exclusão, com verificação do vínculo atual.
5. Implementar feedback por vaga e corrigir métricas: funil desde a visita, vagas distintas,
   recorte semanal e denominador das recusas por grupo de recomendações entregues.
6. Implementar primeira entrega por perfil. Verificar autenticação do dispatch, repetição do
   webhook e concorrência com a execução diária para evitar entregas duplicadas.
7. Publicar a landing, configurar Auth, DNS, SMTP e secrets, aplicar a nova migration e publicar
   as funções. Verificar os fluxos com uma conta de teste antes de recrutar o piloto.

Cada decisão de código segue uma fatia própria com a suíte executada separadamente, conforme
`CLAUDE.md`. A publicação e a aplicação remota ainda não foram feitas nesta preparação.
