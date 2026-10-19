# Tulemuste kokkuvõte

Genereeritud `oks.report.write_results`-ga failist `data/tulemused/paarid.parquet`. Meetod: [metoodika.md](metoodika.md).

## 1. Ulatus

* 30 teenust, 43 ökosüsteemi/alamökosüsteemi üksust (taseme kaupa), 3020 seisundipaari hinnangut.
* Parameetrid: klaster 10×10 km, 4000 bootstrapi, min 1,0 ha, FDR α = 0,05.

| Tase | Hinnanguid | Paaritatud: piisavalt andmeid | …neist olulisi (q<0,05) | Paaritamata: piisavalt andmeid | …neist olulisi | Oluline mõlemal ja sama märk |
|---|---|---|---|---|---|---|
| Ökosüsteem | 333 | 293 | 191 | 269 | 232 | 141 |
| Alamökosüsteem | 2687 | 1922 | 938 | 2122 | 1258 | 852 |

## 2. Ökosüsteemide tase: mitu teenust muutub seisundi paranedes

Paaritatud hinnang, ainult hinnangud, kus on piisavalt andmeid. „Kasvab” = Δ > 0 ja q < 0,05; „väheneb” = Δ < 0 ja q < 0,05.

| Ökosüsteem | Seisundipaar | Teenuseid | Kasvab | Väheneb | Ei ole oluline |
|---|---|---|---|---|---|
| Rohumaad | vilets → keskmine | 26 | 6 | 6 | 14 |
| Rohumaad | keskmine → hea | 26 | 8 | 5 | 13 |
| Rohumaad | vilets → hea | 26 | 7 | 12 | 7 |
| Sood | vilets → keskmine | 24 | 9 | 8 | 7 |
| Sood | keskmine → hea | 22 | 4 | 4 | 14 |
| Sood | vilets → hea | 22 | 10 | 8 | 4 |
| Metsad | vilets → keskmine | 26 | 16 | 9 | 1 |
| Metsad | keskmine → hea | 26 | 16 | 4 | 6 |
| Metsad | vilets → hea | 26 | 17 | 6 | 3 |
| Põllumaad | vilets → keskmine | 23 | 9 | 5 | 9 |
| Põllumaad | keskmine → hea | 23 | 8 | 2 | 13 |
| Põllumaad | vilets → hea | 23 | 7 | 5 | 11 |

## 3. Suurimad muutused (vilets → hea, paaritatud, olulised)

### Rohumaad

| Teenus | Ühik | Keskm. vilets | Keskm. hea | Δ | Δ % | 95 % CI (Δ) | Märkus |
|---|---|---|---|---|---|---|---|
| Elupaikade säilitamine looduslikele liikidele | indeks 0-10 | 3,32 | 8,07 | 2,64 | +51 % | 2,56 … 2,72 |  |
| Ökosüsteemide tugi tolmeldajatele | indeks 0-1 | 0,144 | 0,172 | 0,039 | +24 % | 0,032 … 0,047 |  |
| Maismaaökosüsteemide summaarne virgestusväärtus | skoor | 15,4 | 26,0 | 5,06 | +24 % | 4,64 … 5,48 |  |
| Loodusturismi hüve – looduslikkuse suhteline väärtus loodusobjektina | skoor | 48,7 | 80,4 | 13,7 | +20 % | 13,0 … 14,4 |  |
| Fosfori mullaerosiooniga ärakande hind | EUR/ha/a | 3,64 | 0,463 | -0,319 | -46 % | -0,593 … -0,118 |  |
| Fosfori ärakanne | kg/ha/a | 0,909 | 0,116 | -0,080 | -46 % | -0,148 … -0,029 |  |
| Mustikate ja pohlade potentsiaalne tulu | EUR/ha/a | 2,38 | 0,709 | -1,01 | -67 % | -1,94 … -0,335 |  |
| Mustikate ja pohlade potentsiaalne saagikus | kg/ha | 0,951 | 0,283 | -0,405 | -67 % | -0,775 … -0,134 |  |

### Sood

| Teenus | Ühik | Keskm. vilets | Keskm. hea | Δ | Δ % | 95 % CI (Δ) | Märkus |
|---|---|---|---|---|---|---|---|
| Elupaikade säilitamine looduslikele liikidele | indeks 0-10 | 3,50 | 8,73 | 2,42 | +41 % | 2,35 … 2,50 |  |
| Maismaaökosüsteemide summaarne virgestusväärtus | skoor | 13,1 | 26,2 | 4,20 | +20 % | 3,99 … 4,42 |  |
| Loodusturismi hüve rahaline väärtus tarbijakulude alusel | EUR/ha | 159,7 | 226,5 | 33,6 | +18 % | 32,1 … 35,2 |  |
| Loodusturismi hüve – looduslikkuse suhteline väärtus loodusobjektina | skoor | 51,3 | 72,1 | 10,6 | +18 % | 10,3 … 10,8 |  |
| Fosfori mullaerosiooniga ärakande hind | EUR/ha/a | 0,028 | 0,002 | -0,002 | -41 % | -0,002 … -0,001 |  |
| Fosfori ärakanne | kg/ha/a | 0,007 | 0,001 | -0,000 | -41 % | -0,001 … -0,000 |  |
| Orgaanilise süsiniku ärakanne | kg/ha/a | 0,223 | 0,017 | -0,019 | -51 % | -0,027 … -0,013 |  |
| Söögiseente potentsiaalne saagikus | kg/ha | 4,18 | 0,081 | -7,22 | -99 % | -7,66 … -6,78 |  |

### Metsad

| Teenus | Ühik | Keskm. vilets | Keskm. hea | Δ | Δ % | 95 % CI (Δ) | Märkus |
|---|---|---|---|---|---|---|---|
| Metsa puitsesse biomassi seotud süsiniku varu | t C/ha | 34,4 | 86,4 | 62,0 | +165 % | 60,1 … 63,9 |  |
| Elupaikade säilitamine looduslikele liikidele | indeks 0-10 | 2,76 | 8,16 | 4,20 | +125 % | 4,18 … 4,21 |  |
| Söögiseente potentsiaalne saagikus | kg/ha | 22,0 | 42,2 | 18,2 | +72 % | 17,2 … 19,1 |  |
| Söögiseentest saadav potentsiaalne tulu | EUR/ha/a | 110,2 | 206,2 | 79,4 | +64 % | 74,9 … 83,8 |  |
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

* Võrreldavaid hinnanguid: 2179; sama märgiga: 1722 (79 %).
* Mõlemal hinnangul olulised, kuid **vastupidise märgiga**: 11 (nende puhul muudab asukoha/koosseisu kontroll järelduse suunda).

| Teenus | Üksus | Seisundipaar | Δ paaritatud | Δ paaritamata |
|---|---|---|---|---|
| Õhusaaste puhverdamisvõime | Rohumaad | vilets → keskmine | -0,003 | 0,031 |
| Õhusaaste puhverdamisvõime rahaline väärtus | Rohumaad | vilets → keskmine | -0,010 | 0,095 |
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
| Ökosüsteemide tugi tolmeldajatele | Metsad | 0,90 | 0,13 |

## 6. Tundlikkus

Põhijooksu olulistest hinnangutest (paaritatud) säilis oluliseks sama märgiga:

| Variant | Tase | Võrreldavaid | Põhijooksu olulisi | Säilinud | Säilinud % | Uusi olulisi | Spearman ρ (Δ) |
|---|---|---|---|---|---|---|---|
| klaster5km | okosusteem | 293 | 191 | 191 | +100 % | 4 | 1,000 |
| klaster5km | alam | 1922 | 938 | 928 | +99 % | 19 | 1,000 |
| klaster20km | okosusteem | 293 | 191 | 184 | +96 % | 1 | 1,000 |
| klaster20km | alam | 1922 | 938 | 915 | +98 % | 18 | 1,000 |
| ala_0_25ha | okosusteem | 293 | 191 | 190 | +99 % | 6 | 0,978 |
| ala_0_25ha | alam | 1922 | 938 | 919 | +98 % | 56 | 0,957 |
| ala_4ha | okosusteem | 291 | 190 | 181 | +95 % | 4 | 0,946 |
| ala_4ha | alam | 1357 | 759 | 675 | +89 % | 20 | 0,916 |
| seeme_2 | okosusteem | 293 | 191 | 191 | +100 % | 0 | 1,000 |
| seeme_2 | alam | 1922 | 938 | 931 | +99 % | 7 | 1,000 |

Variandid: `klaster5km`, `klaster20km` (bootstrap-klastri suurus), `ala_0_25ha`, `ala_4ha` (minimaalne ala stratumis), `seeme_2` (teine juhuslik seeme).
