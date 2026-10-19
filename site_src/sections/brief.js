  /* ---------- Lähteülesande täitmine ---------- */
  function briefView(root) {
    const N = D.N; if (!N) { h('p', { class: 'empty' }, root, 'Andmed puuduvad.'); return; }
    const card = h('section', { class: 'card' }, root);
    h('h2', {}, card, 'Lähteülesande täitmine ja kriitiline hinnang');
    h('p', { class: 'sub' }, card, 'Allikad: LTK kaasneva kasu hindamise lähteülesanne (edaspidi lähteülesanne) ja kvantitatiivse analüüsi lähtekas. Iga nõude juures on märgitud, kas ja kus see on täidetud.');
    const cnt = (s) => N.nouded.filter((r) => r.staatus === s).length;
    const row = h('div', { class: 'progress' }, card);
    for (const [st, cls, txt] of [['täidetud', 'done', 'täidetud'], ['osaliselt', 'part', 'osaliselt'], ['ootel', 'wait', 'ootab välist sisendit'], ['ei ole tehtud', 'todo', 'tegemata']]) { const p = h('div', { class: `prog ${cls}` }, row); h('b', {}, p, String(cnt(st))); h('span', {}, p, txt); }
    if (!S.br) S.br = { allikas: 'kõik' };
    const tools = h('div', { class: 'tools' }, card); h('span', { class: 'tl' }, tools, 'Allikas');
    const sg = h('div', { class: 'seg', role: 'group', 'aria-label': 'Allikas' }, tools);
    for (const [v, t] of [['kõik', 'kõik'], ['lähteülesanne', 'lähteülesanne'], ['lähtekas', 'lähtekas (kvantitatiivne)']]) { const b = h('button', { type: 'button', 'aria-pressed': String(S.br.allikas === v) }, sg, t); b.onclick = () => { S.br.allikas = v; renderAll(true); }; }
    const sc = h('div', { class: 'scroll' }, card), t = h('table', { class: 'data req' }, sc), hd = h('tr', {}, h('thead', {}, t));
    for (const x of ['', 'Nõue', 'Seis', 'Kus', 'Kommentaar']) h('th', {}, hd, x);
    const tb = h('tbody', {}, t);
    for (const r of N.nouded.filter((x) => S.br.allikas === 'kõik' || x.allikas === S.br.allikas)) {
      const tr = h('tr', {}, tb); h('td', { class: 'rid' }, tr, r.id); h('td', {}, tr, r.nouue);
      const sc2 = h('td', {}, tr); h('span', { class: `stt ${r.staatus === 'täidetud' ? 'done' : r.staatus === 'osaliselt' ? 'part' : r.staatus === 'ootel' ? 'wait' : 'todo'}` }, sc2, r.staatus);
      h('td', {}, tr, r.kus); h('td', {}, tr, r.kommentaar);
    }
    const c2 = h('section', { class: 'card' }, root);
    h('h2', {}, c2, 'Kriitilised tähelepanekud');
    h('p', { class: 'sub' }, c2, 'Mis piirab tulemuste tõlgendust ja kasutust (sh sotsiaalmajandusliku mõju hindaja jaoks).');
    const ol = h('div', { class: 'crit' }, c2);
    N.kriitika.forEach(([t1, tx], i) => { const a = h('article', {}, ol); h('span', { class: 'n' }, a, String(i + 1)); h('div', {}, a); h('h3', {}, a.lastChild, t1); h('p', {}, a.lastChild, tx); });
    const c3 = h('section', { class: 'card' }, root);
    h('h2', {}, c3, 'Avatud küsimused (vajavad otsust või kinnitust)');
    const ul = h('ol', { class: 'ideas' }, c3); for (const q of N.kusimused) h('li', {}, ul, q);
    const c4 = h('section', { class: 'card' }, root);
    h('h2', {}, c4, 'Ajakava');
    h('p', {}, c4, 'Lähteülesande järgi: meetmete nimekiri KLIMilt augustis → esialgne versioon KLIMile tagasisideks → parandused → lõppraport ja andmetabel 4. novembril 2026. See leht ja Excel on esialgne versioon tagasisideks; meetmete nimekirja ei ole meil olnud.');
  }
