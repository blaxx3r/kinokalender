import requests
from bs4 import BeautifulSoup
from ics import Calendar, Event
from datetime import datetime
from collections import defaultdict

# URL der Filmvorschau-Seiten
BASE_URL = "https://www.filmstarts.de/filme-vorschau/?page={}"

# Deutsche Monatsnamen übersetzen
GERMAN_MONTHS = {
    "Januar": "January", "Februar": "February", "März": "March",
    "April": "April", "Mai": "May", "Juni": "June",
    "Juli": "July", "August": "August", "September": "September",
    "Oktober": "October", "November": "November", "Dezember": "December"
}

def translate_month(date_str):
    """Übersetzt Monatsnamen ins Englische für datetime-Kompatibilität."""
    for de, en in GERMAN_MONTHS.items():
        if de in date_str:
            return date_str.replace(de, en)
    return date_str

def remove_duplicates_by_title(movies):
    """
    Behalte nur den frühesten Termin pro Filmname.
    """
    earliest = defaultdict(lambda: datetime.max.date())
    for title, date in movies:
        if date < earliest[title]:
            earliest[title] = date
    return list(earliest.items())

def scrape_all_pages(max_safe_pages=30):
    """Liest alle Seiten der Filmvorschau, bis keine weiteren Filme gefunden werden."""
    page = 1
    all_entries = []

    while page <= max_safe_pages:
        url = BASE_URL.format(page)
        print(f"🔎 Lade Seite {page}: {url}")
        response = requests.get(url)
        soup = BeautifulSoup(response.text, "html.parser")

        film_items = soup.select("div.card.entity-card.entity-card-list")
        if not film_items:
            print("🚫 Keine weiteren Filme gefunden – Abbruch.")
            break

        for item in film_items:
            title_tag = item.select_one("h2.meta-title a.meta-title-link")
            date_tag = item.select_one("div.meta-body-info span.date")
            if not title_tag or not date_tag:
                continue

            title = title_tag.text.strip()
            raw_date = date_tag.text.strip()
            translated_date = translate_month(raw_date)

            try:
                date = datetime.strptime(translated_date, "%d. %B %Y").date()
            except ValueError:
                continue

            all_entries.append((title, date))

        page += 1

    return all_entries

def create_ics_file(movies, filename="kinostarts.ics"):
    """Erzeugt eine .ics-Kalenderdatei aus den Kinostarts."""
    calendar = Calendar()
    for title, date in movies:
        event = Event()
        event.name = f"🍿 {title}"
        event.begin = date.isoformat()
        event.make_all_day()
        calendar.events.add(event)

    with open(filename, "w", encoding="utf-8") as f:
        f.writelines(calendar)
    print(f"\n✅ {len(movies)} Filme exportiert nach '{filename}'")

if __name__ == "__main__":
    kinostarts = scrape_all_pages()
    if kinostarts:
        unique_kinostarts = remove_duplicates_by_title(kinostarts)
        create_ics_file(unique_kinostarts)
    else:
        print("⚠️ Keine Filme gefunden.")
