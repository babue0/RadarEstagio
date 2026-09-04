# HANDOFF — Radar de Estágio

**Última atualização:** 04/09/2026, fim do dia

Documento para quem continuar com contexto novo. O plano de trabalho está em
[`docs/plano-geral.md`](docs/plano-geral.md); aqui é o estado operacional e o que já foi tentado.

## Goal

Levar o Radar de demonstração técnica a produto validado com estudantes. O gargalo não é mais
código: é medir se a vaga entregue **serviu**. A North Star do projeto é o percentual de estudantes
ativados que encontram ao menos uma vaga útil por semana, e ela ainda não é calculável.

## Current Progress

| | |
|---|---|
| `main` | `eaeff26`, limpo, sincronizado |
| PR aberta | **#9** — painel da conta (editar, pausar, desvincular, excluir) |
| Migrations aplicadas no banco | até a **`0012`** |
| No repositório e **não aplicada** | `0013`, só na branch da PR #9 |
| Testes | 378 no `main`, 385 na branch; 20 Deno; lint limpo |

Entregue nos dois últimos dias: custo de IA deixou de crescer com o número de usuários (extração
por vaga, reaproveitada entre perfis); avaliação gravada antes do envio; perfil pausado após falhas
seguidas; resumo de cada execução no chat de operação; link rastreável; feedback por botões
numerados; leitura do funil; token de vínculo de uso único; perfil sintético; aviso de privacidade.

**Nada disso está no ar.** A landing não está hospedada, a função `ir` nunca foi publicada e a
`telegram-webhook` precisa ser republicada com o feedback.

## What Worked

- **Separar extração de pontuação.** A IA passou a ler só o anúncio; a comparação com o perfil é
  Python puro. O custo virou O(vagas) em vez de O(usuários × vagas), e o teste
  `test_dobrar_os_usuarios_nao_dobra_as_vagas_extraidas` impede a regressão.
- **Revisar plano como se revisa código.** Duas passadas do Codex sobre os documentos acharam vinte
  problemas, todos procedentes — inclusive afirmações falsas que teriam ido para a política de
  privacidade.
- **Migration antes do código.** O job das 07:23 roda o `main` sem revisão; inverter essa ordem
  quebra produção na manhã seguinte.
- **Commits fatiados por decisão**, com `pytest` em comando separado antes de cada um. Regra que
  entrou no `CLAUDE.md` em 04/09.

## What Didn't Work

- **Uma mensagem por vaga no Telegram.** Cinco vagas viraram cinco mensagens com teclado. Ficou
  poluído no teste real. Substituído por uma mensagem só com botões numerados. **Não voltar atrás.**
- **Desligar a confirmação de e-mail** para encurtar o funil. Rejeitado: o produto pretende enviar
  e-mail, e endereço não verificado gera bounce, que derruba a reputação do domínio.
- **Rotina na nuvem abrindo PR sozinha.** Fez os sete itens, mas o app do GitHub tem acesso só de
  leitura — `git push` devolve 403. Entregou por `git bundle` na conversa. Se for repetir, resolver
  a permissão antes.
- **`codex exec review --commit`** não aceita instruções customizadas junto. Use
  `git show <sha> | codex exec -m <modelo> "<instruções>"`.
- **`git add -A`** engoliu uma worktree inteira e um bundle de 590 KB num commit. Confira
  `git status` antes.
- **Alterar branches empilhadas no lugar** com `commit --amend` quebra a pilha: as de cima
  continuam apontando para o commit antigo. Rebasear na ordem, de baixo para cima.
- **`deno fmt` na raiz** reformata bloco de código dentro de markdown. Sempre com caminho:
  `deno fmt supabase/functions/`.
- **Duas afirmações minhas que se provaram falsas** e podem estar na sua cabeça se você leu versões
  antigas dos documentos: que o domínio trava a hospedagem (não trava — Cloudflare Pages publica em
  `*.pages.dev`), e que o formato antigo de feedback emitia `vaga_util` (nenhum commit alcançável
  jamais gravou esse evento).

## Next Steps

1. **Publicar a landing no `*.pages.dev`.** Grátis, sem dependência, e destrava a medição de
   abertura. É o passo mais barato que existe agora.
2. **Registrar o endereço em Site URL e Redirect URLs** do Supabase Auth, senão a confirmação de
   e-mail não volta para a página publicada.
3. **Criar `URL_DA_LANDING` (Supabase) e `URL_DE_RASTREIO` (secrets do GitHub)**, publicar a função
   `ir` e republicar a `telegram-webhook`.
4. **Decidir como capturar vaga útil.** `vaga_util` e `candidatura_iniciada` estão no catálogo e
   nenhuma linha do código os grava. As duas saídas estão na seção 3 do `plano-geral.md`. Sem isso o
   piloto roda e não mede o que importa.
5. **Reescrever a `0013`** com a exclusão em duas etapas e os 60 dias, **editando no lugar** — ela
   nunca foi aplicada, e empilhar uma `0014` corrigindo perde essa vantagem. Depois, revisão nova.

Do 1 ao 3 nada é código.

## Decisões pendentes que travam trabalho

| Assunto | Quem decide |
|---|---|
| Como capturar `vaga_util` e `candidatura_iniciada` | produto |
| Piloto começa com entrega em 24h, ou o sprint 2 vem antes? | produto — a auditoria trata isso como bloqueador |
| Dados pessoais no histórico do git: reescrever e quebrar clones? | o grupo |
| Domínio em nome de quem | o grupo |

## Armadilhas do ambiente

- **`testar-local` não serve para testar fluxo**, só formato: roda sem banco, com perfil sintético,
  e os botões aparecem sem funcionar porque não há `envios` gravado.
- **Codex está instalado e autenticado.** `gpt-5.6-sol` para código, `gpt-6-astra` para documentos.
  `gpt-5.6-astra` não existe; `gpt-6-astra` sim.
- **As skills em `.agents/skills/`** não são carregadas pelo Claude Code. Há material bom lá,
  incluindo `revenue-centric-design`, que originou a auditoria.
