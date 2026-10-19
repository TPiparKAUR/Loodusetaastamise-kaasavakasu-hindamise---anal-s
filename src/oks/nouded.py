"""Lähteülesande nõuded, nende täitmise seis, kriitilised tähelepanekud ja avatud küsimused.

Allikas on kaks dokumenti (``docs/lahteulesanne.md`` kirjeldab neid): LTK kaasneva kasu hindamise lähteülesanne
(LTM; edaspidi „lähteülesanne“) ja kvantitatiivse analüüsi lähtekas (edaspidi „lähtekas“). Sama sisu on veebilehel
(vahekaart „Lähteülesande täitmine“) ja failis ``docs/lahteulesanne.md`` (``report.write_requirements``).

Staatused: ``täidetud``, ``osaliselt``, ``ootel`` (vajab välist sisendit) ja ``ei ole tehtud``.
"""

from __future__ import annotations

from typing import TypedDict


class Requirement(TypedDict):
    """Üks lähteülesande nõue ja selle täitmise seis."""

    id: str
    allikas: str
    nouue: str
    staatus: str
    kus: str
    kommentaar: str


DONE, PART, WAIT, TODO = "täidetud", "osaliselt", "ootel", "ei ole tehtud"

REQUIREMENTS: list[Requirement] = [
    {
        "id": "L1",
        "allikas": "lähteülesanne",
        "nouue": "Hinnata LTK meetmete ja tegevuste mõju ökosüsteemiteenustele ELME/ELME2 loodushüvede raamistiku põhjal; biofüüsikalised ja rahalised väärtused selgelt eristatud.",
        "staatus": PART,
        "kus": "Tulemustabel; Excel; Stsenaarium",
        "kommentaar": "Kvantitatiivne alus on valmis ja biofüüsikaline ning rahaline on eraldi veergudes. Seos konkreetsete meetmetega puudub, sest Kliimaministeeriumi meetmete nimekiri ei ole meil olemas.",
    },
    {
        "id": "L2",
        "allikas": "lähteülesanne",
        "nouue": "Rahalise väärtuse hindamisel lähtuda erinevatest asjakohastest hindamismeetoditest.",
        "staatus": PART,
        "kus": "Kvalitatiivne; Teenuste kirjeldus (Excel)",
        "kommentaar": "Kasutatud on ELME2 kihtides juba olemasolevad väärtused (turuhind, asenduskulu, ülekantud kulud, süsiniku hind, riigi kogusumma jaotus). Iga teenuse meetod ja kasutatavus on kirjas; uusi hindamismeetodeid ei ole rakendatud.",
    },
    {
        "id": "L3",
        "allikas": "lähteülesanne",
        "nouue": "Valida KLIMi meetmete nimekirjast otsese mõjuga meetmed; koostada tabel meetmetest ja tegevustest CICES v5.1 hierarhia järgi (varustav, reguleeriv ja säilitav, kultuuriline).",
        "staatus": WAIT,
        "kus": "Kvalitatiivne (CICES sektsioonid), Excel (mall)",
        "kommentaar": "Meetmete nimekiri puudub. Iga teenus on paigutatud CICES sektsiooni; CICES rühmad on ettepanek, klasside koode ei ole lähteandmetes ega kirjutatud.",
    },
    {
        "id": "L4",
        "allikas": "lähteülesanne",
        "nouue": "Meetmete ja tegevuste nimekiri valideeritakse KLIMiga; lõplik nimekiri kinnitatakse kirjalikult (augustis).",
        "staatus": WAIT,
        "kus": "–",
        "kommentaar": "Väline sisend. Nimekirja tähtaeg oli august; seda ei ole selles töös kasutada.",
    },
    {
        "id": "L5",
        "allikas": "lähteülesanne",
        "nouue": "Kvalitatiivne hindamine: mõju suund, tugevus, ajaline raamistik, ulatus; loodusõnnetuste ja äärmuslike ilmastikunähtuste ennetus ja leevendus; ekspertide kaasamine; tulemus kirjalikult ja tabelina iga tegevuse juures.",
        "staatus": PART,
        "kus": "Kvalitatiivne; Excel (Kvalitatiivne, Tõendusbaas)",
        "kommentaar": "Teenuste kaupa on olemas raamistik ja andmepõhine tõendus (suund ja tugevuse ettepanek vilets → hea). Ajaraam, ulatus ja seos äärmusnähtustega on ettepanekud, mida eksperdid ei ole valideerinud. Tegevuspõhist hinnangut ei ole. Linna-, vee- ja mereökosüsteemid ja nende kirjandus (CleanEST, WetEST) ei kuulu ELME2 maismaakihtidesse ja on hindamata.",
    },
    {
        "id": "L6",
        "allikas": "lähteülesanne",
        "nouue": "Kvantitatiivselt hinnata ainult otsese mõjuga tegevusi; kaudseid (nõustamine, teavitus) mitte.",
        "staatus": WAIT,
        "kus": "Stsenaarium",
        "kommentaar": "Tegevuste liigitamine vajab nimekirja. Stsenaariumi kalkulaator on valmis: tüüp, seisundi muutus ja pindala → muutus teenuste kaupa.",
    },
    {
        "id": "L7",
        "allikas": "lähteülesanne",
        "nouue": "Stsenaarium: ökoloogiliselt viletsas ja heas seisundis ökosüsteemide loodushüve keskväärtuste võrdlus ökosüsteemi tüübi ja alamtüübi kaupa (ELME2 baaskaardi klassid).",
        "staatus": DONE,
        "kus": "Tulemustabel; Stsenaarium",
        "kommentaar": "Keskväärtused hea / keskmine / vilets iga ELME2 baaskaardi tüübi kohta. Seisundiklasside vastavus (A–F → hea/keskmine/vilets) on lähtekasu taustatabeliga kontrollitud ja ühtib. Tabeli 3.1 (Helm et al. 2023) nimekirjaga ei ole klassinimesid võrreldud, sest aruanne ei ole meil.",
    },
    {
        "id": "L8",
        "allikas": "lähteülesanne",
        "nouue": "Loodushüve väärtus biofüüsikalise indikaatori kogusena ja võimalusel majandusliku väärtusena.",
        "staatus": DONE,
        "kus": "Tulemustabel; Excel",
        "kommentaar": "Mõlemad on veergudena, kus kiht olemas. Rahaline kiht puudub: niidu ja soo puitse biomassi süsinik, mikrokliima, elupaik, tolmeldamine, põllu toiduteenus, orgaanilise süsiniku ärakanne, kahjuritõrje (eraldi rasterit ei ole).",
    },
    {
        "id": "L9",
        "allikas": "lähteülesanne",
        "nouue": "Kui ELME kaardikihtidest ei saa hinnata, lähtuda teaduskirjandusest; muutuste stsenaariumid Helm et al. 2020 ja 2023 lõpparuannetest.",
        "staatus": TODO,
        "kus": "–",
        "kommentaar": "Kirjandusülevaadet ei ole tehtud; mõlemad aruanded ei ole selle töö sisendiks. Tegevuse seose ELME stsenaariumidega peab tegema ekspert.",
    },
    {
        "id": "L10",
        "allikas": "lähteülesanne",
        "nouue": "Tulemused esitada struktuuris, mida saab kasutada sotsiaalmajandusliku mõju hindamise sisendina.",
        "staatus": DONE,
        "kus": "Excel; CSV; JSON",
        "kommentaar": "Pikad (masinloetavad) tabelid iga väärtuse katvuse, esinemise osa ja staatusega ning laiad tabelid. Meetmepõhine ühildatavus sõltub nimekirjast (L3).",
    },
    {
        "id": "L11",
        "allikas": "lähteülesanne",
        "nouue": "Töö vormistatakse raporti ja andmetabelina; tegevuste koondtabelis on 13 nõutud veergu (meede, ökosüsteem, hüve, suund ja tugevus, ajaline avaldumine, biofüüsikaline näitaja, rahaline väärtus, kasutatavus kulu-kasu võrdluses, meetod ja allikas, topeltarvestuse risk, ebakindlus, märkus hindajale).",
        "staatus": PART,
        "kus": "Excel (mall); docs/",
        "kommentaar": "Andmetabel ja tegevuste koondtabeli mall (veerud ja rippmenüüd) on olemas. Täidetud tegevuste ridu ja vormistatud lõppraportit ei ole.",
    },
    {
        "id": "L12",
        "allikas": "lähteülesanne",
        "nouue": "Esialgne versioon KLIMile tagasisideks; lõppraport ja andmetabel 4. novembril 2026.",
        "staatus": WAIT,
        "kus": "Avaleht",
        "kommentaar": "See leht ja Excel on esialgne versioon tagasisideks. Tähtaeg 4. november 2026.",
    },
    {
        "id": "L13",
        "allikas": "lähteülesanne",
        "nouue": "Sotsiaalmajandusliku mõju hindamine ja kaasneva kasu hindamine peavad olema meetmepõhiselt võrreldavad ja ühildatavad.",
        "staatus": WAIT,
        "kus": "–",
        "kommentaar": "Sõltub meetmete nimekirjast ja teise töö tulemustest.",
    },
    {
        "id": "L14",
        "allikas": "lähteülesanne",
        "nouue": "Toetada meetmete vajalikkuse, rakendatavuse, kulutõhususe, kaasneva kasu, sotsiaalmajandusliku mõju, proportsionaalsuse ja kava koostamise põhimõtetega kooskõla hindamist.",
        "staatus": PART,
        "kus": "Stsenaarium; Kvalitatiivne",
        "kommentaar": "Kaasneva kasu osa on kaetud. Kulutõhusus ja proportsionaalsus eeldavad kulusid, mida selles töös ei ole.",
    },
    {
        "id": "L15",
        "allikas": "lähteülesanne",
        "nouue": "Ökosüsteemide kaupa väliseksperdid analüüsi valideerimiseks; tulemuste tutvustamine juhtkomisjonile.",
        "staatus": WAIT,
        "kus": "Avaleht (esitluseks)",
        "kommentaar": "Valideerimine ei ole toimunud; vt avatud küsimused.",
    },
    {
        "id": "K1",
        "allikas": "lähtekas",
        "nouue": "Aluseks ELME2 baas- ja seisundikaart ning ÖST kaardid. Ära kasuta parandatud metsaseisundit koos parandamata ÖST kaartidega: huvitab seisundi ja teenuse seos.",
        "staatus": DONE,
        "kus": "Meetod",
        "kommentaar": "Kasutatud on algset ELME2 seisundikaarti (OS_det_seisund_det_2022_5m). Metsade seisundi süsteemne viga kandub tulemustesse; see on piirang, mitte analüüsi viga (vt kriitika).",
    },
    {
        "id": "K2",
        "allikas": "lähtekas",
        "nouue": "Lisaks vilets ja hea ka keskmise ökoloogilise seisundi keskväärtus.",
        "staatus": DONE,
        "kus": "Tulemustabel",
        "kommentaar": "Keskmine on igal real hea ja vilets kõrval.",
    },
    {
        "id": "K3",
        "allikas": "lähtekas",
        "nouue": "Keskväärtused iga detailse ELME2 ökosüsteemitüübi ja seisundiklassi kohta (rannaniit, loopealne, sinihelmikaniit jne) ja analüüsitud ökosüsteemide pindala (ha).",
        "staatus": DONE,
        "kus": "Tulemustabel (Tüübid × seisund); Excel",
        "kommentaar": "Pindala on baaskaardi pindala hektarites (5 m piksel). Veerg „kate“ pikas tabelis näitab, kui suur osa pikslitest on kehtiv.",
    },
    {
        "id": "K4",
        "allikas": "lähtekas",
        "nouue": "Tabeli struktuur: rida = tüüp + seisund; veerud = pindala ja iga teenuse keskmine kogus ning hind.",
        "staatus": DONE,
        "kus": "Excel (Tüübid × seisund)",
        "kommentaar": "Struktuur vastab näitele; kogus ja hind on iga teenuse juures kõrvuti, kus rahaline kiht on olemas.",
    },
    {
        "id": "K5",
        "allikas": "lähtekas",
        "nouue": "Kui teenust tüübis ei ole, märgi tabelis; kui seda on väga-väga vähe, järeldame, et kooslus teenust ei paku.",
        "staatus": DONE,
        "kus": "Tulemustabel",
        "kommentaar": "„ei paku“, kui nullist erinevaid piksleid on alla 1 % kehtivatest; „–“, kui kehtivaid piksleid alla 5 %. Lävi 1 % on meie otsus (lähtekas ei määratle); see on parameeter ja pikas tabelis on osakaal alles.",
    },
    {
        "id": "K6",
        "allikas": "lähtekas",
        "nouue": "Suure pildi tabel suurte ökosüsteemide kaupa: mets, soo, niit, põld, rannik; klassi „muud“ ei liideta.",
        "staatus": DONE,
        "kus": "Tulemustabel (Suured ökosüsteemid)",
        "kommentaar": "Kaalutud keskmised kehtiva pindalaga; lisaks „kokku“ read. „Asustus ja muu“ ei ole liidetud.",
    },
    {
        "id": "K7",
        "allikas": "lähtekas",
        "nouue": "Loogikakontroll: keskmine arvutada kogu klassi pindala kohta, nullid arvesse võttes (nt mustikad 25 ha-l 100 ha-st).",
        "staatus": DONE,
        "kus": "Meetod; Excel (Loe mind)",
        "kommentaar": "Nullid on kehtivad väärtused. Parandus: eelmine versioon jättis nullid välja kihtidest, kus tabelis deklareeritud NoData on 0 (söögiseente hind, õhusaaste puhverdamine, niidu ja soo puitne biomass); neis kihtides on 0 nüüd kehtiv null.",
    },
    {
        "id": "K8",
        "allikas": "lähtekas",
        "nouue": "Hinnata kõiki usaldusväärseid ELME2 ÖST kihte kaustast GIS-lõplik, vajadusel ELME1.",
        "staatus": PART,
        "kus": "Teenuste kirjeldus (Excel)",
        "kommentaar": "Meil on ligipääs ainult arhiivile (kihitabeli eval = TRUE, 31 kihti) ja lisaks neli kihti, mida lähtekas eeldab (kaks mulla süsiniku hinda, metsa süsiniku hind, sidusus). Kausta GIS-lõplik sisu ei ole kontrollitud.",
    },
    {
        "id": "K9",
        "allikas": "lähtekas",
        "nouue": "Elupaigateenus: üks sidusus (nt 1 km raadiusega loodusmaastik); komponendikihte (sidusus, seisund, unikaalsus) ei ole vaja; puidutooraine välja.",
        "staatus": DONE,
        "kus": "Teenuste kirjeldus",
        "kommentaar": "Lisatud on sidusus_1km_2022_10m ja kiht elupaigahuve_pakkumine. Raadius ja tõlgendus tuleb kinnitada; sidusus on arvutatud heas seisundis ökosüsteemide osakaalust, seega on seos seisundiga osaliselt definitsiooniline.",
    },
    {
        "id": "K10",
        "allikas": "lähtekas",
        "nouue": "Arvestada kihtide rastrisuurusi, NoData väärtusi ja loogikaid (nt lokaalne kliima negatiivne väärtus).",
        "staatus": PART,
        "kus": "Meetod; Teenuste kirjeldus",
        "kommentaar": "NoData on kihi kaupa tabelist; baaskaart on 5 m, teenused 5, 10 või 930 m. 930 m kihtidel on hinnang uuriv (segumudel). Mikrokliima kiht (kliimaregulatsioon) kasutab väiksemat väärtust paremaks; kihtidest on negatiivne väärtus ainult pohlade saagikuse skaalal (−1), mis on tabeli järgi kehtiv.",
    },
]

CRITIQUE: list[tuple[str, str]] = [
    (
        "Ruumiline võrdlus ei ole ajaline muutus",
        "Keskväärtuste vahe viletsas ja heas seisundis on kahe erineva koha võrdlus samal ajahetkel. See ei ole põhjuslik hinnang sellele, mida taastamine konkreetsel alal annab: seisundid erinevad ka mulla, kliima ja varasema maakasutuse poolest, osa viletsas seisus alasid ei jõua kunagi heasse seisundisse ja taastumine võtab aastakümneid. Meie täpsem (paaritatud) hinnang võrdleb seisundeid sama 1 km ploki ja alamökosüsteemi sees ning vähendab seda eelarvamust, kuid ei kõrvalda seda.",
    ),
    (
        "Mõned teenused on seisundiga seotud definitsiooni tõttu",
        "Mikrokliima ja kahjuritõrje väärtus on arvutatud baaskaardi klassist või põllu seisundiklassist, põllu toiduteenuse väärtusklass langeb kokku seisundiklassiga, sidusus arvestab heas seisundis alade osakaalu ning loodusturismi kaalud koondavad heas seisus ökosüsteeme. Neil kihtidel on seisundite erinevus osaliselt kihi ehituse tulemus, mitte iseseisev tõend. Sellised kihid on tabelites märgitud (†) ja η² näitaja on lehel „Statistiline analüüs“.",
    ),
    (
        "Rahalised väärtused ei ole omavahel summeeritavad ega ühtlasi piirkasu",
        "Virgestuse (320 mln EUR), loodusturismi (637 mln EUR) ja õhusaaste puhverdamise (20,88 mln EUR) rahalised kihid jagavad riigi aastase kogusumma ruumis kaalude alusel. Ühe hektari seisundi paranemine ei muuda neid kogusummasid, seega ei ole nende hektari väärtused kasutatavad kasuna otseses kulu-kasu võrdluses ilma täiendava põhjenduseta. Süsiniku väärtused on varu (EUR/ha), seente ja marjade väärtused on aastane potentsiaalne tulu (EUR/ha/a); neid ei tohi summeerida ega võrrelda ilma ajaühikut arvestamata. Biofüüsikaline ja rahaline versioon on sama hüve (topeltarvestus).",
    ),
    (
        "Mulla süsiniku hind on kokku leppimata",
        "Kihitabeli märkus on „Hind kokku leppida“. ETS 2022 keskmine börsihind 80,68 EUR/t CO2 ja sotsiaalse kulu hind 169,77 EUR/t CO2 erinevad 2,1 korda. Tabelis on mõlemad; valik on otsus, mitte analüüsi tulemus.",
    ),
    (
        "Nullid ja NoData",
        "Kihid on loodud eri meetoditega ja NoData väärtus tähendab eri asju (0, 255, 65535, −1, −9999, NaN). Tabelis, kus NoData on 0 ja 0 tähendab „teenust ei ole“, ei ole nulli võimalik eristada puuduvast väärtusest; seal loetakse 0 kehtivaks nulliks ja teenust mitte pakkuvad tüübid jäetakse välja 1 % läve alusel. Kihi „ohusaaste_puhverdusvoime“ märkus „255 käitub kui 0“ on tõlgendatud nii. Tõlgenduse peab kinnitama kihi autor.",
    ),
    (
        "Keskmine peidab jaotuse",
        "Paljud teenused on nullidega täidetud ja väga viltused (marjad, seened, erosioon). Keskmine kogu pindala kohta on õige suurus sotsiaalmajanduslikuks summeerimiseks, kuid peidab, kas teenus esineb vähestes kohtades suurelt või paljudes väikesena. Seetõttu on iga väärtuse juures esinemise osa ja lehel jaotused.",
    ),
    (
        "ELME2 metsaseisundi viga",
        "Lähtekasu järgi on ELME2 seisundikaardil süsteemne metsade seisundi viga. Me kasutame algset kaarti, et seisund ja teenused vastaksid üksteisele, kuid metsade (suurim ala) tulemused kannavad seda viga. Parandatud seisundikaardiga arvutamine nõuab parandatud teenuste kaarte.",
    ),
    (
        "Aastate ja eraldusvõimete erinevus",
        "Seisund on 2022 (5 m); loodusannid (marjad, seened, kasemahl) on 2020. aasta ELME1 kihid ja teenuste eraldusvõime on 5, 10 või 930 m. Baaskaart võetakse teenuse ruudustikule lähima naabri meetodil.",
    ),
    (
        "Mudelkihid, mitte mõõtmised",
        "Kõik teenused on modelleeritud kihid; nende endi ebakindlust ei ole teada. Bootstrap-usaldusvahemikud kirjeldavad ainult valimivigu ja ruumilist sõltuvust, mitte mudeli ebakindlust.",
    ),
    (
        "Ainult maismaa",
        "ELME2 kihtidega saab katta ainult maismaaökosüsteeme (rohumaad, sood, metsad, põllud, rannikud). Linna-, mere-, jõgede ja järvede ökosüsteeme lähteülesanne nõuab, kuid need vajavad teadus­kirjandust või teisi projekte.",
    ),
    (
        "Kvalitatiivne osa vajab eksperte",
        "Mõju tugevuse, ajaraamistiku ja ulatuse hinnangud on kokku lepitud ettepanekud (lävendid ja skaalad ei tule andmetest). Neid peab ökosüsteemi ekspert enne KLIMile esitamist kinnitama.",
    ),
    (
        "Ajakava",
        "Lõppraport on KLIMile tähtaja järgi 4. novembril 2026. Meetmete nimekirjata ei saa täita tegevuste koondtabelit; see on kitsaskoht.",
    ),
]

QUESTIONS: list[str] = [
    "Kliimaministeeriumi kinnitatud meetmete ja tegevuste nimekiri (lähteülesande järgi augustis): kas see on olemas ja kus?",
    "Millised kihid on kaustas Y:\\...\\GIS-lõplik (ja ELME1-st) peale arhiivi kihtide? Arhiivis on neli faili, mis ei ole ametlikus tabelis (Elupaigahuve/.tif nimeta, johvikad_hind_2022_10m_cog_mode.tif, sidusus_2020_100m.tif, output.fgb).",
    "Mulla süsiniku hind: ETS 80,68 või sotsiaalse kulu hind 169,77 EUR/t CO2? Kas kasutada varu väärtust või varu muutust ajas?",
    "„255 käitub kui 0“ (ohusaaste puhverdamine): kas 255 on mitte-hinnatud ala (nulliks) või tegelik väärtus?",
    "Kas 1 % on sobiv lävi teenuse „väga-väga vähe“ jaoks?",
    "Sidusus: kas 1 km raadius on sobiv ja kas kihil on skaala 0–100 (osakaal)?",
    "Mõju tugevuse (nõrk / keskmine / tugev) ja ajaraamistiku (lühi- / keskpikk / pikaajaline) lävendid.",
    "Kas ökosüsteemitüüpide nimed (RAT) vastavad Helm et al. 2023 tabelile 3.1? Aruannet meil ei ole.",
    "Kas rannikud (seisundita) tuleb esitada ainult keskmisena, kuna vilets → hea stsenaariumi nende jaoks ei saa arvutada?",
    "Mikrokliima kiht on baaskaardi klassi tabelväärtus; kas seda tohib kasutada seisundi ja teenuse seose tõendina?",
    "Kas rahalised kihid, mis on riigi kogusumma jaotus (virgestus, loodusturism, õhusaaste), tuleb sotsiaalmajanduslikust võrdlusest välja jätta?",
    "Litsents: ELME/KAUR andmete kasutustingimused enne tulemuste taasavaldamist.",
]
