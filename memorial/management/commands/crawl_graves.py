import hashlib
import re
import time
import unicodedata
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from memorial.models import Martyr, SyncRun

BASE_URL = "https://nghiatranglietsyvietlao.org.vn"
ALLOWED_PREFIX = "/tra-cuu-phan-mo/"
DISALLOWED = ("/admin/", "/data/", "/includes/", "/install/", "/modules/", "/users/", "/statistics/")

def normalize(value):
    value = value.replace("đ", "d").replace("Đ", "D")
    return re.sub(r"\s+", " ", "".join(c for c in unicodedata.normalize("NFD", value) if unicodedata.category(c) != "Mn")).lower().strip()

class Command(BaseCommand):
    help = "Import public grave-list pages politely; never visits robots.txt-disallowed paths."

    def add_arguments(self, parser):
        parser.add_argument("--start-page", type=int, default=1)
        parser.add_argument("--end-page", type=int, default=217)
        parser.add_argument("--delay", type=float, default=1.2)
        parser.add_argument("--retries", type=int, default=3)

    def handle(self, *args, **opts):
        start, end, delay = opts["start_page"], opts["end_page"], max(opts["delay"], 1.0)
        retries = max(opts["retries"], 1)
        if start < 1 or end < start:
            raise CommandError("Invalid page range")
        run = SyncRun.objects.create()
        session = requests.Session()
        session.headers["User-Agent"] = "LietSiVietLao-CommunityArchive/1.0 (+https://lietsivietlao.8tech.vn; respectful public-data sync)"
        try:
            for page_no in range(start, end + 1):
                path = ALLOWED_PREFIX if page_no == 1 else f"{ALLOWED_PREFIX}page-{page_no}/"
                if any(path.startswith(blocked) for blocked in DISALLOWED):
                    raise CommandError(f"Blocked path: {path}")
                rows = []
                last_error = None
                for attempt in range(1, retries + 1):
                    try:
                        response = session.get(urljoin(BASE_URL, path), timeout=30)
                        response.raise_for_status()
                        soup = BeautifulSoup(response.text, "html.parser")
                        rows = soup.select("table tbody tr")
                        if rows:
                            break
                        last_error = f"empty response on attempt {attempt}"
                    except requests.RequestException as exc:
                        last_error = str(exc)
                    if attempt < retries:
                        time.sleep(attempt * 3)
                if not rows:
                    raise CommandError(f"No records found on page {page_no} after {retries} attempts ({last_error}); stopping safely")
                for row in rows:
                    cells = [cell.get_text(" ", strip=True) for cell in row.select("td")]
                    link = row.select_one('a[href*="/detail/liet-sy-"]')
                    if not link or len(cells) < 8:
                        continue
                    match = re.search(r"liet-sy-(\d+)", link.get("href", ""))
                    if not match:
                        continue
                    source_id = int(match.group(1))
                    values = {"name": cells[1], "normalized_name": normalize(cells[1]), "hometown": cells[2],
                        "birth_text": cells[3], "death_text": cells[4], "zone": cells[5], "grave_row": cells[6],
                        "grave_number": cells[7], "source_url": urljoin(BASE_URL, link["href"]),
                        "source_hash": hashlib.sha256("|".join(cells[1:8]).encode()).hexdigest()}
                    obj, created = Martyr.objects.update_or_create(source_id=source_id, defaults=values)
                    run.records_created += int(created)
                    run.records_updated += int(not created)
                    run.records_seen += 1
                run.pages_processed += 1
                run.save(update_fields=["pages_processed", "records_seen", "records_created", "records_updated"])
                self.stdout.write(f"page={page_no} records={run.records_seen}")
                if page_no < end:
                    time.sleep(delay)
            run.status, run.finished_at = "completed", timezone.now()
        except Exception as exc:
            run.status, run.finished_at, run.message = "failed", timezone.now(), str(exc)
            raise
        finally:
            run.save()
