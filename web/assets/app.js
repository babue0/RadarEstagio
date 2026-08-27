const TELA = document.getElementById("tela");
const TRILHA = document.getElementById("trilha");
const AVISOS = document.getElementById("avisos");
const MENU = document.getElementById("menu-lateral");

const ROTAS = {
  hoje: { titulo: "Hoje", render: telaHoje },
  historico: { titulo: "Histórico", render: telaHistorico },
  mercado: { titulo: "Mercado", render: telaMercado },
  perfil: { titulo: "Perfil", render: telaPerfil },
  configuracoes: { titulo: "Configurações", render: telaConfiguracoes },
};

const MODALIDADES = {
  remoto: "Remoto",
  hibrido: "Híbrido",
  presencial: "Presencial",
  indiferente: "Indiferente",
};

const ESTADOS_VAGA = {
  enviada: "Enviada no Telegram",
  curtida: "Curtida",
  descartada: "Descartada",
};

function icone(id, classe) {
  return `<svg class="icone${classe ? " " + classe : ""}" viewBox="0 0 24 24" aria-hidden="true"><use href="#i-${id}"></use></svg>`;
}

function escapar(texto) {
  const div = document.createElement("div");
  div.textContent = texto ?? "";
  return div.innerHTML;
}

function classeDaNota(nota) {
  if (nota >= 80) return "nota-alta";
  if (nota >= 55) return "nota-media";
  return "nota-baixa";
}

function avisar(mensagem, tipo = "info") {
  const icones = { sucesso: "check", erro: "x", info: "seta", atencao: "alerta" };
  const elemento = document.createElement("div");
  elemento.className = `aviso aviso-${tipo}`;
  elemento.setAttribute("role", tipo === "erro" ? "alert" : "status");
  elemento.innerHTML = `${icone(icones[tipo] || "seta")}<span>${escapar(mensagem)}</span>`;
  AVISOS.appendChild(elemento);
  setTimeout(() => {
    elemento.style.opacity = "0";
    elemento.style.transition = "opacity 0.3s ease";
    setTimeout(() => elemento.remove(), 300);
  }, 3600);
}

function montarTrilha(rota) {
  TRILHA.innerHTML = `
    <a href="#/hoje">Painel</a>
    ${icone("seta")}
    <span aria-current="page">${ROTAS[rota].titulo}</span>
  `;
}

function marcarMenuAtivo(rota) {
  document.querySelectorAll(".menu-item").forEach((item) => {
    if (item.dataset.rota === rota) {
      item.setAttribute("aria-current", "page");
    } else {
      item.removeAttribute("aria-current");
    }
  });
}

function navegar() {
  const rota = (location.hash.replace(/^#\/?/, "") || "hoje").split("?")[0];
  const alvo = ROTAS[rota] ? rota : "hoje";
  montarTrilha(alvo);
  marcarMenuAtivo(alvo);
  document.title = `${ROTAS[alvo].titulo} — Radar de Estágio (mockup)`;
  TELA.innerHTML = "";
  ROTAS[alvo].render(TELA);
  document.getElementById("conteudo").focus();
  fecharMenu();
}

function cabecalho(titulo, subtitulo, acaoHtml = "") {
  return `
    <div class="cabecalho-tela">
      <div>
        <h1>${escapar(titulo)}</h1>
        ${subtitulo ? `<p class="subtitulo">${escapar(subtitulo)}</p>` : ""}
      </div>
      ${acaoHtml}
    </div>
  `;
}

function telaHoje(raiz) {
  const { data, vagas } = DADOS.hoje;
  const enviadas = vagas.filter((vaga) => vaga.estado !== "descartada").length;

  raiz.innerHTML =
    cabecalho(
      "Vagas de hoje",
      `${data} · ${enviadas} vagas enviadas no seu Telegram, ranqueadas pela IA`,
      `<a class="botao" href="#/historico">Ver histórico ${icone("seta")}</a>`,
    ) + `<div class="grade-vagas">${vagas.map(cartaoVaga).join("")}</div>`;

  raiz.querySelectorAll("[data-feedback]").forEach((botao) => {
    botao.addEventListener("click", () => aplicarFeedback(botao));
  });
}

function cartaoVaga(vaga) {
  return `
    <article class="vaga${vaga.estado === "descartada" ? " descartada" : ""}" data-id="${vaga.id}">
      <div class="nota ${classeDaNota(vaga.nota)}">
        ${vaga.nota}<small>NOTA</small>
      </div>
      <div>
        <div class="vaga-titulo">${escapar(vaga.titulo)}</div>
        <div class="vaga-empresa">${escapar(vaga.empresa)}</div>
        <div class="vaga-meta">
          <span>${icone("local")} ${escapar(vaga.localizacao)}</span>
          <span class="etiqueta ${vaga.modalidade === "remoto" ? "etiqueta-remoto" : ""}">${MODALIDADES[vaga.modalidade]}</span>
          <span>${escapar(vaga.publicada)}</span>
        </div>

        <div class="motivo">
          <b>Por que essa nota</b>
          ${escapar(vaga.motivo)}
        </div>

        ${
          vaga.alerta
            ? `<div class="faixa-aviso">${icone("alerta")}<span><b>Atenção:</b> ${escapar(vaga.alerta)}</span></div>`
            : ""
        }

        <div class="acoes-vaga">
          <a class="botao botao-primario" href="#" onclick="return false">${icone("link-externo")} Ver vaga</a>
          <button class="botao" type="button" data-feedback="curtida" aria-pressed="${vaga.estado === "curtida"}">
            ${icone("curtir")} Curtir
          </button>
          <button class="botao botao-perigo" type="button" data-feedback="descartada" aria-pressed="${vaga.estado === "descartada"}">
            ${icone("descartar")} Descartar
          </button>
        </div>
      </div>
    </article>
  `;
}

function aplicarFeedback(botao) {
  const cartao = botao.closest(".vaga");
  const tipo = botao.dataset.feedback;
  const jaAtivo = botao.getAttribute("aria-pressed") === "true";
  const grupo = cartao.querySelectorAll("[data-feedback]");

  grupo.forEach((outro) => outro.setAttribute("aria-pressed", "false"));
  cartao.classList.remove("descartada");

  if (jaAtivo) {
    avisar("Feedback removido dessa vaga.", "info");
    return;
  }

  botao.setAttribute("aria-pressed", "true");
  if (tipo === "descartada") {
    cartao.classList.add("descartada");
    avisar("Vaga descartada. A IA vai evitar vagas parecidas.", "atencao");
  } else {
    avisar("Vaga curtida. A IA vai priorizar vagas parecidas.", "sucesso");
  }
}

function telaHistorico(raiz) {
  const linhas = DADOS.historico;

  raiz.innerHTML =
    cabecalho("Histórico", "Vagas avaliadas nos últimos dias") +
    `
    <form class="filtros" onsubmit="return false" aria-label="Filtros do histórico">
      <div class="campo">
        <label for="filtro-de">De</label>
        <input type="date" id="filtro-de" value="2026-08-21" />
      </div>
      <div class="campo">
        <label for="filtro-ate">Até</label>
        <input type="date" id="filtro-ate" value="2026-08-26" />
      </div>
      <div class="campo">
        <label for="filtro-nota">Nota mínima</label>
        <input type="number" id="filtro-nota" min="0" max="100" step="5" value="0" placeholder="0 a 100" />
      </div>
      <div class="campo">
        <label for="filtro-estado">Estado</label>
        <select id="filtro-estado">
          <option value="">Todos</option>
          <option value="enviada">Enviada</option>
          <option value="curtida">Curtida</option>
          <option value="descartada">Descartada</option>
        </select>
      </div>
      <button class="botao botao-primario" type="button" id="aplicar-filtros">Aplicar filtros</button>
    </form>

    <div class="rolagem-tabela">
      <table class="tabela">
        <thead>
          <tr><th>Data</th><th>Vaga</th><th>Empresa</th><th>Nota</th><th>Estado</th></tr>
        </thead>
        <tbody>
          ${linhas
            .map(
              (linha) => `
            <tr>
              <td>${escapar(linha.data)}</td>
              <td><a href="#" onclick="return false">${escapar(linha.titulo)}</a></td>
              <td>${escapar(linha.empresa)}</td>
              <td>${linha.nota}</td>
              <td><span class="estado-linha estado-${linha.estado}">${ESTADOS_VAGA[linha.estado]}</span></td>
            </tr>`,
            )
            .join("")}
        </tbody>
      </table>
    </div>
  `;

  raiz.querySelector("#aplicar-filtros").addEventListener("click", () => {
    avisar("Filtros aplicados (protótipo — a lista é fixa).", "info");
  });
}

function telaMercado(raiz) {
  const { numeros, habilidades, modalidades, empresas } = DADOS.mercado;
  const maxHab = Math.max(...habilidades.map((h) => h.valor));
  const maxEmp = Math.max(...empresas.map((e) => e.valor));

  raiz.innerHTML =
    cabecalho("Mercado", "O que as vagas de estágio andam pedindo — base dos últimos 30 dias") +
    `
    <div class="painel-numeros">
      ${numeros
        .map(
          (n) => `<div class="numero"><div class="numero-valor">${escapar(n.valor)}</div><div class="numero-rotulo">${escapar(n.rotulo)}</div></div>`,
        )
        .join("")}
    </div>

    <section class="secao">
      <h2>Habilidades mais pedidas</h2>
      <p class="subtitulo">Percentual de vagas que citam cada habilidade.</p>
      ${habilidades.map((h) => barra(h.nome, h.valor, maxHab, "%")).join("")}
    </section>

    <section class="secao">
      <h2>Modalidade de trabalho</h2>
      <p class="subtitulo">Distribuição entre as vagas avaliadas.</p>
      ${modalidades.map((m) => barra(m.nome, m.valor, 100, "%")).join("")}
    </section>

    <section class="secao">
      <h2>Empresas que mais publicaram</h2>
      <p class="subtitulo">Número de vagas de estágio abertas no período.</p>
      ${empresas.map((e) => barra(e.nome, e.valor, maxEmp, "")).join("")}
    </section>
  `;
}

function barra(rotulo, valor, maximo, sufixo) {
  const largura = Math.round((valor / maximo) * 100);
  return `
    <div class="barra-dado">
      <span>${escapar(rotulo)}</span>
      <span class="barra-trilho"><span class="barra-preenchida" style="width: ${largura}%"></span></span>
      <span class="barra-valor">${valor}${sufixo}</span>
    </div>
  `;
}

function telaPerfil(raiz) {
  const p = DADOS.perfil;

  raiz.innerHTML =
    cabecalho("Perfil", "A IA compara cada vaga com estes dados. É o perfil fixo do MVP, aqui editável.") +
    `
    <form class="cartao" id="form-perfil" onsubmit="return false">
      <div class="form-grade">
        <div class="campo">
          <label for="perfil-curso">Curso</label>
          <input type="text" id="perfil-curso" value="${escapar(p.curso)}" placeholder="Ex.: Engenharia de Software" />
        </div>
        <div class="campo">
          <label for="perfil-periodo">Período atual</label>
          <input type="number" id="perfil-periodo" min="1" max="12" value="${p.periodo}" placeholder="1 a 12" />
        </div>

        <div class="campo largura-total">
          <label for="perfil-skill">Habilidades</label>
          <span class="ajuda">Digite uma habilidade e pressione Enter para adicionar.</span>
          <div class="tags" id="lista-tags">
            ${p.habilidades.map(tag).join("")}
            <input type="text" id="perfil-skill" placeholder="Ex.: TypeScript" style="border: none; min-width: 120px; flex: 1" />
          </div>
        </div>

        <div class="campo">
          <label for="perfil-cidade">Cidade</label>
          <input type="text" id="perfil-cidade" value="${escapar(p.cidade)}" placeholder="Cidade, UF (ex.: Rio de Janeiro, RJ)" />
        </div>
        <div class="campo">
          <label>Modalidade preferida</label>
          <div class="grupo-radio">
            ${["remoto", "hibrido", "presencial", "indiferente"]
              .map(
                (m) => `
              <label class="opcao-radio">
                <input type="radio" name="modalidade" value="${m}" ${m === p.modalidade ? "checked" : ""} />
                ${MODALIDADES[m]}
              </label>`,
              )
              .join("")}
          </div>
        </div>

        <div class="campo largura-total">
          <label for="perfil-nota">Nota mínima para receber no Telegram: <b id="valor-nota">${p.notaMinima}</b></label>
          <span class="ajuda">Vagas abaixo dessa nota são avaliadas, mas não entram na mensagem diária.</span>
          <input type="range" id="perfil-nota" min="0" max="100" step="5" value="${p.notaMinima}" />
        </div>
      </div>

      <div class="acoes-form">
        <button class="botao botao-primario" type="button" id="salvar-perfil">Salvar perfil</button>
        <button class="botao" type="reset">Desfazer alterações</button>
      </div>
    </form>
  `;

  const entradaSkill = raiz.querySelector("#perfil-skill");
  const lista = raiz.querySelector("#lista-tags");
  entradaSkill.addEventListener("keydown", (evento) => {
    if (evento.key !== "Enter") return;
    evento.preventDefault();
    const valor = entradaSkill.value.trim();
    if (!valor) return;
    entradaSkill.insertAdjacentHTML("beforebegin", tag(valor));
    ligarRemocaoDeTags(lista);
    entradaSkill.value = "";
  });
  ligarRemocaoDeTags(lista);

  raiz.querySelector("#perfil-nota").addEventListener("input", (evento) => {
    raiz.querySelector("#valor-nota").textContent = evento.target.value;
  });

  raiz.querySelector("#salvar-perfil").addEventListener("click", () => {
    avisar("Perfil salvo (protótipo — nada é gravado).", "sucesso");
  });
}

function tag(nome) {
  return `<span class="tag">${escapar(nome)}<button type="button" aria-label="Remover ${escapar(nome)}">${icone("x")}</button></span>`;
}

function ligarRemocaoDeTags(lista) {
  lista.querySelectorAll(".tag button").forEach((botao) => {
    botao.onclick = () => botao.parentElement.remove();
  });
}

function telaConfiguracoes(raiz) {
  const c = DADOS.configuracoes;

  raiz.innerHTML =
    cabecalho("Configurações", "Entrega da mensagem diária e fontes de vagas") +
    `
    <form class="cartao secao" id="form-config" onsubmit="return false">
      <div class="linha-config">
        <div>
          <div class="rotulo">Telegram — chat id</div>
          <div class="descricao">Para onde a mensagem diária é enviada.</div>
        </div>
        <input type="text" inputmode="numeric" pattern="[0-9]*" value="${escapar(c.telegramChatId)}" placeholder="Somente números (ex.: 123456789)" style="width: 220px" />
      </div>

      <div class="linha-config">
        <div>
          <div class="rotulo">Horário de entrega</div>
          <div class="descricao">Fuso de Brasília. O GitHub Actions pode atrasar alguns minutos.</div>
        </div>
        <input type="time" value="${escapar(c.horarioEntrega)}" style="width: 220px" />
      </div>

      <div class="linha-config">
        <div>
          <div class="rotulo">Vagas por mensagem</div>
          <div class="descricao">Quantas das melhores vagas entram na mensagem.</div>
        </div>
        <input type="number" min="1" max="15" value="${c.quantidadeVagas}" placeholder="1 a 15" style="width: 220px" />
      </div>

      <div class="linha-config">
        <div>
          <div class="rotulo">Janela de busca</div>
          <div class="descricao">Considera vagas publicadas nos últimos N dias.</div>
        </div>
        <input type="number" min="1" max="7" value="${c.diasRecentes}" placeholder="1 a 7" style="width: 220px" />
      </div>

      <div class="acoes-form">
        <button class="botao botao-primario" type="button" id="salvar-config">Salvar configurações</button>
        <button class="botao" type="button" id="testar-telegram">${icone("enviar")} Enviar mensagem de teste</button>
      </div>
    </form>

    <section class="cartao">
      <h2 style="font-size: var(--texto-lg); margin-bottom: var(--space-1)">Fontes de vagas</h2>
      <p class="subtitulo" style="margin-bottom: var(--space-3)">Na Fase 1 só a Adzuna está ativa. As demais entram nas próximas fases.</p>
      ${c.fontes
        .map(
          (fonte) => `
        <div class="fonte-item">
          ${icone(fonte.estado === "ativa" ? "check" : "historico")}
          <span>${escapar(fonte.nome)}</span>
          <span class="etiqueta ${fonte.estado === "ativa" ? "etiqueta-remoto" : ""}">${fonte.estado === "ativa" ? "Ativa" : "Em breve"}</span>
        </div>`,
        )
        .join("")}
    </section>
  `;

  raiz.querySelector("#salvar-config").addEventListener("click", () => {
    avisar("Configurações salvas (protótipo).", "sucesso");
  });
  raiz.querySelector("#testar-telegram").addEventListener("click", () => {
    avisar("Mensagem de teste enviada para o Telegram (simulação).", "info");
  });
}

function abrirMenu() {
  MENU.classList.add("aberto");
  document.querySelector(".recuo-menu")?.classList.add("ativo");
}

function fecharMenu() {
  MENU.classList.remove("aberto");
  document.querySelector(".recuo-menu")?.classList.remove("ativo");
}

function configurarTema() {
  const chave = "radar-tema";
  const salvo = localStorageSeguro(() => localStorage.getItem(chave));
  if (salvo) document.documentElement.dataset.tema = salvo;

  document.getElementById("alternar-tema").addEventListener("click", () => {
    const atual = document.documentElement.dataset.tema;
    const claroAgora =
      atual === "claro" ||
      (atual === "auto" && !window.matchMedia("(prefers-color-scheme: dark)").matches);
    const proximo = claroAgora ? "escuro" : "claro";
    document.documentElement.dataset.tema = proximo;
    localStorageSeguro(() => localStorage.setItem(chave, proximo));
  });
}

function localStorageSeguro(acao) {
  try {
    return acao();
  } catch {
    return null;
  }
}

const recuo = document.createElement("div");
recuo.className = "recuo-menu";
recuo.addEventListener("click", fecharMenu);
document.body.appendChild(recuo);

document.getElementById("alternar-menu").addEventListener("click", abrirMenu);
document.getElementById("busca-global").addEventListener("keydown", (evento) => {
  if (evento.key === "Enter") {
    evento.preventDefault();
    avisar("Busca ainda não implementada neste protótipo.", "info");
  }
});

configurarTema();
window.addEventListener("hashchange", navegar);
navegar();
