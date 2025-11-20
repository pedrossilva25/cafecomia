from dotenv import load_dotenv
import os, json, time, urllib.request, urllib.error

load_dotenv()

API = "https://api.browser-use.com/api/v1"
KEY = os.getenv("BROWSER_USE_API_KEY") or os.getenv("BROWSER_USE_CLOUD_API_KEY")
if not KEY:
    raise SystemExit("Faltou a API key no .env (BROWSER_USE_API_KEY=bu_...).")

TASK = "Acesse a url http://localhost/#/usuario/login?refresh=1 realize o login inserindo no campo login o email pedro.ssilva@linx.com.br e no campo senha insira a senha Hs015985 após autenticar direcione para rota http://localhost/#/relatorio_estoque_critico e ao abrir atela clique no botão consultar e realize testes em todos os botões para validar se todos estão funcionando corretamente.Em seguida, validese os resultados apresentados na tela, certificando-se de que os dados exibidos estão corretos e consistentes com as expectativas. Após concluir os testes, gere um relatório detalhado destacando quaisquer problemas encontrados. Em seguida criei todos os casos de testes realizados na pagina e me retorne escrito em portugues Brasil."
PAYLOAD = {
    "task": TASK,
    "allowed_domains": ["localhost"],
    "llm_model": "gemini-flash-latest"
}

def http_post(url, data):
    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode("utf-8"),
        headers={"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))

def http_get(url):
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {KEY}"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))

def extract_output(info: dict) -> str | None:
    # Cloud pode devolver o texto com chaves diferentes
    return (
        info.get("output")
        or info.get("result")
        or info.get("final_response")
        or info.get("text")
        or info.get("content")
    )

def main():
    try:
        print("➡️  Enviando tarefa...")
        job = http_post(f"{API}/run-task", PAYLOAD)
        task_id = job.get("id")
        if not task_id:
            raise SystemExit(f"Resposta inesperada ao criar tarefa: {job}")

        print(f"✅ Tarefa criada: {task_id}")
        print("⏳ Aguardando conclusão (tempo máx. 180s)...")

        TERMINAIS = {"completed", "finished", "failed", "canceled"}
        seen_live = False
        start = time.time()

        while True:
            info = http_get(f"{API}/task/{task_id}")
            status = (info.get("status") or "").lower()
            live_url = info.get("live_url")

            if live_url and not seen_live:
                print(f"🔴 Live view: {live_url}")
                seen_live = True

            elapsed = int(time.time() - start)
            print(f"  • status={status} (t+{elapsed}s)")

            if status in TERMINAIS:
                print("—" * 60)
                if status in {"completed", "finished"}:
                    out = extract_output(info)
                    if out:
                        print("🎉 Concluído!\n")
                        print(out)
                    else:
                        print("⚠️ Concluído, mas sem 'output' padronizado. Payload completo abaixo:")
                        print(json.dumps(info, ensure_ascii=False, indent=2))
                else:
                    print(f"❌ Finalizado com status: {status}")
                    err = info.get("error")
                    if err:
                        print(f"Erro: {err}")
                    else:
                        print(json.dumps(info, ensure_ascii=False, indent=2))
                break

            if elapsed >= 180:
                print("⌛ Timeout (180s). Abra o live_url acima para ver o progresso.")
                break

            time.sleep(2)

    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="ignore")
        print(f"HTTP {e.code} {e.reason}:\n{body}")
    except KeyboardInterrupt:
        print("\n(Interrompido pelo usuário enquanto aguardava a tarefa.)")

if __name__ == "__main__":
    main()
 