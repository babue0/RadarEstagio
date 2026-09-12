# Documentação do Radar de Estágio

Consolidada em 09/09/2026. Implementação, publicação e validação com usuários são estados
diferentes. Esta revisão reorganizou registros locais; não consultou serviços externos.

## Por onde começar

- [Funcionalidades](funcionalidades.md): capacidades implementadas, dependências e limitações.
- [Plano geral](plano-geral.md): acompanhamento único de pendências e decisões da equipe.
- [Plano de migração para React](plano-migracao-react.md): proposta em revisão para React com
  JavaScript, preservando interface e contratos; implementação não iniciada.
- [Guia de publicação e piloto](guia-publicacao-e-piloto.md): configuração, evidências datadas,
  ordem de publicação, reversão e roteiro de validação.
- [README do projeto](../README.md): instalação, execução e desenvolvimento do frontend.
- [Arquitetura](arquitetura.md): camadas, justificativas técnicas, correções da auditoria e riscos.
- [Contrato frontend](contrato-front.md): cadastro, Auth, RPCs, privacidade e formação acadêmica.
- [Métricas](metricas.md): eventos, cálculos, denominadores e limites de interpretação.
- [Pré-PRD](pre-prd.md): definição, hipóteses, evidências e viabilidade para a disciplina.
- [Auditorias](auditorias/): revisões datadas com achados numerados; o que virou pendência está
  no plano geral, e o que virou regra, na arquitetura e no `CLAUDE.md`.
- [Termos](termos-de-uso.md) e [Política de Privacidade](politica-de-privacidade.md): rascunhos
  para revisão; sincronizar com HTML e versão aceita antes da vigência.
- [Cobertura](cobertura-estagios.md), [aquisição e prova](aquisicao-e-prova.md),
  [custos](custos-operacao.md) e [hipótese comercial](hipotese-comercial.md): procedimentos e
  decisões externas ainda abertos, com dados ausentes explicitados.

## Consolidação para exclusão posterior

Os nove arquivos abaixo continuam no repositório para revisão e consulta histórica.
Seus comandos e estados antigos não são uma fila atual de trabalho. Nenhum foi excluído.
O detalhamento histórico, cenários de aceite e resultados intermediários permanece neles
e no Git; os documentos permanentes recebem a síntese útil para manutenção.

| Arquivo histórico | Destino do conteúdo de manutenção |
|---|---|
| `plano-expansao-revenue-centric.md` | Estado, escopo e seis frentes externas no plano geral |
| `execucao-expansao/00-protocolo.md` | Publicação compatível e verificações no guia; regras gerais já em `CLAUDE.md` |
| `execucao-expansao/01-landing-e-cadastro.md` | Capacidades no catálogo; cadastro e decisões de interface no contrato frontend |
| `execucao-expansao/02-metricas-e-retencao.md` | Cálculos em métricas; motivo de pausa no contrato |
| `execucao-expansao/03-evidencias-e-decisoes.md` | Guia, cobertura, aquisição, custos, hipótese comercial e seção acadêmica do contrato |
| `execucao-expansao/progresso.md` | Conclusão e pendências no plano geral; testes históricos e visual pendente no guia |
| `execucao-expansao/decisoes-da-revisao.md` | Justificativas na arquitetura, contrato, métricas e guia; demonstração no catálogo |
| `auditorias/2026-09-08-expansao-adversarial.md` | A01–A06, regressões e limites na arquitetura; casos novos na matriz de cobertura |
| `../web/README.md` | Desenvolvimento no README principal; configuração no guia; comportamento no contrato |

Antes da exclusão, revisar o diff da consolidação e conferir se alguma mudança posterior
nesses arquivos precisa ser incorporada. Remover os nove em conjunto evita deixar referências
internas dos documentos históricos apontando para arquivos apagados. Esta tabela usa caminhos
como texto para não criar dependência de navegação dos arquivos a retirar.

## Como manter

Ao mudar uma função, atualizar o catálogo e o contrato afetado. Ao publicar ou validar,
registrar data, versão e resultado no guia e ajustar o estado no plano geral. Decisões de
cálculo ficam em métricas; justificativas técnicas na arquitetura. Não duplicar o backlog.

O piloto permanece informal por decisão do Igor em 07/09: entrevistas, coorte mínima e D7
não são condições para divulgar. A conferência operacional e a revisão dos textos estão no
plano geral. Hipótese não vira medição, teste local não vira deploy e histórico não vira
instrução para reaplicar uma entrega.
