#!/usr/bin/env python3
import os
import glob
import json
import random
import datetime
import re
import struct
import zlib
import requests
from bs4 import BeautifulSoup
import google.generativeai as genai
from typing import List, Dict, Optional
from dotenv import load_dotenv

# Constants for binary sermon file
SERMON_MAGIC = b'SOLLE01'
SERMON_VERSION = 1
SERMON_XOR_KEY = b'DorotheeS\xc3\xb6lle1929-2003MystiekEnVerzet'
SERMON_DATA_FILE = os.path.join(os.path.dirname(__file__), "data", "sermons.dat")

# Load environment variables from .env file
load_dotenv()

# Configuration
API_KEY = os.getenv("GEMINI_API_KEY")
MODEL_NAME = "gemini-3-flash-preview"

if not API_KEY:
    print("Warning: GEMINI_API_KEY environment variable not set in .env")

class BibleFetcher:
    """Fetches Bible text from bible.hispage.nl (HSV)."""
    
    # Standaard canonieke volgorde (1-66) + Veelvoorkomende afkortingen
    BOOK_MAPPING = {
        # Oude Testament
        "genesis": 1, "gen": 1, "exodus": 2, "ex": 2, "leviticus": 3, "lev": 3, "numeri": 4, "num": 4, 
        "deuteronomium": 5, "deut": 5, "dt": 5,
        "jozua": 6, "joz": 6, "richteren": 7, "rechters": 7, "ri": 7, "ruth": 8, "rut": 8,
        "1 samuel": 9, "1sam": 9, "1 sa": 9, "2 samuel": 10, "2sam": 10, "2 sa": 10,
        "1 koningen": 11, "1kon": 11, "1 ko": 11, "2 koningen": 12, "2kon": 12, "2 ko": 12,
        "1 kronieken": 13, "1kr": 13, "1 kr": 13, "2 kronieken": 14, "2kr": 14, "2 kr": 14,
        "ezra": 15, "nehemia": 16, "neh": 16, "esther": 17, "est": 17,
        "job": 18, "psalmen": 19, "psalm": 19, "ps": 19, "spreuken": 20, "spr": 20,
        "prediker": 21, "pred": 21, "hooglied": 22, "hgl": 22,
        "jesaja": 23, "jes": 23, "jeremia": 24, "jer": 24, "klaagliederen": 25, "kla": 25,
        "ezechiël": 26, "ezechiel": 26, "ez": 26, "daniël": 27, "daniel": 27, "dan": 27,
        "hosea": 28, "hos": 28, "joël": 29, "joel": 29, "amos": 30, "am": 30,
        "obadja": 31, "ob": 31, "jona": 32, "micha": 33, "mi": 33, "mic": 33,
        "nahum": 34, "na": 34, "nah": 34, "habakuk": 35, "hab": 35, "zefanja": 36, "zef": 36,
        "haggai": 37, "hag": 37, "zacharia": 38, "zach": 38, "zac": 38, "maleachi": 39, "mal": 39,
        # Nieuwe Testament
        "mattheüs": 40, "mattheus": 40, "matt": 40, "mt": 40, "marcus": 41, "marc": 41, "mk": 41, "mc": 41,
        "lucas": 42, "lukas": 42, "luc": 42, "luk": 42, "lc": 42, "johannes": 43, "joh": 43, "jn": 43,
        "handelingen": 44, "hand": 44, "hnd": 44, "romeinen": 45, "rom": 45,
        "1 korintiërs": 46, "1 korintiers": 46, "1kor": 46, "1 kor": 46, "1ko": 46,
        "2 korintiërs": 47, "2 korintiers": 47, "2kor": 47, "2 kor": 47, "2ko": 47,
        "galaten": 48, "gal": 48, "efesiërs": 49, "efesiers": 49, "efeze": 49, "ef": 49,
        "filippenzen": 50, "fil": 50, "kolossenzen": 51, "kol": 51,
        "1 tessalonicenzen": 52, "1tess": 52, "1 tess": 52, "1th": 52,
        "2 tessalonicenzen": 53, "2tess": 53, "2 tess": 53, "2th": 53,
        "1 timoteüs": 54, "1 timotheus": 54, "1tim": 54, "1 tim": 54, "1ti": 54,
        "2 timoteüs": 55, "2 timotheus": 55, "2tim": 55, "2 tim": 55, "2ti": 55,
        "titus": 56, "tit": 56, "filemon": 57, "film": 57, "flm": 57,
        "hebreeën": 58, "hebreeen": 58, "hebr": 58, "heb": 58,
        "jakobus": 59, "jak": 59,
        "1 petrus": 60, "1pet": 60, "1 pet": 60, "1pe": 60,
        "2 petrus": 61, "2pet": 61, "2 pet": 61, "2pe": 61,
        "1 johannes": 62, "1joh": 62, "1 joh": 62, "1jo": 62,
        "2 johannes": 63, "2joh": 63, "2 joh": 63, "2jo": 63,
        "3 johannes": 64, "3joh": 64, "3 joh": 64, "3jo": 64,
        "judas": 65, "jud": 65, "openbaring": 66, "openbaringen": 66, "op": 66
    }

    @staticmethod
    def parse_reference(reference: str) -> tuple[Optional[int], Optional[str], Optional[str], str]:
        """
        Parses 'Lukas 2:1-4' into (42, '2', '1-4', 'match_type').
        Returns: (book_id, chapter, verses, log_message)
        """
        # Improved regex to handle '1 Joh', '1Joh', '1 Johannes', 'Lucas', 'Lk'
        # Matches optional digit + space + word(s) + space + digit
        
        # Stap 1: Normaliseren (lowercase, spaties rond cijfers)
        ref_norm = reference.lower().strip()
        
        # Zoek naar het patroon: (Boek) (Hoofdstuk) : (Verzen)
        # We splitsen eerst op het laatste cijfergroep die het hoofdstuk is.
        
        match = re.match(r"^(\d?\s*[a-zëï]+)\.?\s*(\d+)(?:[:\.](\d+(?:-\d+)?))?$", ref_norm)
        
        if not match:
            return None, None, None, f"Regex parse mislukt voor '{reference}'"
        
        book_part = match.group(1).strip()
        chapter = match.group(2)
        verses = match.group(3)
        
        log_msg = f"Geparsed: Boek='{book_part}', Hst='{chapter}', Vers='{verses}'"

        # Mapping check
        book_id = BibleFetcher.BOOK_MAPPING.get(book_part)
        match_type = "exact"
        
        if not book_id:
            # Fuzzy Matching
            # 1. Probeer zonder spaties (1 joh -> 1joh)
            compact_name = book_part.replace(" ", "")
            book_id = BibleFetcher.BOOK_MAPPING.get(compact_name)
            if book_id:
                match_type = "compact_match"
            else:
                # 2. Startswith search in keys (riskant bij 'joh' -> 'johannes' vs 'jona'?)
                # We sorteren keys op lengte om eerst 'johannes' te matchen als input 'johannes' is, 
                # maar als input 'joh' is, matcht het 'johannes'. 
                # Om veilig te zijn: als input 'joh' is, en 'joh' staat in keys (wat zo is), pakken we die.
                # Als input 'luk' is, en 'luk' staat in keys, pakken we die.
                # Als input 'lu' is?
                for key, bid in BibleFetcher.BOOK_MAPPING.items():
                    if key.startswith(book_part):
                        book_id = bid
                        match_type = f"fuzzy_startswith_'{key}'"
                        break
        
        if book_id:
            log_msg += f" -> ID gevonden: {book_id} ({match_type})"
        else:
            log_msg += " -> GEEN ID gevonden."

        return book_id, chapter, verses, log_msg

    @staticmethod
    def fetch_text(reference: str) -> tuple[str, str]:
        """
        Fetches the text from multiple sources, trying bijbel.net first (more reliable),
        then falling back to bible.hispage.nl.
        Returns: (text, log_details)
        """
        book_id, chapter, verses, parse_log = BibleFetcher.parse_reference(reference)

        if not book_id or not chapter:
            return f"[Kon tekst niet automatisch ophalen. Fallback op interne kennis.]", parse_log

        fetch_log = parse_log

        # Try debijbel.nl first (Nederlandse Bijbelgenootschap - cleaner HTML)
        text, log = BibleFetcher._try_debijbel(reference, book_id, chapter, verses)
        fetch_log += log
        if not text.startswith("["):
            return text, fetch_log

        # Fallback to hispage.nl
        text, log = BibleFetcher._try_hispage(book_id, chapter)
        fetch_log += log
        return text, fetch_log

    @staticmethod
    def _try_debijbel(reference: str, book_id: int, chapter: str, verses: Optional[str]) -> tuple[str, str]:
        """Try to fetch from debijbel.nl (NBG - cleaner, more reliable)."""
        log = "\n\n--- Poging 1: debijbel.nl (HSV) ---"

        # Map book_id to debijbel.nl book abbreviation
        book_abbrevs = {
            1: "GEN", 2: "EXO", 3: "LEV", 4: "NUM", 5: "DEU", 6: "JOZ", 7: "RIC", 8: "RUT",
            9: "1SA", 10: "2SA", 11: "1KO", 12: "2KO", 13: "1KR", 14: "2KR", 15: "EZR",
            16: "NEH", 17: "EST", 18: "JOB", 19: "PSA", 20: "SPR", 21: "PRE", 22: "HOO",
            23: "JES", 24: "JER", 25: "KLA", 26: "EZE", 27: "DAN", 28: "HOS", 29: "JOE",
            30: "AMO", 31: "OBA", 32: "JON", 33: "MIC", 34: "NAH", 35: "HAB", 36: "SEF",
            37: "HAG", 38: "ZAC", 39: "MAL", 40: "MAT", 41: "MAR", 42: "LUK", 43: "JOH",
            44: "HAN", 45: "ROM", 46: "1KOR", 47: "2KOR", 48: "GAL", 49: "EFE", 50: "FIL",
            51: "KOL", 52: "1TES", 53: "2TES", 54: "1TIM", 55: "2TIM", 56: "TIT", 57: "FLM",
            58: "HEB", 59: "JAK", 60: "1PE", 61: "2PE", 62: "1JOH", 63: "2JOH", 64: "3JOH",
            65: "JUD", 66: "OPE"
        }

        abbrev = book_abbrevs.get(book_id, "")
        if not abbrev:
            log += f"\nGeen abbreviatie voor book_id {book_id}"
            return "[Boek niet gevonden]", log

        # debijbel.nl HSV format: https://debijbel.nl/bijbel/HSV/PSA.23
        url = f"https://debijbel.nl/bijbel/HSV/{abbrev}.{chapter}"
        log += f"\nURL: {url}"
        print(f"   (Ophalen van {url}...)")

        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'nl-NL,nl;q=0.9,en;q=0.8'
            }
            response = requests.get(url, headers=headers, timeout=15)
            log += f"\nHTTP Status: {response.status_code}"

            if response.status_code != 200:
                return f"[HTTP {response.status_code}]", log

            soup = BeautifulSoup(response.content, 'html.parser')

            # Find verse containers - debijbel.nl uses specific classes
            verses_text = []

            # Try multiple selectors
            verse_elements = soup.find_all('span', class_=lambda x: x and 'verse' in x.lower()) or \
                            soup.find_all('div', class_=lambda x: x and 'verse' in x.lower()) or \
                            soup.find_all(class_=lambda x: x and 'tekst' in x.lower())

            if verse_elements:
                for elem in verse_elements:
                    text = elem.get_text(strip=True)
                    if text and len(text) > 5:  # Filter out tiny elements
                        verses_text.append(text)

            # If specific verse elements not found, try main content area
            if not verses_text:
                main_content = soup.find('main') or soup.find('article') or soup.find('div', class_='content')
                if main_content:
                    # Get all paragraphs
                    for p in main_content.find_all(['p', 'div']):
                        text = p.get_text(strip=True)
                        # Filter: verse text usually starts with number or has Dutch words
                        if text and len(text) > 10 and not any(nav in text.lower() for nav in
                            ['genesis', 'exodus', 'leviticus', 'king james', 'statenvertaling',
                             'lutherse', 'copyright', 'bijbelgenootschap', 'cookie', 'privacy']):
                            verses_text.append(text)

            if verses_text:
                full_text = " ".join(verses_text)
                # Clean up
                full_text = re.sub(r'\s+', ' ', full_text).strip()
                if len(full_text) > 6000:
                    full_text = full_text[:6000] + "..."
                log += f"\nSucces: {len(full_text)} karakters opgehaald."
                return full_text, log

            log += "\nGeen verzen gevonden op debijbel.nl"
            return "[Geen tekst gevonden]", log

        except Exception as e:
            log += f"\nException: {str(e)}"
            return f"[Fout: {str(e)}]", log

    @staticmethod
    def _try_hispage(book_id: int, chapter: str) -> tuple[str, str]:
        """Fallback to bible.hispage.nl with improved parsing."""
        log = "\n\n--- Poging 2: hispage.nl ---"

        # v[]=6 is HSV (Herziene Statenvertaling)
        url = f"https://bible.hispage.nl/index.php?book={book_id}&chapter={chapter}&v[]=6&language=1"
        log += f"\nURL: {url}"
        print(f"   (Ophalen van {url}...)")

        try:
            headers = {'User-Agent': 'Mozilla/5.0 (compatible; SermonBot/1.0)'}
            response = requests.get(url, headers=headers, timeout=10)
            log += f"\nHTTP Status: {response.status_code}"

            if response.status_code != 200:
                return f"[Fout bij ophalen: HTTP {response.status_code}]", log

            soup = BeautifulSoup(response.content, 'html.parser')

            # Remove navigation elements, scripts, styles
            for element in soup.find_all(['script', 'style', 'nav', 'header', 'footer', 'select', 'option', 'button']):
                element.decompose()

            # Remove elements with navigation-like content
            for element in soup.find_all(['div', 'span', 'td', 'a']):
                text = element.get_text(strip=True).lower()
                # Skip if it looks like navigation/menu
                if any(nav in text for nav in ['genesis', 'exodus', 'leviticus', 'numbers', 'deuteronomy',
                    'matthew', 'mark', 'luke', 'john', 'king james', 'statenvertaling',
                    'lutherse vertaling', 'leidse vertaling', 'nbg', 'het boek', 'basisbijbel',
                    'new international', 'louis segond', 'vulgate', 'and or']):
                    if len(text) < 100:  # Only remove if it's a short nav element
                        element.decompose()

            # Now extract text
            # Look for table cells that contain verse numbers followed by text
            verses = []

            # Find all table rows
            for row in soup.find_all('tr'):
                cells = row.find_all('td')
                for cell in cells:
                    text = cell.get_text(separator=' ', strip=True)
                    # Check if this looks like a verse (starts with number or contains Dutch text)
                    if text and len(text) > 20:
                        # Check for verse pattern: number at start followed by text
                        if re.match(r'^\d+\s+\w', text):
                            verses.append(text)
                        # Or just substantial Dutch text
                        elif any(dutch in text.lower() for dutch in ['heere', 'god', 'jezus', 'christus', 'hij', 'zij', 'mij', 'zijn']):
                            verses.append(text)

            if verses:
                # Take only unique verses and join
                seen = set()
                unique_verses = []
                for v in verses:
                    v_clean = v[:50]  # Use first 50 chars for dedup
                    if v_clean not in seen:
                        seen.add(v_clean)
                        unique_verses.append(v)

                full_text = " ".join(unique_verses)
                full_text = re.sub(r'\s+', ' ', full_text).strip()

                if len(full_text) > 6000:
                    full_text = full_text[:6000] + "..."

                log += f"\nSucces: {len(full_text)} karakters opgehaald."
                return full_text, log

            log += "\nGeen verzen gevonden met verbeterde parsing."
            return "[Kon geen leesbare tekst extraheren.]", log

        except Exception as e:
            log += f"\nException: {str(e)}"
            return f"[Fout bij ophalen: {str(e)}]", log

def setup_client():
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


def load_random_examples(n: int = 6) -> List[Dict]:
    """Loads n random sermons from the binary sermon data file."""
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
                'text': data.get('text', '')[:1500] + "..."
            })

    return examples

def construct_system_prompt() -> str:
    """Constructs the system prompt based on Sölle's theology and style."""
    
    analysis = """
    **ROL: Jij bent Dorothee Sölle (1929–2003).**
    Je schrijft een preek in het Nederlands (anno 2025).

    **KERNINSTRUCTIE: SHOW, DON'T TELL.**
    Dit is de belangrijkste regel.
    *   **VERBODEN:** Gebruik *nooit* metataal zoals: "Ik gebruik nu theopoëzie", "Ik demytologiseer dit verhaal", "Mijn hermeneutiek is...", "Laten we dit verhaal symbolisch duiden".
    *   **GEBODEN:** *Doe* het gewoon. Als je een beeld wilt gebruiken, schilder het beeld. Als je kritiek hebt op macht, benoem de machthebber (Shell, Amazon, PostNL), maar zeg niet "ik heb kritiek op het kapitalisme".
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
    return analysis

def perform_pre_work(model, scripture: str, bible_text: str) -> str:
    """Asks the model to perform extensive contextual analysis before writing."""
    prompt = f"""
    **STAP 1: DIEPGAANDE CONTEXT & TEKST ANALYSE**

    Je bent Dorothee Sölle en bereidt een preek voor. Voordat je schrijft, moet je de tekst grondig doordenken
    volgens de methode van het Politisches Nachtgebet: INFORMATIE → MEDITATIE → DISCUSSIE → ACTIE.

    **De Bijbeltekst (HSV) voor {scripture}:**
    \"\"\"{bible_text}\"\"\"

    ---

    ## DEEL A: EXEGETISCHE ANALYSE

    1.  **Historische Context:** Wat is de oorspronkelijke setting van deze tekst? Wie zijn de actoren?
        Wat was de politieke/sociale situatie waarin deze woorden werden gesproken of geschreven?

    2.  **Kernthema's:** Welke 3-4 centrale theologische thema's zitten in deze tekst?
        Denk aan: macht/machteloosheid, bevrijding, lijden, gemeenschap, verzet, hoop, gerechtigheid.

    3.  **Spanning in de tekst:** Waar zit de 'steen door de ruit'? Wat is confronterend,
        verontrustend of radicaal aan deze tekst als je hem serieus neemt?

    ---

    ## DEEL B: ACTUELE WERELDSITUATIE (DECEMBER 2025)

    Benoem EXPLICIET en CONCREET de actuele crises en hoe deze tekst daarop kan inbreken:

    4.  **Oorlog en Geweld:**
        - Gaza/Palestina-Israël conflict: de voortdurende humanitaire crisis, burgerdoden, vluchtelingen
        - Oekraïne: de oorlog die voortduurt, de vermoeidheid van het Westen, de vluchtelingencrisis
        - Sudan, Yemen, Congo: de vergeten oorlogen waar niemand meer naar kijkt
        - Wat zegt deze tekst tegen de wapenindustrie? Tegen Lockheed Martin, Rheinmetall, de exporteurs?

    5.  **Klimaat en Schepping:**
        - De klimaattop COP29 en de gebroken beloften van rijke landen
        - Shell, ExxonMobil, TotalEnergies die recordwinsten boeken terwijl de aarde brandt
        - De overstromingen, droogtes, klimaatvluchtelingen die geen status krijgen
        - Wat betekent 'rentmeesterschap' als je aandelen hebt in fossiele brandstoffen?

    6.  **Economische Ongelijkheid:**
        - De rijkste 1% bezit meer dan de onderste 50% van de wereldbevolking
        - Amazon, Zalando, de pakketbezorgers die geen tijd hebben om te plassen
        - Woningnood in Nederland: studenten in containers, gezinnen in hotels
        - Voedselbanken die overstroomd worden terwijl supermarkten voedsel weggooien

    7.  **Technologie en Dehumanisering:**
        - AI die banen overneemt, die deepfakes maakt, die surveillance mogelijk maakt
        - Social media en de epidemie van eenzaamheid onder jongeren
        - De algoritmische bubbels die ons verdelen

    8.  **Specifiek Nederland/Europa 2025:**
        - De politieke verschuiving naar rechts, het migratiedebat
        - De toeslagenaffaire en institutioneel wantrouwen
        - De asielcrisis, Ter Apel, de bootvluchtelingen in de Middellandse Zee
        - De verharding van de samenleving, de afname van empathie

    ---

    ## DEEL C: THEOLOGISCHE VERBINDING (Sölle's methode)

    9.  **De Apathie ontmaskeren:**
        Hoe houdt deze tekst ons een spiegel voor? Waar zijn WIJ de toeschouwers die wegkijken?
        Waar zitten wij veilig in onze huizen terwijl anderen lijden?

    10. **God in het lijden:**
        Waar is God in deze situaties? Niet als de almachtige die ingrijpt, maar als de
        weerloze kracht van liefde, de Shekinah die meegaat in ballingschap?

    11. **De oproep tot plaatsbekleding:**
        Wat betekent het om de 'plaats vrij te houden' in deze context?
        Niet: wat doet God voor ons? Maar: waar roept God ons om naast de slachtoffers te staan?

    ---

    ## DEEL D: ZINTUIGLIJKE BEELDEN EN LANDINGSPLAATSEN

    12. **Vijf concrete beelden:**
        Geef 5 zintuiglijke, poëtische beelden die je kunt gebruiken om de preek te 'landen':
        - Een BEELD (iets wat je ziet)
        - Een GELUID (iets wat je hoort)
        - Een GEUR (iets wat je ruikt)
        - Een TEXTUUR (iets wat je voelt)
        - Een LOCATIE (een concrete plek in 2025 waar deze tekst thuishoort)

    13. **De opening van de preek:**
        Geef 3 mogelijke openingszinnen die MIDDEN in de realiteit van vandaag beginnen.
        Geen 'Lieve gemeente', maar een nieuwsbericht, een observatie, een gevoel van onmacht.

    ---

    Geef deze analyse uitgebreid en puntsgewijs. Dit is het fundament voor de preek.
    Wees concreet, noem namen van bedrijven, politici, plaatsen. Geen abstracties.
    """
    response = model.generate_content(prompt)
    return response.text

def generate_sermon(model, scripture: str, bible_text: str, context_analysis: str, examples: List[Dict]) -> str:
    """Generates an extensive sermon using the examples and context analysis."""

    examples_str = "\n\n".join([f"--- STIJLVOORBEELD (Sölle) ---\n{ex['text']}..." for ex in examples])

    prompt = f"""
    **STAP 2: DE UITGEBREIDE PREEK**

    Je bent Dorothee Sölle. Schrijf nu een volledige, diepgaande preek.
    Gebruik je voorbereidende analyse als fundament, maar de preek zelf moet TONEN, niet VERTELLEN.

    ---

    ## INPUT

    **Bijbelgedeelte:** {scripture}

    **Volledige Bijbeltekst (HSV):**
    \"\"\"{bible_text}\"\"\"

    **Jouw Voorbereidende Analyse:**
    {context_analysis}

    ---

    ## STRUCTUUR VAN DE PREEK (Volg dit strak!)

    ### DEEL 1: DE LANDING (300-400 woorden)
    Begin MIDDEN in de realiteit van december 2025.
    - Open met een concreet beeld, een nieuwsfeit, een observatie op straat
    - Schilder een scène die de toehoorder meteen vastgrijpt
    - Laat de spanning, de pijn, de onmacht van onze tijd voelen
    - Gebruik zintuiglijke details: wat zie je, hoor je, ruik je?
    - GEEN abstracte stellingen, GEEN theologische inleidingen

    ### DEEL 2: DE TEKST ALS STEEN DOOR DE RUIT (400-500 woorden)
    Laat de bijbeltekst inbreken op de werkelijkheid die je net hebt geschetst.
    - Citeer de tekst, maar niet als decoratie - als onderbreking
    - Wat zegt deze tekst tegen de machthebbers van nu?
    - Wat zegt deze tekst tegen onze apathie, ons wegkijken?
    - Maak de verbinding tussen de bijbelse situatie en onze situatie CONCREET
    - Noem namen: bedrijven, politici, plaatsen, instanties
    - Laat de tekst schuren, pijn doen, wakker schudden

    ### DEEL 3: DE THEOLOGISCHE DIEPTE (300-400 woorden)
    Ga dieper in op wat dit betekent voor ons Godsbeeld en ons mens-zijn.
    - Waar is God in dit alles? Niet als de almachtige regelaar, maar als...?
    - Wat betekent het dat God 'geen andere handen heeft dan de onze'?
    - Spreek over schuld en verantwoordelijkheid, maar zonder te moraliseren
    - Wat is de zonde hier? (Hint: apathie, wegkijken, ons comfort beschermen)
    - Spreek persoonlijk: waar ben JIJ (als Sölle) medeplichtig?

    ### DEEL 4: HET VISIOEN VAN VERZET EN TEDERHEID (300-400 woorden)
    Eindig niet met goedkope hoop, maar met koppige, trotse hoop.
    - Wat kunnen wij DOEN? Wees concreet maar niet naïef
    - Spreek over de kleine daden van verzet, de tederheid voor wie gebroken is
    - Eindig met een beeld, een zin die blijft hangen
    - Geen applausende conclusie, maar een uitnodiging om op te staan

    ---

    ## HARDE EISEN

    1.  **SHOW, DON'T TELL.**
        - VERBODEN: "Ik gebruik nu theopoëzie", "Laten we demytologiseren", "De hermeneutiek van..."
        - GEBODEN: Schilder beelden, vertel verhalen, laat de theologie GEBEUREN

    2.  **IK-VORM EN PERSOONLIJK**
        - "Ik las gisteren...", "Ik stond bij de halte en zag...", "Ik schaam me..."
        - Wees kwetsbaar, wees eerlijk, wees aanwezig

    3.  **GEEN DOMINEESTAAL**
        - VERBODEN: "Lieve gemeente", "De Heer zegt tot ons", "Laten wij bidden"
        - GEBODEN: Taal van de straat, van de krant, van de poëzie

    4.  **LENGTE: 1500-2000 WOORDEN**
        - Dit is een volledige preek, geen samenvatting
        - Neem de tijd om beelden uit te werken, spanningen op te bouwen

    5.  **ACTUALITEIT**
        - Noem MAN EN PAARD: Shell, Amazon, Ter Apel, Gaza, namen van politici
        - Wees niet bang om politiek te zijn - politieke theologie IS politiek

    6.  **NEDERLANDS PUBLIEK**
        - Deze preek is voor NEDERLANDSE hoorders in een Nederlandse kerk/gemeenschap
        - Gebruik HERKENBARE Nederlandse voorbeelden:
          * Plaatsen: Amsterdam, Rotterdam, Ter Apel, de Bijlmer, Schiphol, de Veluwe
          * Bedrijven: Shell, Ahold, PostNL, Booking.com, ASML, ING, Rabobank
          * Media: NOS, RTL, de Volkskrant, Trouw
          * Politiek: Tweede Kamer, toeslagenaffaire, asielbeleid, woningcrisis
          * Cultuur: voedselbanken, zwarte pieten-discussie, Koningsdag
          * Instituties: UWV, Belastingdienst, IND, COA
        - Vermijd Amerikaanse voorbeelden tenzij universeel (Amazon, Google)
        - Spreek over 'wij Nederlanders', 'hier in dit land', 'onze polders'

    7.  **POËTISCH MAAR TOEGANKELIJK**
        - Geen academisch jargon
        - Wel: metaforen, herhalingen, ritme, stilte

    8.  **FEITELIJK CORRECT**
        - Controleer je feiten! Geen onjuistheden over technologie, bedrijven, geografie, bijbel
        - Tesla's zijn ELEKTRISCH (geen uitlaatgassen!)
        - Zonnepanelen en windmolens produceren geen CO2
        - Als je wilt spreken over vervuiling, gebruik: vrachtwagens, dieselauto's, vliegtuigen, cruiseschepen, kolencentrales
        - Controleer bijbelse verwijzingen: wie, wat, waar, wanneer
        - Controleer statistieken: zijn de getallen plausibel?

    ---

    ## STIJLINSPIRATIE (Gebruik de cadans en toon, NIET de inhoud!)

    {examples_str}

    ---

    **SCHRIJF NU DE PREEK:**
    """

    response = model.generate_content(prompt)
    return response.text

def main():
    setup_client()
    
    # 1. Input Scripture
    scripture = input("Geef de Bijbeltekst op (bijv. Lukas 2:1-4): ")
    if not scripture:
        print("Geen tekst opgegeven.")
        return

    # 2. Initialize Model
    try:
        model = genai.GenerativeModel(
            model_name=MODEL_NAME,
            system_instruction=construct_system_prompt()
        )
    except Exception as e:
        print(f"Error initializing model {MODEL_NAME}: {e}")
        model = genai.GenerativeModel(
            model_name="gemini-3-preview",
            system_instruction=construct_system_prompt()
        )

    # 3. Fetch Bible Text
    print(f"Ophalen van tekst voor '{scripture}' van hispage.nl...")
    bible_text, fetch_log = BibleFetcher.fetch_text(scripture)
    print(f"   > Gevonden tekst (eerste 100 tekens): {bible_text[:100]}...")

    # 4. Load Examples
    print("Ophalen van willekeurige voorbeeldpreken...")
    examples = load_random_examples(n=4)
    
    # 5. Pre-work (Context Analysis)
    print("Analyseren van de context...")
    context_analysis = perform_pre_work(model, scripture, bible_text)
    print(f"\n--- Analyse ---\n{context_analysis}\n---------------")

    # 6. Generate Sermon
    print("Schrijven van de preek...")
    sermon = generate_sermon(model, scripture, bible_text, context_analysis, examples)
    
    # 7. Output and Log
    print("\n--- Preek van Dorothee Sölle (LLM) ---\n")
    print(sermon)
    
    # Create output directory
    output_dir = "output/preken"
    os.makedirs(output_dir, exist_ok=True)
    
    # Create a safe filename
    timestamp_fs = datetime.datetime.now().strftime("%Y%m%d_%H%M")
    safe_scripture = re.sub(r'[^\w\s-]', '', scripture).strip().replace(' ', '_')
    base_filename = f"{timestamp_fs}_{safe_scripture}"
    
    sermon_path = os.path.join(output_dir, f"{base_filename}.md")
    log_path = os.path.join(output_dir, f"{base_filename}.log")
    
    # Save Sermon
    with open(sermon_path, "w", encoding="utf-8") as f:
        f.write(f"# Preek over {scripture}\n")
        f.write(f"*Gegenereerd op: {datetime.datetime.now().strftime('%d-%m-%Y %H:%M')}*\n\n")
        f.write(sermon)
    
    # Save Log
    with open(log_path, "w", encoding="utf-8") as f:
        f.write("=== GENERATION LOG ===\n")
        f.write(f"Timestamp: {datetime.datetime.now()}\n")
        f.write(f"Scripture Input: {scripture}\n")
        f.write(f"Model: {MODEL_NAME}\n\n")
        
        f.write("--- BIBLE FETCHING ---\n")
        f.write(fetch_log + "\n\n")
        f.write(f"--- FULL SCRAPED BIBLE TEXT (HSV) ---\n{bible_text}\n\n")
        
        f.write("--- CONTEXT ANALYSIS ---\n")
        f.write(context_analysis + "\n\n")

        f.write("--- EXAMPLES USED ---\n")
        for ex in examples:
            f.write(f"- {ex['title']} ({ex['scripture']})\n")

        f.write("\n--- GENERATED SERMON ---\n")
        f.write(sermon + "\n")

    print(f"\nPreek opgeslagen in: {sermon_path}")
    print(f"Logbestand opgeslagen in: {log_path}")

if __name__ == "__main__":
    main()