import glob, csv, json, os
from datetime import datetime

# Mapeamento de nichos e palavras-chave (ajusta se quiser)
NICHES = {
  "clinics": ["clinic","clinic.","medical","dentist","odontologia","clínica","consultorio","consultório"],
  "ecom": ["shop","store","cart","checkout","loja","ecommerce","e-commerce","produto","product"],
  "services": ["agency","marketing","design","consulting","developer","dev","agência","serviços","service"]
}

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
            rows.append(r)
    return rows

def detect_niche(domain, title=""):
    text = (domain + " " + (title or "")).lower()
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
    for r in rows:
        domain = r.get("domain") or r.get("Domain") or (r and list(r.values())[0])
        domain = (domain or "").strip()
        if not domain:
            continue
        title = ""
        niche = detect_niche(domain, title)
        score = 1
        item = {"domain": domain, "title": title, "niche": niche, "score": score}
        items.append(item)
        per_niche.setdefault(niche, []).append(item)

    feed = {"updated": datetime.utcnow().isoformat()+"Z", "count": len(items), "items": items}
    with open("feed.json", "w", encoding="utf-8") as f:
        json.dump(feed, f, ensure_ascii=False, indent=2)
    print(f"[OK] feed.json criado — {len(items)} itens (fonte: {csvfile})")

    # grava CSVs por nicho
    for niche, list_items in per_niche.items():
        fname = f"fresh_{niche}.csv"
        with open(fname, "w", newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["domain","title","score"])
            for it in list_items:
                writer.writerow([it["domain"], it["title"], it["score"]])
        print(f"[OK] {len(list_items)} itens -> {fname}")

if __name__ == "__main__":
    main()
