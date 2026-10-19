/* Ökosüsteemiteenused ja seisund – interaktiivne vaade (ilma välisteekideta). */
(() => {
  'use strict';

  /* ---------- abifunktsioonid ---------- */
  const SVG = new Set(['svg', 'g', 'rect', 'line', 'path', 'circle', 'text', 'title', 'polygon', 'polyline']);
  const NS = 'http://www.w3.org/2000/svg';
  function h(tag, attrs, parent, text) {
    const e = SVG.has(tag) ? document.createElementNS(NS, tag) : document.createElement(tag);
    for (const [k, v] of Object.entries(attrs || {})) if (v !== null && v !== undefined && v !== false) e.setAttribute(k, v === true ? '' : v);
    if (text !== undefined && text !== null) e.textContent = text;
    if (parent) parent.append(e);
    return e;
  }
  const $ = (s, r = document) => r.querySelector(s);
  const nfs = {};
  const nf = (d) => (nfs[d] ||= new Intl.NumberFormat('et-EE', { minimumFractionDigits: d, maximumFractionDigits: d }));
  function fmt(x, sig) {
    if (x === null || x === undefined || !Number.isFinite(x)) return '–';
    const a = Math.abs(x);
    if (a === 0) return '0';
    if (a >= 1000) return nf(0).format(x);
    if (a >= 100) return nf(1).format(x);
    if (a >= 10) return nf(sig ? 1 : 1).format(x);
    if (a >= 1) return nf(2).format(x);
    if (a >= 0.01) return nf(3).format(x);
    return x.toExponential(1);
  }
  const pct = (r, d = 0) => (r === null || r === undefined || !Number.isFinite(r) ? '–' : `${r > 0 ? '+' : ''}${nf(d).format(r * 100)} %`);
  const sgn = (x) => (x === null || x === undefined || !Number.isFinite(x) ? '–' : `${x > 0 ? '+' : ''}${fmt(x)}`);
  const pfmt = (p) => (p === null || p === undefined ? '–' : p < 0.001 ? '< 0,001' : nf(3).format(p));
  function niceTicks(lo, hi, n = 5) {
    if (!(hi > lo)) { hi = lo + 1; }
    const span = hi - lo, raw = span / n, mag = 10 ** Math.floor(Math.log10(raw));
    const step = [1, 2, 2.5, 5, 10].map((m) => m * mag).find((s) => s >= raw) || raw;
    const a = Math.floor(lo / step) * step, b = Math.ceil(hi / step) * step, t = [];
    for (let v = a; v <= b + step / 2; v += step) t.push(Math.abs(v) < step * 1e-9 ? 0 : +v.toPrecision(12));
    return { ticks: t, lo: t[0], hi: t[t.length - 1] };
  }
  const cssVar = (n) => getComputedStyle(document.documentElement).getPropertyValue(n).trim();
  function hex(c) { const m = /^#?([0-9a-f]{6})$/i.exec(c); const v = parseInt(m ? m[1] : '808080', 16); return [(v >> 16) & 255, (v >> 8) & 255, v & 255]; }
  function mixHex(a, b, t) { const A = hex(a), B = hex(b); return `rgb(${A.map((x, i) => Math.round(x + (B[i] - x) * t)).join(',')})`; }
  function lum(rgb) { const [r, g, b] = rgb.match(/\d+/g).map(Number).map((v) => { v /= 255; return v <= 0.03928 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4; }); return 0.2126 * r + 0.7152 * g + 0.0722 * b; }

  /* ---------- tooltip ---------- */
  const tip = $('#tip');
  function tipShow(build, ev, anchor) {
    tip.replaceChildren();
    build(tip);
    tip.style.display = 'block';
    const r = tip.getBoundingClientRect();
    let x, y;
    if (ev && ev.clientX !== undefined && ev.type !== 'focus') { x = ev.clientX + 14; y = ev.clientY + 14; } else { const b = anchor.getBoundingClientRect(); x = b.left + b.width / 2; y = b.bottom + 6; }
    x = Math.max(8, Math.min(x, innerWidth - r.width - 8)); y = Math.max(8, Math.min(y, innerHeight - r.height - 8));
    tip.style.left = `${x}px`; tip.style.top = `${y}px`;
  }
  const tipHide = () => { tip.style.display = 'none'; };
  function tipOn(node, build) {
    node.addEventListener('pointermove', (e) => tipShow(build, e, node));
    node.addEventListener('pointerleave', tipHide);
    node.addEventListener('focus', (e) => tipShow(build, e, node));
    node.addEventListener('blur', tipHide);
  }
  function tl(parent, cls, text) { return h('div', { class: cls }, parent, text); }

  /* ---------- andmed ---------- */
  let D; // {meta, P, L, K, byPair, byCell}
  async function load() {
    const raw = window.__OKS__ || Object.fromEntries(await Promise.all(['meta', 'paarid', 'lahtrid', 'klassid', 'jaotused'].map(async (n) => {
      try { const r = await fetch(`data/${n}.json`); return [n, r.ok ? await r.json() : null]; } catch { return [n, null]; }
    })));
    const meta = raw.meta;
    const obj = (rows, cols) => rows.map((r) => Object.fromEntries(cols.map((c, i) => [c, r[i]])));
    const P = obj(raw.paarid, meta.paarid_veerud), L = obj(raw.lahtrid, meta.lahtrid_veerud), K = obj(raw.klassid, meta.klassid_veerud);
    const byPair = new Map(P.map((r) => [`${r.layer_id}|${r.unit_code}|${r.pair}`, r]));
    const byCell = new Map(L.map((r) => [`${r.layer_id}|${r.unit_code}|${r.state}`, r]));
    const classMeta = new Map(meta.klassid.map((c) => [c.kood, c]));
    const kByLayer = new Map();
    for (const r of K) { if (!kByLayer.has(r.layer_id)) kByLayer.set(r.layer_id, []); kByLayer.get(r.layer_id).push(r); }
    const dist = new Map(); const distSpec = (raw.jaotused && raw.jaotused.spec) || {};
    for (const [l, u, st, shares, zero] of (raw.jaotused ? raw.jaotused.rows : [])) dist.set(`${l}|${u}|${st}`, { shares, zero });
    D = { meta, P, L, K, byPair, byCell, classMeta, kByLayer, dist, distSpec };
  }

  /* ---------- olek ---------- */
  const S = {
    tab: 'ulevaade', level: 'okosusteem', ecos: new Set(), alamSel: new Set(), alamN: 12,
    groups: new Set(), props: new Set(), layers: new Set(), pair: 2, est: 'm', sig: 'all', minRel: 0,
    detail: { layer: 0, unit: 0 }, profUnit: 0, sort: { col: 'rel', dir: -1 },
  };
  const eco = (u) => D.meta.uhikud[u].eco;
  const unitArea = (u) => D.meta.uhikud[u].pind.reduce((a, b) => a + (b || 0), 0);

  function visLayers() {
    return D.meta.teenused.map((t, i) => ({ t, i })).filter(({ t }) => S.groups.has(t.grupp) && S.props.has(t.omadus || 'muu') && S.layers.has(t.id));
  }
  function visUnits() {
    const all = D.meta.uhikud.map((u, i) => ({ u, i })).filter(({ u }) => S.ecos.has(u.eco) && u.tase === S.level);
    if (S.level === 'okosusteem') return all.map((x) => x.i);
    let sel = all;
    if (S.alamSel.size) sel = all.filter(({ i }) => S.alamSel.has(i));
    else sel = [...all].sort((a, b) => unitArea(b.i) - unitArea(a.i)).slice(0, S.alamN);
    return sel.sort((a, b) => a.u.eco - b.u.eco || unitArea(b.i) - unitArea(a.i)).map((x) => x.i);
  }
  function est(r) {
    if (!r) return null;
    const m = S.est === 'm';
    return m
      ? { d: r.delta_m, rel: r.rel_m, lo: r.ci_m_lo, hi: r.ci_m_hi, p: r.p_m, q: r.q_m, sig: !!r.oluline_m, ok: !!r.enough_m && r.delta_m !== null }
      : { d: r.delta_u, rel: r.rel_u, lo: r.ci_u_lo, hi: r.ci_u_hi, p: r.p_u, q: r.q_u, sig: !!r.oluline_u, ok: !!r.enough_u && r.delta_u !== null };
  }
  function passes(r) {
    const e = est(r);
    if (!e || !e.ok) return false;
    if (S.sig === 'sig' && !e.sig) return false;
    if (S.sig === 'both' && !r.kooskolas) return false;
    if (S.minRel > 0 && !(e.rel !== null && Math.abs(e.rel) >= S.minRel / 100)) return false;
    return true;
  }
  const pairsSel = () => (S.pair === '*' ? [0, 1, 2] : [S.pair]);
  const filtersActive = () => S.sig !== 'all' || S.minRel > 0;

  /* ---------- filtririda ---------- */

  /* ---------- filtrite selgitused (info-nupud) ---------- */
  const INFO = {
    tase: ['Tase', ['Ökosüsteem: neli suurt rühma (rohumaad, sood, metsad, põllumaad). Rannikud ning asustus ja muu on baaskaardil „seisundita” ja analüüsis puuduvad.', 'Alamökosüsteem: täpsem baaskaardi tüüp (nt Salumets, 6410 sinihelmikaniidud). Lehel on alamökosüsteemid, millel on vähemalt kaks seisundit.']],
    okosusteem: ['Ökosüsteem', ['Piirab, milliste ökosüsteemide tulemused näidatakse. Algsed seisundiklassid (A–F) on ökosüsteemiti erinevad, seepärast võrreldakse seisundeid alati ühe ökosüsteemi sees.']],
    alam: ['Alamökosüsteem', ['Vali konkreetsed alamökosüsteemid. Kui valikut pole, näidatakse valitud ökosüsteemide suurima pindalaga alamökosüsteeme (arvu määrab „Kui valikut pole: suurimaid”).', 'Pindala (km²) on kolme seisundi summa baaskaardil.']],
    alamN: ['Kui valikut pole: suurimaid', ['Mitu suurima pindalaga alamökosüsteemi kuvatakse, kui sa neid ise ei vali.']],
    grupp: ['Teenusegrupp', ['ELME kihitabeli teemarühm (nt Loodusannid, Puhverdavad teenused). Piirab, milliseid teenuseid näidatakse.']],
    omadus: ['Omadus', ['biofüüsikaline: väärtus füüsikalistes ühikutes (nt t C/ha, kg/ha).', 'rahaline: rahaline hinnang (EUR/ha).', 'muu: indeks või skoor (nt elupaikade säilitamine 0–10).', 'Allikas: ametlik kihitabel (veerg properties).']],
    teenus: ['Teenus', ['Valik analüüsitud teenustest (kihitabelis eval = TRUE). Mõnel teenusel on tulemus ainult teatud ökosüsteemides (nt metsa puitse biomassi süsinik ainult metsades).', 'Ühik on kihitabelist; kus tabel ühikut ei nimeta, on see tühi.']],
    paar: ['Seisundipaar', ['Mida võrreldakse: halvem → parem seisund. Muutus Δ = parema seisundi keskmine − halvema seisundi keskmine; suhteline muutus = Δ jagatud halvema seisundi keskmisega.', 'Seisundid on ühtlustatud kolmeks klassiks (vilets, keskmine, hea); need tulevad ökosüsteemiti erinevatest algklassidest A–F.', 'Kuumkaart kasutab valitud paari (valikul „kõik” paari vilets → hea); tabel näitab valitud paari või kõiki kolme; profiil näitab alati paari vilets → hea.']],
    hinnang: ['Hinnang: paaritatud ja paaritamata', ['Paaritatud (soovitatav): võrdleb seisundeid, mis esinevad samas 1 km plokis ja samas alamökosüsteemis (kummaski vähemalt 1 ha). Nii ei sega asukoht (mullastik, kliima) ega alamökosüsteemide erinev koosseis. Ökosüsteemi tulemus on kõigi selliste paaride kaalutud keskmine.', 'Paaritamata: kõigi pikslite keskmiste vahe valitud seisundite vahel. Kasutab kõiki andmeid, kuid kui nt „hea” esineb teistes piirkondades või alamökosüsteemides kui „vilets”, läheb see erinevus muutusesse (ökosüsteemi tasemel on see toorhinnang).', 'Kui hinnangud lähevad lahku (eriti vastupidise märgiga), mõjutab tulemust asukoht või koosseis.']],
    olulisus: ['Olulisus', ['oluline: FDR-korrigeeritud q < 0,05. Olulisus tuleb 10 × 10 km klastrite bootstrapist (arvestab ruumilist sõltuvust) ja Benjamini–Hochbergi mitmese testimise parandusest. Hinnang vajab vähemalt 20 paari (paaritamata: plokki) ja 5 klastrit.', 'oluline mõlemal hinnangul: nii paaritatud kui paaritamata hinnang on olulised ja sama märgiga.', 'Statistiline olulisus ei tähenda, et muutus on suur; suuruse piiramiseks kasuta filtrit „Min |muutus|”.']],
    minrel: ['Min |muutus|', ['Peidab hinnangud, mille suhteline muutus (% halvema seisundi keskmisest) on absoluutväärtuselt valitud lävest väiksem. 0 % = kõik. Praktilise tähtsuse piiri valid sina; seda ei ole ette seatud.']],
  };
  let infoKey = null;
  function renderInfo() {
    const box = $('#infopanel'); if (!box) return;
    box.replaceChildren();
    if (!infoKey || !INFO[infoKey]) { box.hidden = true; return; }
    const [title, paras] = INFO[infoKey]; box.hidden = false;
    const x = h('button', { type: 'button', class: 'ghost x', 'aria-label': 'Sulge selgitus' }, box, '×'); x.onclick = () => { infoKey = null; renderInfo(); renderFilters(true); };
    h('h4', {}, box, title); for (const t of paras) h('p', {}, box, t);
  }
  function infoBtn(parent, key, label) {
    const b = h('button', { type: 'button', class: 'info', 'aria-label': `Info: ${label}`, 'aria-expanded': String(infoKey === key), 'aria-controls': 'infopanel' }, parent, 'i');
    b.onclick = (e) => { e.preventDefault(); infoKey = infoKey === key ? null : key; renderInfo(); renderFilters(true); };
    return b;
  }
  function lbl(g, text, key, forId) {
    const l = h(forId ? 'label' : 'span', forId ? { for: forId, class: 'lbl' } : { class: 'lbl' }, g, text);
    if (key) infoBtn(l, key, INFO[key][0]);
    return l;
  }
  function seg(parent, label, opts, get, set, cls, info) {
    const g = h('div', { class: `fgrp ${cls || ''}` }, parent); lbl(g, label, info);
    const s = h('div', { class: 'seg', role: 'group', 'aria-label': label }, g);
    for (const [v, t] of opts) { const b = h('button', { type: 'button', 'aria-pressed': String(get() === v) }, s, t); b.onclick = () => { set(v); renderAll(); }; }
    return g;
  }
  function chips(parent, label, items, setObj, info) {
    const g = h('div', { class: 'fgrp' }, parent); lbl(g, label, info);
    const c = h('div', { class: 'chips' }, g);
    for (const [v, t] of items) { const b = h('button', { type: 'button', class: 'chip', 'aria-pressed': String(setObj.has(v)) }, c, t); b.onclick = () => { setObj.has(v) ? setObj.delete(v) : setObj.add(v); renderAll(); }; }
  }
  function dropdown(parent, label, summary, sections, opts = {}) {
    const g = h('div', { class: 'fgrp' }, parent); lbl(g, label, opts.info);
    const d = h('details', { class: 'dd' }, g); h('summary', { class: 'sel' }, d, summary);
    const p = h('div', { class: 'dd-panel' }, d);
    let q = null;
    if (opts.search) { q = h('input', { type: 'search', placeholder: 'Otsi…', 'aria-label': `${label}: otsi` }, p); }
    const acts = h('div', { class: 'acts' }, p);
    const all = h('button', { type: 'button', class: 'ghost' }, acts, 'Vali kõik'), none = h('button', { type: 'button', class: 'ghost' }, acts, 'Tühjenda');
    const rows = [];
    for (const sec of sections) {
      if (sec.title) h('h4', {}, p, sec.title);
      for (const it of sec.items) {
        const r = h('label', { class: 'row' }, p); const cb = h('input', { type: 'checkbox' }, r); cb.checked = it.get();
        cb.onchange = () => { it.set(cb.checked); renderAll(true); };
        const sp = h('span', {}, r, it.label); if (it.small) h('small', {}, sp, ` ${it.small}`);
        rows.push({ r, cb, it, text: `${it.label} ${it.small || ''}`.toLowerCase() });
      }
    }
    const bulk = (v) => { for (const x of rows) if (x.r.style.display !== 'none') { x.cb.checked = v; x.it.set(v); } renderAll(true); };
    all.onclick = () => bulk(true); none.onclick = () => bulk(false);
    if (q) q.oninput = () => { const s = q.value.trim().toLowerCase(); for (const x of rows) x.r.style.display = x.text.includes(s) ? '' : 'none'; };
    return d;
  }
  const openDD = new Set();
  function renderFilters(keepOpen) {
    const box = $('#filters');
    const opened = keepOpen ? [...box.querySelectorAll('details.dd')].map((d) => d.open) : [];
    const sy = scrollY;
    box.replaceChildren();
    const M = D.meta;
    seg(box, 'Tase', [['okosusteem', 'Ökosüsteem'], ['alam', 'Alamökosüsteem']], () => S.level, (v) => { S.level = v; }, '', 'tase');
    const ecoItems = M.uhikud.filter((u) => u.tase === 'okosusteem').map((u) => [u.kood, u.nimi]);
    chips(box, 'Ökosüsteem', ecoItems, S.ecos, 'okosusteem');
    if (S.level === 'alam') {
      const items = M.uhikud.map((u, i) => ({ u, i })).filter(({ u }) => u.tase === 'alam' && S.ecos.has(u.eco)).sort((a, b) => a.u.eco - b.u.eco || unitArea(b.i) - unitArea(a.i));
      dropdown(box, 'Alamökosüsteem', S.alamSel.size ? `${S.alamSel.size} valitud` : `${Math.min(S.alamN, items.length)} suurimat`,
        [{ items: items.map(({ u, i }) => ({ label: u.nimi, small: `${nf(0).format(unitArea(i))} km²`, get: () => S.alamSel.has(i), set: (v) => (v ? S.alamSel.add(i) : S.alamSel.delete(i)) })) }], { search: true, info: 'alam' });
      const g = h('div', { class: 'fgrp' }, box); lbl(g, 'Kui valikut pole: suurimaid', 'alamN', 'alamN');
      const sel = h('select', { id: 'alamN' }, g);
      for (const n of [6, 12, 20, 40]) { const o = h('option', { value: n }, sel, String(n)); if (n === S.alamN) o.selected = true; }
      sel.onchange = () => { S.alamN = +sel.value; renderAll(); };
    }
    const groups = [...new Set(M.teenused.map((t) => t.grupp))];
    dropdown(box, 'Teenusegrupp', `${S.groups.size}/${groups.length}`, [{ items: groups.map((g) => ({ label: g, get: () => S.groups.has(g), set: (v) => (v ? S.groups.add(g) : S.groups.delete(g)) })) }], { info: 'grupp' });
    chips(box, 'Omadus', [['biofüüsikaline', 'biofüüsikaline'], ['rahaline', 'rahaline'], ['muu', 'muu']], S.props, 'omadus');
    const secs = groups.map((g) => ({ title: g, items: M.teenused.filter((t) => t.grupp === g).map((t) => ({ label: t.nimi, small: t.uhik, get: () => S.layers.has(t.id), set: (v) => (v ? S.layers.add(t.id) : S.layers.delete(t.id)) })) }));
    dropdown(box, 'Teenus', `${S.layers.size}/${M.teenused.length}`, secs, { search: true, info: 'teenus' });
    seg(box, 'Seisundipaar (halvem → parem)', [...M.paarid.map((p, i) => [i, p.replace('→', ' → ')]), ['*', 'kõik']], () => S.pair, (v) => { S.pair = v; }, '', 'paar');
    seg(box, 'Hinnang', [['m', 'Paaritatud'], ['u', 'Paaritamata']], () => S.est, (v) => { S.est = v; }, '', 'hinnang');
    const g = h('div', { class: 'fgrp' }, box); lbl(g, 'Olulisus', 'olulisus', 'sigsel');
    const ss = h('select', { id: 'sigsel' }, g);
    for (const [v, t] of [['all', 'kõik hinnangud'], ['sig', 'oluline (FDR q < 0,05)'], ['both', 'oluline mõlemal hinnangul']]) { const o = h('option', { value: v }, ss, t); if (S.sig === v) o.selected = true; }
    ss.onchange = () => { S.sig = ss.value; renderAll(); };
    const g2 = h('div', { class: 'fgrp' }, box); const l2w = lbl(g2, '', 'minrel', 'minrel'); const l2 = h('span', {}, null, `Min |muutus|: ${S.minRel} %`); l2w.prepend(l2);
    const rg = h('input', { type: 'range', id: 'minrel', min: 0, max: 200, step: 5, value: S.minRel }, g2);
    rg.oninput = () => { l2.textContent = `Min |muutus|: ${rg.value} %`; }; rg.onchange = () => { S.minRel = +rg.value; renderAll(true); };
    const rs = h('button', { type: 'button', class: 'ghost' }, box, 'Lähtesta'); rs.onclick = () => { initState(); renderAll(); };
    h('span', { class: 'count', id: 'count' }, box, '');
    if (keepOpen) box.querySelectorAll('details.dd').forEach((d, i) => { d.open = !!opened[i]; });
    renderInfo();
    scrollTo(0, sy);
  }

  /* ---------- vahekaardid ---------- */
  const TABS = [['ulevaade', 'Ülevaade'], ['teenus', 'Teenuse detail'], ['profiil', 'Profiil'], ['jaotused', 'Jaotused'], ['tabel', 'Tabel'], ['meetod', 'Meetod ja piirangud']];
  function renderTabs() {
    const n = $('#tabs'); n.replaceChildren();
    for (const [k, t] of TABS) { const b = h('button', { role: 'tab', type: 'button', 'aria-selected': String(S.tab === k) }, n, t); b.onclick = () => { S.tab = k; renderAll(true); }; }
  }

  /* ---------- Ülevaade: kuumkaart ---------- */
  function divColor(rel, sig) {
    const t = Math.min(1, Math.abs(rel));
    return { fill: mixHex(cssVar('--mid'), cssVar(rel >= 0 ? '--pos' : '--neg'), t), op: sig ? 1 : 0.38 };
  }
  function heatmap(root) {
    const layers = visLayers(), units = visUnits();
    const pair = S.pair === '*' ? 2 : S.pair;
    const rows = [];
    for (const { t, i } of layers) {
      const cells = units.map((u) => D.byPair.get(`${i}|${u}|${pair}`));
      if (!cells.some(Boolean)) continue;
      if (filtersActive() && !cells.some((c) => c && passes(c))) continue;
      rows.push({ t, i, cells });
    }
    const card = h('section', { class: 'card' }, root);
    h('h2', {}, card, `Seisundi muutus: ${D.meta.paarid[pair].replace('→', ' → ')}`);
    h('p', { class: 'sub' }, card, `Värv = teenuse suhteline muutus (parem − halvem seisund, % halvema seisundi keskmisest), hinnang: ${S.est === 'm' ? 'paaritatud (sama 1 km plokk ja alamökosüsteem)' : 'paaritamata (kõik pikslid)'}. Täisvärv = statistiliselt oluline (FDR q < 0,05), kahvatu = ei ole oluline, tühi = andmeid pole või filter välistab. Klõpsa lahtrit või teenuse nime, et avada detail.`);
    if (S.est === 'u' && S.level === 'okosusteem') h('p', { class: 'warn' }, card, 'Paaritamata hinnang ökosüsteemi tasemel on toorhinnang: seisundiklasside alamökosüsteemide koosseis võib erineda ja see mõjutab tulemust. Soovitatav on paaritatud hinnang.');
    if (!rows.length || !units.length) { h('p', { class: 'empty' }, card, 'Valitud filtritele ei vasta ühtegi tulemust.'); return; }
    const wrapW0 = Math.max(root.clientWidth - 40, 300), labelW = wrapW0 < 700 ? 176 : 360, maxCh = Math.floor(labelW / 6.4), hdrH = S.level === 'alam' ? 150 : 44, rowH = 26, gap = 2;
    const wrapW = Math.max(root.clientWidth - 40, 300);
    const cw = Math.max(S.level === 'alam' ? 54 : 52, Math.min(130, Math.floor((wrapW - labelW) / units.length)));
    const W = labelW + units.length * cw + (S.level === "alam" ? 90 : 10);
    let nGroups = 0, last = null; for (const r of rows) if (r.t.grupp !== last) { nGroups++; last = r.t.grupp; }
    const Hh = hdrH + rows.length * rowH + nGroups * 20 + 10;
    const sc = h('div', { class: 'scroll' }, card);
    const svg = h('svg', { width: W, height: Hh, role: 'group', 'aria-label': 'Kuumkaart: teenused ja ökosüsteemid' }, sc);
    units.forEach((u, j) => {
      const U = D.meta.uhikud[u], x = labelW + j * cw + cw / 2;
      if (S.level === 'alam') h('text', { x, y: hdrH - 6, transform: `rotate(-45 ${x} ${hdrH - 6})`, class: 'lbl' }, svg, U.nimi.length > 34 ? `${U.nimi.slice(0, 33)}…` : U.nimi);
      else h('text', { x, y: hdrH - 10, 'text-anchor': 'middle', class: 'strong' }, svg, U.nimi);
    });
    let y = hdrH; last = null;
    for (const r of rows) {
      if (r.t.grupp !== last) { h('text', { x: 0, y: y + 14, class: 'strong' }, svg, r.t.grupp); y += 20; last = r.t.grupp; }
      const lab = h('g', { class: 'rowlbl', tabindex: 0, role: 'button', 'aria-label': `Ava detail: ${r.t.nimi}` }, svg);
      const unitTxt = r.t.uhik ? ` · ${r.t.uhik.split(' (')[0]}` : '';
      const mark = ((r.t.meetod || '').startsWith('segumudel') ? ' ‡' : '') + (r.t.definitsiooniline ? ' †' : '');
      const full = `${r.t.nimi}${unitTxt}${mark}`;
      const keep = Math.max(8, maxCh - unitTxt.length - mark.length - 1);
      const nm = full.length > maxCh ? `${r.t.nimi.slice(0, keep)}…${unitTxt}${mark}` : full;
      h('text', { x: 8, y: y + rowH / 2 + 4, class: 'lbl' }, lab, nm);
      h('title', {}, lab, `${r.t.pealkiri || r.t.nimi} (${r.t.uhik || 'ühik dokumenteerimata'})`);
      const go = () => { S.detail.layer = r.i; const u0 = units[0]; S.detail.unit = r.cells.findIndex(Boolean) >= 0 ? units[r.cells.findIndex(Boolean)] : u0; S.tab = 'teenus'; renderAll(true); scrollTo(0, 0); };
      lab.onclick = go; lab.onkeydown = (e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); go(); } };
      r.cells.forEach((c, j) => {
        const x = labelW + j * cw;
        const e = est(c);
        const g = h('g', { class: 'cell', tabindex: c ? 0 : -1 }, svg);
        const ok = c && e.ok && passes(c);
        let fill = 'none', op = 1, txt = '', tc = cssVar('--ink-2');
        if (ok) {
          if (e.rel !== null) { const d = divColor(e.rel, e.sig); fill = d.fill; op = d.op; txt = pct(e.rel); tc = lum(fill) < 0.4 ? '#ffffff' : '#0b0b0b'; if (!e.sig) tc = cssVar('--ink'); }
          else { fill = cssVar('--mid'); txt = 'Δ'; }
        }
        h('rect', { class: 'bg', x: x + 1, y: y + 1, width: cw - gap, height: rowH - gap, rx: 3, fill, 'fill-opacity': op, stroke: ok ? 'none' : cssVar('--line'), 'stroke-dasharray': ok ? null : '2 2' }, g);
        if (ok && cw >= 46) h('text', { x: x + cw / 2, y: y + rowH / 2 + 4, 'text-anchor': 'middle', fill: tc, style: `fill:${tc};font-weight:${e.sig ? 600 : 400};font-size:11px` }, g, txt);
        if (ok && c) { const eta = D.meta.teenused[r.i].eta2[String(eco(units[j]))]; if (eta && eta[0] >= 0.9) h('polygon', { points: `${x + cw - 9},${y + 2} ${x + cw - 2},${y + 2} ${x + cw - 2},${y + 9}`, fill: cssVar('--ink'), 'fill-opacity': 0.55 }, g); }
        if (c) {
          g.setAttribute('role', 'img'); g.setAttribute('aria-label', `${r.t.nimi}, ${D.meta.uhikud[units[j]].nimi}: ${ok ? pct(e.rel) : 'pole hinnatav või välja filtreeritud'}`);
          tipOn(g, (t) => pairTip(t, c));
          g.onclick = () => { S.detail.layer = r.i; S.detail.unit = units[j]; S.tab = 'teenus'; renderAll(true); scrollTo(0, 0); };
          g.onkeydown = (ev) => { if (ev.key === 'Enter') g.onclick(); };
        }
      });
      y += rowH;
    }
    const lg = h('ul', { class: 'legend' }, card);
    const li1 = h('li', {}, lg); h('span', { class: 'ramp' }, li1); h('span', {}, li1, '−100 % … 0 … +100 % (punane = väärtus väheneb, sinine = väärtus kasvab; järsemad muutused küllastuvad)');
    const li3 = h('li', {}, lg); h('span', {}, li3, '‡ = uuriv segumudel (jäme ruudustik); tõlgendada ettevaatlikult');
    const li4 = h('li', {}, lg); h('span', {}, li4, '† = seos seisundiga on osaliselt definitsiooniline (kihi väärtus on tuletatud seisundiklassist; vt teenuse detail)');
    const li2 = h('li', {}, lg); h('svg', { width: 12, height: 12 }, li2).append(h('polygon', { points: '12,0 12,10 2,0', fill: cssVar('--ink'), 'fill-opacity': 0.55 })); h('span', {}, li2, 'nurgamärk: ≥ 90 % kihi dispersioonist on baaskaardi klassi tabelväärtus (mudelipõhine; seisundi mõju osaliselt definitsiooniline)');
    h('p', { class: 'note' }, card, 'Suund pole hinnang: näiteks erosiooni ärakandel tähendab positiivne muutus suuremat ärakannet, kliimaregulatsiooni indeksil tähendab väiksem väärtus ühtlasemat temperatuuri. Vt teenuse detaili.');
  }

  function pairTip(t, c) {
    const T = D.meta.teenused[c.layer_id], U = D.meta.uhikud[c.unit_code], e = est(c), eta = T.eta2[String(U.eco)];
    tl(t, 'm', `${T.nimi}`); tl(t, 'm', `${U.nimi} · ${D.meta.paarid[c.pair].replace('→', ' → ')}`);
    if (!e || !e.ok) { tl(t, 'm', 'Pole piisavalt andmeid selle hinnangu jaoks'); return; }
    tl(t, 'v', `${pct(e.rel, 1)}  (${sgn(e.d)} ${T.uhik || ''})`);
    tl(t, 'm', `95 % CI: ${sgn(e.lo)} … ${sgn(e.hi)}`);
    tl(t, 'm', `${S.est === 'm' ? 'paaritatud' : 'paaritamata'} · p ${pfmt(e.p)} · q ${pfmt(e.q)} · ${e.sig ? 'oluline' : 'ei ole oluline'}`);
    tl(t, 'm', `keskmine ${fmt(c.mean_a)} → ${fmt(c.mean_b)}`);
    if (S.est === 'm') tl(t, 'm', `${nf(0).format(c.n_strata)} paari (plokk × alamökosüsteem), ${c.n_clusters_m} klastrit`);
    else tl(t, 'm', `${nf(0).format(c.blocks_a)} / ${nf(0).format(c.blocks_b)} plokki`);
    if (eta) tl(t, 'm', `η² (klass → väärtus): ${nf(2).format(eta[0])}`);
  }

  /* ---------- Teenuse detail ---------- */
  function stateColor(s) { return cssVar(`--st-${s + 1}`); }
  function yScale(lo, hi, H, m) { return (v) => m.t + (H - m.t - m.b) * (1 - (v - lo) / (hi - lo || 1)); }
  function detail(root) {
    const M = D.meta, li = S.detail.layer, ui = S.detail.unit, T = M.teenused[li], U = M.uhikud[ui];
    const card = h('section', { class: 'card' }, root);
    const ctl = h('div', { class: 'frow' }, card);
    const g1 = h('div', { class: 'fgrp wide' }, ctl); h('label', { for: 'dl' }, g1, 'Teenus');
    const sl = h('select', { id: 'dl' }, g1);
    for (const [i, t] of M.teenused.entries()) { const o = h('option', { value: i }, sl, `${t.grupp} · ${t.nimi}${t.uhik ? ` (${t.uhik})` : ''}`); if (i === li) o.selected = true; }
    sl.onchange = () => { S.detail.layer = +sl.value; renderAll(true); };
    const g2 = h('div', { class: 'fgrp' }, ctl); h('label', { for: 'du' }, g2, 'Ökosüsteem / alamökosüsteem');
    const su = h('select', { id: 'du' }, g2);
    const us = M.uhikud.map((u, i) => ({ u, i })).filter(({ i }) => D.byCell.has(`${li}|${i}|0`) || D.byCell.has(`${li}|${i}|1`) || D.byCell.has(`${li}|${i}|2`));
    for (const { u, i } of us) { const o = h('option', { value: i }, su, `${u.tase === 'okosusteem' ? '▪ ' : '   '}${u.nimi}`); if (i === ui) o.selected = true; }
    if (!us.some(({ i }) => i === ui) && us.length) S.detail.unit = us[0].i;
    su.onchange = () => { S.detail.unit = +su.value; renderAll(true); };
    h('h2', {}, card, T.nimi);
    if (T.pealkiri && T.pealkiri !== T.nimi) h('p', { class: 'sub' }, card, T.pealkiri);
    const b = h('div', { class: 'badges' }, card);
    for (const x of [T.grupp, T.omadus, T.tuup && `tüüp: ${T.tuup}`, T.uhik && `ühik: ${T.uhik}`, T.res && `${T.res} m`, T.aasta && `${T.aasta}`, T.allikas, T.meetod && `meetod: ${T.meetod}`].filter(Boolean)) h('span', { class: 'badge' }, b, String(x));
    if (T.markus) h('p', { class: 'warn' }, card, T.markus);
    if (T.tabeli_markus) h('p', { class: 'warn' }, card, `Kihitabeli märkus: ${T.tabeli_markus}`);
    const eta = T.eta2[String(U.eco)];
    if (eta && eta[0] >= 0.9) h('p', { class: 'warn' }, card, `Mudelipõhisuse hoiatus: ${nf(0).format(eta[0] * 100)} % selle kihi dispersioonist ${M.uhikud.find((u) => u.tase === 'okosusteem' && u.eco === U.eco).nimi.toLowerCase()} sees on seletatav baaskaardi klassiga (η² = ${nf(2).format(eta[0])}; seisundi osa alamökosüsteemi sees η² = ${nf(2).format(eta[2])}). Kihi väärtus sõltub suures osas klassi tabelväärtusest, mitte iseseisvast mõõtmisest; muutus seisundi vahel on seega osaliselt definitsiooniline.`);
    if (T.kirjeldus) { const d = h('details', {}, card); h('summary', {}, d, 'Kihi kirjeldus (ametlik kihitabel)'); h('p', { class: 'note' }, d, T.kirjeldus); }
    h('h3', {}, card, `${U.nimi}: pindala seisundi kaupa`);
    h('p', { class: 'note' }, card, M.seisundid.map((s, i) => `${s}: ${nf(0).format(U.pind[i] || 0)} km²`).join(' · '));

    const grid = h('div', { class: 'grid2' }, root);
    const dcard = h('section', { class: 'card wide' }, grid);
    const cards = [0, 1, 2, 3].map(() => h('section', { class: 'card' }, grid));
    const tcard = h('section', { class: 'card' }, root);
    distChart(dcard, li, ui);
    levelsChart(cards[0], li, ui);
    deltaChart(cards[1], li, ui, 'rel');
    deltaChart(cards[2], li, ui, 'abs');
    classChart(cards[3], li, ui);
    pairTable(tcard, li, ui);
  }


  /* ---------- Jaotused (pikslitaseme histogrammid) ---------- */
  function distFor(li, ui) {
    const spec = D.distSpec[li];
    if (!spec) return null;
    const series = [0, 1, 2].map((st) => D.dist.get(`${li}|${ui}|${st}`) || null);
    return series.some(Boolean) ? { spec, series } : null;
  }
  function binLabels(spec) {
    const f = (v) => fmt(v);
    if (spec.kind === 'lut') return [...spec.edges.map(f), 'muu'];
    const e = spec.edges, out = [`< ${f(e[0])}`];
    for (let i = 0; i < spec.nbins; i++) out.push(`${f(e[i])} … ${f(e[i + 1])}`);
    out.push(`≥ ${f(e[spec.nbins])}`);
    return out;
  }
  function stepPath(shares, x, y, base) {
    let d = `M${x(0)},${y(base)}`;
    shares.forEach((v, i) => { d += ` L${x(i)},${y(v)} L${x(i + 1)},${y(v)}`; });
    return `${d} L${x(shares.length)},${y(base)}`;
  }
  function distChart(card, li, ui) {
    const T = D.meta.teenused[li], U = D.meta.uhikud[ui];
    h('h2', {}, card, `Väärtuste jaotus seisundi kaupa: ${U.nimi}`);
    const dd = distFor(li, ui);
    if (!dd) { h('p', { class: 'sub' }, card, 'Selle teenuse ja üksuse kohta pole pikslitaseme jaotust (uuriv segumudel või puuduvad andmed).'); return; }
    const { spec, series } = dd;
    h('p', { class: 'sub' }, card, `Iga seisundi pikslite osakaal (%) väärtuse vahemikus. Igal seisundil on oma 100 %, seega on kõverad võrreldavad sõltumata seisundi pindalast.${spec.kind === 'sqrt' ? ' Väga viltuse jaotuse tõttu on x-telg ruutjuure skaalal (vahemikud on √x-s võrdse laiusega).' : ''}${spec.kind === 'lut' ? ' Kihil on diskreetsed väärtused (skoorid või klassid).' : ''}`);
    const n = spec.n_bins, W = Math.max(320, Math.min(980, card.clientWidth - 30 || 700)), H = 300, m = { l: 52, r: 12, t: 16, b: 58 };
    const top = Math.max(...series.filter(Boolean).flatMap((d) => d.shares)) / 100;
    const tk = niceTicks(0, top * 1.08, 5), y = (v) => m.t + (H - m.t - m.b) * (1 - v / (tk.hi || 1));
    const x = (i) => m.l + (W - m.l - m.r) * (i / n);
    const sc = h('div', { class: 'scroll' }, card);
    const svg = h('svg', { width: W, height: H, role: 'img', 'aria-label': `${T.nimi}: väärtuste jaotus seisundi kaupa` }, sc);
    for (const v of tk.ticks) { h('line', { x1: m.l, x2: W - m.r, y1: y(v), y2: y(v), class: 'grid' }, svg); h('text', { x: m.l - 6, y: y(v) + 4, 'text-anchor': 'end' }, svg, `${nf(0).format(v)} %`); }
    const labels = binLabels(spec);
    const grouped = spec.kind === 'lut' && n <= 12;
    series.forEach((d, st) => {
      if (!d) return;
      const sh = d.shares.map((v) => v / 100), col = stateColor(st);
      if (grouped) {
        const bw = (W - m.l - m.r) / n, w = Math.min(18, (bw - 6) / 3);
        sh.forEach((v, i) => { if (v > 0) h('rect', { x: x(i) + bw / 2 + (st - 1) * (w + 2) - w / 2, y: y(v), width: w, height: y(0) - y(v), rx: 2, fill: col }, svg); });
      } else {
        h('path', { d: stepPath(sh, x, y, 0), fill: col, 'fill-opacity': 0.12, stroke: 'none' }, svg);
        h('path', { d: `M${x(0)},${y(sh[0])} ` + sh.map((v, i) => `L${x(i)},${y(v)} L${x(i + 1)},${y(v)}`).join(' '), fill: 'none', stroke: col, 'stroke-width': 2, 'stroke-linejoin': 'round' }, svg);
      }
    });
    // x-telje sildid
    if (spec.kind === 'lut') {
      const step = Math.ceil(n / 14);
      labels.forEach((l, i) => { if (i % step === 0 || i === n - 1) h('text', { x: x(i) + (W - m.l - m.r) / n / 2, y: H - m.b + 16, 'text-anchor': 'middle' }, svg, l); });
    } else {
      const e = spec.edges, k = Math.ceil((spec.nbins + 1) / 7);
      for (let i = 0; i <= spec.nbins; i += k) { h('line', { x1: x(i + 1), x2: x(i + 1), y1: y(0), y2: y(0) + 4, class: 'axis' }, svg); h('text', { x: x(i + 1), y: H - m.b + 18, 'text-anchor': 'middle' }, svg, fmt(e[i])); }
      h('text', { x: x(0.5), y: H - m.b + 18, 'text-anchor': 'middle' }, svg, '<');
      h('text', { x: x(n - 0.5), y: H - m.b + 18, 'text-anchor': 'middle' }, svg, '≥');
    }
    h('line', { x1: m.l, x2: W - m.r, y1: y(0), y2: y(0), class: 'axis' }, svg);
    h('text', { x: m.l + (W - m.l - m.r) / 2, y: H - 6, 'text-anchor': 'middle' }, svg, T.uhik || 'väärtus');
    // keskmise märgid
    if (spec.kind !== 'lut') {
      series.forEach((d, st) => {
        const c = D.byCell.get(`${li}|${ui}|${st}`); if (!d || !c) return;
        const e = spec.edges, lo = e[0], hi = e[spec.nbins];
        const t = spec.kind === 'sqrt' ? (Math.sqrt(Math.max(c.mean, 0)) - Math.sqrt(lo)) / (Math.sqrt(hi) - Math.sqrt(lo)) : (c.mean - lo) / (hi - lo);
        const pos = Math.max(0, Math.min(n, 1 + t * spec.nbins));
        h('circle', { cx: x(pos), cy: y(0), r: 5, fill: stateColor(st), stroke: cssVar('--surface'), 'stroke-width': 2 }, svg);
      });
    }
    // hover: vahemik -> kõigi seisundite osakaalud
    for (let i = 0; i < n; i++) {
      const r = h('rect', { x: x(i), y: m.t, width: (W - m.l - m.r) / n, height: H - m.t - m.b, fill: 'transparent' }, svg);
      tipOn(r, (t) => { tl(t, 'm', `${T.nimi} · ${labels[i]} ${T.uhik || ''}`); series.forEach((d, st) => { if (d) { const row = tl(t, 'v', `${nf(1).format(d.shares[i] / 100)} %`); h('span', { class: 'm' }, row, `  ${D.meta.seisundid[st]}`); } }); });
    }
    const lg = h('ul', { class: 'legend' }, card);
    series.forEach((d, st) => {
      if (!d) return; const c = D.byCell.get(`${li}|${ui}|${st}`); const li2 = h('li', {}, lg); h('span', { class: 'sw', style: `--c:${stateColor(st)}` }, li2);
      h('span', {}, li2, `${D.meta.seisundid[st]}${c ? ` · keskmine ${fmt(c.mean)}` : ''}${d.zero >= 500 ? ` · täpselt 0: ${nf(0).format(d.zero / 100)} %` : ''}`);
    });
    const cmp = [[0, 1], [1, 2], [0, 2]].filter(([a, b]) => series[a] && series[b]);
    if (cmp.length) {
      h('h3', {}, card, 'Jaotuste võrdlus');
      const tw = h('div', { class: 'scroll' }, card), tc = h('table', { class: 'data' }, tw), hc = h('tr', {}, h('thead', {}, tc));
      for (const c of ['Seisundipaar', 'Jaotuste kattuvus', 'Parema seisundi piksel on väärtuselt suurem']) h('th', {}, hc, c);
      const tbc = h('tbody', {}, tc);
      for (const [a, b] of cmp) {
        const pa = series[a].shares.map((v) => v / 10000), pb = series[b].shares.map((v) => v / 10000);
        let ov = 0, auc = 0, cum = 0;
        pa.forEach((v, i) => { ov += Math.min(v, pb[i]); auc += pb[i] * (cum + 0.5 * v); cum += v; });
        const tr = h('tr', {}, tbc); h('td', {}, tr, `${D.meta.seisundid[a]} → ${D.meta.seisundid[b]}`); h('td', {}, tr, `${nf(0).format(ov * 100)} %`); h('td', {}, tr, `${nf(0).format(auc * 100)} %`);
      }
      h('p', { class: 'note' }, card, 'Kattuvus = jaotuste ühisosa (100 % = identsed, 0 % = täiesti eraldi). Teine veerg: tõenäosus, et juhuslikult valitud parema seisundi piksli väärtus on suurem kui halvema seisundi pikslil (50 % = vahet pole; võrdsed vahemikud loetakse pooleks). Arvutatud pikslitaseme jaotustest vahemike täpsusega; pikslid on ruumiliselt sõltuvad, seega on need kirjeldavad näitajad, mitte olulisuse testid (olulisus on eespool, 10 km klastrite bootstrapiga).');
    }
    if (spec.kind !== 'lut') h('p', { class: 'note' }, card, 'Punkt x-teljel = pindalakaalutud keskmine (nupp võib jääda vahemiku serva, kui keskmine on väljaspool kuvatud vahemikku).');
    const det = h('details', {}, card); h('summary', {}, det, 'Tabelivaade (osakaal %)');
    const sc2 = h('div', { class: 'scroll' }, det), t2 = h('table', { class: 'data' }, sc2), hr = h('tr', {}, h('thead', {}, t2));
    for (const c of [`Vahemik (${T.uhik || 'väärtus'})`, ...D.meta.seisundid]) h('th', {}, hr, c);
    const tb = h('tbody', {}, t2);
    labels.forEach((l, i) => { const tr = h('tr', {}, tb); h('td', {}, tr, l); series.forEach((d) => h('td', {}, tr, d ? nf(1).format(d.shares[i] / 100) : '–')); });
  }
  function distMini(parent, li, ui) {
    const dd = distFor(li, ui); if (!dd) return false;
    const { spec, series } = dd, n = spec.n_bins, W = 196, H = 64, m = { l: 4, r: 4, t: 4, b: 4 };
    const top = Math.max(...series.filter(Boolean).flatMap((d) => d.shares)) || 1;
    const x = (i) => m.l + (W - m.l - m.r) * (i / n), y = (v) => m.t + (H - m.t - m.b) * (1 - v / top);
    const svg = h('svg', { width: W, height: H, role: 'img', 'aria-label': `${D.meta.teenused[li].nimi}: jaotus seisundi kaupa` }, parent);
    h('line', { x1: m.l, x2: W - m.r, y1: y(0), y2: y(0), class: 'axis' }, svg);
    series.forEach((d, st) => {
      if (!d) return; const col = stateColor(st);
      if (spec.kind === 'lut' && n <= 12) { const bw = (W - m.l - m.r) / n, w = Math.max(2, Math.min(8, (bw - 2) / 3)); d.shares.forEach((v, i) => { if (v > 0) h('rect', { x: x(i) + bw / 2 + (st - 1) * (w + 1) - w / 2, y: y(v), width: w, height: y(0) - y(v), fill: col }, svg); }); }
      else h('path', { d: `M${x(0)},${y(d.shares[0])} ` + d.shares.map((v, i) => `L${x(i)},${y(v)} L${x(i + 1)},${y(v)}`).join(' '), fill: 'none', stroke: col, 'stroke-width': 1.8, 'stroke-linejoin': 'round' }, svg);
    });
    return true;
  }
  function distTab(root) {
    const M = D.meta, card = h('section', { class: 'card' }, root);
    h('h2', {}, card, 'Väärtuste jaotus seisundi kaupa: kõik teenused');
    h('p', { class: 'sub' }, card, 'Iga mini-graafik näitab teenuse pikslite jaotust väärtuse vahemikes kolmes seisundis (igal seisundil oma 100 %). Kui kõverad on üksteisest eraldi, muutub teenus seisundi vahel; kui kattuvad, ei muutu. Klõpsa graafikut, et avada täpne jaotus, tabel ja hinnangud.');
    const ctl = h('div', { class: 'frow' }, card); const g = h('div', { class: 'fgrp wide' }, ctl); h('label', { for: 'du2' }, g, 'Ökosüsteem / alamökosüsteem');
    const sel = h('select', { id: 'du2' }, g);
    const us = M.uhikud.map((u, i) => ({ u, i })).filter(({ u }) => S.ecos.has(u.eco));
    if (!us.some(({ i }) => i === S.profUnit) && us.length) S.profUnit = us[0].i;
    for (const { u, i } of us) { const o = h('option', { value: i }, sel, `${u.tase === 'okosusteem' ? '▪ ' : '   '}${u.nimi}`); if (i === S.profUnit) o.selected = true; }
    sel.onchange = () => { S.profUnit = +sel.value; renderAll(true); };
    const minis = h('div', { class: 'minis' }, card); let n = 0;
    for (const { t, i } of visLayers()) {
      const probe = distFor(i, S.profUnit); if (!probe) continue;
      const m = h('div', { class: 'mini', tabindex: 0, role: 'button', 'aria-label': `Ava detail: ${t.nimi}` }, minis);
      h('h4', {}, m, t.nimi); h('div', { class: 'u' }, m, `${t.grupp}${t.uhik ? ` · ${t.uhik}` : ''}`);
      distMini(m, i, S.profUnit);
      const r2 = D.byPair.get(`${i}|${S.profUnit}|2`), e = est(r2);
      h('div', { class: 'u' }, m, e && e.ok ? `vilets → hea: ${pct(e.rel)}${e.sig ? '' : ' (ei ole oluline)'}` : 'vilets → hea: ebapiisavalt andmeid');
      const go = () => { S.detail.layer = i; S.detail.unit = S.profUnit; S.tab = 'teenus'; renderAll(true); scrollTo(0, 0); };
      m.onclick = go; m.onkeydown = (ev) => { if (ev.key === 'Enter') go(); };
      n++;
    }
    if (!n) h('p', { class: 'empty' }, card, D.distSpec && Object.keys(D.distSpec).length ? 'Selles üksuses pole valitud teenustel jaotust.' : 'Jaotuse andmed puuduvad.');
    const lg = h('ul', { class: 'legend' }, card);
    M.seisundid.forEach((s, i) => { const li2 = h('li', {}, lg); h('span', { class: 'sw', style: `--c:${stateColor(i)}` }, li2); h('span', {}, li2, s); });
  }

  function levelsChart(card, li, ui) {
    const T = D.meta.teenused[li];
    h('h2', {}, card, 'Teenuse tase seisundi kaupa');
    h('p', { class: 'sub' }, card, 'Punkt = pindalakaalutud keskmine; kast = 1 km plokkide keskmiste vahemik Q1–Q3, vurr = 5.–95. protsentiil, vahetõmmis = mediaan.');
    const cells = [0, 1, 2].map((s) => D.byCell.get(`${li}|${ui}|${s}`));
    if (!cells.some(Boolean)) { h('p', { class: 'empty' }, card, 'Andmeid pole.'); return; }
    const W = Math.max(320, Math.min(560, card.clientWidth - 30 || 520)), H = 290, m = { l: 62, r: 12, t: 26, b: 40 };
    const vals = cells.filter(Boolean).flatMap((c) => [c.q05, c.q95, c.mean].filter((v) => v !== null));
    let lo = Math.min(...vals), hi = Math.max(...vals); if (lo > 0 && lo < 0.35 * hi) lo = 0;
    const pad = (hi - lo) * 0.06 || 1; const tk = niceTicks(lo - (lo === 0 ? 0 : pad), hi + pad, 5);
    const y = yScale(tk.lo, tk.hi, H, m);
    const svg = h('svg', { width: W, height: H, role: 'img', 'aria-label': `${T.nimi}: tase seisundi kaupa` }, card);
    for (const v of tk.ticks) { h('line', { x1: m.l, x2: W - m.r, y1: y(v), y2: y(v), class: 'grid' }, svg); h('text', { x: m.l - 6, y: y(v) + 4, 'text-anchor': 'end' }, svg, fmt(v)); }
    h('text', { x: 4, y: 12 }, svg, T.uhik || '');
    const bw = (W - m.l - m.r) / 3;
    cells.forEach((c, s) => {
      const cx = m.l + bw * s + bw / 2, w = Math.min(44, bw * 0.45);
      h('text', { x: cx, y: H - 22, 'text-anchor': 'middle', class: 'lbl' }, svg, D.meta.seisundid[s]);
      if (!c) { h('text', { x: cx, y: H - 8, 'text-anchor': 'middle' }, svg, 'andmeid pole'); return; }
      const g = h('g', { tabindex: 0, role: 'img', 'aria-label': `${D.meta.seisundid[s]}: keskmine ${fmt(c.mean)}` }, svg);
      h('line', { x1: cx, x2: cx, y1: y(c.q05), y2: y(c.q95), stroke: cssVar('--ink-2'), 'stroke-width': 1.5 }, g);
      h('rect', { x: cx - w / 2, y: y(c.q75), width: w, height: Math.max(2, y(c.q25) - y(c.q75)), rx: 3, fill: stateColor(s) }, g);
      h('line', { x1: cx - w / 2, x2: cx + w / 2, y1: y(c.q50), y2: y(c.q50), stroke: cssVar('--surface'), 'stroke-width': 2 }, g);
      h('circle', { cx, cy: y(c.mean), r: 5, fill: cssVar('--ink'), stroke: cssVar('--surface'), 'stroke-width': 2 }, g);
      h('text', { x: cx + w / 2 + 8, y: y(c.mean) + 4, class: 'strong' }, svg, fmt(c.mean));
      h('text', { x: cx, y: H - 8, 'text-anchor': 'middle' }, svg, `${nf(0).format(c.n * (D.meta.teenused[li].res || 10) ** 2 / 1e6)} km²`);
      tipOn(g, (t) => { tl(t, 'm', `${T.nimi} · ${D.meta.seisundid[s]}`); tl(t, 'v', `${fmt(c.mean)} ${T.uhik || ''}`); tl(t, 'm', `pikslisisene SD ${fmt(c.sd)}`); tl(t, 'm', `plokkide Q1–Q3: ${fmt(c.q25)} … ${fmt(c.q75)} (${nf(0).format(c.blocks)} plokki)`); });
    });
  }

  function deltaChart(card, li, ui, mode) {
    const T = D.meta.teenused[li];
    h('h2', {}, card, mode === 'rel' ? 'Muutus seisundipaaride vahel (suhteline)' : `Muutus seisundipaaride vahel (${(T.uhik || 'absoluutne').split(' (')[0]})`);
    h('p', { class: 'sub' }, card, 'Punkt = hinnang, joon = 95 % usaldusvahemik (10 km klastrite bootstrap). Täis punkt = paaritatud, tühi ring = paaritamata. Sinine = oluline (FDR q < 0,05), hall = ei ole oluline.');
    const rows = [];
    for (let p = 0; p < 3; p++) { const r = D.byPair.get(`${li}|${ui}|${p}`); if (!r) continue; for (const k of ['m', 'u']) { const e = (k === 'm') ? { d: r.delta_m, rel: r.rel_m, lo: r.ci_m_lo, hi: r.ci_m_hi, sig: !!r.oluline_m, ok: !!r.enough_m, p: r.p_m, q: r.q_m } : { d: r.delta_u, rel: r.rel_u, lo: r.ci_u_lo, hi: r.ci_u_hi, sig: !!r.oluline_u, ok: !!r.enough_u, p: r.p_u, q: r.q_u }; rows.push({ p, k, r, e }); } }
    const val = (e) => (mode === 'rel' ? { v: e.rel, lo: e.lo !== null && e.d ? e.rel * (e.lo / e.d) : null, hi: e.hi !== null && e.d ? e.rel * (e.hi / e.d) : null } : { v: e.d, lo: e.lo, hi: e.hi });
    const pts = rows.filter((x) => x.e.ok && val(x.e).v !== null);
    if (!pts.length) { h('p', { class: 'empty' }, card, 'Selle ühiku kohta pole piisavalt andmeid hinnangu jaoks.'); return; }
    const W = Math.max(320, Math.min(560, card.clientWidth - 30 || 520)), rowH = 30, m = { l: 214, r: 16, t: 10, b: 30 }, H = m.t + m.b + rows.length * rowH;
    const all = pts.flatMap((x) => { const v = val(x.e); return [v.v, v.lo, v.hi, 0].filter((z) => z !== null && z !== undefined); });
    const tk = niceTicks(Math.min(...all), Math.max(...all), 5);
    const x = (v) => m.l + (W - m.l - m.r) * ((v - tk.lo) / (tk.hi - tk.lo || 1));
    const svg = h('svg', { width: W, height: H, role: 'img', 'aria-label': 'Hinnangud ja usaldusvahemikud' }, card);
    for (const v of tk.ticks) { h('line', { x1: x(v), x2: x(v), y1: m.t, y2: H - m.b, class: 'grid' }, svg); h('text', { x: x(v), y: H - 12, 'text-anchor': 'middle' }, svg, mode === 'rel' ? `${nf(0).format(v * 100)} %` : fmt(v)); }
    h('line', { x1: x(0), x2: x(0), y1: m.t, y2: H - m.b, class: 'zero' }, svg);
    rows.forEach((row, i) => {
      const cy = m.t + rowH * i + rowH / 2, v = val(row.e);
      h('text', { x: 4, y: cy + 4, class: 'lbl' }, svg, `${D.meta.paarid[row.p].replace('→', ' → ')} · ${row.k === 'm' ? 'paaritatud' : 'paaritamata'}`);
      const g = h('g', { tabindex: 0, role: 'img', 'aria-label': `${D.meta.paarid[row.p]} ${row.k}: ${row.e.ok ? pct(row.e.rel, 1) : 'pole hinnatav'}` }, svg);
      if (!row.e.ok || v.v === null) { h('text', { x: m.l + 6, y: cy + 4 }, g, 'ebapiisavalt andmeid'); }
      else {
        const col = row.e.sig ? cssVar('--accent') : cssVar('--muted');
        if (v.lo !== null && v.hi !== null) h('line', { x1: x(v.lo), x2: x(v.hi), y1: cy, y2: cy, stroke: col, 'stroke-width': 2, 'stroke-linecap': 'round' }, g);
        h('circle', { cx: x(v.v), cy, r: 5, fill: row.k === 'm' ? col : cssVar('--surface'), stroke: col, 'stroke-width': row.k === 'm' ? 2 : 2.5 }, g);
      }
      h('rect', { x: m.l - 4, y: cy - rowH / 2, width: W - m.l, height: rowH, fill: 'transparent' }, g);
      tipOn(g, (t) => pairTip(t, row.r));
    });
    const lg = h('ul', { class: 'legend' }, card);
    const a = h('li', {}, lg); h('span', { class: 'sw dot', style: `--c:${cssVar('--accent')}` }, a); h('span', {}, a, 'oluline');
    const b2 = h('li', {}, lg); h('span', { class: 'sw dot', style: `--c:${cssVar('--muted')}` }, b2); h('span', {}, b2, 'ei ole oluline');
  }

  const LETTER_ORDER = ['A', 'A1', 'A2', 'A-B', 'A-C', 'B', 'B1', 'B2', 'C', 'C1', 'C2', 'D', 'D1', 'D2', 'E', 'F'];
  function classChart(card, li, ui) {
    const T = D.meta.teenused[li], U = D.meta.uhikud[ui];
    h('h2', {}, card, 'Algsel seisundiskaalal');
    h('p', { class: 'sub' }, card, `Keskmine iga algse seisundiklassi (${U.tase === 'alam' ? 'alamökosüsteemi' : 'ökosüsteemi kõigi alamökosüsteemide'}) kohta; värv = ühtlustatud seisund. Näitab, kas muutus on astmeline või ühtlane.`);
    const rows = (D.kByLayer.get(li) || []).map((r) => ({ r, c: D.classMeta.get(r.kood) })).filter(({ c }) => c && c.seisund && (U.tase === 'alam' ? c.alam === U.kood : c.eco === U.eco));
    const pooled = new Map();
    for (const { r, c } of rows) { const k = c.seisund_algne; const o = pooled.get(k) || { n: 0, s: 0, st: c.seisund }; o.n += r.n; o.s += r.n * r.mean; pooled.set(k, o); }
    const items = [...pooled.entries()].map(([k, o]) => ({ k, n: o.n, mean: o.s / o.n, st: D.meta.seisundid.indexOf(o.st) })).sort((a, b) => LETTER_ORDER.indexOf(a.k) - LETTER_ORDER.indexOf(b.k));
    if (!items.length) { h('p', { class: 'empty' }, card, 'Andmeid pole.'); return; }
    const W = Math.max(320, Math.min(560, card.clientWidth - 30 || 520)), H = 270, m = { l: 62, r: 10, t: 26, b: 44 };
    const hi = Math.max(...items.map((i) => i.mean), 0), lo = Math.min(...items.map((i) => i.mean), 0);
    const tk = niceTicks(lo, hi * 1.05 || 1, 5), y = yScale(tk.lo, tk.hi, H, m);
    const svg = h('svg', { width: W, height: H, role: 'img', 'aria-label': 'Keskmine algse seisundiklassi kaupa' }, card);
    for (const v of tk.ticks) { h('line', { x1: m.l, x2: W - m.r, y1: y(v), y2: y(v), class: 'grid' }, svg); h('text', { x: m.l - 6, y: y(v) + 4, 'text-anchor': 'end' }, svg, fmt(v)); }
    h('text', { x: 4, y: 12 }, svg, T.uhik || '');
    const bw = (W - m.l - m.r) / items.length, w = Math.min(24, bw * 0.7);
    items.forEach((it, i) => {
      const cx = m.l + bw * i + bw / 2, y0 = y(0), y1 = y(it.mean);
      const g = h('g', { tabindex: 0, role: 'img', 'aria-label': `${it.k}: ${fmt(it.mean)}` }, svg);
      const top = Math.min(y0, y1), ht = Math.max(1, Math.abs(y1 - y0));
      h('path', { d: `M${cx - w / 2},${y0} V${top + 4} q0,-4 4,-4 h${w - 8} q4,0 4,4 V${y0} z`, fill: stateColor(it.st >= 0 ? it.st : 0), transform: it.mean < 0 ? `rotate(180 ${cx} ${y0})` : null }, g);
      h('rect', { x: cx - w / 2 - 2, y: top - 4, width: w + 4, height: ht + 8, fill: 'transparent' }, g);
      h('text', { x: cx, y: H - 28, 'text-anchor': 'middle', class: 'lbl' }, svg, it.k);
      if (bw >= 38) h('text', { x: cx, y: (it.mean >= 0 ? top : top + ht) + (it.mean >= 0 ? -5 : 13), 'text-anchor': 'middle' }, svg, fmt(it.mean));
      tipOn(g, (t) => { tl(t, 'm', `${T.nimi} · klass ${it.k} (${D.meta.seisundid[it.st] || ''})`); tl(t, 'v', `${fmt(it.mean)} ${T.uhik || ''}`); tl(t, 'm', `${nf(0).format(it.n)} pikslit`); });
    });
    h('text', { x: m.l, y: H - 8 }, svg, 'algne seisundiklass (A = parim)');
    const lg = h('ul', { class: 'legend' }, card);
    D.meta.seisundid.forEach((s, i) => { const li2 = h('li', {}, lg); h('span', { class: 'sw', style: `--c:${stateColor(i)}` }, li2); h('span', {}, li2, s); });
  }

  function pairTable(card, li, ui) {
    h('h2', {}, card, 'Tabelivaade');
    const sc = h('div', { class: 'scroll' }, card);
    const t = h('table', { class: 'data' }, sc);
    const hd = h('tr', {}, h('thead', {}, t));
    for (const c of ['Seisundipaar', 'Hinnang', 'Δ', 'Δ %', '95 % CI (Δ)', 'p', 'q (FDR)', 'Oluline', 'Paare/plokke']) h('th', {}, hd, c);
    const tb = h('tbody', {}, t);
    for (let p = 0; p < 3; p++) {
      const r = D.byPair.get(`${li}|${ui}|${p}`); if (!r) continue;
      for (const k of ['m', 'u']) {
        const e = est2(r, k), tr = h('tr', {}, tb);
        h('td', {}, tr, D.meta.paarid[p].replace('→', ' → ')); h('td', {}, tr, k === 'm' ? 'paaritatud' : 'paaritamata');
        h('td', {}, tr, e.ok ? sgn(e.d) : '–'); h('td', {}, tr, e.ok ? pct(e.rel, 1) : '–'); h('td', {}, tr, e.ok ? `${sgn(e.lo)} … ${sgn(e.hi)}` : '–');
        h('td', {}, tr, e.ok ? pfmt(e.p) : '–'); h('td', {}, tr, e.ok ? pfmt(e.q) : '–'); h('td', { class: e.ok && e.sig ? 'sig-y' : 'sig-n' }, tr, e.ok ? (e.sig ? 'jah' : 'ei') : 'ebapiisav');
        h('td', {}, tr, k === 'm' ? `${nf(0).format(r.n_strata || 0)} paari` : `${nf(0).format(r.blocks_a)} / ${nf(0).format(r.blocks_b)} plokki`);
      }
    }
  }
  function est2(r, k) {
    return k === 'm' ? { d: r.delta_m, rel: r.rel_m, lo: r.ci_m_lo, hi: r.ci_m_hi, p: r.p_m, q: r.q_m, sig: !!r.oluline_m, ok: !!r.enough_m && r.delta_m !== null }
      : { d: r.delta_u, rel: r.rel_u, lo: r.ci_u_lo, hi: r.ci_u_hi, p: r.p_u, q: r.q_u, sig: !!r.oluline_u, ok: !!r.enough_u && r.delta_u !== null };
  }

  /* ---------- Profiil: kõik teenused ühe üksuse sees ---------- */
  function profile(root) {
    const M = D.meta, card = h('section', { class: 'card' }, root);
    h('h2', {}, card, 'Kõik teenused ühe ökosüsteemi sees');
    h('p', { class: 'sub' }, card, 'Iga mini-graafik näitab teenuse keskmist kolmes seisundis, indekseerituna halvima seisundi (vilets) keskmise = 100. Joon on ainult lugemise abi; hinnangud ja olulisus on teenuse detailis. Klõpsa graafikut, et avada detail.');
    const ctl = h('div', { class: 'frow' }, card); const g = h('div', { class: 'fgrp wide' }, ctl); h('label', { for: 'pu' }, g, 'Ökosüsteem / alamökosüsteem');
    const sel = h('select', { id: 'pu' }, g);
    const us = M.uhikud.map((u, i) => ({ u, i })).filter(({ u }) => S.ecos.has(u.eco));
    if (!us.some(({ i }) => i === S.profUnit) && us.length) S.profUnit = us[0].i;
    for (const { u, i } of us) { const o = h('option', { value: i }, sel, `${u.tase === 'okosusteem' ? '▪ ' : '   '}${u.nimi}`); if (i === S.profUnit) o.selected = true; }
    sel.onchange = () => { S.profUnit = +sel.value; renderAll(true); };
    const minis = h('div', { class: 'minis' }, card); let n = 0, lastG = null;
    for (const { t, i } of visLayers()) {
      const cs = [0, 1, 2].map((s) => D.byCell.get(`${i}|${S.profUnit}|${s}`));
      if (!cs.every(Boolean) || !(Math.abs(cs[0].mean) > 1e-12)) continue;
      n++;
      const idx = cs.map((c) => (c.mean / cs[0].mean) * 100), r2 = D.byPair.get(`${i}|${S.profUnit}|2`), e = est(r2);
      const m = h('div', { class: 'mini', tabindex: 0, role: 'button', 'aria-label': `Ava detail: ${t.nimi}` }, minis);
      h('h4', {}, m, t.nimi); h('div', { class: 'u' }, m, `${t.grupp}${t.uhik ? ` · ${t.uhik}` : ''}`);
      const W = 190, H = 70, mm = { l: 6, r: 6, t: 8, b: 8 };
      const lo = Math.min(...idx, 100), hi = Math.max(...idx, 100), y = yScale(lo - (hi - lo) * 0.1, hi + (hi - lo) * 0.1, H, mm), x = (s) => mm.l + (W - mm.l - mm.r) * (s / 2);
      const svg = h('svg', { width: W, height: H, role: 'img', 'aria-label': `${t.nimi}: indeks ${idx.map((v) => nf(0).format(v)).join(', ')}` }, m);
      h('line', { x1: mm.l, x2: W - mm.r, y1: y(100), y2: y(100), class: 'grid' }, svg);
      h('polyline', { points: idx.map((v, s) => `${x(s)},${y(v)}`).join(' '), fill: 'none', stroke: cssVar('--ink-2'), 'stroke-width': 2, 'stroke-linejoin': 'round' }, svg);
      idx.forEach((v, s) => h('circle', { cx: x(s), cy: y(v), r: 5, fill: stateColor(s), stroke: cssVar('--surface'), 'stroke-width': 2 }, svg));
      h('div', { class: 'u' }, m, e && e.ok ? `vilets → hea: ${pct(e.rel)}${e.sig ? '' : ' (ei ole oluline)'}` : 'vilets → hea: ebapiisavalt andmeid');
      const go = () => { S.detail.layer = i; S.detail.unit = S.profUnit; S.tab = 'teenus'; renderAll(true); scrollTo(0, 0); };
      m.onclick = go; m.onkeydown = (ev) => { if (ev.key === 'Enter') go(); };
      tipOn(m, (tp) => { tl(tp, 'm', t.nimi); tl(tp, 'v', `indeks: ${idx.map((v) => nf(0).format(v)).join(' → ')}`); tl(tp, 'm', `keskmine: ${cs.map((c) => fmt(c.mean)).join(' → ')} ${t.uhik || ''}`); });
    }
    if (!n) h('p', { class: 'empty' }, card, 'Selles üksuses pole ühtegi teenust, millel oleks andmed kõigis kolmes seisundis.');
    const lg = h('ul', { class: 'legend' }, card);
    M.seisundid.forEach((s, i) => { const li2 = h('li', {}, lg); h('span', { class: 'sw dot', style: `--c:${stateColor(i)}` }, li2); h('span', {}, li2, s); });
  }

  /* ---------- Tabel ---------- */
  const COLS = [
    ['teenus', 'Teenus', (r) => D.meta.teenused[r.layer_id].nimi], ['grupp', 'Grupp', (r) => D.meta.teenused[r.layer_id].grupp],
    ['uhik', 'Ühik', (r) => D.meta.teenused[r.layer_id].uhik || ''], ['unit', 'Üksus', (r) => D.meta.uhikud[r.unit_code].nimi],
    ['pair', 'Seisundipaar', (r) => D.meta.paarid[r.pair]], ['a', 'Keskmine (halvem)', (r) => r.mean_a], ['b', 'Keskmine (parem)', (r) => r.mean_b],
    ['d', 'Δ', (r) => est(r).d], ['rel', 'Δ %', (r) => est(r).rel], ['lo', 'CI alumine', (r) => est(r).lo], ['hi', 'CI ülemine', (r) => est(r).hi],
    ['p', 'p', (r) => est(r).p], ['q', 'q (FDR)', (r) => est(r).q], ['sig', 'Oluline', (r) => (est(r).sig ? 'jah' : 'ei')],
    ['n', 'Paare / plokke', (r) => (S.est === 'm' ? r.n_strata : Math.min(r.blocks_a, r.blocks_b))], ['eta', 'η² (klass)', (r) => { const e = D.meta.teenused[r.layer_id].eta2[String(D.meta.uhikud[r.unit_code].eco)]; return e ? e[0] : null; }],
  ];
  function tableRows() {
    const layers = new Set(visLayers().map((x) => x.i)), units = new Set(visUnits());
    return D.P.filter((r) => layers.has(r.layer_id) && units.has(r.unit_code) && pairsSel().includes(r.pair) && passes(r));
  }
  function table(root) {
    const card = h('section', { class: 'card' }, root);
    h('h2', {}, card, 'Tabelivaade');
    h('p', { class: 'sub' }, card, 'Kõik praeguste filtritega sobivad hinnangud. Veeru päisele klõpsates sorteerub tabel. CSV sisaldab filtreeritud ridu täpsete väärtustega.');
    const rows = tableRows(), c = COLS.find((x) => x[0] === S.sort.col) || COLS[8];
    const val = (r) => { const v = c[2](r); return v === null || v === undefined || Number.isNaN(v) ? null : v; };
    rows.sort((a, b) => { const x = val(a), y = val(b); if (x === null) return 1; if (y === null) return -1; return (typeof x === 'string' ? x.localeCompare(y, 'et') : x - y) * S.sort.dir; });
    const bar = h('div', { class: 'frow' }, card);
    const dl = h('button', { type: 'button', class: 'ghost' }, bar, `Laadi alla CSV (${rows.length} rida)`);
    dl.onclick = () => downloadCsv(rows);
    const cp = h('button', { type: 'button', class: 'ghost' }, bar, 'Kopeeri CSV');
    cp.onclick = async () => {
      const txt = csvText(rows);
      try { await navigator.clipboard.writeText(txt); cp.textContent = 'Kopeeritud'; setTimeout(() => { cp.textContent = 'Kopeeri CSV'; }, 1500); } catch {
        let ta = $('#csvbox'); if (!ta) ta = h('textarea', { id: 'csvbox', class: 'csvbox', readonly: true, 'aria-label': 'CSV' }, card);
        ta.value = txt; ta.focus(); ta.select();
      }
    };
    if (!rows.length) { h('p', { class: 'empty' }, card, 'Valitud filtritele ei vasta ühtegi tulemust.'); return; }
    const wrap = h('div', { class: 'tblwrap' }, card), t = h('table', { class: 'data' }, wrap), hd = h('tr', {}, h('thead', {}, t));
    for (const col of COLS) { const th = h('th', { 'aria-sort': S.sort.col === col[0] ? (S.sort.dir > 0 ? 'ascending' : 'descending') : 'none', tabindex: 0 }, hd, `${col[1]}${S.sort.col === col[0] ? (S.sort.dir > 0 ? ' ▲' : ' ▼') : ''}`); const f = () => { S.sort = { col: col[0], dir: S.sort.col === col[0] ? -S.sort.dir : 1 }; renderAll(true); }; th.onclick = f; th.onkeydown = (e) => { if (e.key === 'Enter') f(); }; }
    const tb = h('tbody', {}, t);
    for (const r of rows.slice(0, 500)) {
      const tr = h('tr', {}, tb), e = est(r);
      COLS.forEach((col, i) => {
        const v = col[2](r); let s;
        if (['rel'].includes(col[0])) s = pct(v, 1); else if (['p', 'q'].includes(col[0])) s = pfmt(v); else if (typeof v === 'number') s = col[0] === 'n' || col[0] === 'eta' ? nf(col[0] === 'eta' ? 2 : 0).format(v) : fmt(v); else s = v ?? '–';
        h('td', { class: col[0] === 'sig' ? (e.sig ? 'sig-y' : 'sig-n') : null }, tr, s);
      });
    }
    if (rows.length > 500) h('p', { class: 'note' }, card, `Näidatud on esimesed 500 rida ${rows.length}-st; CSV sisaldab kõiki.`);
  }
  function csvText(rows) {
    const q = (v) => (v === null || v === undefined || Number.isNaN(v) ? '' : typeof v === 'string' ? `"${v.replaceAll('"', '""')}"` : String(v));
    const head = COLS.map((c) => q(c[1])).join(',');
    return [head, ...rows.map((r) => COLS.map((c) => q(c[2](r))).join(','))].join('\n');
  }
  function downloadCsv(rows) {
    const blob = new Blob(['\ufeff', csvText(rows)], { type: 'text/csv;charset=utf-8' });
    const a = h('a', { href: URL.createObjectURL(blob), download: 'okosusteemiteenused_seisund.csv' }); document.body.append(a); a.click(); a.remove();
  }

  /* ---------- Meetod ---------- */
  function method(root) {
    const M = D.meta, p = M.parameetrid, card = h('section', { class: 'card prose' }, root);
    const P = (t) => h('p', {}, card, t);
    h('h2', {}, card, 'Meetod lühidalt');
    P('Täielik kirjeldus on repositooriumi failis docs/metoodika.md. Siin on olulisim.');
    h('h3', {}, card, 'Seisund');
    P('Seisundiklassid pärinevad baaskaardilt (2022, 5 m): „seisund_uldine” 1 = hea, 2 = keskmine, 3 = vilets. Vastavus algsetele klassidele (A–F) on iga ökosüsteemi sees erinev ja tuletati täisresolutsiooni ristiksist (iga detailne kood kaardistub täpselt ühele seisundile).');
    const t = h('table', {}, card); const hr = h('tr', {}, h('thead', {}, t)); for (const c of ['Ökosüsteem', 'hea', 'keskmine', 'vilets']) h('th', {}, hr, c);
    for (const r of [['Rohumaad', 'A, B', 'C', 'D1, D2'], ['Sood', 'A1, A2', 'B1, B2', 'C1, C2, D, E'], ['Metsad', 'A', 'A-B, A-C, B, C', 'D, E, F'], ['Põllumaad', 'A', 'B', 'C, D']]) { const tr = h('tr', {}, t); for (const c of r) h('td', {}, tr, c); }
    h('h3', {}, card, 'Hinnang ja olulisus');
    P(`Muutus Δ = parema seisundi keskmine − halvema seisundi keskmine. Paaritatud hinnang võrdleb seisundeid, mis esinevad samas 1 km plokis ja samas alamökosüsteemis (kummaski vähemalt ${p.min_area_ha} ha), kaaludes ploki n_a·n_b/(n_a+n_b) järgi. See kontrollib asukoha ja alamökosüsteemi koosseisu mõju. Paaritamata hinnang on kõigi pikslite keskmiste vahe.`);
    P(`Olulisus: ${nf(0).format(p.cluster_blocks)} × ${nf(0).format(p.cluster_blocks)} km klastrite bootstrap (${nf(0).format(p.n_boot)} kordust) arvestab ruumilist autokorrelatsiooni; kahepoolsed p-väärtused korrigeeritakse Benjamini–Hochbergi meetodiga (FDR) eraldi ökosüsteemi ja alamökosüsteemi taseme jaoks (α = ${p.alpha}). Hinnang on „oluline”, kui q < ${p.alpha} ja vähemalt ${p.min_strata} paari ning ${p.min_clusters} klastrit.`);
    h('h3', {}, card, 'Piirangud, mida tuleb arvestada');
    const ul = h('ul', {}, card);
    for (const s of [
      'Statistiline olulisus ei tähenda põhjuslikkust: seisund ja teenus võivad sõltuda ühistest teguritest (mullastik, asukoht). Paaritamine vähendab, kuid ei kõrvalda seda.',
      'Osa kihte on arvutatud baaskaardi klassi või seisundi põhjal (kihi kirjelduse järgi nt kliimaregulatsioon ja kahjuritõrje; kontrollitud ka toiduteenus). Neil on muutus seisundi vahel osaliselt definitsiooniline; seda näitavad nurgamärk (η² ≥ 0,9), märk † ja hoiatus teenuse detailis.',
      'Teenuste aastad on erinevad (2020 ja 2022), baaskaart on 2022. Eraldusvõimed on 5 ja 10 m, baaskaart võetakse teenuse ruudustikule lähima naabriga.',
      'Mõnede kihtide väärtused on diskreetsed klassid või skoorid (järjestusskaala); keskmine on siis skoori keskmine, mitte füüsikaline suurus.',
      'Ühikud on võetud ametlikust kihitabelist; kus tabel ühikut ei nimeta, on see tühi.',
      'Jämedama eraldusvõimega kihid (930 m) ja ruudustikupõhised vektorkihid on analüüsitud segumudeliga ainult ökosüsteemi tasemel ja on uuriva iseloomuga.',
    ]) h('li', {}, ul, s);
    h('p', { class: 'note' }, card, `Analüüs koostatud ${M.koostatud}. Andmeallikas: ELME kihid (KAUR). Kasutustingimused: kontrolli enne taasavaldamist.`);
  }

  /* ---------- koostamine ---------- */
  function initState() {
    const M = D.meta;
    S.level = 'okosusteem'; S.ecos = new Set(M.uhikud.filter((u) => u.tase === 'okosusteem').map((u) => u.kood));
    S.alamSel = new Set(); S.alamN = 12; S.groups = new Set(M.teenused.map((t) => t.grupp)); S.props = new Set(['biofüüsikaline', 'rahaline', 'muu']);
    S.layers = new Set(M.teenused.map((t) => t.id)); S.pair = 2; S.est = 'm'; S.sig = 'all'; S.minRel = 0;
  }
  function renderAll(keep) {
    renderFilters(keep); renderTabs();
    const root = $('#view'); root.replaceChildren();
    tipHide();
    ({ ulevaade: heatmap, teenus: detail, profiil: profile, jaotused: distTab, tabel: table, meetod: method })[S.tab](root);
    const n = tableRows().length; const c = $('#count'); if (c) c.textContent = `${n} sobivat hinnangut`;
  }
  async function main() {
    await load(); initState();
    const best = D.P.filter((r) => D.meta.uhikud[r.unit_code].tase === 'okosusteem' && r.enough_m && r.pair === 2).sort((a, b) => (b.n_strata || 0) - (a.n_strata || 0))[0] || D.P[0];
    if (best) { S.detail.layer = best.layer_id; S.detail.unit = best.unit_code; S.profUnit = best.unit_code; }
    $('#theme').onclick = () => { const r = document.documentElement, cur = r.getAttribute('data-theme'); const dark = cur ? cur === 'dark' : matchMedia('(prefers-color-scheme: dark)').matches; r.setAttribute('data-theme', dark ? 'light' : 'dark'); renderAll(true); };
    matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => renderAll(true));
    let rt; addEventListener('resize', () => { clearTimeout(rt); rt = setTimeout(() => renderAll(true), 200); });
    if (innerWidth < 900) $('#fdet').open = false;
    renderAll();
  }
  main().catch((e) => { $('#view').replaceChildren(h('p', { class: 'empty' }, null, `Andmete laadimine ebaõnnestus: ${e.message}. Ava leht veebiserveri kaudu (nt python -m http.server) või kasuta ühefailset varianti.`)); console.error(e); });
})();
