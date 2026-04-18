// ——— Bible book order ———
const OT_BOOKS = [
    'Genesis','Exodus','Leviticus','Numbers','Deuteronomy',
    'Joshua','Judges','Ruth','1 Samuel','2 Samuel',
    '1 Kings','2 Kings','1 Chronicles','2 Chronicles',
    'Ezra','Nehemiah','Esther','Job','Psalm','Proverbs',
    'Ecclesiastes','Song of Solomon','Isaiah','Jeremiah','Lamentations',
    'Ezekiel','Daniel','Hosea','Joel','Amos',
    'Obadiah','Jonah','Micah','Nahum','Habakkuk',
    'Zephaniah','Haggai','Zechariah','Malachi'
];
const NT_BOOKS = [
    'Matthew','Mark','Luke','John','Acts',
    'Romans','1 Corinthians','2 Corinthians','Galatians','Ephesians',
    'Philippians','Colossians','1 Thessalonians','2 Thessalonians',
    '1 Timothy','2 Timothy','Titus','Philemon','Hebrews',
    'James','1 Peter','2 Peter','1 John','2 John','3 John',
    'Jude','Revelation'
];
const ALL_BOOKS = [...OT_BOOKS, ...NT_BOOKS];
const bookIndex = Object.create(null);
ALL_BOOKS.forEach((b, i) => bookIndex[b] = i);

// ——— Parse a reference string ———
function parseRef(ref) {
    const m = ref.match(/^(.+?)\s+(\d+):(\d+)(?:-(\d+))?$/);
    if (!m) return { book: ref, chapter: 0, verse: 0, verseEnd: 0 };
    const v1 = parseInt(m[3], 10);
    const v2 = m[4] ? parseInt(m[4], 10) : v1;
    return { book: m[1], chapter: parseInt(m[2], 10), verse: v1, verseEnd: v2 };
}

function refVerseCount(ref) {
    const p = parseRef(ref);
    return p.verseEnd - p.verse + 1;
}

function refSortKey(ref) {
    const p = parseRef(ref);
    const bi = bookIndex[p.book];
    return (bi !== undefined ? bi : 99) * 1000000 + p.chapter * 1000 + p.verse;
}

function compareRefs(a, b) {
    return refSortKey(a) - refSortKey(b);
}

// ——— Scripture reference links & popovers ———
let popoverCounter = 0;
const verseCache = new Map(); // ref string → Promise<html string>

function makeRefLink(ref) {
    const a = document.createElement('a');
    a.href = '#';
    a.className = 'ref-link';
    a.textContent = ref;
    a.addEventListener('click', (e) => {
        e.preventDefault();
        togglePopover(a, ref);
    });
    return a;
}

function makeRefLinks(refs) {
    const frag = document.createDocumentFragment();
    refs.forEach((ref, i) => {
        if (i > 0) frag.appendChild(document.createTextNode(', '));
        frag.appendChild(makeRefLink(ref));
    });
    return frag;
}

function esc(s) {
    const d = document.createElement('div');
    d.textContent = s;
    return d.innerHTML;
}

function fetchVerseText(ref) {
    if (verseCache.has(ref)) return verseCache.get(ref);
    const passage = encodeURIComponent(ref);
    const url = `https://labs.bible.org/api/?passage=${encodeURIComponent(passage)}&type=json`;
    const promise = fetch(url)
        .then(r => {
            if (!r.ok) throw new Error(r.status);
            return r.json();
        })
        .then(verses => {
            return verses.map(v => `<sup>${esc(v.verse)}</sup>${v.text}`).join('');
        })
        .catch(err => {
            verseCache.delete(ref);
            return `<em class="popover-error">Failed to load: ${esc(err.message)}</em>`;
        });
    verseCache.set(ref, promise);
    return promise;
}

function togglePopover(anchor, ref) {
    const existing = anchor._popoverEl;
    if (existing && existing.matches(':popover-open')) {
        existing.hidePopover();
        existing.remove();
        anchor._popoverEl = null;
        return;
    }

    popoverCounter++;
    const id = 'pop-' + popoverCounter;

    const pop = document.createElement('div');
    pop.id = id;
    pop.className = 'verse-popover';
    pop.setAttribute('popover', 'manual');
    const netUrl = 'https://netbible.org/bible/' + ref.replace(/\s+/g, '+').replace(/-\d+$/, '');
    pop.innerHTML = `<div class="popover-header"><strong>${ref}</strong> <span class="popover-net">(NET)</span><button class="popover-close" aria-label="Close">&times;</button></div><div class="popover-body">Loading…</div><div class="popover-footer"><a href="${encodeURI(netUrl)}" target="_blank" rel="noopener">Show in context →</a></div>`;

    document.body.appendChild(pop);
    anchor._popoverEl = pop;

    pop.querySelector('.popover-close').addEventListener('click', () => {
        pop.hidePopover();
        pop.remove();
        anchor._popoverEl = null;
    });

    pop.showPopover();
    positionPopover(anchor, pop);

    fetchVerseText(ref).then(html => {
        pop.querySelector('.popover-body').innerHTML = html;
    });
}

function positionPopover(anchor, pop) {
    const rect = anchor.getBoundingClientRect();
    const scrollX = window.scrollX;
    const scrollY = window.scrollY;

    pop.style.position = 'absolute';
    pop.style.top = (rect.bottom + scrollY + 4) + 'px';
    pop.style.left = (rect.left + scrollX) + 'px';

    requestAnimationFrame(() => {
        const popRect = pop.getBoundingClientRect();
        if (popRect.right > window.innerWidth - 8) {
            pop.style.left = Math.max(8, window.innerWidth - popRect.width - 8 + scrollX) + 'px';
        }
    });
}

// ——— DOM refs ———
const statusEl = document.getElementById('status');
const tbodyOT = document.getElementById('tbody-ot');
const tbodyNT = document.getElementById('tbody-nt');
const filterSelect = document.getElementById('book-filter');
const rowCountEl = document.getElementById('row-count');
const panelOT = document.getElementById('panel-ot');
const panelNT = document.getElementById('panel-nt');
const tabButtons = document.querySelectorAll('.tab-bar button');
const toggleTextsBtn = document.getElementById('toggle-texts');

let activeTab = 'ot';
let textsShown = false;
let textsPopulatedOT = false;
let textsPopulatedNT = false;

// ——— Batch fetching ———
const BATCH_SIZE = 30;

function batchFetchVerses(refs) {
    // Filter out refs already in cache
    const uncached = refs.filter(r => !verseCache.has(r));
    if (uncached.length === 0) return Promise.resolve();

    const batches = [];
    for (let i = 0; i < uncached.length; i += BATCH_SIZE) {
        batches.push(uncached.slice(i, i + BATCH_SIZE));
    }

    return Promise.all(batches.map(batch => fetchBatch(batch)));
}

function fetchBatch(refs) {
    // Deduplicate individual verses across all refs in the batch.
    // The NET API merges overlapping verse requests and returns each
    // verse only once, so we must request only unique verses and then
    // map results back to each ref.

    // Build ordered list of unique "Book Ch:V" single-verse passages
    const seenVerses = new Set();
    const singleVerses = []; // ordered unique single verses to request
    const refExpansions = []; // for each input ref, list of single-verse strings

    for (const ref of refs) {
        const p = parseRef(ref);
        const expanded = [];
        for (let v = p.verse; v <= p.verseEnd; v++) {
            const sv = `${p.book} ${p.chapter}:${v}`;
            expanded.push(sv);
            if (!seenVerses.has(sv)) {
                seenVerses.add(sv);
                singleVerses.push(sv);
            }
        }
        refExpansions.push(expanded);
    }

    const passage = singleVerses.map(r => encodeURIComponent(r)).join(';');
    const url = `https://labs.bible.org/api/?passage=${passage}&type=json`;
    return fetch(url)
        .then(r => {
            if (!r.ok) throw new Error(r.status);
            return r.json();
        })
        .then(allVerses => {
            // Results arrive in the same order as the deduplicated request,
            // one entry per single verse. Build a map from single-verse
            // string to its API result.
            const verseTextMap = new Map();
            for (let i = 0; i < singleVerses.length && i < allVerses.length; i++) {
                const v = allVerses[i];
                verseTextMap.set(singleVerses[i], `<sup>${esc(v.verse)}</sup>${v.text}`);
            }

            // Assemble HTML for each original ref from its expanded verses
            for (let i = 0; i < refs.length; i++) {
                const parts = refExpansions[i].map(sv => verseTextMap.get(sv) || '');
                const html = parts.join('');
                verseCache.set(refs[i], Promise.resolve(html || '<em class="popover-error">No text found</em>'));
            }
        })
        .catch(err => {
            // On error, store error for each ref so we don't retry endlessly
            for (const ref of refs) {
                if (!verseCache.has(ref)) {
                    verseCache.set(ref, Promise.resolve(
                        `<em class="popover-error">Failed to load: ${esc(err.message)}</em>`
                    ));
                }
            }
        });
}

// ——— Populate text cells for a tab ———
function populateTexts(tab) {
    const tbody = tab === 'ot' ? tbodyOT : tbodyNT;
    const rows = tbody.querySelectorAll(':scope > tr');

    // Collect all unique refs
    const allRefs = new Set();
    for (const tr of rows) {
        const primaryRef = tr.dataset.ref;
        if (primaryRef) allRefs.add(primaryRef);
        const secondaryRefs = tr.dataset.secondaryRefs;
        if (secondaryRefs) {
            secondaryRefs.split('|').forEach(r => allRefs.add(r));
        }
    }

    // Show loading in all text cells
    for (const tr of rows) {
        const cells = tr.querySelectorAll('td');
        if (cells[1] && !cells[1].dataset.loaded) cells[1].textContent = 'Loading\u2026';
        if (cells[3] && !cells[3].dataset.loaded) cells[3].textContent = 'Loading\u2026';
    }

    // Batch fetch then populate
    batchFetchVerses(Array.from(allRefs)).then(() => {
        for (const tr of rows) {
            const cells = tr.querySelectorAll('td');

            // Column 2: primary ref text
            const primaryRef = tr.dataset.ref;
            if (primaryRef && cells[1] && !cells[1].dataset.loaded) {
                verseCache.get(primaryRef).then(html => {
                    cells[1].innerHTML = html;
                    cells[1].dataset.loaded = '1';
                });
            }

            // Column 4: secondary refs with texts in a mini table
            const secondaryRefs = tr.dataset.secondaryRefs;
            if (secondaryRefs && cells[3] && !cells[3].dataset.loaded) {
                const refList = secondaryRefs.split('|');
                const miniTable = document.createElement('table');
                miniTable.className = 'ref-text-table';
                const mtBody = document.createElement('tbody');

                const rowPromises = refList.map(ref => {
                    return verseCache.get(ref).then(html => {
                        const mtr = document.createElement('tr');
                        const mtd1 = document.createElement('td');
                        mtd1.appendChild(makeRefLink(ref));
                        const mtd2 = document.createElement('td');
                        mtd2.innerHTML = html;
                        mtr.appendChild(mtd1);
                        mtr.appendChild(mtd2);
                        return mtr;
                    });
                });

                Promise.all(rowPromises).then(mtrList => {
                    for (const mtr of mtrList) mtBody.appendChild(mtr);
                    miniTable.appendChild(mtBody);
                    cells[3].textContent = '';
                    cells[3].appendChild(miniTable);
                    cells[3].dataset.loaded = '1';
                });
            }
        }
    });
}

// ——— Build tables ———
fetch('./quotations.json')
    .then(r => { if (!r.ok) throw new Error(r.status); return r.json(); })
    .then(data => {
        statusEl.style.display = 'none';

        const otMap = new Map();
        const ntMap = new Map();

        for (const row of data) {
            const nt = row.nt || row.scripture_reference;
            const ot = row.ot || row.quoted_from;
            if (!nt || !ot) continue;

            if (!otMap.has(ot)) otMap.set(ot, []);
            if (!otMap.get(ot).includes(nt)) otMap.get(ot).push(nt);

            if (!ntMap.has(nt)) ntMap.set(nt, []);
            if (!ntMap.get(nt).includes(ot)) ntMap.get(nt).push(ot);
        }

        const otKeys = Array.from(otMap.keys()).sort(compareRefs);
        const ntKeys = Array.from(ntMap.keys()).sort(compareRefs);

        for (const refs of otMap.values()) refs.sort(compareRefs);
        for (const refs of ntMap.values()) refs.sort(compareRefs);

        const otFrag = document.createDocumentFragment();
        for (const otRef of otKeys) {
            const tr = document.createElement('tr');
            const td1 = document.createElement('td');
            const td2 = document.createElement('td');
            const td3 = document.createElement('td');
            const td4 = document.createElement('td');

            td1.appendChild(makeRefLink(otRef));
            td2.className = 'col-text';
            td3.className = 'col-refs';
            td3.appendChild(makeRefLinks(otMap.get(otRef)));
            td4.className = 'col-text';

            tr.dataset.book = parseRef(otRef).book;
            tr.dataset.ref = otRef;
            tr.dataset.secondaryRefs = otMap.get(otRef).join('|');

            tr.appendChild(td1);
            tr.appendChild(td2);
            tr.appendChild(td3);
            tr.appendChild(td4);
            otFrag.appendChild(tr);
        }
        tbodyOT.appendChild(otFrag);

        const ntFrag = document.createDocumentFragment();
        for (const ntRef of ntKeys) {
            const tr = document.createElement('tr');
            const td1 = document.createElement('td');
            const td2 = document.createElement('td');
            const td3 = document.createElement('td');
            const td4 = document.createElement('td');

            td1.appendChild(makeRefLink(ntRef));
            td2.className = 'col-text';
            td3.className = 'col-refs';
            td3.appendChild(makeRefLinks(ntMap.get(ntRef)));
            td4.className = 'col-text';

            tr.dataset.book = parseRef(ntRef).book;
            tr.dataset.ref = ntRef;
            tr.dataset.secondaryRefs = ntMap.get(ntRef).join('|');

            tr.appendChild(td1);
            tr.appendChild(td2);
            tr.appendChild(td3);
            tr.appendChild(td4);
            ntFrag.appendChild(tr);
        }
        tbodyNT.appendChild(ntFrag);

        const otBooksPresent = OT_BOOKS.filter(b => otKeys.some(k => parseRef(k).book === b));
        const ntBooksPresent = NT_BOOKS.filter(b => ntKeys.some(k => parseRef(k).book === b));

        window._otBooksPresent = otBooksPresent;
        window._ntBooksPresent = ntBooksPresent;

        populateFilter();
        updateRowCount();
    })
    .catch(err => {
        statusEl.textContent = 'Failed to load data: ' + err.message;
        statusEl.classList.add('error');
    });

// ——— Filter dropdown ———
function populateFilter() {
    const books = activeTab === 'ot' ? window._otBooksPresent : window._ntBooksPresent;
    filterSelect.innerHTML = '<option value="">All books</option>';
    if (!books) return;
    for (const b of books) {
        const opt = document.createElement('option');
        opt.value = b;
        opt.textContent = b;
        filterSelect.appendChild(opt);
    }
}

function applyFilter() {
    const book = filterSelect.value;
    const tbody = activeTab === 'ot' ? tbodyOT : tbodyNT;
    const rows = tbody.querySelectorAll(':scope > tr');
    for (const tr of rows) {
        tr.style.display = (!book || tr.dataset.book === book) ? '' : 'none';
    }
    updateRowCount();
}

function updateRowCount() {
    const tbody = activeTab === 'ot' ? tbodyOT : tbodyNT;
    const visible = tbody.querySelectorAll('tr:not([style*="display: none"])');
    rowCountEl.textContent = visible.length + ' row' + (visible.length !== 1 ? 's' : '');
}

filterSelect.addEventListener('change', applyFilter);

// ——— Tab switching ———
for (const btn of tabButtons) {
    btn.addEventListener('click', () => {
        activeTab = btn.dataset.tab;

        for (const b of tabButtons) b.classList.remove('active');
        btn.classList.add('active');

        panelOT.classList.toggle('active', activeTab === 'ot');
        panelNT.classList.toggle('active', activeTab === 'nt');

        filterSelect.value = '';
        populateFilter();
        applyFilter();

        // If texts are shown and this tab hasn't been populated yet, populate
        if (textsShown) {
            if (activeTab === 'ot' && !textsPopulatedOT) {
                textsPopulatedOT = true;
                populateTexts('ot');
            } else if (activeTab === 'nt' && !textsPopulatedNT) {
                textsPopulatedNT = true;
                populateTexts('nt');
            }
        }
    });
}

// ——— Toggle texts ———
toggleTextsBtn.addEventListener('click', () => {
    textsShown = !textsShown;
    document.body.classList.toggle('show-texts', textsShown);
    toggleTextsBtn.textContent = textsShown ? 'Hide all texts' : 'Show all texts';

    if (textsShown) {
        // Populate current tab if needed
        if (activeTab === 'ot' && !textsPopulatedOT) {
            textsPopulatedOT = true;
            populateTexts('ot');
        } else if (activeTab === 'nt' && !textsPopulatedNT) {
            textsPopulatedNT = true;
            populateTexts('nt');
        }
    }
});
