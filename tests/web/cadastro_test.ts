import assert from "assert";
import { JSDOM } from "jsdom";

const html = await Deno.readTextFile(
  new URL("../../web/index.html", import.meta.url),
);
const script = await Deno.readTextFile(
  new URL("../../web/assets/app.js", import.meta.url),
);
const user = {
  id: "00000000-0000-4000-8000-000000000001",
  email: "teste@example.com",
};
const profile = {
  curso: "Computação",
  periodo: 3,
  habilidades: ["Python"],
  cidade: "Recife, PE",
  modalidade: "remoto",
  areas_de_interesse: [],
  token_vinculo: "token",
  ativo: true,
  aceita_emails: false,
  telegram_chat_id: null,
};

function app(
  {
    session = null,
    savedProfile = null,
    url = "https://radarestagio.com/",
    key = "",
  } = {},
) {
  const dom = new JSDOM(html, { url, runScripts: "outside-only" });
  const w = dom.window;
  const calls = [];
  let authCallback;
  const client = {
    auth: {
      getSession: async () => ({ data: { session } }),
      onAuthStateChange: (callback) => {
        authCallback = callback;
      },
      signUp: async (args) => {
        calls.push(["signup", args]);
        return { data: { session: null } };
      },
      signInWithPassword: async (args) => {
        calls.push(["login", args]);
        return { data: { session: { user } } };
      },
      resend: async (args) => {
        calls.push(["resend", args]);
        return {};
      },
      resetPasswordForEmail: async (email, options) => {
        calls.push(["reset", email, options]);
        return {};
      },
      updateUser: async (args) => {
        calls.push(["password", args]);
        return {};
      },
      signOut: async () => {
        calls.push(["logout"]);
        return {};
      },
    },
    from: (table) => {
      const query = {
        select: () => query,
        eq: () => query,
        insert: async (args) => {
          calls.push(["insert", table, args]);
          return {};
        },
        update: (args) => {
          calls.push(["update", table, args]);
          return query;
        },
        maybeSingle: async () => ({ data: savedProfile }),
        single: async () => ({ data: savedProfile }),
      };
      return query;
    },
    rpc: async (name, args) => {
      calls.push(["rpc", name, args]);
      return { data: {} };
    },
  };
  w.RADAR_CONFIG = {
    supabaseUrl: "https://example.com",
    supabasePublishableKey: "public",
    telegramBot: "bot",
    turnstileSiteKey: key,
  };
  w.supabase = { createClient: () => client };
  w.eval(script);
  return {
    w,
    calls,
    client,
    close: () => w.close(),
    authEvent: (event) => authCallback(event),
  };
}

async function settle() {
  await new Promise((resolve) => setTimeout(resolve, 15));
}

function fill(w) {
  const form = w.document.querySelector("#signup-form");
  for (
    const [key, value] of Object.entries({
      curso: "Computação",
      periodo: "3",
      cidade: "Recife, PE",
      email: user.email,
      senha: "uma-senha-forte",
    })
  ) form.elements[key].value = value;
  form.querySelector('[value="remoto"]').checked = true;
  w.document.querySelector('[data-skill="Python"]').click();
  form.elements.aceitou_termos.checked = true;
  return form;
}

Deno.test("cadastro exige aceite e envia perfil e sessão sem guardar senha localmente", async () => {
  const a = app();
  try {
    const form = fill(a.w);
    form.elements.aceitou_termos.checked = false;
    form.dispatchEvent(new a.w.Event("submit", { cancelable: true }));
    await settle();
    assert.equal(a.calls.filter(([name]) => name === "signup").length, 0);
    form.elements.aceitou_termos.checked = true;
    form.dispatchEvent(new a.w.Event("submit", { cancelable: true }));
    await settle();
    const signup = a.calls.find(([name]) => name === "signup")[1];
    assert.equal(
      signup.options.data.cadastro_radar.perfil.cidade,
      "Recife, PE",
    );
    assert.equal(signup.options.data.cadastro_radar.aceita_emails, false);
    assert.equal(
      signup.options.data.cadastro_radar.versao_dos_termos,
      "2026-09-05",
    );
    assert.equal(a.w.localStorage.getItem("radar-perfil-pendente"), null);
    assert.equal(
      a.w.document.querySelector("#assistance-submit").disabled,
      true,
    );
  } finally {
    a.close();
  }
});

Deno.test("confirmação em outro aparelho consulta banco sem perfil no navegador", async () => {
  const a = app({
    session: { user },
    savedProfile: profile,
    url: "https://radarestagio.com/#access_token=fake",
  });
  try {
    await settle();
    assert.equal(a.w.document.querySelector("#success-state").hidden, false);
    assert.equal(a.w.document.querySelector("#telegram-link").hidden, false);
    assert.equal(
      a.calls.filter(([name]) => name === "rpc" || name === "update").length,
      0,
    );
  } finally {
    a.close();
  }
});

Deno.test("login preserva perfil existente mesmo com formulário diferente", async () => {
  const a = app({ savedProfile: { ...profile, telegram_chat_id: "123" } });
  try {
    const form = fill(a.w);
    a.w.setAuthMode("login");
    form.elements.cidade.value = "Outra cidade";
    form.dispatchEvent(new a.w.Event("submit", { cancelable: true }));
    await settle();
    assert.equal(a.calls.filter(([name]) => name === "login").length, 1);
    assert.equal(
      a.calls.filter(([name]) => name === "update" || name === "rpc").length,
      0,
    );
    assert.equal(a.w.document.querySelector("#account-state").hidden, false);
  } finally {
    a.close();
  }
});

Deno.test("edição após login mostra preferências e salva sem pedir novo aceite", async () => {
  const a = app({
    session: { user },
    savedProfile: { ...profile, telegram_chat_id: "123" },
  });
  try {
    await settle();
    a.w.setAuthMode("login");
    a.w.document.querySelector("#edit-profile").click();
    await settle();
    const form = a.w.document.querySelector("#signup-form");
    form.elements.cidade.value = "Natal, RN";
    assert.equal(form.elements.cidade.closest(".field").hidden, false);
    assert.equal(form.elements.aceitou_termos.required, false);
    form.dispatchEvent(new a.w.Event("submit", { cancelable: true }));
    await settle();
    const update = a.calls.find(([name, table]) =>
      name === "update" && table === "perfis"
    );
    assert.equal(update[2].cidade, "Natal, RN");
    assert.equal(update[2].versao_dos_termos, undefined);
    assert.equal(a.calls.some(([name]) => name === "signup"), false);
  } finally {
    a.close();
  }
});

Deno.test("preferência de e-mail pode ser revogada e falha preserva o valor anterior", async () => {
  const a = app({ session: { user }, savedProfile: profile });
  try {
    await settle();
    const checkbox = a.w.document.querySelector("#account-emails");
    checkbox.checked = false;
    checkbox.dispatchEvent(new a.w.Event("change"));
    await settle();
    assert.equal(
      a.calls.find(([name]) => name === "update")[2].aceita_emails,
      false,
    );
    assert.equal(checkbox.checked, false);
    a.client.from = () => {
      throw new Error("indisponível");
    };
    checkbox.checked = true;
    checkbox.dispatchEvent(new a.w.Event("change"));
    await settle();
    assert.equal(checkbox.checked, false);
    assert.equal(checkbox.disabled, false);
  } finally {
    a.close();
  }
});

Deno.test("CAPTCHA válido segue na autenticação e é descartado após tentativa", async () => {
  const a = app({ key: "chave-publica" });
  try {
    let widget;
    let resets = 0;
    a.w.turnstile = {
      render: (_, options) => {
        widget = options;
        return 1;
      },
      reset: () => {
        resets++;
      },
    };
    a.w.radarCaptchaReady();
    widget.callback("token-valido");
    const form = fill(a.w);
    form.dispatchEvent(new a.w.Event("submit", { cancelable: true }));
    await settle();
    assert.equal(
      a.calls.find(([name]) => name === "signup")[1].options.captchaToken,
      "token-valido",
    );
    assert.equal(resets, 1);
    assert.throws(() => a.w.requireCaptcha());
  } finally {
    a.close();
  }
});

Deno.test("reenvio usa e-mail editado e bloqueia clique repetido por um minuto", async () => {
  const a = app();
  try {
    a.w.showAssistance("resend", user.email);
    a.w.document.querySelector("#assistance-email").value =
      "corrigido@example.com";
    const submit = () =>
      a.w.document.querySelector("#assistance-form").dispatchEvent(
        new a.w.Event("submit", { cancelable: true }),
      );
    submit();
    await settle();
    submit();
    await settle();
    const resend = a.calls.filter(([name]) => name === "resend");
    assert.equal(resend.length, 1);
    assert.equal(resend[0][1].email, "corrigido@example.com");
  } finally {
    a.close();
  }
});

Deno.test("link expirado oferece e-mail editável sem contexto local", async () => {
  const a = app({ url: "https://radarestagio.com/#error_code=otp_expired" });
  try {
    await settle();
    assert.equal(a.w.document.querySelector("#auth-assistance").hidden, false);
    assert.equal(
      a.w.document.querySelector("#assistance-email").required,
      true,
    );
    assert.match(
      a.w.document.querySelector("#form-message").textContent,
      /expirou/,
    );
  } finally {
    a.close();
  }
});

Deno.test("CAPTCHA configurado impede autenticação sem token", async () => {
  const a = app({ key: "public-key" });
  try {
    const form = fill(a.w);
    form.dispatchEvent(new a.w.Event("submit", { cancelable: true }));
    await settle();
    assert.equal(a.calls.filter(([name]) => name === "signup").length, 0);
    assert.match(
      a.w.document.querySelector("#form-message").textContent,
      /verificação de segurança/,
    );
  } finally {
    a.close();
  }
});

Deno.test("recuperação exige evento autenticado antes de trocar senha", async () => {
  const a = app({ session: { user } });
  try {
    a.w.showAssistance("new-password");
    const submit = () => {
      a.w.document.querySelector("#assistance-password").value =
        "nova-senha-forte";
      a.w.document.querySelector("#assistance-form").dispatchEvent(
        new a.w.Event("submit", { cancelable: true }),
      );
    };
    submit();
    await settle();
    assert.equal(a.calls.filter(([name]) => name === "password").length, 0);
    a.authEvent("PASSWORD_RECOVERY");
    await settle();
    submit();
    await settle();
    assert.equal(a.calls.filter(([name]) => name === "password").length, 1);
    assert.equal(a.w.document.querySelector("#assistance-password").value, "");
  } finally {
    a.close();
  }
});
