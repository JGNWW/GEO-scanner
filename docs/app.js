const CSV_URL = "data/results.csv";
const REPORTS_INDEX = "reports.json";

async function main() {
  const [csvText, reports] = await Promise.all([
    fetch(CSV_URL).then(r => r.ok ? r.text() : "").catch(() => ""),
    fetch(REPORTS_INDEX).then(r => r.ok ? r.json() : []).catch(() => []),
  ]);

  const rows = parseCSV(csvText);
  if (rows.length === 0) {
    document.getElementById("meta").textContent = "Nog geen scan-resultaten beschikbaar.";
    renderReports(reports);
    return;
  }

  const dates = [...new Set(rows.map(r => r.date))].sort();
  const latest = dates[dates.length - 1];
  const prev = dates.length > 1 ? dates[dates.length - 2] : null;
  document.getElementById("meta").textContent =
    `Laatste scan: ${latest} · ${dates.length} scan${dates.length === 1 ? "" : "s"} · ${rows.length} queries totaal`;

  const latestRows = rows.filter(r => r.date === latest);
  const prevRows = prev ? rows.filter(r => r.date === prev) : [];

  renderCards(latestRows, prevRows);
  renderTrend(rows, dates);
  renderShareOfVoice(latestRows);
  renderPromptTable(latestRows);
  renderReports(reports);
}

function parseCSV(text) {
  if (!text.trim()) return [];
  const lines = splitCSVLines(text);
  const header = parseCSVLine(lines[0]);
  return lines.slice(1).filter(l => l.trim()).map(line => {
    const cells = parseCSVLine(line);
    const obj = {};
    header.forEach((h, i) => obj[h] = cells[i] ?? "");
    obj.target_mentioned = obj.target_mentioned === "True";
    obj.target_cited = obj.target_cited === "True";
    try { obj.competitor_mentions = JSON.parse(obj.competitor_mentions || "{}"); }
    catch { obj.competitor_mentions = {}; }
    try { obj.competitor_citations = JSON.parse(obj.competitor_citations || "{}"); }
    catch { obj.competitor_citations = {}; }
    return obj;
  });
}

function splitCSVLines(text) {
  const lines = [];
  let cur = "";
  let inQ = false;
  for (const ch of text) {
    if (ch === '"') inQ = !inQ;
    if (ch === "\n" && !inQ) { lines.push(cur); cur = ""; continue; }
    cur += ch;
  }
  if (cur) lines.push(cur);
  return lines;
}

function parseCSVLine(line) {
  const out = [];
  let cur = "";
  let inQ = false;
  for (let i = 0; i < line.length; i++) {
    const ch = line[i];
    if (ch === '"') {
      if (inQ && line[i+1] === '"') { cur += '"'; i++; }
      else inQ = !inQ;
    } else if (ch === "," && !inQ) { out.push(cur); cur = ""; }
    else cur += ch;
  }
  out.push(cur.replace(/\r$/, ""));
  return out;
}

function pct(n, total) {
  if (total === 0) return "0%";
  return Math.round(100 * n / total) + "%";
}

function renderCards(latest, prev) {
  const total = latest.length;
  const mentioned = latest.filter(r => r.target_mentioned).length;
  const cited = latest.filter(r => r.target_cited).length;

  const compMentions = {};
  latest.forEach(r => {
    Object.entries(r.competitor_mentions).forEach(([k, v]) => {
      if (v) compMentions[k] = (compMentions[k] || 0) + 1;
    });
  });
  const topComp = Object.entries(compMentions).sort((a, b) => b[1] - a[1])[0];

  const prevMentioned = prev.length ? prev.filter(r => r.target_mentioned).length / prev.length : null;
  const prevCited = prev.length ? prev.filter(r => r.target_cited).length / prev.length : null;

  const cards = [
    card("Queries", total, ""),
    card("Genoemd", pct(mentioned, total), delta(mentioned / total, prevMentioned)),
    card("Geciteerd", pct(cited, total), delta(cited / total, prevCited)),
    card("Sterkste concurrent", topComp ? `${topComp[0]}` : "—", topComp ? `${pct(topComp[1], total)} mentions` : ""),
  ];
  document.getElementById("cards").innerHTML = cards.join("");
}

function card(label, value, deltaHtml) {
  return `<div class="card"><div class="label">${label}</div><div class="value">${value}</div><div class="delta">${deltaHtml}</div></div>`;
}

function delta(now, prev) {
  if (prev === null || prev === undefined) return "geen vorige scan";
  const diff = Math.round(100 * (now - prev));
  if (diff === 0) return "gelijk aan vorige scan";
  const cls = diff > 0 ? "up" : "down";
  const sign = diff > 0 ? "+" : "";
  return `<span class="${cls}">${sign}${diff}pp t.o.v. vorige</span>`;
}

function renderTrend(rows, dates) {
  const byDate = {};
  dates.forEach(d => byDate[d] = rows.filter(r => r.date === d));

  const mentionedSeries = dates.map(d => {
    const r = byDate[d];
    return r.length ? Math.round(100 * r.filter(x => x.target_mentioned).length / r.length) : 0;
  });
  const citedSeries = dates.map(d => {
    const r = byDate[d];
    return r.length ? Math.round(100 * r.filter(x => x.target_cited).length / r.length) : 0;
  });

  new Chart(document.getElementById("trend"), {
    type: "line",
    data: {
      labels: dates,
      datasets: [
        { label: "Genoemd %", data: mentionedSeries, borderColor: "#154273", backgroundColor: "#15427322", tension: 0.3, fill: true },
        { label: "Geciteerd %", data: citedSeries, borderColor: "#d52b1e", backgroundColor: "#d52b1e22", tension: 0.3, fill: true },
      ],
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      scales: { y: { beginAtZero: true, max: 100, ticks: { callback: v => v + "%" } } },
    },
  });
}

function renderShareOfVoice(latest) {
  const total = latest.length;
  const tally = { "NederlandWereldwijd": latest.filter(r => r.target_mentioned).length };
  latest.forEach(r => {
    Object.entries(r.competitor_mentions).forEach(([k, v]) => {
      if (v) tally[k] = (tally[k] || 0) + 1;
    });
  });

  const labels = Object.keys(tally);
  const data = labels.map(l => Math.round(100 * tally[l] / total));

  new Chart(document.getElementById("sov"), {
    type: "bar",
    data: {
      labels,
      datasets: [{
        label: "Mentions %",
        data,
        backgroundColor: labels.map(l => l === "NederlandWereldwijd" ? "#154273" : "#9aa3b2"),
      }],
    },
    options: {
      indexAxis: "y",
      responsive: true, maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: { x: { beginAtZero: true, max: 100, ticks: { callback: v => v + "%" } } },
    },
  });
}

function renderPromptTable(latest) {
  const tbody = document.querySelector("#prompt-table tbody");
  tbody.innerHTML = latest.map(r => {
    const compCites = Object.entries(r.competitor_citations)
      .filter(([, n]) => Number(n) > 0)
      .map(([k, n]) => `${k} (${n})`)
      .join(", ") || "—";
    return `<tr>
      <td>${escape(r.prompt_id)}</td>
      <td>${escape(r.provider)}</td>
      <td>${escape(r.run)}</td>
      <td>${pill(r.target_mentioned)}</td>
      <td>${pill(r.target_cited)}</td>
      <td>${escape(compCites)}</td>
    </tr>`;
  }).join("");
}

function pill(v) {
  return v ? `<span class="pill yes">ja</span>` : `<span class="pill no">nee</span>`;
}

function escape(s) {
  return String(s).replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

function renderReports(reports) {
  const ul = document.getElementById("reports");
  if (!reports.length) { ul.innerHTML = "<li>Nog geen rapporten.</li>"; return; }
  ul.innerHTML = reports.slice().reverse().map(name =>
    `<li><a href="reports/${name}">${name}</a></li>`
  ).join("");
}

main();
