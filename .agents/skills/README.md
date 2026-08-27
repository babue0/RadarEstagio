# Skills do RadarEstágio

Este diretório reúne as instruções reutilizáveis que orientam os agentes durante o desenvolvimento do projeto. Cada skill possui seu próprio `SKILL.md`, que é a fonte completa das regras e do fluxo de trabalho.

## Skills disponíveis

| Skill | Resumo | Quando usar |
| --- | --- | --- |
| `grilling` | Entrevista o responsável pelo projeto para eliminar dúvidas e testar decisões antes da implementação. | Quando uma ideia, requisito ou decisão ainda estiver pouco definida. |
| `domain-modeling` | Mantém o vocabulário do domínio e registra decisões duradouras em `CONTEXT.md` e ADRs. | Ao definir ou alterar conceitos como Vaga, Perfil, Compatibilidade, Coleta e Entrega. |
| `codebase-design` | Orienta a criação de módulos profundos, interfaces pequenas e limites testáveis. | Ao desenhar ou refatorar as camadas de domínio, coleta, matching e notificação. |
| `tdd` | Conduz ciclos curtos de vermelho, verde e refatoração, priorizando comportamento e interfaces públicas. | Ao implementar funcionalidades ou corrigir defeitos com `pytest`. |
| `humanizer` | Reescreve textos artificiais ou genéricos sem alterar fatos e significado. | Ao revisar documentação, mensagens do Telegram e textos voltados ao usuário. |
| `revenue-centric-design` | Reúne princípios de produto para aquisição, ativação, retenção, monetização e posicionamento. | Ao planejar landing pages, onboarding, modelo de receita, métricas ou estratégia de produto. |
| `handoff` | Cria ou atualiza um `HANDOFF.md` com o contexto necessário para continuar o trabalho. | Antes de encerrar uma conversa e transferir a tarefa para outro agente. |

## Fluxo recomendado

1. Use `grilling` quando uma ideia ou decisão ainda precisar ser esclarecida.
2. Use `domain-modeling` quando termos ou decisões duradouras precisarem ser documentados.
3. Aplique `codebase-design` ao definir interfaces e limites entre módulos.
4. Implemente em ciclos curtos de vermelho, verde e refatoração com `tdd`.
5. Use `humanizer` quando o resultado incluir texto destinado a pessoas.
6. Consulte `revenue-centric-design` nas decisões de produto, experiência e monetização.
7. Use `handoff` quando outro agente precisar continuar o trabalho em uma nova conversa.

## Origem

- `humanizer`: [blader/humanizer](https://github.com/blader/humanizer), licença MIT.
- Skills de engenharia: [mattpocock/skills](https://github.com/mattpocock/skills), licença MIT.
- `revenue-centric-design`: [heliocosta-dev/revenue-centric-design](https://github.com/heliocosta-dev/revenue-centric-design), licença própria com atribuição obrigatória e proibição de uso em apostas, cassinos e jogos de azar.
- `handoff`: [ykdojo/claude-code-tips](https://github.com/ykdojo/claude-code-tips/tree/main/skills/handoff).

A instalação de `revenue-centric-design` é enxuta: mantém as referências textuais e a licença, mas omite os recursos multimídia e os scripts opcionais de atualização.

As cópias deste diretório são versionadas com o projeto. Atualizações das fontes não são aplicadas automaticamente e devem ser revisadas antes de entrar no repositório.
