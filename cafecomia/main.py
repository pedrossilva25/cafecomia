import os
import asyncio
import json
import time
from dotenv import load_dotenv
import aiohttp

# 🔐 1. Carrega variáveis do .env
load_dotenv()

# 🌐 2. Configurações da API e autenticação
API = "https://api.browser-use.com/api/v1"
KEY = os.getenv("BROWSER_USE_API_KEY") or os.getenv("BROWSER_USE_CLOUD_API_KEY")
if not KEY:
    raise SystemExit("Faltou a API key no .env (BROWSER_USE_API_KEY=bu_...).")

# 📦 3. Define a tarefa e payload
TASK = (
    "Acesse o site https://www.totvs.com e elabore um resumo da página principal e, "
    "em seguida, descreva-a de forma detalhada. Depois, monte um script de testes "
    "em JavaScript para essa página e me retorne o código pronto para execução."
)
PAYLOAD = {
    "task": TASK,
    "allowed_domains": ["totvs.com"],
    "llm_model": "gemini-flash-latest"
}

# 🧠 4. Função para extrair o output independentemente do campo usado
def extract_output(info: dict) -> str | None:
    return (
        info.get("output")
        or info.get("result")
        or info.get("final_response")
        or info.get("text")
        or info.get("content")
    )

# 🚀 5. Função principal assíncrona
async def main():
    headers = {
        "Authorization": f"Bearer {KEY}",
        "Content-Type": "application/json"
    }

    async with aiohttp.ClientSession() as session:
        # 🔄 Envia a tarefa (POST)
        print("➡️ Enviando tarefa...")
        async with session.post(f"{API}/run-task", json=PAYLOAD, headers=headers) as resp:
            if resp.status != 200:
                raise SystemExit(f"Erro ao criar tarefa: {resp.status} {await resp.text()}")
            job = await resp.json()

        task_id = job.get("id")
        if not task_id:
            raise SystemExit(f"Resposta inesperada ao criar tarefa: {job}")

        print(f"✅ Tarefa criada: {task_id}")
        print("⏳ Aguardando conclusão (tempo máx. 180s)...")

        TERMINAIS = {"completed", "finished", "failed", "canceled"}
        start = time.time()
        seen_live = False

        # 🔁 Verifica o status até terminar ou até o timeout
        while True:
            async with session.get(f"{API}/task/{task_id}", headers=headers) as resp:
                if resp.status != 200:
                    raise SystemExit(f"Erro ao obter status: {resp.status} {await resp.text()}")
                info = await resp.json()

            status = (info.get("status") or "").lower()
            live_url = info.get("live_url")

            if live_url and not seen_live:
                print(f"🔴 Live view: {live_url}")
                seen_live = True

            elapsed = int(time.time() - start)
            print(f"  • status={status} (t+{elapsed}s)")

            # ✅ Tarefa finalizada
            if status in TERMINAIS:
                print("—" * 60)
                if status in {"completed", "finished"}:
                    out = extract_output(info)
                    if out:
                        print("🎉 Concluído!\n")
                        print(out)
                    else:
                        print("⚠️ Concluído, mas sem 'output' padronizado. Resposta completa:")
                        print(json.dumps(info, ensure_ascii=False, indent=2))
                else:
                    print(f"❌ Finalizado com status: {status}")
                    err = info.get("error")
                    if err:
                        print(f"Erro: {err}")
                    else:
                        print(json.dumps(info, ensure_ascii=False, indent=2))
                break

            # ⏱️ Timeout de 180s
            if elapsed >= 180:
                print("⌛ Timeout (180s). Abra o live_url acima para acompanhar.")
                break

            await asyncio.sleep(2)

# ▶️ 6. Executa o programa
if __name__ == "__main__":
    asyncio.run(main())
