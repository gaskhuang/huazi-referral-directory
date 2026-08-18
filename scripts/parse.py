#!/usr/bin/env python3
"""把華資 45 秒簡報（pptx）解析成 members.json / groups.json"""
import json, re, os

SRC = "data/slides.json"

LABELS = {"我的專業", "三層引薦", "本週引薦需求", "引薦需求", "本週我有", "本週我要",
          "本周我有", "本周我要", "我有", "我要", "本週我有資源"}

# 版面切分（EMU，投影片寬 12179300）
X_MID = 4_100_000      # 三層引薦欄的右界
X_WANT = 7_900_000     # 本週我要欄的左界
Y_HEAD = 1_800_000     # 姓名／公司區的下界
Y_BOTTOM = 4_300_000   # 下半部（三層引薦／我有我要）的上界


def clean(s):
    s = s.replace("\x0b", "\n").replace("\r", "\n")
    s = re.sub(r"[ \t　]+", " ", s)
    s = "\n".join(l.strip() for l in s.split("\n"))
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s.strip()


def is_label(t):
    s = t.replace("：", "").replace(":", "").strip()
    return (not s) or s in {l.replace("：", "") for l in LABELS}


def strip_label(t):
    return re.sub(r"^\s*(本[週周])?(我有|我要)(資源)?\s*[：:]?\s*", "", t).strip()


NAME_RE = re.compile(r"^\s*(?:no\.?\s*)?(\d{1,3})?\s*([一-鿿]{2,4})(?![一-鿿])(.*)$", re.S | re.I)
HASH_RE = re.compile(r"[#＃]\s*([^#＃\n]+)")


def parse_member(boxes, group):
    used = set()
    r = {"group": group}

    # --- 姓名列：頭部區、含中文姓名，優先取有編號的 ---
    cands = []
    for b in boxes:
        if b["y"] > Y_HEAD or is_label(b["t"]):
            continue
        first = clean(b["t"]).split("\n")[0]
        m = NAME_RE.match(first)
        if m and m.group(2):
            cands.append((0 if m.group(1) else 1, -b["y"], b, m))
    cands.sort(key=lambda c: (c[0], c[1]))

    name_box = None
    if cands:
        _, _, name_box, m = cands[0]
        used.add(id(name_box))
        r["no"] = m.group(1).zfill(3) if m.group(1) else ""
        r["name"] = m.group(2)
        rest = clean(m.group(3) + "\n" + "\n".join(clean(name_box["t"]).split("\n")[1:]))
    else:
        r["no"], r["name"], rest = "", "", ""

    # 暱稱：姓名後的括號或拉丁字
    nick = ""
    mp = re.match(r"^\s*[（(]([^）)]*)[）)]\s*(.*)$", rest, re.S)
    if mp:
        nick, rest = mp.group(1), mp.group(2)
    else:
        mt = re.match(r"^\s*([A-Za-z][A-Za-z0-9.\-']*(?:\s+[A-Za-z][A-Za-z0-9.\-']*)?)\s*(.*)$", rest, re.S)
        if mt:
            nick, rest = mt.group(1), mt.group(2)
    r["nickname"] = nick.strip()

    # --- 公司／職稱：姓名列上方最近的一框 ---
    ny = name_box["y"] if name_box else 1_000_000
    comp = [b for b in boxes if id(b) not in used and not is_label(b["t"])
            and b["y"] < ny + 40_000 and b["y"] > 300_000]
    comp.sort(key=lambda b: -b["y"])
    r["company"] = clean(comp[0]["t"]) if comp else ""
    if comp:
        used.add(id(comp[0]))

    # --- 三層引薦 ---
    tier = None
    for b in boxes:
        if id(b) in used:
            continue
        if re.search(r"(一般引薦|基本引薦|一般\s*[：:])", b["t"]):
            tier = b
            break
    if tier is None:
        c = [b for b in boxes if id(b) not in used and not is_label(b["t"])
             and b["y"] > Y_BOTTOM and b["x"] < X_MID]
        tier = max(c, key=lambda b: len(b["t"])) if c else None
    if tier:
        used.add(id(tier))
    r["tier_raw"] = clean(tier["t"]) if tier else ""

    # --- 本週我有 / 本週我要 ---
    def grab(kw, xmin, xmax):
        hits = [b for b in boxes if id(b) not in used and re.search(kw, b["t"])]
        for b in sorted(hits, key=lambda b: -len(b["t"])):
            used.add(id(b))
            body = strip_label(clean(b["t"]))
            if body:
                return body
            below = [c for c in boxes if id(c) not in used and not is_label(c["t"])
                     and c["y"] > b["y"] and abs(c["x"] - b["x"]) < 900_000]
            if below:
                c = min(below, key=lambda c: c["y"])
                used.add(id(c))
                return clean(c["t"])
            return ""
        c = [b for b in boxes if id(b) not in used and not is_label(b["t"])
             and b["y"] > Y_BOTTOM and xmin <= b["x"] < xmax]
        if c:
            b = max(c, key=lambda b: len(b["t"]))
            used.add(id(b))
            return strip_label(clean(b["t"]))
        return ""

    r["have"] = grab(r"^\s*本?[週周]?\s*我有", X_MID, X_WANT)
    r["want"] = grab(r"^\s*本?[週周]?\s*我要", X_WANT, 99_000_000)

    # --- 我的專業：姓名列下方～下半部之上 ---
    exp = [b for b in boxes if id(b) not in used and not is_label(b["t"])
           and b["y"] > ny + 100_000 and b["y"] < Y_BOTTOM]
    exp.sort(key=lambda b: (b["y"], b["x"]))
    r["expertise_raw"] = "\n".join(clean(b["t"]) for b in exp)
    for b in exp:
        used.add(id(b))

    r["leftover"] = [clean(b["t"]) for b in boxes if id(b) not in used and not is_label(b["t"])]

    # --- hashtag 專業標籤（姓名列 + 專業區都可能有）---
    tag_src = rest + "\n" + r["expertise_raw"]
    r["tags"] = [clean(t) for t in HASH_RE.findall(tag_src) if 1 < len(clean(t)) <= 20][:6]
    r["trade"] = clean(re.sub(r"[#＃][^#＃\n]+", "", rest)).replace("\n", " ").strip(" /|、")
    return r


def split_tiers(raw):
    if not raw:
        return {"basic": "", "ideal": "", "dream": ""}

    def seg(a, b):
        ma = re.search(a, raw)
        if not ma:
            return ""
        start = ma.end()
        mb = re.search(b, raw[start:]) if b else None
        end = start + mb.start() if mb else len(raw)
        return clean(raw[start:end].lstrip("：: \n"))

    A = r"(?:一般引薦|基本引薦|一般)\s*[：:]?"
    B = r"(?:理想引薦|理想)\s*[：:]?"
    C = r"(?:夢幻引薦|夢幻)\s*[：:]?"
    return {"basic": seg(A, B), "ideal": seg(B, C), "dream": seg(C, None)}


def bullets(s):
    if not s:
        return []
    out = []
    for ln in s.split("\n"):
        ln = re.sub(r"^\s*(?:[●•‧・⬥◆▪\-—*]|\d+\s*[.、)）])\s*", "", ln).strip()
        ln = ln.strip("＊*　 ")
        if ln and ln not in {"：", ":"}:
            out.append(ln)
    return out


def main():
    slides = json.load(open(SRC, encoding="utf-8"))

    group = "籌備／幹部"
    members, groups, intros = [], [], {}

    for s in slides:
        boxes = s["boxes"]
        texts = [clean(b["t"]) for b in boxes]

        # 分組隔頁
        if len(boxes) == 1 and "華資" in texts[0] and "組" in texts[0]:
            group = re.sub(r"^華資\s*[【\[]?|[】\]]?$", "", texts[0]).strip()
            groups.append(group)
            continue

        # 純圖片頁
        if not boxes:
            continue

        # 成員頁一定有「三層引薦」這個標籤
        if not any(t.replace("：", "").strip() == "三層引薦" for t in texts):
            intros.setdefault(group, []).append({"slide": s["i"], "texts": texts})
            continue

        r = parse_member(boxes, group)
        exp = bullets(r["expertise_raw"])
        trade = r["trade"]
        tags = list(r["tags"])
        if not trade and exp and len(exp) > 1:
            head = exp[0]
            if HASH_RE.search(head):
                # 第一行是 hashtag 串，整串當標籤、不當專業別
                for t in HASH_RE.findall(head):
                    t = clean(t)
                    if 1 < len(t) <= 20 and t not in tags:
                        tags.append(t)
                exp = exp[1:]
            elif len(head) <= 20:
                trade, exp = head, exp[1:]
        members.append({
            "no": r["no"],
            "name": r["name"],
            "nickname": r["nickname"],
            "trade": trade,
            "tags": tags[:6],
            "company": r["company"],
            "group": r["group"],
            "tiers": split_tiers(r["tier_raw"]),
            "tier_raw": r["tier_raw"],
            "have": bullets(r["have"]),
            "want": bullets(r["want"]),
            "expertise": exp,
            "slide": s["i"],
            "leftover": r["leftover"],
        })

    seen, deduped = {}, []
    for m in members:
        sig = m["tier_raw"][:80]
        if not m["no"] and sig and sig in seen:
            continue
        if sig:
            seen[sig] = True
        deduped.append(m)
    dropped = len(members) - len(deduped)
    members = deduped

    os.makedirs("data", exist_ok=True)
    json.dump(members, open("data/members.json", "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    json.dump(intros, open("data/intros.json", "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)

    print(f"重覆頁略過 {dropped} 頁")
    print(f"成員 {len(members)} 位，小組 {len(groups)} 個：{groups}")
    print(f"小組介紹頁：{ {g: len(v) for g, v in intros.items()} }")
    for k, label in (("name", "姓名"), ("company", "公司"), ("trade", "專業別")):
        miss = [m["no"] + m["name"] for m in members if not m[k]]
        print(f"缺{label}：{len(miss)} {miss[:12]}")
    print("缺三層引薦：", [m["no"] + m["name"] for m in members if not m["tiers"]["basic"]])
    print("缺編號：", [m["name"] for m in members if not m["no"]])


if __name__ == "__main__":
    main()
