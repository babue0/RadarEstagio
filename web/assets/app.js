const dialog = document.querySelector("#signup-dialog");
const form = document.querySelector("#signup-form");
const successState = document.querySelector("#success-state");
const progressWrap = document.querySelector(".progress-wrap");
const progressLabel = document.querySelector("#progress-label");
const progressPercent = document.querySelector("#progress-percent");
const progressBar = document.querySelector("#progress-bar");
const formMessage = document.querySelector("#form-message");
const submitProfile = document.querySelector("#submit-profile");
const toggleAuthMode = document.querySelector("#toggle-auth-mode");
const telegramLink = document.querySelector("#telegram-link");
const accountState = document.querySelector("#account-state");
const accountMessage = document.querySelector("#account-message");
const accountConfirm = document.querySelector("#account-confirm");
const toggleDeliveries = document.querySelector("#toggle-deliveries");
const credenciais = document.querySelector("#credenciais");
const accountSwitch = document.querySelector("#account-switch");
let editandoPerfilExistente = false;
const HORARIO_DA_BUSCA = "todo dia por volta das 7h20 da manhã";
const MENSAGEM_SEM_SESSAO = "Sua sessão expirou. Feche e entre de novo para continuar.";
const MENSAGEM_SEM_PERFIL = "Não encontramos seu perfil. Feche e entre de novo.";
const DIAS_ATE_APAGAR = 60;
const pendingProfileKey = "radar-perfil-pendente";
const eventSessionKey = "radar-sessao-eventos";
const landingViewKey = "radar-landing-vista";
const uuidPattern = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
let currentStep = 1;
let authMode = "signup";
let radarClient = null;
const selectedSkills = new Set();
const totalSteps = 3;
const modalidadesAceitas = new Set(["remoto", "presencial", "hibrido", "indiferente"]);
const mensagensValidacao = {
  curso: "Informe seu curso para continuar.",
  periodo: "Selecione seu período atual para continuar.",
  cidade: "Informe uma cidade válida para continuar.",
  modalidade: "Escolha uma modalidade para continuar.",
  email: "Digite um e-mail válido para continuar.",
  senha: "Use uma senha com pelo menos 8 caracteres para continuar.",
};

function getClient() {
  if (radarClient) return radarClient;
  const config = window.RADAR_CONFIG;
  if (!window.supabase?.createClient || !config?.supabaseUrl || !config?.supabasePublishableKey) {
    throw new Error(
      "O cadastro ainda não foi configurado. Informe a chave pública do Supabase em web/config.js.",
    );
  }
  radarClient = window.supabase.createClient(config.supabaseUrl, config.supabasePublishableKey, {
    auth: { persistSession: true, autoRefreshToken: true, detectSessionInUrl: true },
  });
  return radarClient;
}

function eventSessionId() {
  const existing = localStorage.getItem(eventSessionKey);
  if (existing && uuidPattern.test(existing)) return existing;
  const created = crypto.randomUUID();
  localStorage.setItem(eventSessionKey, created);
  return created;
}

async function registerEvent(name, properties = {}) {
  try {
    const client = getClient();
    const { data } = await client.auth.getSession();
    const { error } = await client.from("eventos_produto").insert({
      nome: name,
      sessao_id: eventSessionId(),
      user_id: data.session?.user.id ?? null,
      propriedades: properties,
    });
    if (error) throw error;
  } catch (error) {
    console.warn(`Radar: o evento "${name}" não foi registrado.`, error);
    return false;
  }
  return true;
}

function landingJaContadaNestaSessao() {
  try {
    if (sessionStorage.getItem(landingViewKey)) return true;
    sessionStorage.setItem(landingViewKey, "1");
    return false;
  } catch {
    return false;
  }
}

function showStep(step) {
  currentStep = step;
  document.querySelectorAll(".form-step").forEach((element) => {
    element.classList.toggle("is-active", Number(element.dataset.step) === step);
  });
  const percent = Math.round((step / totalSteps) * 100);
  progressLabel.textContent = `Etapa ${step} de ${totalSteps}`;
  progressPercent.textContent = `${percent}%`;
  progressBar.style.width = `${percent}%`;
  document.querySelector(
    `.form-step[data-step="${step}"] input:not([type="hidden"]), .form-step[data-step="${step}"] select, .form-step[data-step="${step}"] button`,
  )?.focus();
}

function validateStep(step) {
  if (step === 2 && selectedSkills.size === 0) {
    setFormMessage("Escolha ou digite pelo menos uma habilidade.");
    document.querySelector("#custom-skill").focus();
    return false;
  }
  setFormMessage();
  const fields = [...document.querySelectorAll(
    `.form-step[data-step="${step}"] input:not([type="hidden"]), .form-step[data-step="${step}"] select`,
  )];
  const invalid = fields.find((field) => {
    if (field.name === "cidade" && field.value.trim().length < 2) return true;
    if (field.name === "modalidade" && !modalidadesAceitas.has(form.elements.modalidade.value)) return true;
    return !field.checkValidity();
  });
  if (invalid) {
    setFormMessage(mensagensValidacao[invalid.name] ?? "Revise os campos antes de continuar.");
    invalid.reportValidity();
    invalid.focus();
    return false;
  }
  return true;
}

function renderSkills() {
  form.elements.habilidades.value = [...selectedSkills].join(",");
  document.querySelectorAll("[data-skill]").forEach((button) => {
    const active = selectedSkills.has(button.dataset.skill);
    button.classList.toggle("is-selected", active);
    button.setAttribute("aria-pressed", String(active));
  });
  const container = document.querySelector("#selected-skills");
  container.replaceChildren(...[...selectedSkills].map((skill) => {
    const chip = document.createElement("button");
    chip.type = "button";
    chip.textContent = `${skill} ×`;
    chip.setAttribute("aria-label", `Remover ${skill}`);
    chip.addEventListener("click", () => {
      selectedSkills.delete(skill);
      renderSkills();
    });
    return chip;
  }));
}

function addCustomSkill() {
  const input = document.querySelector("#custom-skill");
  const skill = input.value.trim();
  if (!skill) return;
  selectedSkills.add(skill);
  input.value = "";
  renderSkills();
  setFormMessage();
}

function validationError(message) {
  const error = new Error(message);
  error.name = "RadarValidationError";
  return error;
}

function humanizeError(error, { profilePending = false } = {}) {
  const message = String(error?.message ?? "").toLowerCase();
  const code = String(error?.code ?? "").toLowerCase();
  const status = Number(error?.status);

  if (message.startsWith("o cadastro ainda não foi configurado")) {
    return error.message;
  }
  if (error?.name === "RadarValidationError") return error.message;
  if (profilePending) {
    return "Sua conta foi criada, mas o perfil ainda não foi salvo. Seus dados continuam salvos neste navegador. Tente enviar novamente.";
  }
  if (code === "user_already_exists" || code === "email_exists" || message.includes("user already registered")) {
    return "Já existe uma conta com esse e-mail. Escolha “Entrar” ou use outro e-mail.";
  }
  if (code === "invalid_credentials" || message.includes("invalid login credentials")) {
    return "E-mail ou senha incorretos. Confira os dados ou crie uma conta.";
  }
  if (code === "email_not_confirmed" || message.includes("email not confirmed")) {
    return "Confirme seu e-mail pelo link recebido antes de entrar.";
  }
  if (code === "weak_password" || message.includes("password should be at least")) {
    return "A senha precisa ter pelo menos 8 caracteres.";
  }
  if (code === "over_email_send_rate_limit" || status === 429) {
    return "Muitas tentativas em pouco tempo. Aguarde alguns minutos e tente novamente.";
  }
  if (code === "23505" || message.includes("duplicate key")) {
    return "Este perfil já existe. Recarregue a página e tente novamente.";
  }
  if (code === "42501" || message.includes("row-level security") || message.includes("permission denied")) {
    return "Não foi possível salvar o perfil nesta conta. Entre novamente e tente outra vez.";
  }
  if (message.includes("failed to fetch") || message.includes("network") || message.includes("fetch")) {
    return "Não foi possível conectar ao cadastro. Verifique a conexão e tente novamente.";
  }
  return "Não foi possível concluir o cadastro agora. Verifique os dados e tente novamente.";
}

function setFormMessage(message = "") {
  formMessage.textContent = message;
  formMessage.hidden = !message;
}

function setSubmitting(submitting) {
  submitProfile.disabled = submitting;
  if (submitting) {
    submitProfile.textContent = "Salvando…";
    return;
  }
  if (editandoPerfilExistente) {
    submitProfile.textContent = "Salvar alterações";
    return;
  }
  submitProfile.textContent = authMode === "signup"
    ? "Criar conta e continuar →"
    : "Entrar e continuar →";
}

function setAuthMode(mode) {
  authMode = mode;
  const password = form.elements.senha;
  password.autocomplete = mode === "signup" ? "new-password" : "current-password";
  toggleAuthMode.textContent = mode === "signup" ? "Entrar" : "Criar conta";
  toggleAuthMode.parentElement.firstChild.textContent = mode === "signup"
    ? "Já possui uma conta? "
    : "Ainda não possui uma conta? ";
  setSubmitting(false);
  setFormMessage();
}

function sairDoModoEdicao() {
  editandoPerfilExistente = false;
  credenciais.hidden = false;
  accountSwitch.hidden = false;
  form.elements.email.required = true;
  form.elements.senha.required = true;
}

function entrarNoModoEdicao() {
  editandoPerfilExistente = true;
  credenciais.hidden = true;
  accountSwitch.hidden = true;
  form.elements.email.required = false;
  form.elements.senha.required = false;
  submitProfile.textContent = "Salvar alterações";
}

function resetDialogView() {
  sairDoModoEdicao();
  form.hidden = false;
  successState.hidden = true;
  accountState.hidden = true;
  accountConfirm.hidden = true;
  setAccountMessage();
  progressWrap.hidden = false;
  telegramLink.hidden = true;
  setFormMessage();
  setSubmitting(false);
  showStep(1);
}

function openDialog() {
  if (typeof dialog.showModal === "function") dialog.showModal();
  else dialog.setAttribute("open", "");
  document.body.style.overflow = "hidden";
}

function closeSignup() {
  if (dialog.open && typeof dialog.close === "function") dialog.close();
  else dialog.removeAttribute("open");
  document.body.style.overflow = "";
}

function profileFromForm() {
  addCustomSkill();
  const data = new FormData(form);
  const profile = {
    curso: data.get("curso").trim(),
    periodo: Number(data.get("periodo")),
    habilidades: data
      .get("habilidades")
      .split(",")
      .map((item) => item.trim())
      .filter(Boolean),
    cidade: data.get("cidade").trim(),
    modalidade: data.get("modalidade"),
    areas_de_interesse: data.getAll("areas"),
  };
  if (!profile.curso) throw validationError("Informe seu curso para continuar.");
  if (!Number.isInteger(profile.periodo) || profile.periodo < 1) {
    throw validationError("Selecione seu período atual para continuar.");
  }
  if (profile.habilidades.length === 0) {
    throw validationError("Escolha ou digite pelo menos uma habilidade.");
  }
  if (profile.cidade.length < 2) throw validationError("Informe uma cidade válida para continuar.");
  if (!modalidadesAceitas.has(profile.modalidade)) {
    throw validationError("Escolha uma modalidade para continuar.");
  }
  return profile;
}

function savePendingProfile(profile) {
  localStorage.setItem(pendingProfileKey, JSON.stringify(profile));
}

function readPendingProfile() {
  try {
    return JSON.parse(localStorage.getItem(pendingProfileKey));
  } catch {
    return null;
  }
}

function clearPendingProfile() {
  localStorage.removeItem(pendingProfileKey);
}

function showSuccess({ kicker, title, copy, token, linked = false }) {
  form.hidden = true;
  progressWrap.hidden = true;
  successState.hidden = false;
  document.querySelector("#success-kicker").textContent = kicker;
  document.querySelector("#success-title").textContent = title;
  document.querySelector("#success-copy").textContent = copy;
  telegramLink.hidden = !token || linked;
  if (token && !linked) {
    const bot = window.RADAR_CONFIG.telegramBot;
    telegramLink.href = `https://t.me/${bot}?start=${token}`;
  }
  const target = telegramLink.hidden
    ? document.querySelector("#finish-signup")
    : telegramLink;
  target.focus();
}

function showConfirmation(email) {
  showSuccess({
    kicker: "Confirme seu e-mail",
    title: "Falta só confirmar sua conta.",
    copy: `Enviamos um link para ${email}. Abra-o neste navegador para salvar o perfil e ativar o Telegram.`,
  });
}

function mostrarEstadoDoPerfil(profile) {
  if (profile.telegram_chat_id) {
    showAccount(profile);
    return;
  }
  showActivation(profile);
}

function showActivation(profile) {
  if (profile.telegram_chat_id) {
    showSuccess({
      kicker: "Radar ativado",
      title: "As vagas certas já podem chegar até você.",
      copy: "Seu Telegram está vinculado. O Radar enviará as oportunidades compatíveis nas próximas execuções.",
      linked: true,
    });
    return;
  }
  showSuccess({
    kicker: "Perfil salvo",
    title: "Agora, ative as entregas.",
    copy: "Vincule seu Telegram para receber as vagas selecionadas pelo Radar.",
    token: profile.token_vinculo,
  });
}


function setAccountMessage(message = "") {
  accountMessage.textContent = message;
  accountMessage.hidden = !message;
}

function resumoDoPerfil(profile) {
  const modalidades = {
    remoto: "remoto",
    presencial: "presencial",
    hibrido: "híbrido",
    indiferente: "qualquer modalidade",
  };
  const habilidades = profile.habilidades.join(", ");
  return `${profile.curso}, ${profile.periodo}º período · ${profile.cidade} · ${modalidades[profile.modalidade]}\n${habilidades}`;
}

function estadoDasEntregas(profile) {
  if (profile.excluida_em) {
    return `Exclusão pedida. Seus dados são apagados em ${dataDoApagamento(profile.excluida_em)}.`;
  }
  if (!profile.telegram_chat_id) return "Telegram ainda não vinculado.";
  if (!profile.ativo) return "Entregas pausadas. Nada chega até você retomar.";
  return `Entregas ativas: o Radar procura ${HORARIO_DA_BUSCA}.`;
}

function showAccount(profile) {
  form.hidden = true;
  progressWrap.hidden = true;
  successState.hidden = true;
  accountConfirm.hidden = true;
  accountState.hidden = false;
  setAccountMessage();
  document.querySelector("#account-summary").textContent = resumoDoPerfil(profile);
  document.querySelector("#account-schedule").textContent = estadoDasEntregas(profile);
  const emExclusao = Boolean(profile.excluida_em);
  toggleDeliveries.textContent = profile.ativo ? "Pausar entregas" : "Retomar entregas";
  toggleDeliveries.hidden = !profile.telegram_chat_id || emExclusao;
  document.querySelector("#unlink-telegram").hidden = !profile.telegram_chat_id || emExclusao;
  document.querySelector("#delete-account").hidden = emExclusao;
  document.querySelector("#cancel-deletion").hidden = !emExclusao;
  document.querySelector("#close-account").focus();
}

function preencherFormularioCom(profile) {
  form.elements.curso.value = profile.curso;
  form.elements.periodo.value = String(profile.periodo);
  form.elements.cidade.value = profile.cidade;
  form.elements.modalidade.value = profile.modalidade;
  selectedSkills.clear();
  profile.habilidades.forEach((skill) => selectedSkills.add(skill));
  renderSkills();
  document.querySelectorAll('input[name="areas"]').forEach((campo) => {
    campo.checked = (profile.areas_de_interesse ?? []).includes(campo.value);
  });
}

async function perfilAtual() {
  const session = await currentSession();
  if (!session) throw validationError(MENSAGEM_SEM_SESSAO);
  const profile = await loadProfile(session.user.id);
  if (!profile) throw validationError(MENSAGEM_SEM_PERFIL);
  return profile;
}

async function alternarEntregas(profile) {
  const session = await currentSession();
  if (!session) throw validationError(MENSAGEM_SEM_SESSAO);
  const { error } = await getClient()
    .from("perfis")
    .update({ ativo: !profile.ativo, atualizado_em: new Date().toISOString() })
    .eq("user_id", session.user.id);
  if (error) throw error;
}

function dataDoApagamento(marcadaEm) {
  const marcada = marcadaEm ? new Date(marcadaEm) : new Date();
  marcada.setDate(marcada.getDate() + DIAS_ATE_APAGAR);
  return marcada.toLocaleDateString("pt-BR");
}

function pedirConfirmacao(copy, acao) {
  document.querySelector("#account-confirm-copy").textContent = copy;
  accountConfirm.hidden = false;
  accountConfirm.dataset.acao = acao;
  document.querySelector("#account-confirm-yes").focus();
}

async function currentSession() {
  const { data, error } = await getClient().auth.getSession();
  if (error) throw error;
  return data.session;
}

async function loadProfile(userId) {
  const { data, error } = await getClient()
    .from("perfis")
    .select("curso,periodo,habilidades,cidade,modalidade,areas_de_interesse,telegram_chat_id,token_vinculo,ativo,excluida_em")
    .eq("user_id", userId)
    .maybeSingle();
  if (error) throw error;
  return data;
}

async function persistProfile(userId, profile) {
  const existing = await loadProfile(userId);
  const fields = { ...profile, atualizado_em: new Date().toISOString() };
  const query = existing
    ? getClient().from("perfis").update(fields).eq("user_id", userId)
    : getClient().from("perfis").insert({ user_id: userId, ...profile });
  const { data, error } = await query
    .select("curso,periodo,habilidades,cidade,modalidade,areas_de_interesse,telegram_chat_id,token_vinculo,ativo,excluida_em")
    .single();
  if (error) throw error;
  clearPendingProfile();
  void registerEvent("perfil_salvo");
  return data;
}

async function authenticate(email, password) {
  if (authMode === "login") {
    const { data, error } = await getClient().auth.signInWithPassword({ email, password });
    if (error) throw error;
    return data.session;
  }
  const emailRedirectTo = window.location.href.split("#")[0].split("?")[0];
  const { data, error } = await getClient().auth.signUp({
    email,
    password,
    options: { emailRedirectTo },
  });
  if (error) throw error;
  if (data.user?.identities?.length === 0) {
    const login = await getClient().auth.signInWithPassword({ email, password });
    if (login.error) throw login.error;
    return login.data.session;
  }
  return data.session;
}

async function refreshActivationStatus() {
  try {
    const session = await currentSession();
    if (!session) return;
    const profile = await loadProfile(session.user.id);
    if (profile) mostrarEstadoDoPerfil(profile);
  } catch {
    document.querySelector("#success-copy").textContent =
      "O Telegram foi aberto, mas ainda não conseguimos confirmar o vínculo. Tente voltar a esta janela novamente.";
  }
}

async function openSignup() {
  resetDialogView();
  openDialog();
  try {
    const session = await currentSession();
    if (!session) return;
    form.elements.email.value = session.user.email ?? "";
    const profile = await loadProfile(session.user.id);
    if (profile) mostrarEstadoDoPerfil(profile);
  } catch (error) {
    setFormMessage(humanizeError(error));
  }
}

async function resumeConfirmedSignup() {
  const pending = readPendingProfile();
  if (!pending) return;
  try {
    const session = await currentSession();
    if (!session) return;
    openDialog();
    const profile = await persistProfile(session.user.id, pending);
    mostrarEstadoDoPerfil(profile);
  } catch (error) {
    resetDialogView();
    openDialog();
    setFormMessage(humanizeError(error, { profilePending: true }));
  }
}

function completeProfileStep() {
  if (!validateStep(1)) return;
  void registerEvent("etapa_perfil_concluida");
  showStep(2);
}

function completeSkillsStep() {
  addCustomSkill();
  if (!validateStep(2)) return;
  void registerEvent("etapa_habilidades_concluida", { quantidade: selectedSkills.size });
  showStep(3);
}

document.querySelectorAll(".js-open-signup").forEach((button) => {
  button.addEventListener("click", () => {
    void registerEvent("cta_cadastro_aberto", {
      origem: button.dataset.eventOrigin ?? "desconhecida",
    });
    openSignup();
  });
});
document.querySelector("#close-dialog").addEventListener("click", closeSignup);
document.querySelector("#close-account").addEventListener("click", closeSignup);

document.querySelector("#edit-profile").addEventListener("click", async () => {
  try {
    const profile = await perfilAtual();
    preencherFormularioCom(profile);
    accountState.hidden = true;
    form.hidden = false;
    progressWrap.hidden = false;
    entrarNoModoEdicao();
    setSubmitting(false);
    showStep(1);
  } catch (error) {
    setAccountMessage(humanizeError(error));
  }
});

toggleDeliveries.addEventListener("click", async () => {
  setAccountMessage();
  try {
    const profile = await perfilAtual();
    await alternarEntregas(profile);
    showAccount({ ...profile, ativo: !profile.ativo });
  } catch (error) {
    setAccountMessage(humanizeError(error));
  }
});

document.querySelector("#unlink-telegram").addEventListener("click", () => {
  pedirConfirmacao(
    "Desvincular para de entregar vagas neste Telegram e invalida o link antigo. Você pode vincular de novo depois.",
    "desvincular",
  );
});

document.querySelector("#delete-account").addEventListener("click", () => {
  pedirConfirmacao(
    "As entregas param na hora. Sua conta e seus dados são apagados definitivamente 60 dias " +
      "depois; até lá você pode cancelar entrando aqui de novo.",
    "excluir",
  );
});

document.querySelector("#cancel-deletion").addEventListener("click", async () => {
  setAccountMessage();
  try {
    const { error } = await getClient().rpc("cancelar_exclusao_da_minha_conta");
    if (error) throw error;
    const profile = await perfilAtual();
    showAccount(profile);
  } catch (error) {
    setAccountMessage(humanizeError(error));
  }
});

document.querySelector("#account-confirm-no").addEventListener("click", () => {
  accountConfirm.hidden = true;
});

document.querySelector("#account-confirm-yes").addEventListener("click", async () => {
  const acao = accountConfirm.dataset.acao;
  accountConfirm.hidden = true;
  setAccountMessage();
  try {
    if (acao === "desvincular") {
      const { error } = await getClient().rpc("desvincular_meu_telegram");
      if (error) throw error;
      const profile = await perfilAtual();
      if (!profile) {
        showConfirmation(form.elements.email.value);
        return;
      }
      mostrarEstadoDoPerfil(profile);
      return;
    }
    const { data, error } = await getClient().rpc("excluir_minha_conta");
    if (error) throw error;
    showSuccess({
      kicker: "Exclusão agendada",
      title: "As entregas pararam agora.",
      copy: `Seus dados são apagados definitivamente em ${dataDoApagamento(data)}. Até lá, entre aqui de novo para cancelar.`,
    });
  } catch (error) {
    setAccountMessage(humanizeError(error));
  }
});
document.querySelector("#finish-signup").addEventListener("click", closeSignup);
document.querySelector("#previous-step").addEventListener("click", () => showStep(2));
document.querySelector("#next-step").addEventListener("click", completeProfileStep);
document.querySelector("[data-previous-step]").addEventListener("click", () => showStep(1));
document.querySelector("[data-next-step]").addEventListener("click", completeSkillsStep);
document.querySelectorAll("[data-skill]").forEach((button) => {
  button.addEventListener("click", () => {
    const skill = button.dataset.skill;
    if (selectedSkills.has(skill)) selectedSkills.delete(skill);
    else selectedSkills.add(skill);
    renderSkills();
    setFormMessage();
  });
});
document.querySelector("#custom-skill").addEventListener("keydown", (event) => {
  if (event.key !== "Enter") return;
  event.preventDefault();
  addCustomSkill();
});
toggleAuthMode.addEventListener("click", () => {
  setAuthMode(authMode === "signup" ? "login" : "signup");
});

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (!validateStep(3)) return;
  void registerEvent("etapa_preferencias_concluida");
  const email = form.elements.email.value.trim();
  const password = form.elements.senha.value;
  let profileSaveStarted = false;
  setFormMessage();
  setSubmitting(true);
  try {
    const profile = profileFromForm();
    savePendingProfile(profile);
    const existingSession = await currentSession();
    if (editandoPerfilExistente && !existingSession) {
      sairDoModoEdicao();
      setFormMessage(MENSAGEM_SEM_SESSAO);
      return;
    }
    if (existingSession && existingSession.user.email !== email) {
      const { error } = await getClient().auth.signOut();
      if (error) throw error;
    }
    const session = existingSession?.user.email === email
      ? existingSession
      : await authenticate(email, password);
    form.elements.senha.value = "";
    if (!session) {
      showConfirmation(email);
      return;
    }
    profileSaveStarted = true;
    const savedProfile = await persistProfile(session.user.id, profile);
    mostrarEstadoDoPerfil(savedProfile);
  } catch (error) {
    setFormMessage(humanizeError(error, { profilePending: profileSaveStarted }));
  } finally {
    setSubmitting(false);
  }
});

telegramLink.addEventListener("click", () => {
  void registerEvent("telegram_aberto");
  window.setTimeout(refreshActivationStatus, 1500);
});

window.addEventListener("focus", () => {
  if (!dialog.open || telegramLink.hidden) return;
  refreshActivationStatus();
});

dialog.addEventListener("click", (event) => {
  if (event.target === dialog) closeSignup();
});
dialog.addEventListener("close", () => { document.body.style.overflow = ""; });

document.addEventListener("keydown", (event) => {
  if (event.key === "Escape" && dialog.open) closeSignup();
  if (event.key === "Enter" && dialog.open && currentStep === 1 && event.target.matches("input, select")) {
    event.preventDefault();
    completeProfileStep();
  }
});

if (!landingJaContadaNestaSessao()) {
  void registerEvent("landing_visualizada", { pagina: window.location.pathname });
}
resumeConfirmedSignup();
