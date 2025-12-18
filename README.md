# Sölle Preekgenerator

Een Large Language Model (LLM)-gestuurd systeem voor het genereren van preken in de stijl en theologische traditie van **Dorothee Sölle** (1929–2003), de Duitse politiek theologe, dichteres en mysticus.

## Inhoudsopgave

- [Over dit project](#over-dit-project)
- [Wie was Dorothee Sölle?](#wie-was-dorothee-sölle)
- [De scripts](#de-scripts)
- [Installatie](#installatie)
- [Gebruik](#gebruik)
- [Bronmateriaal](#bronmateriaal)
- [Technische details](#technische-details)
- [Licentie en verantwoording](#licentie-en-verantwoording)

---

## Over dit project

Dit project bevat twee Python-scripts die samen een preekgeneratiesysteem vormen:

1. **`01__generate_sermon_solle.py`** — Genereert een nieuwe preek op basis van een bijbelgedeelte
2. **`02__feedback_sermon.py`** — Analyseert en verbetert een gegenereerde preek

De scripts gebruiken Google's Gemini AI-model, gevoed met:
- Theologische instructies gebaseerd op Sölles methode
- 28 authentieke voorbeeldpreken van Sölle (in Nederlandse vertaling)
- Actuele bijbelteksten opgehaald van debijbel.nl (HSV)

Het doel is niet om Sölle te "vervangen", maar om haar profetische stem te laten resoneren in de context van vandaag — een stem die vraagt om **mystiek én verzet**, om **tederheid én scherpte**.

### Voorbeelden

Bekijk hier twee voorbeelden van gegenereerde preken:
- [Genesis 4:1-14](output/preken/Genesis_4_1-14_improved.md)
- [Psalm 137](output/preken/Psalm_137_improved.md)

---

## Wie was Dorothee Sölle?

Dorothee Sölle (1929–2003) was een van de meest invloedrijke en controversiële theologen van de twintigste eeuw. Haar werk kenmerkt zich door een radicale verbinding van **mystieke spiritualiteit** en **politiek activisme**.

### Theologische kernpunten

| Concept | Traditionele benadering | Sölles benadering |
|---------|------------------------|-------------------|
| **Godsbeeld** | Transcendent, almachtig, heerser | Immanent, lijdend met slachtoffers, machteloos in liefde |
| **Jezus** | Plaatsvervanger (maakt ons passief) | Plaatsbekleder (roept ons op tot actie) |
| **Zonde** | Moreel falen, overtreding van regels | Apathie — het onvermogen om pijn te voelen, wegkijken |
| **Geloofstaal** | Dogmatisch, juridisch, abstract | Theo-poëzie: concreet, zintuiglijk, poëtisch |
| **Context** | Geïsoleerd van politiek | Noodzakelijkerwijs politiek; theologie = maatschappijkritiek |

### Het Politisches Nachtgebet

Vanaf 1968 organiseerde Sölle in Keulen de *Politische Nachtgebete* (Politieke Avondgebeden) — een revolutionaire liturgische vorm die vier fasen volgde:

1. **Informatie** — Feitelijke analyse van actueel onrecht (oorlog, armoede, discriminatie)
2. **Meditatie** — De bijbeltekst laten inbreken op deze realiteit
3. **Discussie** — Democratisch gesprek, geen monoloog van de predikant
4. **Actie** — Concrete stappen: petities, demonstraties, boycots

> *"Gebed zonder actie is huichelarij."* — Dorothee Sölle

### Mystiek en Verzet

In haar magnum opus *Mystiek en verzet* (1997) verbond Sölle de contemplatieve traditie met radicaal engagement. Haar "mystiek van de open ogen" zoekt God niet in de hemel, maar in de gezichten van de lijdenden. De beroemde uitspraak **"God heeft geen andere handen dan de onze"** vat haar theologie samen.

Voor een uitgebreide analyse, zie: [`misc/Solles_Theologie_en_Homiletiek.md`](misc/Solles_Theologie_en_Homiletiek.md)

---

## De scripts

### `01__generate_sermon_solle.py`

Dit script genereert een volledige preek in Sölles stijl.

**Workflow:**

```
┌─────────────────────────────────────────────────────────────┐
│  1. Bijbelreferentie invoeren (bijv. "Lukas 2:1-14")        │
├─────────────────────────────────────────────────────────────┤
│  2. Bijbeltekst ophalen van debijbel.nl (HSV)               │
├─────────────────────────────────────────────────────────────┤
│  3. Diepgaande contextanalyse genereren:                    │
│     - Exegetische analyse                                   │
│     - Actuele wereldsituatie (Gaza, klimaat, woningnood...) │
│     - Theologische verbinding (Sölles methode)              │
│     - Zintuiglijke beelden voor de preek                    │
├─────────────────────────────────────────────────────────────┤
│  4. Willekeurige voorbeeldpreken laden (stijlreferentie)    │
├─────────────────────────────────────────────────────────────┤
│  5. Preek genereren (1500-2000 woorden)                     │
│     Structuur: Landing → Botsing → Diepte → Hoop            │
├─────────────────────────────────────────────────────────────┤
│  6. Opslaan als .md bestand + logbestand                    │
└─────────────────────────────────────────────────────────────┘
```

**Belangrijke kenmerken van de gegenereerde preek:**

- **Show, don't tell** — Geen theologisch jargon, maar beelden en verhalen
- **Actueel** — Noemt concrete bedrijven, politici, plaatsen (Nederlandse context)
- **Persoonlijk** — Geschreven in de ik-vorm
- **Geen domineestaal** — Geen "Lieve gemeente" of "De Heer zegt"
- **Feitelijk correct** — Checkt technische/historische feiten

### `02__feedback_sermon.py`

Dit script analyseert een gegenereerde preek en produceert een verbeterde versie.

**Workflow:**

```
┌─────────────────────────────────────────────────────────────┐
│  1. Preek inladen (laatste of opgegeven bestand)            │
├─────────────────────────────────────────────────────────────┤
│  2. Kritische analyse op 9 dimensies (elk /10):             │
│     1. Opening/Landing                                      │
│     2. Show, don't tell                                     │
│     3. Actualiteit en concreetheid                          │
│     4. Theologische diepte                                  │
│     5. Taal en poëzie                                       │
│     6. Structuur                                            │
│     7. Lengte en diepgang                                   │
│     8. Feitelijke correctheid                               │
│     9. Nederlandse context                                  │
├─────────────────────────────────────────────────────────────┤
│  3. Verbeterde versie genereren op basis van kritiek        │
├─────────────────────────────────────────────────────────────┤
│  4. Opslaan: kritiek + verbeterde preek + log               │
└─────────────────────────────────────────────────────────────┘
```

---

## Installatie

### Vereisten

- Python 3.9+
- Google Gemini API key

### Stappen

```bash
# 1. Clone of download het project
cd solle

# 2. Installeer dependencies
pip install -r requirements.txt

# 3. Maak .env bestand met je API key
cp .env.example .env
# Bewerk .env en vul je GEMINI_API_KEY in

# 4. Test de installatie
python 01__generate_sermon_solle.py
```

### Dependencies

```
google-generativeai
python-dotenv
requests
beautifulsoup4
```

---

## Gebruik

### Een preekconcept genereren (stap 1)

```bash
python 01__generate_sermon_solle.py
```

Je wordt gevraagd om een bijbelreferentie in te voeren, bijvoorbeeld:
- `Psalm 23`
- `Lukas 2:1-14`
- `1 Johannes 3:11-18`
- `Mattheüs 5:1-12`

De output wordt opgeslagen in `output/preken/`:
- `YYYYMMDD_HHMM_bijbelref.md` — De preek
- `YYYYMMDD_HHMM_bijbelref.log` — Volledige log met analyse

### Een preekconcept verbeteren (stap 2)

```bash
# Verbeter het laatst gegenereerde preekconcept
python 02__feedback_sermon.py

# Of specificeer een bestand
python 02__feedback_sermon.py output/preken/20251218_1430_Psalm_23.md
```

Output:
- `*_critique_TIMESTAMP.md` — Gedetailleerde kritiek
- `*_improved_TIMESTAMP.md` — Verbeterde versie
- `*_feedback_TIMESTAMP.log` — Volledig log

---

## Bronmateriaal

### De 28 voorbeeldpreken

De scripts gebruiken 28 authentieke preken van Dorothee Sölle als stijlreferentie. Deze zijn afkomstig uit:

**Dorothee Sölle, *Gesammelte Werke*, Band 11: Löse die Fesseln des Unrechts, Verlag Herder (eBook; 2023)**

Dit elfde deel van Sölles verzameld werk bevat preken uit verschillende periodes van haar leven, gehouden in kerken, bij de Politische Nachtgebete, en bij andere gelegenheden. De preken zijn vertaald naar het Nederlands voor gebruik in dit project.

**Overzicht van de preken:**

| Nr | Titel | Bijbelgedeelte |
|----|-------|----------------|
| 01 | ... dat wij kunnen liefhebben | 1 Johannes 3:11–18 |
| 02 | Van wie is Kerstmis eigenlijk? | Lukas 2:1–20 |
| 03 | Herinner je de regenboog | Genesis 8:21–9:17 |
| 04 | De boom van de kennis en de boom van het leven | Genesis 2–3 |
| 05 | Laat mij Uw ezel zijn, Christus | Mattheüs 21:1–11 |
| 06 | Geldt de belofte voor alle mensen? | Jesaja 2:1–5 |
| 07 | Alles, niet minder | Marcus 10:17–27 |
| 08 | Troost zonder gerechtigheid | Jesaja 40:1–11 |
| 09 | Schatten in de hemel, schatten op aarde | Mattheüs 6:19–21 |
| 10 | Het achtste gebod | Exodus 20:16 |
| 11 | Wie heeft je zo geslagen? | Passieverhaal |
| 12 | Het land is vol afgoden | Jesaja 2:6–22 |
| 13 | Een meditatie voor Goede Vrijdag | Kruisiging |
| 14 | Geef ons heden ons dagelijks brood | Mattheüs 6:11 |
| 15 | Nog leven wij in Babylon | Jeremia 29 |
| 16 | Waarom willen jullie dan sterven? | Ezechiël 18 |
| 17 | Het geloof werkt aan de angst | Marcus 4:35–41 |
| 18 | Het is nog niet geopenbaard | 1 Johannes 3:2 |
| 19 | Tegen de geest van de koopmanschap | Tempelreiniging |
| 20 | Opstanding: Verhalen uit de ochtendschemering | Paasverhalen |
| 21 | Aan de doorwaadbare plaats | Genesis 32 |
| 22 | Getuigen van de waarheid | Johannes 18:37 |
| 23 | De aarde draait teder | Scheppingsverhaal |
| 24 | De opstanding van de vrouwen | Paasverhaal |
| 25 | De handen van God | Psalm 31 |
| 26 | Tel niet ons, maar jullie dagen | Psalm 90 |
| 27 | Lachen en eten | Avondmaal |
| 28 | Bijbelstudie over Psalm 118 | Psalm 118 |

### Bijbelteksten

De scripts halen automatisch bijbelteksten op van **debijbel.nl** in de **Herziene Statenvertaling (HSV)**. Als fallback wordt **bible.hispage.nl** gebruikt.

---

## Technische details

### Binair databestand (`data/sermons.dat`)

De 28 voorbeeldpreken worden niet als leesbare JSON-bestanden meegeleverd, maar in een **gecomprimeerd en geobfusceerd binair formaat**. 
Door ze niet als leesbare tekst mee te leveren, worden ze functioneel onderdeel van de software zonder als zelfstandige teksten verspreid te worden. De preken zijn niet bedoeld om gelezen te worden, maar om het LLM te trainen in Sölles stijl en cadans.

---

## Licentie en verantwoording

### Dit project

De code in dit project is vrij te gebruiken voor educatieve en niet-commerciële doeleinden.

### Theologische disclaimer

Dit project genereert teksten *in de stijl van* Dorothee Sölle. De gegenereerde preken zijn **geen authentieke teksten van Sölle** en moeten niet als zodanig worden gepresenteerd. Ze zijn bedoeld als:

- Studiemateriaal voor haar theologische methode
- Inspiratie voor eigen preken en meditaties
- Experimenteel onderzoek naar LLMs en homiletiek

De gegenereerde preken vertegenwoordigen een interpretatie door een LLM en kunnen afwijken van wat Sölle zelf zou hebben gezegd of geschreven.
