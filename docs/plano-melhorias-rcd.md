# Plano de Melhorias — Revenue-Centric Design

**Projeto:** Radar de Estágio

**Data:** 30/08/2026

**Horizonte inicial:** seis semanas

**Framework:** Revenue-Centric Design (RCD)

**Fase atual do produto:** Fase 2 — MVP de validação com usuários, parcialmente implementada

**Estado atual:** banco, cadastro web, múltiplos usuários, vínculo com o Telegram e evento de
ativação já estão implementados; a validação com usuários e os recursos de retenção continuam
pendentes.

## 1. Objetivo

Transformar o Radar de uma demonstração técnica funcional em um produto capaz de comprovar que:

1. estudantes concluem o cadastro;
2. recebem valor rapidamente;
3. consideram as recomendações úteis;
4. continuam usando o serviço;
5. candidatam-se por causa do Radar;
6. uma parcela aceita pagar pelo resultado.

A ordem de trabalho será:

> **corrigir → medir → ativar → reter → provar → monetizar → diferenciar**

Essa sequência segue o princípio de adequar o trabalho de produto ao estágio atual: no MVP,
encurtar o caminho até o valor; depois ativar, converter, expandir e sistematizar
([referência RCD](https://x.com/richardrx/status/2066476811177877962)).

## 2. Métricas centrais

### 2.1 North Star inicial

> **Percentual de estudantes ativados que encontram pelo menos uma vaga útil por semana.**

### 2.2 Resultado final de negócio

> **Candidaturas qualificadas iniciadas por usuário ativado por semana.**

### 2.3 Definições

- **Ativação:** primeira entrega aceita pelo Telegram contendo ao menos uma vaga recomendada.
- **Vaga útil:** recomendação marcada pelo usuário como relevante ou que gera abertura do anúncio.
- **Candidatura qualificada:** candidatura iniciada a partir de uma recomendação considerada útil.
- **TTV:** tempo entre a criação do perfil e a primeira entrega relevante.
- **Retenção D7:** usuário que volta a interagir com ao menos uma recomendação na semana seguinte.

## 3. Fase 0 — Estabilizar para a entrega

**Prazo:** até 02/09/2026

**Objetivo:** não demonstrar um funil quebrado ou uma promessa que o produto não entrega.

### 3.1 Corrigir o cadastro

**Status:** concluída em 30/08/2026.

- Validar a etapa 3 antes do envio.
- Impedir cidade, modalidade, e-mail ou senha inválidos.
- Tratar o caso de conta criada sem perfil salvo.
- Traduzir erros técnicos do Supabase para mensagens humanas e acionáveis.
- Criar testes para cada falha possível do último passo.

**Critério de conclusão:** nenhum dado inválido chega ao Supabase e todo erro informa como o
usuário pode continuar.

### 3.2 Alinhar promessa e produto

**Status:** concluída em 30/08/2026.

- Remover dos documentos a afirmação de que o Radar aprende com feedback enquanto isso não existir.
- Não prometer edição do perfil sem oferecer a interface correspondente.
- Substituir “Chegue antes” por uma promessa comprovável ou medir o tempo real entre publicação,
  detecção e entrega.
- Atualizar a fase declarada do projeto, pois partes relevantes da Fase 2 já estão implementadas.
- Atualizar números antigos de testes e evidências técnicas.

### 3.3 Tornar a mensagem real igual à demonstração

**Status:** concluída em 30/08/2026.

A mensagem do Telegram agora inclui:

- localização e modalidade, quando informadas;
- fonte da vaga;
- data de publicação;
- nota e justificativa;
- pontos a favor e contra;
- link original.

**Critério de conclusão:** tudo que aparece na demonstração da landing existe na entrega real.

### 3.4 Preparar a apresentação

**Status:** concluída em 30/08/2026. O roteiro está em [`docs/apresentacao.md`](apresentacao.md).

Apresentar separadamente:

- o que foi tecnicamente comprovado;
- o que ainda é hipótese de produto;
- o evento de ativação;
- o risco relacionado ao tempo até o primeiro valor;
- o plano de validação com usuários.

## 4. Fase 1 — Instrumentar o funil

**Prazo:** semana 1

**Objetivo:** localizar cada vazamento antes de redesenhar ou expandir o produto.

### 4.1 Eventos mínimos

**Status:** instrumentação da jornada existente concluída em 30/08/2026.

- `landing_visualizada`
- `cta_cadastro_aberto`
- `etapa_perfil_concluida`
- `etapa_habilidades_concluida`
- `etapa_preferencias_concluida`
- `conta_criada`
- `email_confirmado`
- `perfil_salvo`
- `telegram_aberto`
- `telegram_vinculado`
- `primeira_recomendacao_enviada`
- `vaga_aberta`
- `vaga_util`
- `vaga_irrelevante`
- `candidatura_iniciada`
- `entregas_pausadas`

Os eventos da landing ao primeiro envio são registrados no Supabase. Eventos que dependem de
interações ainda inexistentes — `vaga_aberta`, `vaga_util`, `vaga_irrelevante` e
`candidatura_iniciada` — já pertencem ao contrato, mas só serão emitidos quando o link rastreável
e os botões de feedback forem implementados. Isso evita registrar intenção sem ação real.

### 4.2 Métricas do funil

- Landing → abertura do cadastro.
- Cadastro aberto → perfil salvo.
- Perfil salvo → Telegram vinculado.
- Telegram vinculado → primeira recomendação.
- Taxa de ativação em 24 horas e em 7 dias.
- TTV mediano.
- Recomendação → clique.
- Recomendação → vaga útil.
- Recomendação → candidatura.
- Retenção D7 por interação real.
- Custo de IA por usuário ativado.

Com baixo volume, não serão usados testes A/B. Cinco boas entrevistas e observação de sessões
produzem mais sinal que um experimento sem amostra suficiente
([referência RCD](https://x.com/richardrx/status/2061463480868229189)).

**Critério de conclusão:** uma consulta consegue reconstruir o funil completo de cada coorte.

## 5. Fase 2 — Reduzir o tempo até o primeiro valor

**Prazo:** semana 2

**Objetivo:** entregar a primeira recomendação em minutos, não no dia seguinte.

### 5.1 Jornada desejada

```text
Perfil → conta → Telegram → busca imediata → primeira recomendação
```

Depois do vínculo:

1. mostrar “Telegram vinculado”;
2. informar que o Radar está procurando a primeira oportunidade;
3. executar uma busca específica para o novo perfil;
4. entregar uma recomendação real imediatamente;
5. celebrar o primeiro resultado;
6. registrar `ativado_em`.

O onboarding só termina quando o usuário experimenta o resultado prometido. A prioridade é
reduzir o TTV, não adicionar mais explicações ou funcionalidades
([referência RCD](https://x.com/richardrx/status/2059616501544468624)).

### 5.2 Quando não houver vaga adequada

- Não marcar o perfil como ativado.
- Explicar que nenhuma oportunidade segura foi encontrada.
- Informar quando ocorrerá a próxima busca.
- Oferecer ajuste de cidade ou modalidade.
- Não pressionar o usuário a aceitar vagas ruins apenas para gerar uma entrega.

### 5.3 Metas iniciais

- TTV mediano abaixo de 15 minutos.
- Evolução posterior para menos de 5 minutos.
- Pelo menos 80% dos usuários vinculados recebendo valor em 24 horas.

Esses limites devem ser aprovados antes do piloto e não ajustados posteriormente para justificar
os resultados observados.

## 6. Fase 3 — Dar controle e construir retenção

**Prazo:** semana 3

**Objetivo:** descobrir se as recomendações ajudam e acumular personalização.

### 6.1 Feedback no Telegram

Cada vaga deve permitir:

- `👍 Faz sentido`
- `👎 Não serve para mim`
- `Candidatei-me`
- `Vaga encerrada ou problemática`

Inicialmente, o feedback deve apenas ser registrado. O ranking não deve ser alterado
automaticamente com poucos dados.

### 6.2 Gestão do perfil

Criar uma página simples, sem transformá-la em um dashboard completo:

- editar curso, período e habilidades;
- alterar cidade e modalidade;
- pausar e retomar entregas;
- desvincular Telegram;
- excluir conta e dados;
- consultar quando ocorrerá a próxima busca.

### 6.3 Cadência de comunicação

- Evitar mensagens vazias diárias que possam gerar fadiga.
- Avaliar silêncio nos dias sem vagas, acompanhado por um resumo semanal.
- Manter alertas imediatos somente para oportunidades realmente relevantes.
- Observar se o usuário prefere confirmação diária ou apenas novidades.

### 6.4 Segurança e confiança

- Invalidar ou rotacionar o token após o vínculo.
- Impedir que um link antigo redirecione entregas para outro Telegram.
- Criar uma explicação curta de privacidade e finalidade dos dados.
- Oferecer exclusão dos dados sem contato manual.

**Critério de conclusão:** o usuário consegue controlar o serviço e toda recomendação pode gerar
um sinal mensurável de qualidade.

## 7. Fase 4 — Validar produto e construir prova

**Prazo:** semana 4

**Objetivo:** substituir promessas genéricas por evidências reais.

### 7.1 Piloto

Recrutar de 10 a 20 estudantes que atendam aos critérios:

- universitários de tecnologia;
- buscando o primeiro estágio no momento do teste;
- dispostos a usar Telegram durante duas semanas.

Cada pessoa deve ser acompanhada desde a landing até a primeira candidatura.

### 7.2 Entrevistas

Realizar pelo menos cinco entrevistas aprofundadas:

- Como a pessoa procura estágio hoje?
- Quanto tempo gasta por semana?
- O que faz uma vaga parecer relevante?
- Em quais notas e justificativas confia?
- Telegram é conveniente ou uma barreira?
- Qual recomendação foi útil?
- Por que as outras foram ignoradas?
- O que precisaria acontecer para a pessoa pagar pelo Radar agora?

### 7.3 Landing baseada em prova

Depois do piloto, substituir a faixa de tecnologias por evidências como:

- estudantes ativados;
- recomendações consideradas úteis;
- candidaturas iniciadas;
- TTV mediano;
- depoimento verificável com contexto;
- captura anonimizada de uma recomendação real.

A promessa comercial deve crescer apenas na proporção da prova disponível. Quando landing e
produto divergem, cria-se dívida de expectativa e churn futuro
([referência RCD](https://x.com/richardrx/status/2049568514311172355)).

### 7.4 Copy inicial recomendada

**Headline:**

> Pare de garimpar vagas de estágio todos os dias.

**Subheadline:**

> Receba no Telegram oportunidades de tecnologia compatíveis com seu curso, período e
> habilidades — ranqueadas e explicadas.

**CTA:**

> Montar meu Radar grátis

**Microcopy:**

> Cerca de 2 minutos · sem cartão · o Radar nunca se candidata por você

A microcopy deve explicar o que acontece, quanto demora e qual é o compromisso
([referência RCD](https://x.com/richardrx/status/2058875777739866490)).

## 8. Fase 5 — Validar monetização

**Prazo:** semana 5

**Objetivo:** descobrir se existe disposição real a pagar sem construir uma página de preços
prematuramente.

### 8.1 Calcular os unit economics

- Custo de IA por usuário.
- Custo por busca.
- Custo por usuário ativado.
- Custo de suporte.
- Vida útil esperada de um usuário procurando estágio.
- Quantidade de pagantes necessária para sustentar cada usuário gratuito.

O custo gratuito precisa ser tratado explicitamente: em um produto de IA, o usuário gratuito
continua consumindo recursos variáveis
([referência RCD](https://x.com/richardrx/status/2071962778072469560)).

### 8.2 Hipóteses de modelo

Testar uma hipótese por vez:

1. passe de busca ativa por 30 ou 60 dias;
2. assinatura mensal enquanto o estudante estiver procurando;
3. plano gratuito limitado e entrega diária paga;
4. acesso patrocinado por faculdade ou programa de empregabilidade.

O passe pode se ajustar melhor ao churn estrutural: quando o estudante consegue estágio, o
trabalho para o qual contratou o produto termina.

### 8.3 Teste de transação

- Oferecer um piloto pago aos primeiros dez usuários.
- Entregar uma primeira prova de valor antes de cobrar.
- Pedir pagamento real, não apenas perguntar “você pagaria?”.
- Quando alguém recusar, perguntar o que precisaria existir para pagar.
- Considerar a hipótese promissora se pelo menos três dos dez aceitarem o compromisso financeiro
  definido antes do teste.

Ainda não criar uma estrutura Good–Better–Best, decoy ou página com três planos. Esses mecanismos
só fazem sentido depois de validar o produto e o eixo de valor.

## 9. Fase 6 — Diferenciação e moat

**Prazo:** semana 6 em diante

**Objetivo:** tornar o Radar progressivamente melhor para cada usuário e mais difícil de copiar.

O diferencial defensável não será Gemini, Telegram ou coleta de vagas isoladamente. Será:

- histórico de preferências reais;
- feedback sobre vagas específicas;
- padrões que antecedem candidaturas;
- personalização acumulada;
- confiança nas explicações;
- cobertura e deduplicação comprovadas;
- dados sobre quais oportunidades geram ação.

O feedback só deve influenciar automaticamente o ranking quando houver volume suficiente para
identificar padrões estáveis e evitar que poucos eventos distorçam a recomendação.

## 10. Estratégia inicial de distribuição

A distribuição só deve ser ampliada depois de corrigidos os vazamentos de cadastro e ativação.
Usando o framework Bullseye, o Radar deve concentrar o teste em até três canais:

1. grupos e turmas da própria universidade;
2. comunidades estudantis de tecnologia em Telegram, WhatsApp ou Discord;
3. coordenações de curso, centros acadêmicos e programas de empregabilidade.

Cada canal deve receber identificação de origem para comparar:

- visitantes;
- cadastros;
- ativações;
- vagas úteis;
- candidaturas;
- custo de aquisição, quando existir.

O canal não deve ser avaliado apenas pelo volume de cadastros, mas pela qualidade e retenção dos
usuários que traz ([referência RCD](https://x.com/richardrx/status/2036035304868434115)).

## 11. O que não construir agora

Pelo filtro **Swiss Knife**, ficam fora do roadmap imediato:

- dashboard completo;
- criador de currículo;
- candidatura automática;
- feed de conteúdo;
- cursos ou trilhas de estudo;
- tendências de mercado;
- novos modelos de IA sem evidência de problema;
- novas fontes antes de comprovar insuficiência das atuais;
- sistema de indicação antes de existir retenção;
- três ou mais planos de preço.

Cada funcionalidade nova deve responder:

1. Encurta o TTV?
2. Aumenta ativação?
3. Melhora a qualidade medida das vagas?
4. Aumenta retenção ou receita?
5. Qual custo permanente adiciona?

Se não passar por esses critérios, não entra no produto
([referência RCD](https://x.com/richardrx/status/2059236567533650119)).

## 12. Backlog priorizado

| Prioridade | Entrega | Fase |
| --- | --- | --- |
| P0 | Validar corretamente a etapa 3 | 0 |
| P0 | Alinhar landing, documentação e entrega real | 0 |
| P0 | Adicionar fonte, data, localização e modalidade à mensagem | 0 |
| P0 | Instrumentar o funil completo | 1 |
| P0 | Entregar a primeira recomendação imediatamente após o vínculo | 2 |
| P1 | Permitir editar, pausar e excluir o perfil | 3 |
| P1 | Adicionar feedback e candidatura no Telegram | 3 |
| P1 | Transformar o token de vínculo em uso único | 3 |
| P1 | Executar piloto com 10–20 estudantes | 4 |
| P1 | Construir prova social baseada em resultados | 4 |
| P2 | Testar pagamento com os primeiros dez usuários | 5 |
| P2 | Validar passe ou assinatura | 5 |
| P2 | Personalizar recomendações com feedback suficiente | 6 |
| P3 | Avaliar novas fontes, tendências e expansão de ICP | Posterior |

## 13. Portões de decisão

### Portão A — Funil íntegro

Avançar quando:

- não houver falhas bloqueantes no cadastro;
- landing, documentação e mensagem fizerem a mesma promessa;
- o funil puder ser medido de ponta a ponta.

### Portão B — Ativação comprovada

Avançar quando:

- a maioria dos usuários vinculados receber uma vaga relevante em até 24 horas;
- o TTV mediano estiver dentro do limite aprovado;
- as perdas entre perfil e Telegram forem conhecidas.

### Portão C — Retenção comprovada

Avançar quando:

- houver interação útil em D7;
- os motivos de rejeição das vagas forem conhecidos;
- o usuário conseguir editar, pausar e excluir seus dados.

### Portão D — Monetização validada

Avançar quando:

- o custo por usuário ativado estiver calculado;
- usuários reais aceitarem um pagamento definido previamente;
- o modelo escolhido cobrir o custo de atender usuários gratuitos e pagantes.

## 14. Regra de execução

Cada entrega deve incluir:

- hipótese explícita;
- métrica afetada;
- implementação mínima;
- teste automatizado proporcional ao risco;
- verificação manual de ponta a ponta;
- evento de produto correspondente;
- atualização da documentação;
- decisão de manter, ajustar ou remover com base no resultado.

O objetivo não é redesenhar o Radar do zero. É corrigir os vazamentos existentes, medir o efeito
e ampliar o produto somente quando o comportamento dos usuários justificar o próximo investimento.
