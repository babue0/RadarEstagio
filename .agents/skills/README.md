# Skills do RadarEstágio

Este diretório reúne as instruções reutilizáveis que orientam os agentes durante o desenvolvimento do projeto. Cada skill possui seu próprio `SKILL.md`, que é a fonte completa das regras e do fluxo de trabalho.

## Skills disponíveis

| Skill | Resumo | Quando usar |
| --- | --- | --- |
| `setup-matt-pocock-skills` | Configura o rastreador de tarefas, os rótulos de triagem e a estrutura da documentação de domínio. | Uma vez, antes do primeiro uso das demais skills de engenharia. |
| `grilling` | Entrevista o responsável pelo projeto para eliminar dúvidas e testar decisões antes da implementação. | Quando uma ideia, requisito ou decisão ainda estiver pouco definida. |
| `grill-with-docs` | Combina a entrevista da `grilling` com a atualização do glossário e dos registros de decisão. | Ao planejar funcionalidades ou mudanças arquiteturais que precisam ficar documentadas. |
| `domain-modeling` | Mantém o vocabulário do domínio e registra decisões duradouras em `CONTEXT.md` e ADRs. | Ao definir ou alterar conceitos como Vaga, Perfil, Compatibilidade, Coleta e Entrega. |
| `codebase-design` | Orienta a criação de módulos profundos, interfaces pequenas e limites testáveis. | Ao desenhar ou refatorar as camadas de domínio, coleta, matching e notificação. |
| `tdd` | Conduz o ciclo vermelho, verde e refatoração, priorizando comportamento e interfaces públicas. | Ao implementar funcionalidades ou corrigir defeitos com `pytest`. |
| `code-review` | Revisa uma diferença de código em dois eixos: regras do repositório e aderência à especificação. | Antes de concluir uma branch ou preparar um pull request. |
| `humanizer` | Reescreve textos artificiais ou genéricos sem alterar fatos e significado. | Ao revisar documentação, mensagens do Telegram e textos voltados ao usuário. |
| `revenue-centric-design` | Reúne princípios de produto para aquisição, ativação, retenção, monetização e posicionamento. | Ao planejar landing pages, onboarding, modelo de receita, métricas ou estratégia de produto. |

## Fluxo recomendado

1. Execute `setup-matt-pocock-skills` uma vez para preparar o projeto.
2. Use `grill-with-docs` para esclarecer mudanças relevantes. Ela combina `grilling` e `domain-modeling`.
3. Aplique `codebase-design` ao definir interfaces e limites entre módulos.
4. Implemente em ciclos curtos com `tdd`.
5. Finalize com `code-review`, comparando a branch com seu ponto de origem.
6. Use `humanizer` quando o resultado incluir texto destinado a pessoas.
7. Consulte `revenue-centric-design` nas decisões de produto, experiência e monetização.

## Origem

- `humanizer`: [blader/humanizer](https://github.com/blader/humanizer), licença MIT.
- Skills de engenharia: [mattpocock/skills](https://github.com/mattpocock/skills), licença MIT.
- `revenue-centric-design`: [heliocosta-dev/revenue-centric-design](https://github.com/heliocosta-dev/revenue-centric-design), licença própria com atribuição obrigatória e proibição de uso em apostas, cassinos e jogos de azar.

A instalação de `revenue-centric-design` é enxuta: mantém as referências textuais e a licença, mas omite os recursos multimídia e os scripts opcionais de atualização.

As cópias deste diretório são versionadas com o projeto. Atualizações das fontes não são aplicadas automaticamente e devem ser revisadas antes de entrar no repositório.
