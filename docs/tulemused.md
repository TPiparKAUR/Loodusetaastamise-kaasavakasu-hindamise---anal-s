# Tulemuste kokkuvõte

Genereeritud `oks.report.write_results`-ga failist `data/tulemused/paarid.parquet`. Meetod: [metoodika.md](metoodika.md).

## 1. Ulatus

* 34 teenust, 43 ökosüsteemi/alamökosüsteemi üksust (taseme kaupa), 3697 seisundipaari hinnangut.
* Parameetrid: klaster 10×10 km, 4000 bootstrapi, min 1,0 ha, FDR α = 0,05.

| Tase | Hinnanguid | Paaritatud: piisavalt andmeid | …neist olulisi (q<0,05) | Paaritamata: piisavalt andmeid | …neist olulisi | Oluline mõlemal ja sama märk |
|---|---|---|---|---|---|---|
| Ökosüsteem | 399 | 364 | 219 | 335 | 277 | 171 |
| Alamökosüsteem | 3298 | 2508 | 1117 | 2708 | 1496 | 1016 |

## 2. Ökosüsteemide tase: mitu teenust muutub seisundi paranedes

Paaritatud hinnang, ainult hinnangud, kus on piisavalt andmeid. „Kasvab” = Δ > 0 ja q < 0,05; „väheneb” = Δ < 0 ja q < 0,05.

| Ökosüsteem | Seisundipaar | Teenuseid | Kasvab | Väheneb | Ei ole oluline |
|---|---|---|---|---|---|
| Rohumaad | vilets → keskmine | 31 | 7 | 6 | 18 |
| Rohumaad | keskmine → hea | 31 | 8 | 6 | 17 |
| Rohumaad | vilets → hea | 31 | 8 | 13 | 10 |
| Sood | vilets → keskmine | 29 | 10 | 9 | 10 |
| Sood | keskmine → hea | 28 | 5 | 5 | 18 |
| Sood | vilets → hea | 28 | 11 | 9 | 8 |
| Metsad | vilets → keskmine | 32 | 20 | 9 | 3 |
| Metsad | keskmine → hea | 32 | 20 | 4 | 8 |
| Metsad | vilets → hea | 32 | 21 | 6 | 5 |
| Põllumaad | vilets → keskmine | 30 | 13 | 5 | 12 |
| Põllumaad | keskmine → hea | 30 | 9 | 2 | 19 |
| Põllumaad | vilets → hea | 30 | 8 | 5 | 17 |

## 3. Suurimad muutused (vilets → hea, paaritatud, olulised)

### Rohumaad

| Teenus | Ühik | Keskm. vilets | Keskm. hea | Δ | Δ % | 95 % CI (Δ) | Märkus |
|---|---|---|---|---|---|---|---|
| Elupaikade säilitamine looduslikele liikidele | indeks 0-10 | 3,32 | 8,07 | 2,64 | +51 % | 2,56 … 2,72 |  |
| Ökosüsteemide tugi tolmeldajatele | indeks 0-1 | 0,144 | 0,172 | 0,039 | +24 % | 0,032 … 0,047 |  |
| Maismaaökosüsteemide summaarne virgestusväärtus | skoor | 15,4 | 26,0 | 5,06 | +24 % | 4,64 … 5,48 |  |
| Loodusturismi hüve – looduslikkuse suhteline väärtus loodusobjektina | skoor | 48,7 | 80,4 | 13,7 | +20 % | 13,0 … 14,4 |  |
| Fosfori ärakanne | kg/ha/a | 0,909 | 0,116 | -0,080 | -46 % | -0,148 … -0,029 |  |
| Niidu puitsesse biomassi seotud süsiniku varu | t C/ha | 8,83 | 5,98 | -10,2 | -54 % | -11,4 … -9,11 |  |
| Mustikate ja pohlade potentsiaalne tulu | EUR/ha/a | 2,38 | 0,709 | -1,01 | -67 % | -1,94 … -0,335 |  |
| Mustikate ja pohlade potentsiaalne saagikus | kg/ha | 0,951 | 0,283 | -0,405 | -67 % | -0,775 … -0,134 |  |

### Sood

| Teenus | Ühik | Keskm. vilets | Keskm. hea | Δ | Δ % | 95 % CI (Δ) | Märkus |
|---|---|---|---|---|---|---|---|
| Elupaikade säilitamine looduslikele liikidele | indeks 0-10 | 3,50 | 8,73 | 2,42 | +41 % | 2,35 … 2,50 |  |
| Maismaaökosüsteemide summaarne virgestusväärtus | skoor | 13,1 | 26,2 | 4,20 | +20 % | 3,99 … 4,42 |  |
| Loodusturismi hüve rahaline väärtus tarbijakulude alusel | EUR/ha | 159,7 | 226,5 | 33,6 | +18 % | 32,1 … 35,2 |  |
| Loodusturismi hüve – looduslikkuse suhteline väärtus loodusobjektina | skoor | 51,3 | 72,1 | 10,6 | +18 % | 10,3 … 10,8 |  |
| Soo puitsesse biomassi seotud süsiniku varu | t C/ha | 4,24 | 1,77 | -1,67 | -44 % | -1,91 … -1,45 |  |
| Orgaanilise süsiniku ärakanne | kg/ha/a | 0,223 | 0,017 | -0,019 | -51 % | -0,027 … -0,013 |  |
| Söögiseentest saadav potentsiaalne tulu | EUR/ha/a | 18,7 | 0,363 | -32,1 | -99 % | -34,2 … -30,2 |  |
| Söögiseente potentsiaalne saagikus | kg/ha | 4,18 | 0,081 | -7,22 | -99 % | -7,66 … -6,78 |  |

### Metsad

| Teenus | Ühik | Keskm. vilets | Keskm. hea | Δ | Δ % | 95 % CI (Δ) | Märkus |
|---|---|---|---|---|---|---|---|
| Metsa puitsesse biomassi seotud süsiniku varu rahaline väärtus (aasta keskmine ETS börsihind) | EUR/ha | 7 636 | 24 354 | 19 147 | +215 % | 18 603 … 19 674 |  |
| Metsa puitsesse biomassi seotud süsiniku varu | t C/ha | 34,4 | 86,4 | 62,0 | +165 % | 60,1 … 63,9 |  |
| Elupaikade säilitamine looduslikele liikidele | indeks 0-10 | 2,76 | 8,16 | 4,20 | +125 % | 4,18 … 4,21 |  |
| Söögiseentest saadav potentsiaalne tulu | EUR/ha/a | 96,5 | 189,2 | 82,7 | +74 % | 78,2 … 86,8 |  |
| Pohlade potentsiaalne saagikus | kg/ha | 0,051 | 0,668 | -0,048 | -11 % | -0,068 … -0,028 |  |
| Orgaanilise süsiniku ärakanne | kg/ha/a | 1,07 | 0,574 | -0,166 | -20 % | -0,264 … -0,084 |  |
| Fosfori ärakanne | kg/ha/a | 0,586 | 0,115 | -0,247 | -62 % | -0,327 … -0,176 |  |
| Fosfori mullaerosiooniga ärakande hind | EUR/ha/a | 2,34 | 0,461 | -0,987 | -62 % | -1,31 … -0,706 |  |

### Põllumaad

| Teenus | Ühik | Keskm. vilets | Keskm. hea | Δ | Δ % | 95 % CI (Δ) | Märkus |
|---|---|---|---|---|---|---|---|
| Kahjuritõrje vajaduse vähenemine | arvatavasti % (väli pestits_vahenemine) | 8,74 | 75,7 | 54,8 | +291 % | 51,7 … 57,7 |  |
| Elupaikade säilitamine looduslikele liikidele | indeks 0-10 | 1,22 | 3,45 | 1,62 | +101 % | 1,52 … 1,73 |  |
| Maismaaökosüsteemide summaarne virgestusväärtus | skoor | 7,65 | 14,1 | 3,18 | +31 % | 2,86 … 3,54 |  |
| Maismaaökosüsteemide summaarne virgestusväärtus tarbijakulude alusel | EUR/ha | 47,3 | 70,8 | 10,3 | +18 % | 8,95 … 11,9 |  |
| Loodusturismi hüve rahaline väärtus tarbijakulude alusel | EUR/ha | 134,2 | 147,0 | 1,68 | +1 % | 0,744 … 2,65 |  |
| Põllumajanduslike ökosüsteemide reaalboniteedid | reaalboniteet (väli boniteet) | 43,6 | 38,2 | -0,924 | -2 % | -1,67 … -0,169 |  |
| Mustikate ja pohlade potentsiaalne tulu | EUR/ha/a | 0,137 | 0,089 | -0,103 | -62 % | -0,206 … -0,027 |  |
| Mustikate ja pohlade potentsiaalne saagikus | kg/ha | 0,055 | 0,036 | -0,041 | -62 % | -0,083 … -0,011 |  |

### Uuriv segumudel (930 m rastrid ja 1 km vektorruudud)

Need kihid on jämedamad kui seisundiüksus; hinnang tuleneb klasside pindalaosade lineaarsest segumudelist (metoodika § 7) ja on **uuriv**. Näidatud on kõik ökosüsteemid (vilets → hea), sõltumata olulisusest.

| Teenus | Ökosüsteem | Ühik | β vilets | β hea | Δ % | 95 % CI (Δ) | Oluline |
|---|---|---|---|---|---|---|---|
| Lammimuldade taastamise kulu | Rohumaad | EUR (väli lammide_taastamise_kulu) | 4 702 | 6 634 | +41 % | 864,7 … 3 275 | jah |
| Lammimuldade taastamise kulu | Sood | EUR (väli lammide_taastamise_kulu) | 351,6 | 6 857 | +1850 % | 4 482 … 8 999 | jah |
| Lammimuldade taastamise kulu | Metsad | EUR (väli lammide_taastamise_kulu) | 1 178 | 4 659 | +296 % | 2 554 … 4 372 | jah |
| Lammimuldade taastamise kulu | Põllumaad | EUR (väli lammide_taastamise_kulu) | 2 545 | 3 722 | +46 % | -1 098 … 3 516 | ei |
| Vee puhastamise potentsiaali kaldapuhvrite poolt rahaline väärtus | Rohumaad | EUR/ha | 5,49 | 4,97 | -9 % | -0,805 … -0,286 | jah |
| Vee puhastamise potentsiaali kaldapuhvrite poolt rahaline väärtus | Sood | EUR/ha | 6,75 | 5,84 | -14 % | -1,26 … -0,584 | jah |
| Vee puhastamise potentsiaali kaldapuhvrite poolt rahaline väärtus | Metsad | EUR/ha | 6,59 | 5,93 | -10 % | -0,914 … -0,401 | jah |
| Vee puhastamise potentsiaali kaldapuhvrite poolt rahaline väärtus | Põllumaad | EUR/ha | 6,54 | 5,64 | -14 % | -1,48 … -0,174 | jah |
| Vee puhastamise potentsiaal kaldapuhvrite poolt | Rohumaad | kg/ha/a | 1,37 | 1,24 | -9 % | -0,201 … -0,071 | jah |
| Vee puhastamise potentsiaal kaldapuhvrite poolt | Sood | kg/ha/a | 1,69 | 1,46 | -14 % | -0,314 … -0,146 | jah |
| Vee puhastamise potentsiaal kaldapuhvrite poolt | Metsad | kg/ha/a | 1,65 | 1,48 | -10 % | -0,229 … -0,100 | jah |
| Vee puhastamise potentsiaal kaldapuhvrite poolt | Põllumaad | kg/ha/a | 1,64 | 1,41 | -14 % | -0,370 … -0,043 | jah |

## 4. Paaritatud ja paaritamata hinnang

* Võrreldavaid hinnanguid: 2836; sama märgiga: 2289 (81 %).
* Mõlemal hinnangul olulised, kuid **vastupidise märgiga**: 11 (nende puhul muudab asukoha/koosseisu kontroll järelduse suunda).

| Teenus | Üksus | Seisundipaar | Δ paaritatud | Δ paaritamata |
|---|---|---|---|---|
| Õhusaaste puhverdamisvõime | Rohumaad | vilets → keskmine | -0,003 | 0,031 |
| Õhusaaste puhverdamisvõime rahaline väärtus | Rohumaad | vilets → keskmine | -0,010 | 0,093 |
| Ökosüsteemide tugi tolmeldajatele | Sood | vilets → keskmine | -0,017 | 0,007 |
| Ökosüsteemide tugi tolmeldajatele | Sood | vilets → hea | -0,020 | 0,008 |
| Pohlade potentsiaalne saagikus | Metsad | vilets → keskmine | -0,038 | 0,210 |
| Pohlade potentsiaalne saagikus | Metsad | vilets → hea | -0,048 | 0,617 |
| Maismaaökosüsteemide summaarne virgestusväärtus | Sood | keskmine → hea | -0,201 | 2,27 |
| Maismaaökosüsteemide summaarne virgestusväärtus | alam 20200 | keskmine → hea | -0,371 | 2,11 |
| Maismaaökosüsteemide summaarne virgestusväärtus | alam 20300 | keskmine → hea | -0,266 | 1,79 |
| Maismaaökosüsteemide summaarne virgestusväärtus | alam 20400 | keskmine → hea | -0,163 | 2,10 |
| Maismaaökosüsteemide summaarne virgestusväärtus tarbijakulude alusel | alam 20200 | keskmine → hea | -1,49 | 6,86 |

## 5. Mudelipõhisus (η² ≥ 0,9)

Kihid ja ökosüsteemid, kus ≥ 90 % pikslitaseme dispersioonist on seletatav baaskaardi klassiga. Muutus seisundi vahel on neil osaliselt definitsiooniline.

| Teenus | Ökosüsteem | η² (klass) | η² (seisund alamökosüsteemi sees) |
|---|---|---|---|
| Elupaikade säilitamine looduslikele liikidele | Sood | 0,93 | 0,68 |
| Mikrokliima reguleerimine (temperatuuri erinevuse määr) | Rohumaad | 1,00 | – |
| Mikrokliima reguleerimine (temperatuuri erinevuse määr) | Sood | 1,00 | – |
| Mikrokliima reguleerimine (temperatuuri erinevuse määr) | Metsad | 1,00 | 0,00 |
| Mikrokliima reguleerimine (temperatuuri erinevuse määr) | Põllumaad | 1,00 | – |
| Õhusaaste puhverdamisvõime | Põllumaad | 1,00 | 0,00 |
| Õhusaaste puhverdamisvõime rahaline väärtus | Põllumaad | 1,00 | 0,00 |
| Ökosüsteemide tugi tolmeldajatele | Metsad | 0,90 | 0,13 |

## 6. Tundlikkus

Põhijooksu olulistest hinnangutest (paaritatud) säilis oluliseks sama märgiga:

| Variant | Tase | Võrreldavaid | Põhijooksu olulisi | Säilinud | Säilinud % | Uusi olulisi | Spearman ρ (Δ) |
|---|---|---|---|---|---|---|---|
| klaster5km | okosusteem | 364 | 219 | 217 | +99 % | 1 | 1,000 |
| klaster5km | alam | 2508 | 1117 | 1104 | +99 % | 30 | 1,000 |
| klaster20km | okosusteem | 364 | 219 | 210 | +96 % | 2 | 1,000 |
| klaster20km | alam | 2508 | 1117 | 1099 | +98 % | 22 | 1,000 |
| ala_0_25ha | okosusteem | 364 | 219 | 218 | +100 % | 7 | 0,991 |
| ala_0_25ha | alam | 2508 | 1117 | 1096 | +98 % | 69 | 0,946 |
| ala_4ha | okosusteem | 363 | 218 | 209 | +96 % | 4 | 0,927 |
| ala_4ha | alam | 1779 | 924 | 817 | +88 % | 22 | 0,893 |
| seeme_2 | okosusteem | 364 | 219 | 217 | +99 % | 0 | 1,000 |
| seeme_2 | alam | 2508 | 1117 | 1110 | +99 % | 9 | 1,000 |

Variandid: `klaster5km`, `klaster20km` (bootstrap-klastri suurus), `ala_0_25ha`, `ala_4ha` (minimaalne ala stratumis), `seeme_2` (teine juhuslik seeme).
