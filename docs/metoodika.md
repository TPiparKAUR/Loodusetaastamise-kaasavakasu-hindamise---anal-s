# Metoodika

Dokument kirjeldab, **mida** analüüsiti, **kuidas** ja **millised eeldused ning piirangud** kehtivad.
Kõik arvud, mis siin on, on kontrollitud andmetest või testidest; kus midagi on eeldus, on see nii märgitud.

## 1. Küsimus

Kui seisund liigub ühe ökosüsteemi või alamökosüsteemi sees klasside **vilets → keskmine → hea** vahel:

1. kui palju (absoluutselt ja %) muutub iga ökosüsteemiteenus,
2. mis suunas,
3. kas muutus on statistiliselt oluline, ja kui kindel on see hinnang.

## 2. Andmed

### 2.1 Allikad

| Allikas | Kasutus |
|---|---|
| Arhiiv `https://d549q4t3lqrx1.cloudfront.net/arhiiv/` | 105 andmefaili (rastrid 5, 10 ja 930 m, GeoPackage'id), kokku ~43,6 GB. Inventuur: `data/arhiiv_failid.csv` (`python -m oks` / `oks.inventory`) |
| `alusmaterjalid/metaandmed/layer_definition_checked_vrs2.xlsx` | Ametlik kihtide tabel (136 kihti, veerud `eval`, `nodata`, `has_negative`, `data_type`, `comments`, `abstract` jm). **`eval = TRUE` kihid on analüüsi ulatus** (32 kihti: baaskaart + 31 teenust) |
| ELME2 lõpparuanne | Metoodika viide kihtide abstraktides: <https://loodusveeb.ee/sites/default/files/inline-files/ELME2_LOPPARUANNE_fin_151123.pdf> |

Arhiivi 5 m baaskaart ja teenuste rastrid on EPSG:3301 (L-EST97). Baaskaart on 2022. a, teenuste algandmete aasta
on 2020 või 2022 (kihi nimes ja `data_origin` veerus ELME1/ELME2). Aastate erinevus on analüüsi piirang.

### 2.2 Seisund

Baaskaardil on kolm omavahel ühilduvat kihti (sama 74 200 × 51 600 ruudustik, 5 m):

* `OS_det_seisund_det_2022_5m` – detailne ökosüsteemi tüüp koos algse seisundiklassiga (263 klassi, nimed `.aux.xml` RAT-is),
* `OS_detailne_2022_5m` – alamökosüsteemi tüüp (62 koodi),
* `seisund_uldine_2022_5m` – üldine seisund: tabeli kirjelduse järgi „hea”, „keskmine”, „vilets”, „hindamata”, „määramata”.

Kihi väärtuste tähendus (1 = hea, 2 = keskmine, 3 = vilets, 4–5 = seisundita) **tuletati täisresolutsioonil andmetest** ja
kontrolliti:

* `OS_detailne == OS_det_seisund_det // 100 · 100` kõigis 1 739 miljonis kehtivas pikslis (0 erandit),
* iga detailne kood kaardistub **täpselt ühele** `seisund_uldine` väärtusele (264 koodi, 0 erandit).

| Ökosüsteem | hea | keskmine | vilets |
|---|---|---|---|
| Rohumaad | A, B | C | D1, D2 |
| Sood | A1, A2 | B1, B2 | C1, C2, D, E |
| Metsad | A | A-B, A-C, B, C | D, E, F |
| Põllumaad | A | B | C, D |

Kuna algsed seisundiskaalad on ökosüsteemiti erinevad (nt metsad A–F, sood A1–E), tuleb seisundeid võrrelda
**ökosüsteemi sees**; ökosüsteemide vahel pole „hea” samaväärne. Rannikud ning asustus ja muu on „seisundita”
ja analüüsist välja jäetud.

**Ökosüsteem** = `kood // 10000`; **alamökosüsteem** = `kood // 100 · 100` (62 tüüpi). Alamökosüsteem on analüüsis,
kui baaskaardil on tal vähemalt kaks seisundit.

### 2.3 Teenuste kihid

Analüüsitakse `eval = TRUE` kihid (31 teenust tabelis; tulemustes on **30**, sest `biotorje_kahjuritorje_vahenemine` on sama faili väli, mis `biotorje_2022`, ja kasutatud on ühte, vt allpool). Nende töötlus:

| Rühm | Kihte | Käsitlus |
|---|---|---|
| Rastrid 5 ja 10 m | 25 | Põhianalüüs (plokk × alamökosüsteem, § 4) |
| Põllumassiivide vektorid (`toiduteenus_2022`, `biotorje_2022`) | 2 | Rasteriseeritud 10 m ruudustikule (`oks.fields`), seejärel põhianalüüs. `biotorje_2022` on tabelis kaks kihti (`pestitshind_ha` ja `pestits_vahenemine`, „Kasutada ühte”); kasutatud on `pestits_vahenemine`, sest `pestitshind_ha` on sama muutuja rahas |
| Rastrid 930 m | 2 | Segumudel (§ 7); **uuriv** |
| 1 km ruudustiku vektor `lamm_grd1000_am_drained_2022` | 1 | Segumudel (§ 7); **uuriv** |

Metaandmetes `biotorje_kahjuritorje_vahenemine` ei ole arhiivis eraldi failina; see on `biotorje_2022.gpkg` väli.
Arhiivis on neli faili, mida ametlikus tabelis ei ole (`Elupaigahuve/.tif`, `Loodusannid/johvikad_hind_2022_10m_cog_mode.tif`,
`Sidusus/sidusus_2020_100m.tif`, `output.fgb`); need jäid analüüsist välja. `output.fgb` on maakondade piirid.

Ühikud on loetud tabeli abstraktidest ja pealkirjadest (`oks.catalog.UNITS`); kus tabel ühikut ei nimeta, on see märgitud.

## 3. Eeltöötlus ja kvaliteedikontroll

1. **Ruumiline ühildamine.** Baaskaardi 5 m koodid taasproovitakse teenuse ruudustikule **lähima naabriga**
   (teenuse väärtusi ei interpoleerita). Pärast seda sõltub iga teenusepiksli klass ühe baaskaardi piksli väärtusest piksli keskpunktis.
   See on proovivõtt, mitte pindalakaalutud enamusklass; kontrollitud kihil `sidusus_1km_2022_10m`: 10 m proovivõtu pindala erineb täisresolutsiooni
   (5 m) pindalast kõigis ökosüsteemi × seisundi klassides < 0,03 %.
2. **NoData ja sentinel-väärtused.** Kehtivad on pikslid, mis pole rastri deklareeritud NoData, pole NaN ja millel on
   baaskaardi seisund. Lisaks: `ohusaaste_puhverdusvoime_2022_5m` väärtus 255 käsitletakse NoData-na (tabeli märkus „255 käitub kui 0”,
   NoData on 0); `pohlad_saagikus_2020_10m` −1 on tabeli järgi kehtiv väärtus (`has_negative = 1`).
3. **Ploki jaotus.** Piksel kuulub 1 km plokki (EPSG:3301 ruudustik, joondatud 1000 m kordsetele) piksli **keskpunkti** järgi.
4. **Täisarvude ületäitumine.** Pikslite arv hoitakse `Int64`-ina (Int32 summa ületäitub ~2,1 miljardil); testis ja kontrollis leitud.
5. **Allalaadimise terviklus.** Suurus kontrollitakse serveri `Content-Length` vastu ja poolik fail jätkatakse (`Range`).
6. **Kontrollid.** `data/derived/baaskaart_ristiks_5m.parquet` (täisresolutsiooni ristiks), pindala kontroll, ploki- ja klasside
   testid (`tests/`).

## 4. Aggregeerimine

Iga teenuse jaoks arvutatakse **1 km plokk × detailne klass** kohta: pikslite arv `n`, summa `Σx` ja ruutude summa `Σx²`
(`oks.aggregate`). Kõik edasised hinnangud tuletatakse neist summadest, nii et toorrastrid ei jää kettale.
Tulemus: `data/derived/plokid/<kiht>.parquet`.

## 5. Hinnangud

Seisundid on indekseeritud 0 = vilets, 1 = keskmine, 2 = hea; võrdlused (halvem → parem): vilets → keskmine,
keskmine → hea, vilets → hea. **Δ = parema seisundi keskmine − halvema seisundi keskmine.**
Suhteline muutus = Δ / |halvema keskmine| (tühi, kui nimetaja ≈ 0).

### 5.1 Paaritatud hinnang (peamine)

* **Stratum** = (1 km plokk, alamökosüsteem). Stratumi mõlemad seisundid peavad olema esindatud vähemalt
  `min_area_ha = 1` ha ulatuses (10 m raster: 100 pikslit; 5 m: 400 pikslit).
* Stratumi erinevus `d = keskmine_parem − keskmine_halvem`; kaal `w = n_a·n_b / (n_a + n_b)` (pöördvõrdeline
  dispersiooniga, kui piksli dispersioon on stratumites sama).
* Alamökosüsteemi hinnang = kaalutud keskmine selle alamökosüsteemi stratumitest; **ökosüsteemi hinnang** =
  kaalutud keskmine **kõigist** ökosüsteemi stratumitest. Kuna iga võrdlus tehakse sama alamökosüsteemi sees, on
  ökosüsteemi hinnang automaatselt **koosseisu suhtes kohandatud**.
* Idee: võrrelda seisundeid, mis esinevad samas kohas, nii et asukohast tulenev erinevus (mullastik, kliima, kõrgus)
  ei sega. Sünteetilises testis (`tests/test_stats.py::test_unmatched_differs_from_matched_under_confounding`) taastab paaritatud
  hinnang tõelise efekti täpselt, samal ajal kui paaritamata hinnang on moonutatud, kui „hea” esineb ainult
  kõrgema taustaga plokkides.

### 5.2 Paaritamata hinnang (täiendav)

Pindalakaalutud keskmiste vahe **kõigil** pikslitel ühes ühikus. Alamökosüsteemi tasemel on see mõistlik täiendus
(kasutab kõiki andmeid). **Ökosüsteemi tasemel on see toorhinnang**: seisundiklasside alamökosüsteemide koosseis võib
erineda ja moonutab tulemust (Simpsoni paradoks). Lehel on see märgitud.

## 6. Statistiline olulisus

* **Klastri-bootstrap.** Ruumiline autokorrelatsioon tähendab, et piksleid ega külgnevaid plokke ei saa käsitleda sõltumatutena
  (pikslitasandi p-väärtused oleksid ~10⁹ vaatluse juures mõttetud). Ühikuks on `10 × 10 km` klaster (`cluster_blocks = 10`);
  klastreid valitakse tagasipanekuga (4 000 kordust, sama juhuslik seeme igale kihile). Hinnangu 95 % usaldusvahemik on
  bootstrap-jaotuse 2,5. ja 97,5. protsentiil; kahepoolne p = 2·min(P(Δ* ≤ 0), P(Δ* ≥ 0)),
  alampiir 1/(B+1). Klastri-bootstrapi üldmõte: Künsch (1989), blokk-bootstrap sõltuvatel andmetel.
* **Mitmene testimine.** Benjamini–Hochbergi FDR (Benjamini & Hochberg, 1995) eraldi **ökosüsteemi** ja **alamökosüsteemi**
  tasemel, üle kõigi teenuste, ühikute ja seisundipaaride; `q < 0,05` = „oluline”.
* **Piisavus.** Hinnang on esitatud ja testitav ainult siis, kui on vähemalt `min_strata = 20` paari ja `min_clusters = 5`
  klastrit (paaritamata: vähemalt 20 plokki kummaski seisundis ja 5 klastrit).
* **Praktiline olulisus.** Statistiline olulisus ei tähenda, et muutus on suur. Veebileht lubab filtreerida
  minimaalse |suhtelise muutuse| järgi; lävi ei ole eelseatud, sest see on sisuline otsus.

### 6.1 Kontrollid

* **Plokitasandi Mann–Whitney** (paaritamata) ja **Cliffi δ** efekti suurusena (Cliff, 1993): δ = 2U/(n_a n_b) − 1.
* **Wilcoxoni märgitud astakute test** paaritatud stratumi-erinevustel.
* Need testid kohtlevad plokke sõltumatutena ja on ruumilise sõltuvuse tõttu **optimistlikud**; need on ainult kooskõla kontrolliks.
* Lipp **„oluline mõlemal hinnangul”** = oluline paaritatud *ja* paaritamata hinnangul ning sama märgiga.

### 6.2 Tundlikkus

`oks.analysis.sensitivity` kordab analüüsi teiste klastri suurustega (5 ja 20 km) ja minimaalse alaga (0,25 ja 4 ha).
Tulemused on `data/tulemused/tundlikkus.csv` ja kokkuvõte `docs/tulemused.md` § 6: paaritatud olulistest hinnangutest säilis oluliseks sama märgiga 95–100 % (ökosüsteem) ja 89–99 % (alamökosüsteem; 4 ha puhul langeb osa hinnanguid andmete puudumise tõttu välja); Δ astakkorrelatsioon põhijooksuga ≥ 0,91.

## 7. Jämedad ruudustikud: segumudel (uuriv)

Kui teenuse ruut (930 m, 1 km) on suurem kui seisundiüksus, koosneb ruut mitmest klassist ja ruutu ei saa ühele seisundile omistada.
Eeldatakse, et ruudu väärtus on klasside (ökosüsteem × seisund, 12 klassi + „muu”) pindalaosade lineaarne segu:
`y_c = Σ_k f_ck·β_k + ε_c`; β hinnatakse vähimruutudega ilma vabaliikmeta. Δ = β(parem) − β(halvem). Ebakindlus: klastri-bootstrap
normaalvõrrandite tasemel. Eeldus „väärtus sõltub ainult klassist” on tugev, eriti kihtidel, mis on arvutatud ainult kaldapuhvritele
(`vee_puhastamise_potentsiaal`) või kuivendatud lammidele (`lamm_grd1000…`). **Tulemused on uuriva iseloomuga ja ei ole otse võrreldavad
5/10 m kihtide tulemustega.** Alamökosüsteemi taset ei hinnata.

## 8. Diagnostika: mudelipõhisus

Osa teenuste kihte on tehtud **baaskaardi klassi või seisundi põhjal** (kihi kirjelduse järgi nt kliimaregulatsioon ja
kahjuritõrje; kontrollitud ka `toiduteenus_2022`). Nende puhul on teenuse muutus seisundi vahel osaliselt **definitsiooniline**,
mitte iseseisev tähelepanek. Seda ei saa metaandmetest alati lugeda, seepärast arvutatakse iga kihi ja ökosüsteemi kohta pikslitasandi η²:

* `eta2_det` – osa dispersioonist, mida seletab detailne klass (263 klassi, ökosüsteemi sees),
* `eta2_alam` – osa, mida seletab alamökosüsteem,
* `eta2_state_in_alam` – osa, mida seletab seisund alamökosüsteemi sees.

η² on kirjeldav näitaja (ruumilise sõltuvuse tõttu pole sellel olulisuse tõlgendust). Lehel märgitakse tulemus nurgamärgiga, kui
`eta2_det ≥ 0,9`; kihid, mille seos seisundiga on teadaolevalt definitsiooniline (`toiduteenus_2022`, `biotorje_2022`), saavad lisaks märgi †.
η² ≥ 0,9 on tulemustes ainult kuuel kihi × ökosüsteemi kombinatsioonil (`docs/tulemused.md` § 5), mistõttu η² ei asenda kihi
metoodika tundmist.

**Eraldi leid:** `toiduteenus_2022` väärtusklass A–D langeb põllukultuuride seisundiklassiga (A–D) kokku (keskmine väärtusklass klassides
A/B/C/D = 1,0006 / 2,0000 / 3,0000 / 4,0000, SD ≈ 0,01). Seisund on põllumaal seega tuletatud sama väärtusklassi kaudu, mis on tuletatud
reaalboniteedist; seos seisundi ja boniteedi vahel on osaliselt definitsiooniline.

## 9. Eeldused ja piirangud

1. **Põhjuslikkus.** Tulemus kirjeldab **seoseid** ruumis, mitte seda, mis juhtub ühe koha teenustega, kui selle seisund muutub.
   Paaritamine vähendab segavaid asukohategureid, kuid ei kõrvalda neid (ainult baaskaardi klass on kontrollitud).
2. **Mudelipõhisus** (§ 8): muutus on osaliselt definitsiooniline kihtidel, mis on arvutatud baaskaardi klassi põhjal.
3. **Aastad.** Teenuste algandmed on 2020 või 2022, baaskaart 2022.
4. **Eraldusvõime.** Baaskaardi proovivõtt lähima naabriga; mosaiikses maastikus võib piksli klass erineda ümbritsevast.
5. **Skoorid ja klassid.** Osa kihte on järjestusskaalal (`data_type = Järjestus`/`Diskreetne`); keskmine on siis skoori keskmine.
6. **Suund.** Positiivne Δ tähendab, et väärtus kasvab. Mõnel kihil ei tähenda kasv paremat teenust (nt erosiooni ärakanne;
   `kliimaregulatsioon`: väiksem väärtus = ühtlasem temperatuur). Märkused on iga kihi juures.
7. **Ühikud.** Ühikud on tabelist; mitmel kihil on aastane ja ühekordne väärtus märgitud vaid kirjeldavas tekstis.
8. **Jämedad ruudustikud** (§ 7) on uuriva iseloomuga.
9. **Litsents ja andmed.** Kasutustingimused tuleb kontrollida enne taasavaldamist. Toorrastreid repositooriumis ei hoita.
10. **Isikuandmed.** Analüüs ei kasuta isikuandmeid (`toiduteenus` ja `biotorje` sisaldavad katastritunnuseid ja põllu-ID-sid; need ei
    ole tulemustes ega veebilehel).

## 10. Valideerimine

* Üksus- ja sünteetilised testid (`tests/`): teadaoleva efektiga andmestik (paaritatud/paaritamata hinnang, nullefekt, usaldusvahemiku
  kate, valikuline esinemine), BH-FDR võrdluskäsitsi, klastri indeksid, η², aggregeerimine tehisrastritega (joondatud ja nihutatud ruudustik,
  NoData ja sentinel), segumudel teadaolevate β-dega.
* Pindala kontroll baaskaardiga ja täisresolutsiooni ristiks (§ 3).

## 11. Reprodutseerimine

```bash
uv sync
uv run python -m oks aggregate     # 25 rasterit (laeb ja kustutab toorfailid, ~30 min)
uv run python -m oks fields        # põllumassiivid
uv run python -m oks analyse       # statistika -> data/tulemused
uv run python -m oks site          # veebileht -> site/
uv run pytest
```

## 12. Viited

* Benjamini, Y., Hochberg, Y. (1995). Controlling the false discovery rate: a practical and powerful approach to multiple testing. *J. R. Stat. Soc. B* 57(1): 289–300.
* Cliff, N. (1993). Dominance statistics: ordinal analyses to answer ordinal questions. *Psychological Bulletin* 114(3): 494–509.
* Künsch, H. R. (1989). The jackknife and the bootstrap for general stationary observations. *Annals of Statistics* 17(3): 1217–1241.
* ELME2 lõpparuanne (kihtide metoodika): <https://loodusveeb.ee/sites/default/files/inline-files/ELME2_LOPPARUANNE_fin_151123.pdf>.
