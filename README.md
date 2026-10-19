# Ökosüsteemiteenuste muutus seisundiklasside vahel

Analüüs ja interaktiivne veebileht küsimusele: **kui palju ja kuidas muutuvad ökosüsteemiteenused ühe ökosüsteemi või alamökosüsteemi sees, kui seisund liigub klasside vilets → keskmine → hea vahel, ja kas muutus on statistiliselt oluline.**

Allikas: ELME kihtide arhiiv (`https://d549q4t3lqrx1.cloudfront.net/arhiiv/`, baaskaart 2022) ja ametlik kihtide tabel (`eval = TRUE` kihid, 31 teenust).

| Dokument | Sisu |
|---|---|
| [docs/plaan.md](docs/plaan.md) | Eesmärk, ulatus, plaan |
| [docs/metoodika.md](docs/metoodika.md) | Meetod, eeldused, piirangud, valideerimine |
| [docs/tulemused.md](docs/tulemused.md) | Tulemuste kokkuvõte (genereeritud tulemustabelitest) |
| [docs/andmekataloog.md](docs/andmekataloog.md) | Analüüsitavad kihid, ühikud, märkused, arhiivi failid |
| [docs/seis.md](docs/seis.md) | Seis, avatud küsimused, järgmised sammud |

## Veebileht

* Ehitatud sait: `uv run python -m oks site --out site` → `site/index.html` (vajab veebiserverit, nt `python -m http.server -d site`) ja ühefailne `site/oks-seisund.html` (avaneb otse failina).
* Filtrid: ökosüsteem, alamökosüsteem, teenusegrupp, omadus, teenus, seisundipaar, hinnang (paaritatud/paaritamata), olulisus, minimaalne muutus. Vaated: ülevaade (kuumkaart), teenuse detail (sh **väärtuste jaotus** seisundi kaupa), profiil (keskmised), **jaotused** (kõik teenused ühes üksuses), **kihtide ülevaade** (kõigi kihtide väärtuste jaotus seisundi koosseisuga), tabel (CSV), meetod.
* Disain: seisundid on hallikas punane–kollane–roheline (vilets–keskmine–hea), muutuse suund oranž–sinine; printsiibid ja kolleegi graafiku analüüs on failis [`docs/disain.md`](docs/disain.md).
* Ei kasuta välisteeke ega väliseid päringuid; toetab hele/tume teema, klaviatuuri ja mobiili.

## GitHub Pages

Töövoog `.github/workflows/pages.yml` ehitab saidi igal pushil ja avaldab selle **repo vaikeharust**.

1. Repo **Settings → Pages → Build and deployment → Source: GitHub Actions** (ühekordne).
2. Push vaikeharusse või **Actions → Veebileht → Run workflow**. Valmis aadress: `https://<kasutaja>.github.io/<repo-nimi>/` (praegu repo `kaasavakasu`: `https://tpiparkaur.github.io/kaasavakasu/`).
3. Kui deploy keeldub haru tõttu: **Settings → Environments → github-pages → Deployment branches** lisa vaikeharu.

Repo nime saab muuta: **Settings → General → Repository name**. Pages-aadress muutub nime järgi (vana aadress ei suuna ümber);
git-remote'i saab uuendada käsuga `git remote set-url origin <uus-url>`. Sait kasutab suhtelisi teid, seega töötab igal aadressil.

## Käivitamine

```bash
uv sync                                  # Python 3.12, uv
uv run pytest -q                         # 47 testi (sünteetilised andmed teadaoleva vastusega)
uv run ruff check . && uv run mypy src

# Täielik uuesti arvutus (vajab ligipääsu arhiivi hostile; ~ 40 min, laeb ~ 25 GB, kustutab toorfailid)
uv run python -m oks aggregate           # 25 rasterit -> data/derived/plokid/
uv run python -m oks fields              # põllumassiivide vektorid -> rasteriseeritud -> plokid
uv run python -m oks analyse --sensitivity
uv run python -m oks report              # docs/tulemused.md, docs/andmekataloog.md
uv run python -m oks site --out site
```

Tulemustabelid (`data/tulemused/`) on repositooriumis, nii et sait ehitub ilma toorandmeteta.
Toorrastreid ja plokitabeleid (`data/cache`, `data/derived/plokid`, ~ 0,3 GB) ei hoita; need on taastatavad ülaltoodud käskudega.

## Kataloog

```
src/oks/          analüüsikood (baas, aggregate, stats, mixing, analysis, export, report, sitebuild)
site_src/         veebilehe lähtekood (HTML, CSS, JS; ilma sõltuvusteta)
tests/            pytest
data/tulemused/   tulemustabelid (Parquet/CSV)
data/derived/     baaskaardi klassitabelid ja täisresolutsiooni ristiks
data/teenused.csv, data/arhiiv_failid.csv   kihtide kataloog ja arhiivi inventuur
alusmaterjalid/   ametlik kihtide tabel (xlsx/csv) ja baaskaardi .aux.xml (klassinimed)
docs/             dokumentatsioon
```

## Olulised piirangud (täpsemalt [docs/metoodika.md](docs/metoodika.md))

* Tulemus kirjeldab **seoseid**, mitte põhjuslikku mõju.
* Osa teenuste kihte on arvutatud baaskaardi klassi/seisundi põhjal (nt kliimaregulatsioon, kahjuritõrje, toiduteenus); nende puhul on seisundi mõju osaliselt definitsiooniline (lehel märgitud η²-nurgamärgi ja märgiga †).
* 930 m rastrid ja 1 km vektorruudud on analüüsitud uuriva segumudeliga ainult ökosüsteemi tasemel.
* Ühikud on loetud ametlikust kihitabelist; kus tabel ühikut ei nimeta, on see tühi.
* Andmete kasutustingimused tuleb kontrollida enne taasavaldamist.
