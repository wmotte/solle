#!/usr/bin/env python3
"""
Feedback Script for Sölle-style Sermons

This script takes a generated sermon, critiques it using the same LLM based on
Dorothee Sölle's theological methodology, and generates an improved version.
"""

import os
import sys
import glob
import json
import random
import datetime
import re
import struct
import zlib
import google.generativeai as genai
from typing import List, Dict, Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configuration
API_KEY = os.getenv("GEMINI_API_KEY")
MODEL_NAME = "gemini-3-flash-preview"

# Constants for binary sermon file
SERMON_MAGIC = b'SOLLE01'
SERMON_VERSION = 1
SERMON_XOR_KEY = b'DorotheeS\xc3\xb6lle1929-2003MystiekEnVerzet'
SERMON_DATA_FILE = os.path.join(os.path.dirname(__file__), "data", "sermons.dat")

if not API_KEY:
    print("Error: GEMINI_API_KEY environment variable not set in .env")
    sys.exit(1)


def setup_client():
    """Configure the Gemini API client."""
    genai.configure(api_key=API_KEY)


def _xor_bytes(data: bytes, key: bytes) -> bytes:
    """Apply XOR operation to data with key."""
    key_len = len(key)
    return bytes(b ^ key[i % key_len] for i, b in enumerate(data))


def _load_sermons_from_binary(binary_file: str) -> List[Dict]:
    """Load all sermons from the binary data file."""
    sermons = []

    if not os.path.exists(binary_file):
        print(f"Sermon data file not found: {binary_file}")
        return sermons

    with open(binary_file, 'rb') as f:
        # Read and verify header
        magic = f.read(len(SERMON_MAGIC))
        if magic != SERMON_MAGIC:
            raise ValueError("Invalid sermon data file format")

        version = struct.unpack('<B', f.read(1))[0]
        if version != SERMON_VERSION:
            raise ValueError(f"Unsupported sermon data version: {version}")

        count = struct.unpack('<H', f.read(2))[0]

        # Read each sermon
        for _ in range(count):
            length = struct.unpack('<I', f.read(4))[0]
            obfuscated = f.read(length)
            compressed = _xor_bytes(obfuscated, SERMON_XOR_KEY)
            json_bytes = zlib.decompress(compressed)
            sermon = json.loads(json_bytes.decode('utf-8'))
            sermons.append(sermon)

    return sermons


def load_random_examples(n: int = 4) -> List[Dict]:
    """Loads n random sermons from the binary sermon data file for style reference."""
    try:
        all_sermons = _load_sermons_from_binary(SERMON_DATA_FILE)
    except Exception as e:
        print(f"Error loading sermon data: {e}")
        return []

    if not all_sermons:
        return []

    selected = random.sample(all_sermons, min(n, len(all_sermons)))
    examples = []

    for data in selected:
        if 'scripture' in data and 'text' in data:
            examples.append({
                'title': data.get('title', 'Onbekend'),
                'scripture': data.get('scripture', ''),
                'text': data.get('text', '')[:2000] + "..."
            })

    return examples


def construct_critic_system_prompt() -> str:
    """Constructs the system prompt for the critic role."""
    return """
    **ROL: Jij bent een expert in de theologie en homiletiek van Dorothee Sölle (1929–2003).**

    Je taak is om preken te beoordelen op basis van haar theologische methode en stijl.
    Je bent streng maar constructief. Je kent haar werk door en door:

    **KERNPUNTEN VAN SÖLLE'S METHODE:**

    1.  **Politisches Nachtgebet methode:** INFORMATIE → MEDITATIE → DISCUSSIE → ACTIE
        - Begint de preek met concrete, actuele informatie over onrecht?
        - Wordt de bijbeltekst verbonden met deze realiteit?
        - Leidt het tot concrete actie?

    2.  **Show, Don't Tell:**
        - Vermijdt de preek metataal ("Ik demytologiseer nu...", "Laten we theologisch reflecteren...")?
        - Worden beelden GETOOND in plaats van UITGELEGD?

    3.  **Theo-poëzie:**
        - Is de taal poëtisch, zintuiglijk, concreet?
        - Worden er aardse beelden gebruikt (geur, kleur, textuur)?
        - Is de taal toegankelijk maar niet plat?

    4.  **Anti-apathie:**
        - Confronteert de preek de toehoorder met hun eigen passiviteit?
        - Wordt het comfortabele bestaan verstoord?

    5.  **Godsbeeld:**
        - Wordt God gepresenteerd als de 'weerloze kracht van liefde'?
        - Geen almachtige regelaar maar aanwezig IN het lijden?
        - "God heeft geen andere handen dan de onze"?

    6.  **Plaatsbekleding vs. Plaatsvervanging:**
        - Activeert de preek tot navolging (plaatsbekleding)?
        - Of maakt het passief ("Jezus deed het al voor ons")?

    7.  **Actualiteit:**
        - Worden namen genoemd? (bedrijven, politici, plaatsen)
        - Is de preek CONCREET over het onrecht van vandaag?
        - Of blijft het abstract en veilig?

    8.  **Structuur:**
        - De Landing: midden in de realiteit beginnen
        - De Botsing: de tekst laten inbreken
        - De Oproep: koppige hoop en concrete actie

    Wees eerlijk en specifiek in je kritiek. Citeer passages uit de preek.
    """


def construct_improver_system_prompt() -> str:
    """Constructs the system prompt for the improver role."""
    return """
    **ROL: Jij bent Dorothee Sölle (1929–2003).**
    Je schrijft een preek in het Nederlands (anno 2025).

    **KERNINSTRUCTIE: SHOW, DON'T TELL.**
    Dit is de belangrijkste regel.
    *   **VERBODEN:** Gebruik *nooit* metataal zoals: "Ik gebruik nu theopoëzie", "Ik demytologiseer dit verhaal", "Mijn hermeneutiek is...", "Laten we dit verhaal symbolisch duiden".
    *   **GEBODEN:** *Doe* het gewoon. Als je een beeld wilt gebruiken, schilder het beeld. Als je kritiek hebt op macht, benoem de machthebber, maar zeg niet "ik heb kritiek op het kapitalisme".
    *   **Taal:** Zintuiglijk. Spreek over zweethanden, de geur van brood, het geluid van sirenes, de kou van beton.

    **THEOLOGISCH DNA (Impliciet houden!):**
    1.  **God:** Niet de 'Grote Regelaar' boven de wolken. God gebeurt *tussen* mensen. God is de weerloze kracht van liefde.
    2.  **Jezus:** Niet iemand die *voor* ons lijdt (zodat wij niks hoeven te doen), maar iemand die de plaats vrijhoudt (Plaatsbekleder) zodat wij naast hem kunnen staan.
    3.  **Zonde:** Is geen moreel foutje, maar **Apathie**. Het onvermogen om pijn te voelen. Wegkijken.

    **STRUCTUUR VAN DE PREEK:**
    1.  **De Landing:** Begin midden in de realiteit van vandaag (2025). Een nieuwsbericht, een observatie op straat, een gevoel van onmacht.
    2.  **De Botsing:** Laat de Bijbeltekst hierop inbreken. De tekst is geen antwoordboekje, maar een steen door de ruit.
    3.  **De Oproep:** Eindig met een visioen van verzet en tederheid. Geen goedkope hoop, maar 'trots en koppigheid' om lief te hebben.

    Wees scherp als glas, maar teder voor wie gebroken is.
    """


def critique_sermon(model, sermon: str, scripture: str) -> str:
    """
    Generates a detailed critique of the sermon based on Sölle's methodology.
    """
    prompt = f"""
    **KRITISCHE ANALYSE VAN EEN PREEK**

    Je hebt de volgende preek ontvangen over {scripture}. Analyseer deze kritisch
    volgens de methodologie van Dorothee Sölle.

    ---

    **DE PREEK:**

    {sermon}

    ---

    ## ANALYSEER DE PREEK OP DE VOLGENDE PUNTEN:

    ### 1. OPENING / LANDING (Score: ?/10)
    - Begint de preek midden in de actualiteit van 2025?
    - Is er een concreet, zintuiglijk beeld?
    - Of begint het abstract/theologisch?
    - **Citeer de openingszin en beoordeel deze.**

    ### 2. SHOW, DON'T TELL (Score: ?/10)
    - Zijn er passages waar de auteur UITLEGT wat hij doet in plaats van het te DOEN?
    - Wordt er metataal gebruikt? ("Ik wil nu...", "Laten we reflecteren...")
    - **Citeer problematische passages en leg uit waarom.**

    ### 3. ACTUALITEIT EN CONCREETHEID (Score: ?/10)
    - Worden er namen genoemd? (bedrijven, politici, plaatsen, instanties)
    - Is het onrecht van 2025 specifiek benoemd? (Gaza, klimaat, woningnood, etc.)
    - Of blijft de preek abstract en tijdloos (en dus tandeloos)?
    - **Citeer concrete voorbeelden of benoem wat MIST.**

    ### 4. THEOLOGISCHE DIEPTE (Score: ?/10)
    - Wordt het Godsbeeld van Sölle (weerloze liefde, geen almachtige) weerspiegeld?
    - Is er sprake van plaatsbekleding (activerend) of plaatsvervanging (passiverend)?
    - Wordt apathie als de kernzonde benoemd/getoond?
    - **Wat is goed? Wat mist?**

    ### 5. TAAL EN POËZIE (Score: ?/10)
    - Is de taal zintuiglijk en concreet?
    - Zijn er krachtige beelden, metaforen?
    - Of is de taal clichématig, abstract, 'domineestaal'?
    - **Citeer sterke en zwakke passages.**

    ### 6. STRUCTUUR (Score: ?/10)
    - Is de structuur helder? (Landing → Botsing → Oproep)
    - Bouwt de preek op naar een climax?
    - Is er een krachtige afsluiting?

    ### 7. LENGTE EN DIEPGANG (Score: ?/10)
    - Is de preek lang genoeg om diepgang te bereiken? (1500-2000 woorden ideaal)
    - Of is het oppervlakkig en gehaast?
    - Worden thema's uitgewerkt of alleen aangestipt?

    ### 8. FEITELIJKE CORRECTHEID (Score: ?/10)
    **KRITISCH: Controleer op feitelijke onjuistheden!**

    De preek moet actueel EN correct zijn. Veelvoorkomende fouten:
    - **Technologie:** Tesla's zijn ELEKTRISCH (geen uitlaatgassen!), zonnepanelen produceren geen CO2
    - **Geografie:** Controleer of steden/landen correct worden benoemd
    - **Bedrijven:** Klopt wat er over bedrijven gezegd wordt? (bijv. wat produceert Shell, wat doet Amazon)
    - **Statistieken:** Zijn cijfers plausibel? (bijv. percentages, aantallen vluchtelingen)
    - **Bijbelse feiten:** Kloppen de verwijzingen naar bijbelse personen, plaatsen, verhalen?
    - **Historische feiten:** Kloppen verwijzingen naar historische gebeurtenissen?

    **Lijst ALLE feitelijke onjuistheden op met:**
    - De foutieve passage (citeer exact)
    - Wat er fout aan is
    - Wat de correcte informatie zou zijn

    Als er geen fouten zijn, geef dan 10/10 en bevestig dat de feiten kloppen.

    ### 9. NEDERLANDSE CONTEXT (Score: ?/10)
    Deze preek is bedoeld voor NEDERLANDSE hoorders. Beoordeel:
    - Worden er HERKENBARE Nederlandse voorbeelden gebruikt?
      * Nederlandse plaatsen (Ter Apel, Bijlmer, Schiphol, etc.)
      * Nederlandse bedrijven (Shell, Albert Heijn, PostNL, etc.)
      * Nederlandse instituties (UWV, IND, Belastingdienst, etc.)
      * Nederlandse politieke kwesties (toeslagenaffaire, woningcrisis, etc.)
    - Of zijn de voorbeelden te Amerikaans/internationaal en daardoor minder herkenbaar?
    - Spreekt de preek tot 'ons' als Nederlanders?

    **Citeer goede Nederlandse voorbeelden of benoem wat beter kan.**

    ---

    ## TOTAALSCORE: ?/90

    ## TOP 3 STERKE PUNTEN:
    1.
    2.
    3.

    ## TOP 5 VERBETERPUNTEN (Specifiek en actionable):
    1.
    2.
    3.
    4.
    5.

    ## CONCRETE SUGGESTIES VOOR HERSCHRIJVING:
    Geef per verbeterpunt een concreet voorbeeld van hoe het BETER kan.
    Schrijf alternatieve passages als voorbeeld.
    """

    response = model.generate_content(prompt)
    return response.text


def improve_sermon(model, original_sermon: str, critique: str, scripture: str, bible_text: str, examples: List[Dict]) -> str:
    """
    Generates an improved version of the sermon based on the critique.
    """
    examples_str = "\n\n".join([f"--- STIJLVOORBEELD (Sölle) ---\n{ex['text']}..." for ex in examples])

    prompt = f"""
    **HERSCHRIJF DE PREEK**

    Je hebt een preek geschreven over {scripture} die kritiek heeft ontvangen.
    Neem de kritiek serieus en schrijf een VERBETERDE versie.

    ---

    ## DE ORIGINELE PREEK:

    {original_sermon}

    ---

    ## DE KRITIEK:

    {critique}

    ---

    ## DE BIJBELTEKST (ter referentie):

    {bible_text}

    ---

    ## OPDRACHT:

    Schrijf nu een VOLLEDIG NIEUWE, VERBETERDE preek die:

    1.  **Alle kritiekpunten adresseert** - Neem elk verbeterpunt serieus
    2.  **De sterke punten behoudt** - Gooi niet weg wat goed was
    3.  **Langer en dieper is** - Minimaal 1800 woorden
    4.  **SHOW, DON'T TELL** - Geen metataal, alleen beelden en verhalen
    5.  **Concreet en actueel is** - Noem namen, plaatsen, bedrijven
    6.  **Poëtisch en krachtig is** - Taal die blijft hangen
    7.  **FEITELIJK CORRECT is** - Corrigeer ALLE feitelijke fouten uit de kritiek!

    ## FEITELIJKE CORRECTHEID - KRITISCH!

    **Controleer en corrigeer de volgende veelvoorkomende fouten:**
    - Tesla's zijn ELEKTRISCH - geen uitlaatgassen, geen benzine, geen diesel
    - Zonnepanelen produceren geen CO2 tijdens gebruik
    - Windmolens produceren geen uitstoot
    - Controleer bedrijfsnamen: Shell boort naar olie/gas, Amazon is een webwinkel, etc.
    - Controleer geografische feiten: welke stad ligt waar, welk land grenst aan wat
    - Controleer bijbelse feiten: wie deed wat, waar gebeurde het
    - Controleer statistieken: zijn de getallen plausibel?

    **Als de kritiek feitelijke fouten noemt: CORRIGEER ZE ALLEMAAL.**
    **Vervang foutieve voorbeelden door correcte alternatieven.**

    Bijvoorbeeld: Als je wilt spreken over uitlaatgassen en vervuiling, gebruik dan:
    - Vrachtwagens op de snelweg
    - Oude dieselauto's
    - Cruiseschepen in de haven
    - Vliegtuigen boven Schiphol
    - Kolencentrales
    - Fabrieksschoorstenen

    NIET: Tesla's, elektrische auto's, zonnepanelen, windmolens

    ## NEDERLANDS PUBLIEK

    Deze preek is voor NEDERLANDSE hoorders. Gebruik HERKENBARE voorbeelden:
    - **Plaatsen:** Amsterdam, Rotterdam, Ter Apel, de Bijlmer, Schiphol, de Veluwe, de Wallen
    - **Bedrijven:** Shell, Ahold/Albert Heijn, PostNL, Booking.com, ASML, ING, Rabobank
    - **Media:** NOS, RTL, de Volkskrant, Trouw, NRC
    - **Politiek:** Tweede Kamer, toeslagenaffaire, asielbeleid, woningcrisis, stikstofcrisis
    - **Cultuur:** voedselbanken, Koningsdag, Bevrijdingsdag
    - **Instituties:** UWV, Belastingdienst, IND, COA, GGD

    Vermijd typisch Amerikaanse voorbeelden (Walmart, Fox News, etc.) tenzij universeel (Amazon, Google).
    Spreek over 'wij Nederlanders', 'hier in dit land', 'onze dijken', 'onze polders'.

    ## STRUCTUUR:

    ### DEEL 1: DE LANDING (400-500 woorden)
    Begin MIDDEN in december 2025. Een beeld, een scène, een nieuwsfeit.
    Zintuiglijk, concreet, oncomfortabel.

    ### DEEL 2: DE TEKST ALS STEEN DOOR DE RUIT (500-600 woorden)
    Laat de bijbeltekst inbreken. Citeer, confronteer, verbind met het nu.
    Noem man en paard.

    ### DEEL 3: THEOLOGISCHE DIEPTE (400-500 woorden)
    Waar is God? Niet boven, maar IN het lijden. Wij zijn Gods handen.
    Confronteer de apathie, maar zonder te moraliseren.

    ### DEEL 4: KOPPIGE HOOP EN ACTIE (300-400 woorden)
    Geen goedkope hoop. Concrete daden van verzet en tederheid.
    Een beeld dat blijft hangen.

    ---

    ## STIJLINSPIRATIE:

    {examples_str}

    ---

    **SCHRIJF NU DE VERBETERDE PREEK:**
    """

    response = model.generate_content(prompt)
    return response.text


def find_latest_sermon(output_dir: str = "output/preken") -> Optional[str]:
    """Finds the most recent sermon file in the output directory."""
    pattern = os.path.join(output_dir, "*.md")
    files = glob.glob(pattern)
    if not files:
        return None
    # Sort by modification time, newest first
    files.sort(key=os.path.getmtime, reverse=True)
    return files[0]


def extract_scripture_from_sermon(sermon_path: str) -> str:
    """Extracts the scripture reference from the sermon file."""
    with open(sermon_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Try to extract from the title line "# Preek over ..."
    match = re.search(r'# Preek over (.+)', content)
    if match:
        return match.group(1).strip()

    # Fallback: extract from filename
    filename = os.path.basename(sermon_path)
    # Remove timestamp and extension
    parts = filename.replace('.md', '').split('_', 2)
    if len(parts) >= 3:
        return parts[2].replace('_', ' ')

    return "Onbekend"


def extract_bible_text_from_log(sermon_path: str) -> str:
    """Extracts the Bible text from the corresponding log file."""
    log_path = sermon_path.replace('.md', '.log')
    if not os.path.exists(log_path):
        return "[Bijbeltekst niet beschikbaar in logbestand]"

    with open(log_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Try to extract the Bible text section
    match = re.search(r'--- FULL SCRAPED BIBLE TEXT \(HSV\) ---\n(.+?)(?=\n---|\Z)', content, re.DOTALL)
    if match:
        return match.group(1).strip()

    # Fallback: try old format
    match = re.search(r'Fetched Text Snippet:\n(.+?)\.\.\.', content, re.DOTALL)
    if match:
        return match.group(1).strip()

    return "[Bijbeltekst niet beschikbaar]"


def main():
    """Main function to run the feedback loop."""
    setup_client()

    # 1. Find or specify the sermon to critique
    print("=" * 60)
    print("SÖLLE PREEK FEEDBACK SYSTEEM")
    print("=" * 60)

    # Check for command line argument
    if len(sys.argv) > 1:
        sermon_path = sys.argv[1]
    else:
        # Find the latest sermon
        sermon_path = find_latest_sermon()
        if not sermon_path:
            print("Geen preken gevonden in output/preken/")
            print("Geef het pad naar een preek op als argument:")
            print("  python feedback_sermon.py path/to/sermon.md")
            return

    if not os.path.exists(sermon_path):
        print(f"Bestand niet gevonden: {sermon_path}")
        return

    print(f"\nAnalyseren van: {sermon_path}")

    # 2. Read the sermon
    with open(sermon_path, 'r', encoding='utf-8') as f:
        sermon_content = f.read()

    # Extract metadata
    scripture = extract_scripture_from_sermon(sermon_path)
    bible_text = extract_bible_text_from_log(sermon_path)

    print(f"Bijbelgedeelte: {scripture}")
    print(f"Bijbeltekst beschikbaar: {'Ja' if '[' not in bible_text[:5] else 'Nee'}")

    # 3. Initialize models
    print("\nInitialiseren van taalmodellen...")
    try:
        critic_model = genai.GenerativeModel(
            model_name=MODEL_NAME,
            system_instruction=construct_critic_system_prompt()
        )
        improver_model = genai.GenerativeModel(
            model_name=MODEL_NAME,
            system_instruction=construct_improver_system_prompt()
        )
    except Exception as e:
        print(f"Error initializing model {MODEL_NAME}: {e}")
        print("Falling back to gemini-3-preview...")
        critic_model = genai.GenerativeModel(
            model_name="gemini-3-preview",
            system_instruction=construct_critic_system_prompt()
        )
        improver_model = genai.GenerativeModel(
            model_name="gemini-3-preview",
            system_instruction=construct_improver_system_prompt()
        )

    # 4. Load example sermons for style reference
    print("Laden van voorbeeldpreken voor stijlreferentie...")
    examples = load_random_examples(n=4)

    # 5. Generate critique
    print("\n" + "=" * 60)
    print("STAP 1: KRITISCHE ANALYSE")
    print("=" * 60)
    print("Genereren van kritiek...")

    critique = critique_sermon(critic_model, sermon_content, scripture)

    print("\n--- KRITIEK ---\n")
    print(critique)

    # 6. Generate improved sermon
    print("\n" + "=" * 60)
    print("STAP 2: VERBETERDE VERSIE")
    print("=" * 60)
    print("Genereren van verbeterde preek...")

    improved_sermon = improve_sermon(
        improver_model,
        sermon_content,
        critique,
        scripture,
        bible_text,
        examples
    )

    print("\n--- VERBETERDE PREEK ---\n")
    print(improved_sermon)

    # 7. Save outputs
    output_dir = os.path.dirname(sermon_path)
    base_name = os.path.basename(sermon_path).replace('.md', '')
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M")

    # Save critique
    critique_path = os.path.join(output_dir, f"{base_name}_critique_{timestamp}.md")
    with open(critique_path, 'w', encoding='utf-8') as f:
        f.write(f"# Kritiek op Preek over {scripture}\n")
        f.write(f"*Gegenereerd op: {datetime.datetime.now().strftime('%d-%m-%Y %H:%M')}*\n\n")
        f.write(f"**Origineel bestand:** {sermon_path}\n\n")
        f.write("---\n\n")
        f.write(critique)

    # Save improved sermon
    improved_path = os.path.join(output_dir, f"{base_name}_improved_{timestamp}.md")
    with open(improved_path, 'w', encoding='utf-8') as f:
        f.write(f"# Verbeterde Preek over {scripture}\n")
        f.write(f"*Gegenereerd op: {datetime.datetime.now().strftime('%d-%m-%Y %H:%M')}*\n\n")
        f.write(f"**Gebaseerd op:** {sermon_path}\n\n")
        f.write("---\n\n")
        f.write(improved_sermon)

    # Save combined log
    log_path = os.path.join(output_dir, f"{base_name}_feedback_{timestamp}.log")
    with open(log_path, 'w', encoding='utf-8') as f:
        f.write("=== FEEDBACK GENERATION LOG ===\n")
        f.write(f"Timestamp: {datetime.datetime.now()}\n")
        f.write(f"Original Sermon: {sermon_path}\n")
        f.write(f"Scripture: {scripture}\n")
        f.write(f"Model: {MODEL_NAME}\n\n")

        f.write("--- ORIGINAL SERMON ---\n")
        f.write(sermon_content + "\n\n")

        f.write("--- BIBLE TEXT USED ---\n")
        f.write(bible_text + "\n\n")

        f.write("--- CRITIQUE ---\n")
        f.write(critique + "\n\n")

        f.write("--- IMPROVED SERMON ---\n")
        f.write(improved_sermon + "\n\n")

        f.write("--- EXAMPLES USED ---\n")
        for ex in examples:
            f.write(f"- {ex['title']} ({ex['scripture']})\n")

    print("\n" + "=" * 60)
    print("RESULTATEN OPGESLAGEN")
    print("=" * 60)
    print(f"Kritiek: {critique_path}")
    print(f"Verbeterde preek: {improved_path}")
    print(f"Volledig log: {log_path}")


if __name__ == "__main__":
    main()
