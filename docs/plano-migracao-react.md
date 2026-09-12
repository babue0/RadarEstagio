# Plano de migração do frontend para React

**Proposta registrada em 12/09/2026. Implementação não iniciada.**

Este documento coloca em revisão o plano solicitado pelo Igor: migrar o frontend para
React com JavaScript, sem TypeScript e sem redesenhar a interface. O PR que adiciona este
documento é exclusivamente de planejamento; não instala dependências, altera a aplicação,
publica uma nova versão ou autoriza a execução das etapas abaixo.

O estado da iniciativa fica no [plano geral](plano-geral.md#23-migração-do-frontend-para-react-12092026).
Este documento detalha a proposta técnica, a sequência e os critérios de conclusão.

## 1. Objetivo e base

Separar a interface em componentes e retirar autenticação, acesso a dados e validações do
arquivo monolítico, facilitando a evolução do produto com testes de comportamento. Para o
usuário, a migração deve preservar aparência, conteúdo, URLs, sessão e regras atuais.
React não substitui decisões de arquitetura nem garante ganho de desempenho ou capacidade
do backend por si só.

Base verificada: `main`, commit `0f0ca45aec8188a265cb82a4d57423f27c72cebe`.

- [PR #60](https://github.com/RadarEstagio/RadarEstagio/pull/60): header flutuante sempre
  visível, blur suave, dimensões reduzidas, tema separado do login e reformulação das seções.
- [PR #61](https://github.com/RadarEstagio/RadarEstagio/pull/61): atualizações das fontes,
  remoção da faixa de logos e referências à Gupy, e selos “Jobs by Adzuna”.
- A faixa de logos deve continuar removida, conforme confirmação do Igor. Preservar os
  selos, links, dimensões e tratamento de fundo no tema escuro da Adzuna.
- Os ajustes de coleta, cotas, banco e Telegram já integrados à `main` não são parte desta
  migração e não devem ser revertidos.

Antes da implementação, atualizar a base e registrar o novo SHA caso outras mudanças sejam
integradas. Não usar screenshots anteriores à PR #61 como referência do conteúdo atual.

### PR futuro de implementação

- Branch proposta: `feat/frontend-react`, criada da `main` atualizada após aprovação do plano.
- Título: `refactor(web): migra frontend para React preservando os fluxos atuais`.
- Um PR em rascunho, com commits por decisão e testes junto de cada etapa.
- Não misturar implementação com nova reformulação visual ou funcionalidade.

## 2. Escopo

### Incluído

- Landing, header, tema, navegação, demonstração do hero, FAQ, chamada final e footer.
- Diálogos, login, confirmação, reenvio e recuperação de senha.
- Cadastro em etapas, conclusão de perfil pendente e edição de perfil.
- Conta, preferências de e-mail, pausa e retomada.
- Vínculo e desvínculo do Telegram, exportação, exclusão e cancelamento de exclusão.
- Integração com Supabase, catálogos e eventos de produto.
- Migração da cobertura de interface, build, CI, documentação e preparação de publicação.

### Fora do escopo

- TypeScript na aplicação, Next.js, Redux, Tailwind ou nova biblioteca de componentes.
- Alterações de layout, copy, marca, cores, blur, responsividade ou regras de produto.
- Mudanças em Python, schema, RLS, RPCs, Edge Functions ou regras de recomendação.
- Cobrança, novas telas, mudança de fontes ou decisão acadêmica D01.
- Troca de domínio, hospedagem, configurações remotas do Auth ou ativação de CAPTCHA.
- Mudanças nos textos legais, sua versão aceita ou estado de revisão.

Exceção técnica delimitada: ajustar caminhos em geradores e testes Python se assets forem
movidos, sem mudar conteúdo ou regras. Testes Deno já escritos em TypeScript podem continuar
assim; isso não introduz TypeScript na aplicação.

## 3. Arquitetura proposta

| Responsabilidade | Escolha |
|---|---|
| Interface | React, JavaScript e JSX |
| Desenvolvimento e build | Vite, npm e lockfile versionado |
| Estilos | CSS atual, preservando ordem, seletores e estrutura necessária |
| Dados e autenticação | Supabase, com os mesmos contratos |
| Formulários | Estado local e `useReducer` para as transições do cadastro |
| Sessão | Context restrito à autenticação e coordenação da tela |
| Testes de interface | Vitest, React Testing Library, user-event e JSDOM |
| Testes no navegador | Playwright sobre o artefato de produção |
| Backend e suas suítes | Python e Deno mantidos |

Fixar versões compatíveis no lockfile e a versão de Node usada em desenvolvimento, CI e
build remoto. Migrar o SDK do Supabase do CDN para npm inicialmente na versão já usada,
`2.116.0`; uma atualização do SDK será uma decisão separada.

### HTML público no build

A landing deve continuar entregando conteúdo no HTML inicial. Gerar seu HTML a partir dos
componentes React durante o build e ativar as interações no navegador com `hydrateRoot`.
Não manter uma cópia manual paralela da landing.

- A geração é estática, sem servidor Node em produção e sem chamadas ao Supabase no build.
- O primeiro render do navegador precisa corresponder ao HTML gerado.
- Não acessar `window`, storage ou sessão em módulos executados pelo gerador estático.
- Resolver a sessão após a hidratação, sem exibir um modal incorreto nos retornos do Auth.
- Nenhum perfil, token ou dado privado pode aparecer no HTML gerado.
- Preservar títulos, metadados, conteúdo, âncoras e aplicação inicial do tema.
- Termos e privacidade continuam como entradas HTML estáticas nos mesmos endereços, sem
  carregar autenticação ou analytics. Preservar seu estado de rascunho e `noindex`.

Validar essa configuração em uma pequena prova técnica na primeira etapa de implementação.
A proposta usa a [geração estática do Vite](https://vite.dev/guide/ssr.html#pre-rendering-ssg)
e a [hidratação do React](https://react.dev/reference/react-dom/client/hydrateRoot), sem
introduzir renderização por requisição ou um framework full-stack.

### Organização

```text
web/
├── package.json
├── package-lock.json
├── vite.config.js
├── index.html
├── privacidade.html
├── termos.html
├── assets/
│   └── styles.css
├── public/
│   ├── config.js
│   └── assets/
│       ├── areas.json
│       ├── cidades.json
│       └── adzuna-logo.png
├── src/
│   ├── main.jsx
│   ├── entry-static.jsx
│   ├── app/
│   │   ├── App.jsx
│   │   ├── SessionProvider.jsx
│   │   └── navigation.js
│   ├── features/
│   │   ├── landing/
│   │   ├── autenticacao/
│   │   ├── cadastro/
│   │   └── conta/
│   ├── components/
│   ├── services/
│   └── domain/
├── scripts/
│   └── prerender.mjs
└── tests/
    ├── unit/
    ├── integration/
    └── e2e/
```

- `features`: telas e interações de cada área.
- `components`: elementos realmente compartilhados, como diálogo e campo de senha.
- `services`: cliente único do Supabase, Auth, perfis, RPCs, catálogos e eventos.
- `domain`: validações e normalizações puras, sem DOM ou acesso a rede.
- `app`: sessão e coordenação das telas existentes.

`web/dist/` será o único artefato publicável. Dependências, coverage, relatórios, caches e
saída intermediária da geração estática ficam ignorados pelo Git e fora desse diretório.

Não colocar o `app.js` inteiro em um efeito, executá-lo com `eval` ou injetar a aplicação
como uma grande string HTML. React deve controlar suas subárvores. Integrações imperativas
ficam limitadas a APIs como `<dialog>`, foco e CAPTCHA, com ciclo de vida explícito.

### Navegação e configuração

Preservar `/`, `/index.html`, `?conta`, `?fluxo=recuperar`, âncoras das seções da conta e da
landing, e os caminhos `.html` legais. Centralizar a leitura e atualização das URLs atuais;
não criar uma nova hierarquia de rotas neste PR. Não usar `HashRouter`: fragmentos já são
usados por âncoras e retornos de autenticação.

Preservar `code`, `access_token`, erros e tipo de fluxo até o SDK processar o retorno. Uma
sessão existente na homepage não deve abrir a conta sem a intenção de navegação atual.

Manter `/config.js`, `window.RADAR_CONFIG` e seu formato público. Validar configuração ausente
com mensagem útil, sem tela quebrada. URL e chave pública do Supabase não são credenciais
de servidor; nunca incluir `service_role`, conexão Postgres, tokens do bot ou conteúdo do
`.env` no bundle. Variáveis `VITE_*` não são um cofre de segredos.

## 4. Sequência de implementação e entregáveis

| Etapa | Trabalho | Critério de conclusão |
|---|---|---|
| R0 — Referência | Atualizar SHA, mapear telas, URLs, eventos e testes; capturar screenshots e medições; conferir publicação | Base verificável e matriz de equivalência |
| R1 — Infraestrutura | React/Vite, lockfile, lint e testes; validar HTML estático e hidratação em entrada isolada | Build reproduzível, sem alterar a entrada publicada |
| R2 — Regras e serviços | Separar cliente, Auth, perfis, RPCs, catálogos, eventos e validações | Payloads e regras cobertos sem mudar comportamento |
| R3 — Landing | Converter seções, header, tema, FAQ e componentes compartilhados | HTML inicial completo e comparação visual aprovada |
| R4 — Autenticação | Sessão, login, confirmação, reenvio, recuperação e CAPTCHA | Sucessos, falhas e retornos por URL equivalentes |
| R5 — Cadastro | Etapas, catálogos, consentimentos, perfil pendente e edição | Sem perda de dados, corrida de resposta ou envio duplicado |
| R6 — Conta | Preferências, pausa, Telegram, exportação e exclusão | Contratos preservados e ações sensíveis confirmadas |
| R7 — Substituição | Trocar entrada, adaptar leitores de assets e testes; remover implementação antiga | Uma implementação ativa e todos os cenários mapeados |
| R8 — Entrega | Completar CI, revisão de performance, documentação, preview e plano operacional | Evidências e aprovação antes do merge e publicação |

Os testes acompanham R1–R7; R8 não é a primeira validação. Enquanto coexistirem versões,
usar uma entrada temporária de desenvolvimento/teste que não entre no artefato publicado.
Não disponibilizar acidentalmente duas aplicações ou telas parcialmente migradas ao público.

Manter o desenvolvimento local em `localhost:8000` com `strictPort`, sem avançar para outra
porta silenciosamente e quebrar redirects já configurados.

Ao mover catálogos e logo para `public/assets`, preservar suas URLs públicas e atualizar
`scripts/gerar_cidades.py`, testes Python/Deno e referências HTML afetadas. Não duplicar
catálogos, regenerá-los pela internet ou alterar normalizações para acomodar a mudança de
pasta. O CSS compartilhado também precisa ser processado corretamente nas páginas legais.

## 5. Invariantes e cenários de regressão

O [contrato frontend](contrato-front.md) prevalece sobre exemplos simplificados deste plano.

### Cadastro, perfil e catálogos

- Perfil antes da conta; `signUp` somente no envio final, com bloqueio de submissão duplicada.
- Preservar `options.data.cadastro_radar`, consentimentos, versão dos termos e sessão de eventos.
- Não inserir nem fazer upsert direto em `perfis`. Manter criação pelo fluxo de confirmação
  e `concluir_meu_cadastro({ cadastro })` para usuário confirmado sem perfil.
- Confirmação em outro aparelho não depende de rascunho local. Login não sobrescreve perfil
  existente com dados não salvos do formulário.
- Atualizações de perfil limitadas às colunas permitidas e ao usuário autenticado.
- Manter 0–50 habilidades, limite de 100 caracteres, limpeza de espaços e escolha explícita
  para continuar sem habilidades. Nenhuma habilidade sentinela deve representar lista vazia.
- Preservar regras de cursos, sugestões e áreas, inclusive curso desconhecido, falha de
  catálogo, edição com dados salvos e descarte de respostas antigas.
- Cidades mantêm normalização, estado para homônimos, oito sugestões e navegação por teclado;
  indisponibilidade do catálogo permite entrada manual com aviso, como hoje.
- Não persistir novo rascunho de perfil ou senha no navegador. Preservar tratamento e limpeza
  compatíveis de `radar-perfil-pendente` legado.

### Autenticação e ciclo de vida

- Manter persistência e renovação da sessão, detecção de retorno na URL e comportamento das
  chaves de storage do SDK. Não exigir novo login por causa da migração.
- Recuperação exige sessão/evento válido, não apenas query string. Após trocar a senha,
  preservar o encerramento de sessão e retorno ao login.
- Reenvio mantém e-mail editável, espera de 60 segundos e tratamento de resposta 429.
- CAPTCHA permanece opcional conforme configuração; script/widget únicos, expiração, erro,
  falha de carga e descarte do token após tentativa precisam estar cobertos.
- Limpar assinaturas, listeners e timers. Strict Mode não pode duplicar widgets, analytics,
  mutações, animações ou verificações de sessão.
- Logout limpa estado transitório e invalida respostas pendentes, sem limpar todo o storage
  do navegador. Senhas não aparecem em perfil, eventos, logs ou persistência própria.

### Conta e privacidade

- Pausar salva primeiro; motivo posterior opcional ou com falha não desfaz a pausa.
- Retomar limpa o motivo na mesma atualização.
- Preservar RPCs `desvincular_meu_telegram`, `baixar_meus_dados`, `excluir_minha_conta` e
  `cancelar_exclusao_da_minha_conta`, sem substituí-las por escritas diretas.
- A exclusão continua em duas etapas, com carência de 60 dias e sessão mantida para cancelar.
  Não modificar o estado anterior de pausa; cancelamento exige novo vínculo quando aplicável.
- Confirmar ações sensíveis e devolver o foco ao controle correto; falha de escrita não
  pode apresentar sucesso ou remover opções necessárias para recuperação.
- Exportação preserva `meus-dados-radar.json` e revoga a URL temporária após o download.
- Link do Telegram usa token atualizado. Preservar releitura ao retornar à página e após
  a abertura do bot, sem prometer que a busca começou apenas porque houve vínculo.
- Compartilhar componentes entre modal e conta sem mover manualmente nós gerenciados pelo React.

### Visual, conteúdo e eventos

- Header sempre visível; mesmo blur, dimensões e limites; tema e login separados.
- Manter as seções atuais sem numeração e a faixa de logos removida.
- Preservar os três selos “Jobs by Adzuna”, seus links e o asset oficial, sem recriar referências
  à Gupy ou regras antigas de responsividade das seções substituídas.
- Tema mantém `radar-tema` e aplicação antes da interface carregar, sem inconsistência de
  hidratação. Preservar fallback para armazenamento bloqueado.
- Preservar `radar-sessao-eventos`, `radar-landing-vista`, catálogo de eventos e origem dos CTAs.
- `landing_visualizada` continua deduplicado por sessão de navegador. Falha de analytics
  nunca bloqueia a jornada; eventos não levam senha, token ou texto livre de dados pessoais.
- Manter foco, Escape, navegação por teclado, labels, preenchimento automático e preferências
  de movimento reduzido, sem adicionar wrappers que quebrem CSS ou semântica.

## 6. Estratégia de testes

A validação feita ao conciliar a PR #60 com a `main`, em 12/09, registrou 1.037 testes Python
passando, 27 pulados, 82 testes web passando e lint/formatação passando. Os checks Python,
web e Cloudflare Pages também passaram na PR antes do merge. Isso não é evidência de
implementação React, validação visual ou conferência do deployment de produção.

Dos 82 testes web, 73 estão em `cadastro_test.ts` e usam HTML e `app.js` diretamente. Mapear
cada cenário para o novo teste, não apenas manter a contagem. Os outros nove testes Deno de
banco, métricas e privacidade, além dos testes das Edge Functions, continuam protegidos.

### Matriz inicial de transição

| Cobertura atual | Destino e cuidado |
|---|---|
| `tests/web/cadastro_test.ts` | Vitest/Testing Library com serviços simulados; equivalência dos 73 cenários antes de retirar o harness antigo |
| `tests/test_frontend_activation.py` | Comportamento de Auth/ativação nos testes React e contrato de recursos no artefato; remover dependência de strings de funções/CDN |
| `tests/test_product_copy.py` | Conteúdo renderizado, exemplos, atribuição e estados; preservar verificações da Adzuna e ausência da faixa |
| `tests/test_product_events.py` | Testar payloads, origens, falhas e deduplicação pela fronteira de eventos |
| `tests/test_areas_do_front.py` | Manter contrato do catálogo no Python; verificar campos renderizados no React |
| `tests/test_cidades_do_front.py` e `tests/test_regioes.py` | Ajustar caminho de dados sem perder equivalência com o domínio |
| Demais testes Python/Deno e funções | Manter checks; só alterar consumidores de caminhos quando necessário |

Testes de detalhes internos podem ser substituídos por verificações de comportamento, nunca
apagados apenas para deixar o CI verde. Não conservar um `app.js` morto para satisfazer buscas
de texto. A suíte Python de domínio não deve passar a depender de um build npm para rodar.

### Camadas novas

1. Unitários: validações, normalização, transições de cadastro, URLs e montagem de payloads.
2. Integração: fluxos completos por componentes, operações exatas do Supabase, concorrência,
   indisponibilidade e efeitos repetidos. Preferir queries por papel, label e texto visível.
3. Artefato: conteúdo público no HTML, metadados, documentos legais, paths de config/catálogos/
   logo, ausência de dependências e arquivos privados na saída.
4. Navegador: build real em Chromium, Firefox e WebKit, com desktop e mobile; cadastro,
   login/retorno, conta, diálogos, tema, scroll, âncoras, downloads e recarga direta.
5. Visual: screenshots antes/depois nos mesmos estados e viewports; conferir manualmente
   Safari, blur e autofill. WebKit automatizado não substitui a conferência do Safari real.

Usar mocks na fronteira de serviços ou ambiente de teste. CI, screenshots e preview não podem
gravar métricas de produção, enviar e-mails/Telegram reais ou incluir perfis e tokens reais.
Teste real controlado exige ambiente, conta e autorização explícitos; não é requisito para
rodar a suíte local simulada. Avisos preexistentes de storage no harness antigo devem ser
distintos de regressões, não silenciados com captura genérica de erros.

Registrar bytes transferidos e métricas de carregamento antes/depois na mesma condição.
Definir orçamento a partir da referência medida; não inventar cobertura percentual ou
prometer ganho de velocidade. Regressão relevante precisa de análise e aprovação.

## 7. CI e comandos futuros

Preservar os jobs Python e Deno de `.github/workflows/testes.yml`. Adicionar Node, instalação
reproduzível, lint, testes React, build, validação do artefato e testes no navegador, com
relatórios e screenshots de falhas. Instalar os navegadores compatíveis com a versão fixada
do Playwright no job apropriado. Nenhum check depende de segredos de produção.

Comandos propostos, ainda inexistentes no projeto:

```sh
npm --prefix web ci
npm --prefix web run dev
npm --prefix web run lint
npm --prefix web run test:run
npm --prefix web run build
npm --prefix web run test:artifact
npm --prefix web run test:e2e
npm --prefix web run preview
```

Manter `uv run pytest -q` em comando separado, com resultado conferido antes de cada commit,
além dos testes da etapa, conforme `CLAUDE.md`. Não versionar `dist`, `node_modules`, perfis,
tokens ou relatórios com informações sensíveis.

## 8. Publicação e reversão

O [guia operacional](guia-publicacao-e-piloto.md) registra Cloudflare Pages com raiz do
repositório, build `exit 0` e saída `web`. Confirmar configurações atuais no serviço antes
de alterá-las; o sucesso de um check de preview não confirma a configuração da produção.

| Item | Configuração-alvo proposta |
|---|---|
| Projeto, domínio e branch de produção | Manter os vigentes; confirmar que produção acompanha `main` |
| Raiz de trabalho | Raiz do repositório |
| Build | `npm --prefix web ci && npm --prefix web run build` |
| Saída publicada | `web/dist` |
| Configuração pública | `/config.js`, sem mudar o contrato |
| Runtime | Arquivos estáticos; não usar `vite preview` como servidor de produção |

### Ordem operacional

1. Registrar projeto, domínio efetivo, settings, SHA e deployment de produção anterior.
2. Antes do primeiro push com dependências frontend, verificar como isolar o build e a saída
   do preview. Não deixar a configuração antiga publicar `web/node_modules` ou fontes novas.
3. Preparar preview apenas do artefato `dist`, sem mudar produção para viabilizá-lo. Se o
   projeto não permitir separar as configurações, definir publicação do artefato por um
   mecanismo de preview autorizado antes de prosseguir; não improvisar um cutover de produção.
4. Confirmar preview sem indexação e sem escrita em serviços de produção por padrão. Não
   adicionar um fallback silencioso para credenciais/configuração de produção.
5. Validar HTML, assets, temas, cadastro simulado, conta, URLs e erros. Registrar SHA e URL.
6. Conferir Auth real apenas com conta/ambiente autorizados e redirects permitidos. Não mudar
   allowlist, Site URL ou exigência de CAPTCHA automaticamente para fazer o teste passar.
7. Obter aprovação visual e funcional; coordenar settings de build e merge do PR.
8. Após publicar, conferir o deployment efetivo, início, legal, assets e jornada autorizada.
   Registrar resultado no guia. CI verde e merge não são prova de publicação ou de jornada real.

O Vite produz um [artefato estático](https://vite.dev/guide/static-deploy.html). O Pages
oferece [previews separados de produção](https://developers.cloudflare.com/pages/configuration/preview-deployments/);
verificar a configuração do projeto antes de depender desse comportamento.

### Rollback

- Gatilhos: perda de sessão, quebra de cadastro/retorno, tela indisponível, assets faltantes,
  operações duplicadas ou outra regressão crítica confirmada.
- Restaurar o último deployment de produção válido, cujo identificador foi registrado.
- Reverter o PR pelo fluxo normal do Git e restaurar build/saída anteriores para os próximos
  deployments; não usar reset destrutivo nem reescrever a `main`.
- Conferir landing, assets, sessão e login após a reversão.
- Não há rollback de banco previsto: a migração não altera schema ou contratos. Dados criados
  pelos fluxos existentes durante a nova versão precisam continuar utilizáveis pela antiga.

A [reversão do Pages](https://developers.cloudflare.com/pages/configuration/rollbacks/)
usa deployments anteriores de produção, não previews. A restauração do artefato e a correção
das configurações dos próximos builds são passos distintos.

## 9. Commits e documentação

Sequência sugerida para o PR de implementação, mantendo cada fatia testável:

1. `docs(web): registra referência e critérios da migração`
2. `build(web): prepara React Vite e testes`
3. `refactor(web): separa serviços e validações`
4. `refactor(web): migra landing para componentes React`
5. `refactor(web): migra autenticação e sessão`
6. `refactor(web): migra cadastro e edição de perfil`
7. `refactor(web): migra controles da conta`
8. `refactor(web): substitui entrada legada e adapta cobertura`
9. `ci(web): valida build e fluxos no navegador`
10. `docs(web): atualiza arquitetura publicação e reversão`

Os checks mínimos das etapas precisam existir desde o começo; o commit de CI final completa
a proteção, não adia todos os testes. Usar exclusivamente a identidade Git configurada,
sem coautoria de IA, seguindo as regras de commits do projeto.

Na implementação, atualizar README principal, arquitetura, contrato frontend e guia
operacional conforme o que realmente mudar. Não documentar React como stack já instalada
neste PR de planejamento. `web/README.md` continua histórico, não a fonte de instruções.

## 10. Evidências e checklist de aceite do PR de implementação

A descrição deve apresentar objetivo, escopo, base de referência, mapa de cenários antigos
para novos, resultados dos comandos executados, screenshots, comparação de carregamento,
URL/SHA do preview, procedimento operacional e limitações conhecidas. Separar problemas
preexistentes, testes simulados e validações reais; não tratar item não verificado como sucesso.

- [ ] Plano aprovado e início da implementação autorizado.
- [ ] Base atualizada e referência visual registrada após as PRs #60 e #61.
- [ ] React com JavaScript, sem TypeScript na aplicação ou redesign.
- [ ] Landing entrega HTML público, hidrata sem erro e mantém metadados e URLs.
- [ ] Header e seções preservados; faixa de logos ausente; selos da Adzuna mantidos.
- [ ] Sessões existentes, cadastro, confirmação, reenvio e recuperação equivalentes.
- [ ] Perfil, catálogos, consentimentos e validações preservados.
- [ ] Conta, pausa, Telegram, exportação e exclusão cobertos, inclusive falhas.
- [ ] Eventos sem duplicação e sem dados pessoais indevidos.
- [ ] Teclado, foco, temas, mobile e Safari conferidos.
- [ ] Todos os cenários antigos têm cobertura equivalente registrada.
- [ ] Python, Deno, React, lint, build, artefato e navegador passam.
- [ ] Código legado removido, sem cópias concorrentes de interface ou catálogos.
- [ ] Carregamento comparado com a referência, com desvios analisados.
- [ ] Documentação atualizada e preview aprovado pelo Igor.
- [ ] Publicação e rollback preparados, sem mudança remota implícita.

Não fazer merge com regressão de contrato, perda de cobertura, diferença visual não aprovada,
erro de hidratação, vazamento de configuração privada ou publicação sem reversão preparada.
O resultado deve ser o Radar atual em uma base React organizada; evolução visual e de produto
fica para outros PRs.
