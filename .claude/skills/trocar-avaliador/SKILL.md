---
name: trocar-avaliador
description: Como alternar o avaliador de IA do Radar entre a Gemini API e o Antigravity CLI (agy) — variáveis de ambiente, .env e comandos de verificação.
---

# Trocar o avaliador de IA

`AVALIADOR` escolhe o adapter sem alterar o pipeline:

- `AVALIADOR=gemini_api` usa `AvaliadorGemini`, exige `GEMINI_API_KEY` e usa
  `GEMINI_MODELO` (padrão `gemini-3.6-flash`). É o padrão quando a variável não existe.
- `AVALIADOR=agy` usa `AvaliadorAgy`, não exige `GEMINI_API_KEY` e usa `AGY_MODELO`
  (padrão `gemini-3.6-flash-low`) e `AGY_TIMEOUT_SEGUNDOS` (padrão 300). Requer o comando
  `agy` instalado e autenticado localmente.

Para persistir a escolha, editar o `.env`:

```env
AVALIADOR=agy
AGY_MODELO=gemini-3.6-flash-low
```

Para trocar somente em uma execução, a variável do shell sobrescreve o `.env`:

```bash
AVALIADOR=agy uv run python -m radar avaliar
AVALIADOR=gemini_api uv run python -m radar avaliar
```

`uv run python -m radar verificar` mostra o adapter ativo. `avaliar` testa até três vagas
sem enviar mensagem; `uv run python -m radar` executa o fluxo completo e envia ao Telegram.
O GitHub Actions não define `AVALIADOR`, portanto continua no padrão `gemini_api`.

Cuidado com a cota: a cota gratuita do `gemini-3.6-flash` é de 20 requisições por minuto.
Evitar rodar `avaliar`/`rodar` repetidamente sem necessidade.
