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
const pendingProfileKey = "radar-perfil-pendente";
let currentStep = 1;
let authMode = "signup";
let radarClient = null;
const selectedSkills = new Set();
const totalSteps = 3;

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
  const invalid = fields.find((field) => !field.checkValidity());
  if (invalid) {
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

function resetDialogView() {
  form.hidden = false;
  successState.hidden = true;
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
  return {
    curso: data.get("curso").trim(),
    periodo: Number(data.get("periodo")),
    habilidades: data
      .get("habilidades")
      .split(",")
      .map((item) => item.trim())
      .filter(Boolean),
    cidade: data.get("cidade").trim(),
    modalidade: data.get("modalidade"),
  };
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

async function currentSession() {
  const { data, error } = await getClient().auth.getSession();
  if (error) throw error;
  return data.session;
}

async function loadProfile(userId) {
  const { data, error } = await getClient()
    .from("perfis")
    .select("curso,periodo,habilidades,cidade,modalidade,telegram_chat_id,token_vinculo,ativo")
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
    .select("curso,periodo,habilidades,cidade,modalidade,telegram_chat_id,token_vinculo,ativo")
    .single();
  if (error) throw error;
  clearPendingProfile();
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
    if (profile?.telegram_chat_id) showActivation(profile);
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
    if (profile) showActivation(profile);
  } catch (error) {
    setFormMessage(error.message);
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
    showActivation(profile);
  } catch (error) {
    resetDialogView();
    openDialog();
    setFormMessage(error.message);
  }
}

document.querySelectorAll(".js-open-signup").forEach((button) => {
  button.addEventListener("click", openSignup);
});
document.querySelector("#close-dialog").addEventListener("click", closeSignup);
document.querySelector("#finish-signup").addEventListener("click", closeSignup);
document.querySelector("#previous-step").addEventListener("click", () => showStep(2));
document.querySelector("#next-step").addEventListener("click", () => {
  if (validateStep(1)) showStep(2);
});
document.querySelector("[data-previous-step]").addEventListener("click", () => showStep(1));
document.querySelector("[data-next-step]").addEventListener("click", () => {
  addCustomSkill();
  if (validateStep(2)) showStep(3);
});
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
  if (!validateStep(2)) return;
  const email = form.elements.email.value.trim();
  const password = form.elements.senha.value;
  const profile = profileFromForm();
  setFormMessage();
  setSubmitting(true);
  try {
    savePendingProfile(profile);
    const existingSession = await currentSession();
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
    const savedProfile = await persistProfile(session.user.id, profile);
    showActivation(savedProfile);
  } catch (error) {
    setFormMessage(error.message);
  } finally {
    setSubmitting(false);
  }
});

telegramLink.addEventListener("click", () => {
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
    if (validateStep(1)) showStep(2);
  }
});

resumeConfirmedSignup();
