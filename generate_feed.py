# generate_feed.py  (substitui o existente)
import glob, csv, json, os, re
from datetime import datetime

# --- CONFIGURAÇÃO: ajusta se quiser ---
NICHES = {
  "clinics": ["clinic","medical","dentist","odontologia","clínica","consultorio","consultório"],
  "ecom": ["shop","store","cart","checkout","loja","ecommerce","e-commerce","produto","product"],
  "services": ["agency","marketing","design","consulting","developer","dev","agência","serviços","service"]
}

MONEY_KEYWORDS = ["ai","pay","paym","wallet","wallets","shop","store","app","cloud","data","crm","saas","serve","tech","digital","booking","order","pay","checkout","crypto","token","market"]

PROHIBITED = ["free","cheap","discount","sale","best","202", "2026","download","torrent","crack","hack","login","signup","reset","test","sample"]

SCORE_THRESHOLD = 80  # score mínimo para ser premium (você escolheu 'RARO')

# --------------------------

def find_latest_csv():
    files = sorted(glob.glob("fresh_domains_*.csv"))
    if not files:
        return None
    return files[-1]

def read_domains(csvfile):
    rows = []
    with open(csvfile, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for r in reader:
            # try different possible header names
            if "domain" in r:
                domain = r.get("domain")
            else:
                # pick first non-empty value
                vals = [v for v in r.values() if v]
                domain = vals[0] if vals else ""
            domain = (domain or "").strip().lower()
            if domain:
                rows.append({"domain": domain})
    return rows

def score_domain(domain):
    # base structure
    name = domain.split("//")[-1].split("/")[0]
    name = name.replace("www.", "")
    # strip tld for length calculation
    parts = name.split(".")
    label = parts[0] if parts else name

    score = 0

    # EXTENSION score
    if name.endswith(".com"):
        score += 40
    elif any(name.endswith(ext) for ext in [".io", ".ai", ".app"]):
        score += 30
    elif name.endswith(".co") or name.endswith(".net"):
        score += 15

    # KEYWORD money score
    for kw in MONEY_KEYWORDS:
        if kw in name:
            score += 15
            break

    # LENGTH (short is better)
    ln = len(label)
    if ln <= 6:
        score += 20
    elif ln <= 10:
        score += 10
    elif ln <= 15:
        score += 5
    else:
        score -= 5

    # penalties
    if "-" in label:
        score -= 15
    if re.search(r"\d", label):
        score -= 12

    # prohibited words heavy penalty
    for p in PROHIBITED:
        if p in name:
            score -= 30
            break

    # cap and normalize
    if score < 0: score = 0
    if score > 100: score = 100

    return int(score)

def detect_niche(domain):
    text = domain.lower()
    for niche, kws in NICHES.items():
        for kw in kws:
            if kw in text:
                return niche
    return "other"

def main():
    csvfile = find_latest_csv()
    if not csvfile:
        print("[ERR] Nenhum CSV encontrado: gere fresh_domains_YYYY-MM-DD_HHMM.csv primeiro.")
        return

    rows = read_domains(csvfile)
    items = []
    per_niche = {}
    premium_items = []
    premium_per_niche = {}

    for r in rows:
        domain = r["domain"]
        score = score_domain(domain)
        niche = detect_niche(domain)
        item = {"domain": domain, "niche": niche, "score": score}
        items.append(item)
        per_niche.setdefault(niche, []).append(item)
        if score >= SCORE_THRESHOLD:
            premium_items.append(item)
            premium_per_niche.setdefault(niche, []).append(item)

    # public feed (all)
    feed_public = {"updated": datetime.utcnow().isoformat()+"Z", "count": len(items), "items": items}
    with open("feed.json", "w", encoding="utf-8") as f:
        json.dump(feed_public, f, ensure_ascii=False, indent=2)
    print(f"[OK] feed.json criado — {len(items)} itens (fonte: {csvfile})")

    # premium feed (only high score)
    feed_premium = {"updated": datetime.utcnow().isoformat()+"Z", "count": len(premium_items), "items": premium_items}
    with open("premium_feed.json", "w", encoding="utf-8") as f:
        json.dump(feed_premium, f, ensure_ascii=False, indent=2)
    print(f"[OK] premium_feed.json criado — {len(premium_items)} itens (score>={SCORE_THRESHOLD})")

    # grava CSVs por nicho pública e premium por nicho
    for niche, list_items in per_niche.items():
        fname = f"fresh_{niche}.csv"
        with open(fname, "w", newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["domain","score"])
            for it in list_items:
                writer.writerow([it["domain"], it["score"]])
        print(f"[OK] {len(list_items)} itens -> {fname}")

    for niche, list_items in premium_per_niche.items():
        fname = f"premium_{niche}.csv"
        with open(fname, "w", newline='', encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["domain","score"])
            for it in list_items:
                writer.writerow([it["domain"], it["score"]])
        print(f"[OK] {len(list_items)} itens -> {fname}")

    # summary
    print(f"[SUMMARY] total={len(items)} premium={len(premium_items)}")

if __name__ == "__main__":
    main()
