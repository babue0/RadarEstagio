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
const VERSAO_DOS_TERMOS = "2026-09-05";
let assistanceMode = null;
let recoverySession = false;
let resendAvailableAt = 0;
let resendTimer = null;
let captchaWidget = null;
let captchaToken = "";
const authReturn = new URLSearchParams(window.location.hash.slice(1));
const authQuery = new URLSearchParams(window.location.search);
const returningFromAuth = authReturn.has("access_token") || authQuery.has("code");
const returningFromRecovery = authReturn.get("type") === "recovery" || authQuery.get("fluxo") === "recuperar";
const authLinkError = authReturn.get("error_code") || authQuery.get("error_code") || authReturn.get("error") || authQuery.get("error");
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
  aceitou_termos: "Aceite os Termos de Uso e a Política de Privacidade para continuar.",
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
  radarClient.auth.onAuthStateChange((event) => {
    if (event === "PASSWORD_RECOVERY") {
      recoverySession = true;
      window.setTimeout(() => showAssistance("new-password"), 0);
    }
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
    if (authMode === "login" && !["email", "senha"].includes(field.name)) return false;
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
  if (step === 3 && authMode === "signup" && !editandoPerfilExistente && !form.elements.aceitou_termos.checked) {
    setFormMessage(mensagensValidacao.aceitou_termos);
    form.elements.aceitou_termos.focus();
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
    return "Sua conta foi criada, mas o perfil ainda não foi salvo. Entre novamente para concluir o perfil.";
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
  document.querySelector("#signup-consent").hidden = mode !== "signup";
  form.elements.aceitou_termos.required = mode === "signup";
  document.querySelectorAll('.form-step[data-step="3"] .field-grid > .field').forEach((field) => {
    field.hidden = mode === "login";
  });
  document.querySelector("#previous-step").hidden = mode === "login";
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
  document.querySelector("#signup-consent").hidden = authMode !== "signup";
  form.elements.aceitou_termos.required = authMode === "signup";
}

function entrarNoModoEdicao() {
  setAuthMode("signup");
  editandoPerfilExistente = true;
  credenciais.hidden = true;
  accountSwitch.hidden = true;
  form.elements.email.required = false;
  form.elements.senha.required = false;
  document.querySelector("#signup-consent").hidden = true;
  form.elements.aceitou_termos.required = false;
  submitProfile.textContent = "Salvar alterações";
}

function resetDialogView() {
  assistanceMode = null;
  document.querySelector("#auth-assistance").hidden = true;
  document.querySelector("#captcha-container").hidden = false;
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
  accountState.hidden = true;
  document.querySelector("#auth-assistance").hidden = true;
  document.querySelector("#captcha-container").hidden = true;
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
  showAssistance("resend", email);
  setFormMessage("Se o cadastro foi aceito, você receberá um link. Confirme em qualquer aparelho para continuar.");
  startResendCooldown();
}

function mostrarEstadoDoPerfil(profile) {
  if (profile.telegram_chat_id || profile.excluida_em) {
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
  document.querySelector("#auth-assistance").hidden = true;
  document.querySelector("#captcha-container").hidden = true;
  document.querySelector("#account-emails").checked = Boolean(profile.aceita_emails);
  document.querySelector("#account-emails").disabled = Boolean(profile.excluida_em);
  document.querySelector("#edit-profile").hidden = Boolean(profile.excluida_em);
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
    .select("curso,periodo,habilidades,cidade,modalidade,areas_de_interesse,telegram_chat_id,token_vinculo,ativo,excluida_em,aceita_emails,termos_aceitos_em,versao_dos_termos")
    .eq("user_id", userId)
    .maybeSingle();
  if (error) throw error;
  return data;
}

function cadastroFromProfile(profile) {
  return {
    perfil: profile,
    aceitou_termos: form.elements.aceitou_termos.checked,
    aceita_emails: form.elements.aceita_emails.checked,
    versao_dos_termos: VERSAO_DOS_TERMOS,
    sessao_id: eventSessionId(),
  };
}

async function persistProfile(userId, profile) {
  const existing = await loadProfile(userId);
  if (existing) {
    const { error } = await getClient().from("perfis")
      .update({ ...profile, atualizado_em: new Date().toISOString() }).eq("user_id", userId).select("user_id").single();
    if (error) throw error;
  } else {
    const { error } = await getClient().rpc("concluir_meu_cadastro", { cadastro: cadastroFromProfile(profile) });
    if (error) throw error;
  }
  clearPendingProfile();
  void registerEvent("perfil_salvo");
  return loadProfile(userId);
}

async function authenticate(email, password, profile) {
  const token = requireCaptcha();
  try {
    if (authMode === "login") {
      const { data, error } = await getClient().auth.signInWithPassword({ email, password, options: { captchaToken: token } });
      if (error) throw error;
      return data.session;
    }
    const { data, error } = await getClient().auth.signUp({
      email,
      password,
      options: { emailRedirectTo: authRedirect(), captchaToken: token, data: { cadastro_radar: cadastroFromProfile(profile) } },
    });
    if (error) throw error;
    return data.session;
  } finally {
    resetCaptcha();
  }
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
    else prepareMissingProfile(session);
  } catch (error) {
    setFormMessage(humanizeError(error));
  }
}

async function resumeConfirmedSignup() {
  try {
    const session = await currentSession();
    if (authLinkError) {
      showAssistance(returningFromRecovery ? "reset" : "resend");
      setFormMessage("Esse link expirou ou já foi usado. Solicite um novo abaixo.");
      return;
    }
    if (returningFromRecovery || recoverySession) {
      if (session && recoverySession) showAssistance("new-password");
      else if (!session) showAssistance("reset");
      return;
    }
    if (!session) return;
    const profile = await loadProfile(session.user.id);
    if (!returningFromAuth && !readPendingProfile()) return;
    clearPendingProfile();
    openDialog();
    if (profile) mostrarEstadoDoPerfil(profile);
    else prepareMissingProfile(session);
  } catch (error) {
    resetDialogView();
    openDialog();
    setFormMessage(humanizeError(error, { profilePending: true }));
  }
}

function prepareMissingProfile(session) {
  resetDialogView();
  setAuthMode("signup");
  form.elements.email.value = session.user.email ?? "";
  credenciais.hidden = true;
  form.elements.email.required = false;
  form.elements.senha.required = false;
  accountSwitch.hidden = true;
  setFormMessage("Seu e-mail está confirmado. Complete seu perfil para continuar.");
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
    mostrarEstadoDoPerfil(profile);
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
    const profile = authMode === "login" ? null : profileFromForm();
    const existingSession = await currentSession();
    if (editandoPerfilExistente && !existingSession) {
      sairDoModoEdicao();
      setFormMessage(MENSAGEM_SEM_SESSAO);
      return;
    }
    if (!editandoPerfilExistente && existingSession && existingSession.user.email !== email) {
      const { error } = await getClient().auth.signOut();
      if (error) throw error;
    }
    const session = editandoPerfilExistente || existingSession?.user.email === email
      ? existingSession
      : await authenticate(email, password, profile);
    form.elements.senha.value = "";
    if (!session) {
      showConfirmation(email);
      return;
    }
    const existing = await loadProfile(session.user.id);
    if (existing && !editandoPerfilExistente) {
      mostrarEstadoDoPerfil(existing);
      return;
    }
    if (authMode === "login") {
      prepareMissingProfile(session);
      return;
    }
    profileSaveStarted = true;
    const savedProfile = await persistProfile(session.user.id, profile);
    mostrarEstadoDoPerfil(savedProfile);
  } catch (error) {
    if (error?.code === "email_not_confirmed") showAssistance("resend", email);
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
  if (event.key === "Enter" && dialog.open && !form.hidden && currentStep === 1 && event.target.matches("input, select")) {
    event.preventDefault();
    completeProfileStep();
  }
});

function authRedirect() {
  return window.location.origin + window.location.pathname;
}

function requireCaptcha() {
  if (!window.RADAR_CONFIG.turnstileSiteKey) return undefined;
  if (!captchaToken) throw validationError("Conclua a verificação de segurança antes de continuar.");
  return captchaToken;
}

function resetCaptcha() {
  captchaToken = "";
  if (captchaWidget !== null) window.turnstile?.reset(captchaWidget);
}

function setupCaptcha() {
  if (!window.RADAR_CONFIG.turnstileSiteKey) return;
  window.radarCaptchaReady = () => {
    captchaWidget = window.turnstile.render("#captcha-container", {
      sitekey: window.RADAR_CONFIG.turnstileSiteKey,
      callback: (token) => { captchaToken = token; },
      "expired-callback": () => { captchaToken = ""; },
      "error-callback": () => {
        captchaToken = "";
        setFormMessage("A verificação de segurança falhou. Confira sua conexão e tente novamente.");
      },
    });
  };
  const script = document.createElement("script");
  script.src = "https://challenges.cloudflare.com/turnstile/v0/api.js?onload=radarCaptchaReady&render=explicit";
  script.async = true;
  script.onerror = () => setFormMessage("Não foi possível carregar a verificação de segurança. Recarregue a página.");
  document.head.append(script);
}

function updateResendButton() {
  if (assistanceMode !== "resend") return;
  const remaining = Math.max(0, Math.ceil((resendAvailableAt - Date.now()) / 1000));
  const button = document.querySelector("#assistance-submit");
  button.disabled = remaining > 0;
  button.textContent = remaining > 0 ? `Reenviar em ${remaining}s` : "Reenviar confirmação";
  if (!remaining && resendTimer) {
    window.clearInterval(resendTimer);
    resendTimer = null;
  }
}

function startResendCooldown() {
  resendAvailableAt = Date.now() + 60000;
  if (resendTimer) window.clearInterval(resendTimer);
  resendTimer = window.setInterval(updateResendButton, 1000);
  updateResendButton();
}

function showAssistance(mode, email = "") {
  assistanceMode = mode;
  form.hidden = true;
  progressWrap.hidden = true;
  successState.hidden = true;
  accountState.hidden = true;
  document.querySelector("#auth-assistance").hidden = false;
  document.querySelector("#captcha-container").hidden = mode === "new-password";
  const definingPassword = mode === "new-password";
  const emailInput = document.querySelector("#assistance-email");
  const passwordInput = document.querySelector("#assistance-password");
  document.querySelector("#assistance-email-field").hidden = definingPassword;
  document.querySelector("#assistance-password-field").hidden = !definingPassword;
  emailInput.required = !definingPassword;
  passwordInput.required = definingPassword;
  emailInput.value = email || emailInput.value || form.elements.email.value;
  passwordInput.value = "";
  const content = {
    resend: ["Confirme seu e-mail", "Abra o link em qualquer aparelho. Se precisar, corrija o endereço e solicite outro link.", "Reenviar confirmação"],
    reset: ["Recuperar senha", "Informe o e-mail da sua conta para receber um link de recuperação.", "Enviar link de recuperação"],
    "new-password": ["Defina sua nova senha", "Use uma senha com pelo menos 8 caracteres.", "Salvar nova senha"],
  }[mode];
  document.querySelector("#assistance-title").textContent = content[0];
  document.querySelector("#assistance-copy").textContent = content[1];
  document.querySelector("#assistance-submit").textContent = content[2];
  document.querySelector("#assistance-submit").disabled = false;
  setFormMessage();
  updateResendButton();
  openDialog();
  (definingPassword ? passwordInput : emailInput).focus();
}

document.querySelector("#forgot-password").addEventListener("click", () => showAssistance("reset"));
document.querySelector("#open-resend").addEventListener("click", () => showAssistance("resend"));
document.querySelector("#assistance-back").addEventListener("click", () => {
  resetDialogView();
  setAuthMode("login");
  showStep(3);
});

document.querySelector("#assistance-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const mode = assistanceMode;
  if (mode === "resend" && Date.now() < resendAvailableAt) return;
  const button = document.querySelector("#assistance-submit");
  if (button.disabled) return;
  button.disabled = true;
  setFormMessage();
  try {
    const email = document.querySelector("#assistance-email").value.trim();
    if (mode === "new-password") {
      if (!recoverySession || !(await currentSession())) throw validationError("Solicite um novo link de recuperação para definir sua senha.");
      const password = document.querySelector("#assistance-password").value;
      if (password.length < 8) throw validationError(mensagensValidacao.senha);
      const { error } = await getClient().auth.updateUser({ password });
      if (error) throw error;
      document.querySelector("#assistance-password").value = "";
      recoverySession = false;
      window.history.replaceState(null, "", window.location.pathname);
      const { error: logoutError } = await getClient().auth.signOut();
      if (logoutError) throw logoutError;
      resetDialogView();
      setAuthMode("login");
      showStep(3);
      setFormMessage("Senha atualizada. Entre com sua nova senha.");
      return;
    }
    const token = requireCaptcha();
    const result = mode === "resend"
      ? await getClient().auth.resend({ type: "signup", email, options: { emailRedirectTo: authRedirect(), captchaToken: token } })
      : await getClient().auth.resetPasswordForEmail(email, { redirectTo: authRedirect() + "?fluxo=recuperar", captchaToken: token });
    if (result.error) {
      if (result.error.status === 429 && mode === "resend") startResendCooldown();
      throw result.error;
    }
    if (mode === "resend") startResendCooldown();
    setFormMessage("Se houver uma conta elegível para esse endereço, você receberá o link. Confira também o spam.");
  } catch (error) {
    setFormMessage(humanizeError(error));
  } finally {
    resetCaptcha();
    button.disabled = false;
    updateResendButton();
  }
});

document.querySelectorAll("[data-toggle-password]").forEach((button) => {
  button.addEventListener("click", () => {
    const input = button.dataset.togglePassword === "senha"
      ? form.elements.senha : document.querySelector("#assistance-password");
    const showing = input.type === "password";
    input.type = showing ? "text" : "password";
    button.textContent = showing ? "Ocultar senha" : "Mostrar senha";
    button.setAttribute("aria-pressed", String(showing));
  });
});

document.querySelector("#account-emails").addEventListener("change", async (event) => {
  const input = event.target;
  const requested = input.checked;
  input.disabled = true;
  try {
    const session = await currentSession();
    if (!session) throw validationError(MENSAGEM_SEM_SESSAO);
    const { data, error } = await getClient().from("perfis").update({ aceita_emails: requested })
      .eq("user_id", session.user.id).select("aceita_emails").single();
    if (error) throw error;
    input.checked = data.aceita_emails;
    setAccountMessage("Preferência de e-mails atualizada.");
  } catch (error) {
    input.checked = !requested;
    setAccountMessage(humanizeError(error));
  } finally {
    input.disabled = false;
  }
});

document.querySelector("#download-data").addEventListener("click", async (event) => {
  const button = event.currentTarget;
  button.disabled = true;
  try {
    const { data, error } = await getClient().rpc("baixar_meus_dados");
    if (error) throw error;
    const url = URL.createObjectURL(new Blob([JSON.stringify(data, null, 2)], { type: "application/json" }));
    const link = document.createElement("a");
    link.href = url;
    link.download = "meus-dados-radar.json";
    document.body.append(link);
    link.click();
    link.remove();
    window.setTimeout(() => URL.revokeObjectURL(url), 1000);
    setAccountMessage("Seus dados foram preparados para download.");
  } catch (error) {
    setAccountMessage(humanizeError(error));
  } finally {
    button.disabled = false;
  }
});

document.querySelector("#success-account").addEventListener("click", async () => {
  try {
    showAccount(await perfilAtual());
  } catch (error) {
    setFormMessage(humanizeError(error));
  }
});

document.querySelector("#logout-account").addEventListener("click", async () => {
  const { error } = await getClient().auth.signOut();
  if (error) { setAccountMessage(humanizeError(error)); return; }
  clearPendingProfile();
  form.reset();
  selectedSkills.clear();
  renderSkills();
  resetDialogView();
  setAuthMode("login");
  showStep(3);
});

setupCaptcha();

if (!landingJaContadaNestaSessao()) {
  void registerEvent("landing_visualizada", { pagina: window.location.pathname });
}
resumeConfirmedSignup();
