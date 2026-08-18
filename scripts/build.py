#!/usr/bin/env python3
"""把 members.json / intros.json 打包成網站用的 docs/data/members.js"""
import json, re, os, datetime

GROUP_ORDER = ["籌備／幹部", "企業行銷組", "AI&軟體組", "工廠數位轉型組", "企業工商組", "工程組"]

DECK_URL = ("https://docs.google.com/presentation/d/"
            "1j9lY9x0Iswm-aR6bdR7NBVLIFX7g100DEz7DNt4hXnw/edit")

NOISE = re.compile(r"^\s*(?:\d{1,2}|[0-9]{2})\s*$")
TITLEISH = re.compile(r"^(目標客戶|各小組簡介|目標增加專業別|優先補強的專業別|"
                      r"強力呼喊補強專業別|我們要聚焦服務的客戶群有誰|共同痛點|"
                      r"本組特色|目前已有專業別|優先招募|加分擴充|Team Members|"
                      r"Target Audience|Wanted Roles)")


def clean_items(texts, drop=()):
    """濾掉純編號、標題與過短的碎片"""
    out = []
    for t in texts:
        t = " ".join(t.split())
        if not t or NOISE.match(t) or len(t) < 3:
            continue
        if t in drop or any(t == d for d in drop):
            continue
        if re.fullmatch(r"[A-Z ]{4,}", t):      # TEAM OVERVIEW 這類英文小標
            continue
        if TITLEISH.search(t):                  # 「目標客戶 TA 樣貌」這種頁面標題
            continue
        out.append(t)
    return out


def kind_of(texts):
    """標題可能分散在前幾個文字框（中英各一），一起看才判得準"""
    head = " ".join(texts[:3])
    if re.search(r"補強|Wanted|增加專業|呼喊", head, re.I):
        return "wanted"
    if re.search(r"目標客戶|客戶群|TA 樣貌|ICP|Audience|WHO WE SERVE", head, re.I):
        return "audience"
    return "team"


def build_groups(intros):
    groups = {}
    for g, slides in intros.items():
        info = groups.setdefault(g, {"audience": [], "wanted": [], "tagline": ""})
        for s in slides:
            texts = s["texts"]
            title = " ".join(texts[0].split()) if texts else ""
            k = kind_of(texts)
            items = clean_items(texts[1:], drop=(title,))
            if k == "team":
                # 只收敘述句，別把「洪子翔(Benny) 民事律師服務」這種名單列當成簡介
                cand = [t for t in items
                        if len(t) >= 24 and not re.match(r"^[一-鿿]{2,4}\s*[(（]", t)]
                longest = max(cand, key=len) if cand else ""
                if len(longest) > len(info["tagline"]):
                    info["tagline"] = longest
            else:
                info[k].extend(items)
    for g in groups:
        for k in ("audience", "wanted"):
            seen, uniq = set(), []
            for t in groups[g][k]:
                if t not in seen:
                    seen.add(t)
                    uniq.append(t)
            groups[g][k] = uniq[:14]
    return groups


def main():
    members = json.load(open("data/members.json", encoding="utf-8"))
    intros = json.load(open("data/intros.json", encoding="utf-8"))

    out = []
    for m in members:
        t = m["tiers"]
        out.append({
            "no": m["no"],
            "name": m["name"],
            "nickname": m["nickname"],
            "trade": m["trade"],
            "tags": m["tags"],
            "company": m["company"],
            "group": m["group"],
            "basic": t["basic"],
            "ideal": t["ideal"],
            "dream": t["dream"],
            "have": m["have"],
            "want": m["want"],
            "expertise": m["expertise"],
            "slideUrl": f"{DECK_URL}#slide=id.p{m['slide']}",
            "complete": bool(t["basic"] or t["ideal"] or t["dream"]),
        })

    order = {g: i for i, g in enumerate(GROUP_ORDER)}
    out.sort(key=lambda m: (order.get(m["group"], 99), m["no"] or "zzz", m["name"]))

    groups = build_groups(intros)
    present = [g for g in GROUP_ORDER if any(m["group"] == g for m in out)]

    meta = {
        "updated": datetime.date.today().isoformat(),
        "total": len(out),
        "complete": sum(1 for m in out if m["complete"]),
        "groupOrder": present,
        "groups": groups,
        "deckUrl": DECK_URL,
    }

    os.makedirs("docs/data", exist_ok=True)
    with open("docs/data/members.js", "w", encoding="utf-8") as f:
        f.write("window.HUAZI_META = ")
        json.dump(meta, f, ensure_ascii=False, indent=1)
        f.write(";\nwindow.HUAZI_MEMBERS = ")
        json.dump(out, f, ensure_ascii=False, indent=1)
        f.write(";\n")

    print(f"built docs/data/members.js — {len(out)} 位成員")
    for g in present:
        n = sum(1 for m in out if m["group"] == g)
        gi = groups.get(g, {})
        print(f"  {g}: {n} 位 | 目標客戶 {len(gi.get('audience', []))} 項"
              f" | 補強專業別 {len(gi.get('wanted', []))} 項")


if __name__ == "__main__":
    main()
