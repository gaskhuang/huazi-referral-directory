(function () {
  "use strict";

  var MEMBERS = window.HUAZI_MEMBERS || [];
  var META = window.HUAZI_META || {};

  var elRows = document.getElementById("rows");
  var elChips = document.getElementById("chips");
  var elQ = document.getElementById("q");
  var elEmpty = document.getElementById("empty");
  var elCount = document.getElementById("resultCount");

  var state = { q: "", group: "全部", open: null };

  var MAX_NEEDS = 3;
  var PILL_MAX = 22;

  function esc(s) {
    return String(s == null ? "" : s)
      .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function key(m) { return m.no + "-" + m.name + "-" + m.group; }

  function haystack(m) {
    return [m.no, m.name, m.nickname, m.trade, (m.tags || []).join(" "),
            m.company, m.group, m.basic, m.ideal, m.dream,
            (m.have || []).join(" "), (m.want || []).join(" "),
            (m.expertise || []).join(" ")].join(" ").toLowerCase();
  }

  MEMBERS.forEach(function (m) { m._hay = haystack(m); });

  /* ---------- 「正在找誰」：want → dream → ideal → basic ---------- */

  function splitToItems(text) {
    if (!text) return [];
    var parts = String(text).split("\n").map(function (s) { return s.trim(); })
      .filter(Boolean);
    if (parts.length === 1 && /[、，]/.test(parts[0])) {
      parts = parts[0].split(/[、，]/).map(function (s) { return s.trim(); })
        .filter(Boolean);
    }
    return parts;
  }

  function needsOf(m) {
    if (m.want && m.want.length) return m.want.slice();
    var d = splitToItems(m.dream);
    if (d.length) return d;
    var i = splitToItems(m.ideal);
    if (i.length) return i;
    return splitToItems(m.basic);
  }

  function needsHtml(m) {
    var items = needsOf(m);
    if (!items.length) {
      return '<span class="need-empty">尚未填寫引薦需求</span>';
    }
    var shown = items.slice(0, MAX_NEEDS);
    var html = '<span class="need-label">正在找</span><div class="needs">';
    shown.forEach(function (t) {
      var label = t.length > PILL_MAX ? t.slice(0, PILL_MAX) + "…" : t;
      html += '<span class="need" title="' + esc(t) + '">' + esc(label) + "</span>";
    });
    if (items.length > shown.length) {
      html += '<span class="need-more">+' + (items.length - shown.length) + "</span>";
    }
    return html + "</div>";
  }

  /* ---------- header 資訊 ---------- */

  var src = document.getElementById("sourceLink");
  if (src && META.deckUrl) src.href = META.deckUrl;

  document.getElementById("statTotal").textContent = META.total || MEMBERS.length;
  document.getElementById("statComplete").textContent = META.complete || 0;
  document.getElementById("statGroups").textContent =
    (META.groupOrder || []).filter(function (g) { return g !== "籌備／幹部"; }).length;
  document.getElementById("footMeta").textContent =
    "資料同步自 2026 年華資 45 秒會員簡報 · 最後更新 " + (META.updated || "");

  /* ---------- 小組 chips ---------- */

  function chipHtml(label, n) {
    return '<button class="chip' + (state.group === label ? " is-active" : "") +
      '" data-group="' + esc(label) + '">' + esc(label) +
      '<span class="count">' + n + "</span></button>";
  }

  function buildChips() {
    var counts = {};
    MEMBERS.forEach(function (m) { counts[m.group] = (counts[m.group] || 0) + 1; });
    var order = META.groupOrder || Object.keys(counts);
    var html = chipHtml("全部", MEMBERS.length);
    order.forEach(function (g) {
      if (counts[g]) html += chipHtml(g, counts[g]);
    });
    elChips.innerHTML = html;
  }

  /* ---------- 展開面板 ---------- */

  var ICON_SPARK = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M11 2.8a1 1 0 0 1 2 0l1 5.6a2 2 0 0 0 1.6 1.6l5.6 1a1 1 0 0 1 0 2l-5.6 1a2 2 0 0 0-1.6 1.6l-1 5.6a1 1 0 0 1-2 0l-1-5.6a2 2 0 0 0-1.6-1.6l-5.6-1a1 1 0 0 1 0-2l5.6-1a2 2 0 0 0 1.6-1.6z"></path></svg>';
  var ICON_USER = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m16 11 2 2 4-4"></path><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"></path><circle cx="9" cy="7" r="4"></circle></svg>';
  var ICON_TARGET = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"></circle><circle cx="12" cy="12" r="5"></circle><circle cx="12" cy="12" r="1.4"></circle></svg>';
  var ICON_BOX = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 8v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8"></path><rect x="2" y="3" width="20" height="5" rx="1"></rect><path d="M10 12h4"></path></svg>';
  var ICON_CHEV = '<svg class="chev" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m6 9 6 6 6-6"></path></svg>';

  var TIERS = [
    { cls: "basic", field: "basic", label: "一般引薦", hint: "適合日常案件與上下游合作" },
    { cls: "ideal", field: "ideal", label: "理想引薦", hint: "適合長期合作或 Power Team" },
    { cls: "dream", field: "dream", label: "夢幻引薦", hint: "最希望被介紹到的關鍵對象" }
  ];

  function tierHtml(m, t) {
    var text = m[t.field];
    var body = text
      ? '<p class="tier-body">' + esc(text) + "</p>"
      : '<p class="tier-body is-empty">簡報中尚未填寫</p>';
    return '<div class="tier ' + t.cls + '">' +
      '<span class="tier-label">' + t.label + "</span>" +
      '<span class="tier-hint">' + t.hint + "</span>" + body + "</div>";
  }

  function bulletBox(items, emptyText) {
    if (!items || !items.length) {
      return '<div class="bullet-box is-empty"><p>' + emptyText + "</p></div>";
    }
    return '<div class="bullet-box">' +
      items.map(function (t) { return "<p>" + esc(t) + "</p>"; }).join("") + "</div>";
  }

  function wantBox(m) {
    var body;
    if (m.want && m.want.length) {
      body = '<div class="want-pills">' + m.want.map(function (t) {
        return '<span class="want-pill">' + esc(t) + "</span>";
      }).join("") + "</div>";
    } else {
      body = '<p class="want-empty">本週未填寫。</p>';
    }
    return '<div class="want-box"><div class="panel-title">' + ICON_TARGET +
      " 本週最希望你幫忙找</div>" + body + "</div>";
  }

  function detailHtml(m) {
    return '<tr class="row-detail"><td colspan="6"><div class="detail-inner">' +
      '<div class="detail-grid">' +
        "<div>" +
          '<div class="panel-title">' + ICON_SPARK + " 他希望你幫忙引薦這些人</div>" +
          '<div class="tiers">' + TIERS.map(function (t) { return tierHtml(m, t); }).join("") + "</div>" +
        "</div>" +
        '<div class="side"><div>' +
          '<div class="panel-title muted">' + ICON_USER + " 我的專業</div>" +
          bulletBox(m.expertise, "簡報中尚未填寫專業簡介。") +
        "</div></div>" +
      "</div>" +
      '<div class="exchange">' + wantBox(m) +
        '<div class="have-box"><div class="panel-title muted">' + ICON_BOX +
          " 本週我有（可以給出去的資源）</div>" +
          bulletBox(m.have, "本週未填寫。") + "</div>" +
      "</div>" +
      '<div class="detail-foot"><a class="slide-link" href="' + esc(m.slideUrl) +
        '" target="_blank" rel="noopener">開啟原始簡報 →</a></div>' +
      "</div></td></tr>";
  }

  /* ---------- 主列表 ---------- */

  function bizHtml(m) {
    var html = "";
    if (m.trade) {
      html += '<span class="trade">' + esc(m.trade) + "</span>";
    } else if (m.tags && m.tags.length) {
      html += '<span class="trade">' + esc(m.tags[0]) + "</span>";
    } else {
      html += '<span class="need-empty">未填寫專業別</span>';
    }
    if (m.tags && m.tags.length) {
      var extra = m.trade ? m.tags : m.tags.slice(1);
      if (extra.length) {
        html += '<div class="tags">' + extra.slice(0, 3).map(function (t) {
          return '<span class="tag">#' + esc(t) + "</span>";
        }).join("") + "</div>";
      }
    }
    if (m.company) {
      html += '<div class="company">' + esc(m.company).replace(/\n/g, " · ") + "</div>";
    }
    return html;
  }

  function rowHtml(m) {
    var nick = m.nickname ? '<span class="nick">' + esc(m.nickname) + "</span>" : "";
    var no = m.no ? esc(m.no) : "—";
    return '<tr class="row-main" data-key="' + esc(key(m)) + '">' +
      '<td class="cell-no">' + no + "</td>" +
      '<td class="cell-name">' + esc(m.name) + nick + "</td>" +
      '<td class="cell-biz">' + bizHtml(m) + "</td>" +
      '<td class="cell-need">' + needsHtml(m) + "</td>" +
      '<td class="cell-cat">' + esc(m.group) + "</td>" +
      '<td class="cell-chev">' + ICON_CHEV + "</td>" +
      "</tr>";
  }

  function filtered() {
    var q = state.q.trim().toLowerCase();
    return MEMBERS.filter(function (m) {
      if (state.group !== "全部" && m.group !== state.group) return false;
      if (!q) return true;
      return m._hay.indexOf(q) !== -1;
    });
  }

  function render() {
    var list = filtered();
    state.open = null;
    elRows.innerHTML = list.map(rowHtml).join("");
    elEmpty.hidden = list.length > 0;
    elCount.textContent = "顯示 " + list.length + " / " + MEMBERS.length + " 位夥伴";
    Array.prototype.forEach.call(elChips.children, function (btn) {
      btn.classList.toggle("is-active", btn.dataset.group === state.group);
    });
  }

  function collapse() {
    var open = elRows.querySelector(".row-main.is-open");
    if (open) open.classList.remove("is-open");
    var detail = elRows.querySelector(".row-detail");
    if (detail) detail.remove();
    state.open = null;
  }

  function expand(row) {
    var m = MEMBERS.filter(function (x) { return key(x) === row.dataset.key; })[0];
    if (!m) return;
    row.classList.add("is-open");
    row.insertAdjacentHTML("afterend", detailHtml(m));
    state.open = row.dataset.key;
  }

  /* ---------- 五大小組 ---------- */

  function buildTeams() {
    var grid = document.getElementById("teamGrid");
    if (!grid) return;
    var groups = META.groups || {};
    var counts = {};
    MEMBERS.forEach(function (m) { counts[m.group] = (counts[m.group] || 0) + 1; });

    var html = (META.groupOrder || []).filter(function (g) {
      return g !== "籌備／幹部";
    }).map(function (g) {
      var info = groups[g] || {};
      var s = '<div class="team-card"><div class="team-head">' +
        '<h3>' + esc(g) + "</h3>" +
        '<span class="team-count">' + (counts[g] || 0) + " 位</span></div>";
      if (info.tagline) s += '<p class="team-tagline">' + esc(info.tagline) + "</p>";
      s += listBlock("目標客戶", info.audience);
      s += listBlock("想補強的專業別", info.wanted);
      return s + "</div>";
    }).join("");
    grid.innerHTML = html;
  }

  function listBlock(title, items) {
    if (!items || !items.length) {
      return '<div class="team-block"><span class="team-block-title">' + title +
        '</span><p class="team-empty">簡報中沒有這一頁。</p></div>';
    }
    return '<div class="team-block"><span class="team-block-title">' + title +
      '</span><div class="team-pills">' + items.map(function (t) {
        return '<span class="team-pill">' + esc(t) + "</span>";
      }).join("") + "</div></div>";
  }

  /* ---------- 事件 ---------- */

  elChips.addEventListener("click", function (e) {
    var btn = e.target.closest(".chip");
    if (!btn) return;
    state.group = btn.dataset.group;
    render();
  });

  elRows.addEventListener("click", function (e) {
    if (e.target.closest("a")) return;
    var row = e.target.closest(".row-main");
    if (!row) return;
    var wasOpen = row.classList.contains("is-open");
    collapse();
    if (!wasOpen) expand(row);
  });

  var t;
  elQ.addEventListener("input", function () {
    clearTimeout(t);
    t = setTimeout(function () {
      state.q = elQ.value;
      render();
    }, 120);
  });

  buildChips();
  render();
  buildTeams();
})();
