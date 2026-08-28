const dialog = document.querySelector("#signup-dialog");
const form = document.querySelector("#signup-form");
const successState = document.querySelector("#success-state");
const progressLabel = document.querySelector("#progress-label");
const progressPercent = document.querySelector("#progress-percent");
const progressBar = document.querySelector("#progress-bar");
const toast = document.querySelector("#toast");
let currentStep = 1;

function showStep(step) {
  currentStep = step;
  document.querySelectorAll(".form-step").forEach((element) => {
    element.classList.toggle("is-active", Number(element.dataset.step) === step);
  });
  const percent = step * 50;
  progressLabel.textContent = `Etapa ${step} de 2`;
  progressPercent.textContent = `${percent}%`;
  progressBar.style.width = `${percent}%`;
  document.querySelector(`.form-step[data-step="${step}"] input`)?.focus();
}

function validateStep(step) {
  const fields = [...document.querySelectorAll(`.form-step[data-step="${step}"] input`)];
  const invalid = fields.find((field) => !field.checkValidity());
  if (invalid) {
    invalid.reportValidity();
    invalid.focus();
    return false;
  }
  return true;
}

function resetDialogView() {
  form.hidden = false;
  successState.hidden = true;
  document.querySelector(".progress-wrap").hidden = false;
  showStep(1);
}

function openSignup() {
  resetDialogView();
  if (typeof dialog.showModal === "function") dialog.showModal();
  else dialog.setAttribute("open", "");
  document.body.style.overflow = "hidden";
}

function closeSignup() {
  if (dialog.open && typeof dialog.close === "function") dialog.close();
  else dialog.removeAttribute("open");
  document.body.style.overflow = "";
}

function saveProfile(data) {
  const profile = Object.fromEntries(data.entries());
  profile.habilidades = profile.habilidades.split(",").map((item) => item.trim()).filter(Boolean);
  profile.periodo = Number(profile.periodo);
  profile.salvoEm = new Date().toISOString();
  try {
    localStorage.setItem("radar-perfil", JSON.stringify(profile));
    return true;
  } catch {
    return false;
  }
}

document.querySelectorAll(".js-open-signup").forEach((button) => button.addEventListener("click", openSignup));
document.querySelector("#close-dialog").addEventListener("click", closeSignup);
document.querySelector("#previous-step").addEventListener("click", () => showStep(1));
document.querySelector("#next-step").addEventListener("click", () => {
  if (validateStep(1)) showStep(2);
});
document.querySelector("#finish-signup").addEventListener("click", () => {
  closeSignup();
  toast.hidden = false;
  window.setTimeout(() => { toast.hidden = true; }, 3600);
});

form.addEventListener("submit", (event) => {
  event.preventDefault();
  if (!validateStep(2)) return;
  const saved = saveProfile(new FormData(form));
  form.hidden = true;
  document.querySelector(".progress-wrap").hidden = true;
  successState.hidden = false;
  successState.querySelector("p:last-of-type").textContent = saved
    ? "Os dados foram salvos neste navegador. Na versão integrada, o próximo passo abrirá o bot com um vínculo seguro e temporário."
    : "O navegador bloqueou o armazenamento local, mas o fluxo de cadastro foi concluído. Nenhuma informação foi enviada.";
  successState.querySelector("#finish-signup").focus();
});

dialog.addEventListener("click", (event) => {
  if (event.target === dialog) closeSignup();
});
dialog.addEventListener("close", () => { document.body.style.overflow = ""; });

document.addEventListener("keydown", (event) => {
  if (event.key === "Escape" && dialog.open) closeSignup();
  if (event.key === "Enter" && dialog.open && currentStep === 1 && event.target.matches("input")) {
    event.preventDefault();
    if (validateStep(1)) showStep(2);
  }
});
