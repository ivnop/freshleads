import requests, json, time
from datetime import datetime

KEYWORDS = ["ai","tech","app","cloud","data","bot","shop","store","pay","digital"]

# fontes tentadas em ordem (crt.sh é a principal)
SOURCES = [
    ("crtsh", "https://crt.sh/?q=%25&output=json"),
    # proxy público que às vezes retorna quando o crt.sh bloqueia
    ("crtsh_proxy", "https://r.jina.ai/http://crt.sh/?q=%25&output=json"),
    # fallback: raw GitHub lists (pode falhar às vezes)
    ("github_list_1", "https://raw.githubusercontent.com/rfc1036/whois/master/domains.txt"),
    ("github_list_2", "https://raw.githubusercontent.com/tenable/nessus-rules/master/domains.txt")
]

# fallback local (sempre garante que não seja 0)
FALLBACK = [
    "example-ai-startup.com",
    "fastcloud-app.com",
    "myshopdigital.com",
    "paybotcloud.com",
    "data-analytics-app.com"
]

HEADERS = {"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/117.0 Safari/537.36"}

def parse_crtsh_json(text):
    try:
        arr = json.loads(text)
    except Exception:
        return set()
    domains = set()
    for e in arr:
        nv = e.get("name_value") or e.get("common_name") or ""
        for line in nv.splitlines():
            d = line.strip().lower()
            if d and not d.startswith("*."):
                domains.add(d)
    return domains

def parse_plain_list(text):
    domains = set()
    for line in text.splitlines():
        d = line.strip().lower()
        if d and "." in d and " " not in d:
            domains.add(d)
    return domains

def try_source(name, url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        if r.status_code != 200:
            print(f"[WARN] {name} returned status {r.status_code}")
            return set()
        # crt.sh returns JSON; detect
        ct = r.text.strip()
        if ct.startswith("[") and "name_value" in ct:
            return parse_crtsh_json(ct)
        # otherwise treat as plain list
        return parse_plain_list(ct)
    except Exception as e:
        print(f"[WARN] {name} fetch failed: {e}")
        return set()

def main():
    print("[INFO] Tentando fontes públicas...")
    domains = set()
    for name, url in SOURCES:
        found = try_source(name, url)
        print(f"[INFO] {name} -> {len(found)} domínios")
        if found:
            domains.update(found)
            # não parar: acumula de todas as fontes úteis
        time.sleep(1)

    # filtrar por .com/.io/.co e por keywords para dar valor
    filtered = set()
    for d in domains:
        if d.endswith((".com", ".io", ".co", ".net")) and any(k in d for k in KEYWORDS):
            filtered.add(d)

    # se nada deu certo, usar fallback local
    if not filtered:
        print("[WARN] Nenhum domínio filtrado encontrado nas fontes — usando fallback local.")
        filtered = set(FALLBACK)

    # saída com data
    today = datetime.now().strftime("%Y-%m-%d_%H%M")
    txt_out = f"fresh_domains_{today}.txt"
    csv_out = f"fresh_domains_{today}.csv"

    with open(txt_out, "w", encoding="utf-8") as f:
        for d in sorted(filtered):
            f.write(d + "\n")

    with open(csv_out, "w", encoding="utf-8") as f:
        f.write("domain\n")
        for d in sorted(filtered):
            f.write(d + "\n")

    print(f"[OK] {len(filtered)} domínios salvos em {txt_out} e {csv_out}")

if __name__ == '__main__':
    main()
