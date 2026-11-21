#!/usr/bin/env python3
"""Scan Google Maps for trade businesses in DFW, load them into GoHighLevel
as contacts (deduped by GHL upsert), and attach a drafted, personalized
first-touch email as a note. You review/send from the GHL mobile app.

Env vars: APIFY_TOKEN, GHL_TOKEN (Private Integration token), GHL_LOCATION_ID
Usage:    python scan.py --dry-run          # writes leads_preview.csv only
          python scan.py                    # pushes to GHL
"""
import argparse, csv, os, random, re, sys, time
import requests

TRADES = ["plumber", "electrician", "HVAC contractor", "roofer", "painter",
          "landscaper", "handyman", "concrete contractor", "fence contractor",
          "flooring contractor"]
CITIES = ["Dallas, TX", "Fort Worth, TX", "Arlington, TX", "Plano, TX",
          "Irving, TX", "Garland, TX", "Frisco, TX", "McKinney, TX",
          "Denton, TX", "Grand Prairie, TX", "Mesquite, TX", "Carrollton, TX"]

# Edit this: what you actually offer. {first}, {company}, {trade}, {city},
# {rating}, {reviews} are filled in per lead. Several variants keep it natural.
SENDER = os.environ.get("SENDER_NAME", "YOUR NAME")
OFFER = os.environ.get("OFFER", "YOUR ONE-LINE OFFER")
TEMPLATES = [
    ("Quick question, {company}",
     "Hi {first},\n\nI came across {company} while looking at {trade} businesses in {city}"
     "{review_line} and wanted to reach out directly.\n\n{offer}\n\n"
     "If it's useful, I can send a few details. If not, no worries at all.\n\n{sender}"),
    ("{company} - {city}",
     "Hi {first},\n\nI work with local {trade} companies around DFW. {company} stood out"
     "{review_line}.\n\n{offer}\n\nWorth a quick chat this week?\n\n{sender}"),
]
STOP = set("the and for with you your our we are is to of in on at a an this that "
           "from by call us free estimate service services quality".split())

def looks_english(text):
    words = re.findall(r"[a-zA-Z']+", (text or "").lower())
    if len(words) < 8:
        return None  # not enough text to judge
    return sum(w in STOP for w in words) / len(words) > 0.12

def scan(apify_token, per_search):
    inp = {"searchStringsArray": [f"{t}" for t in TRADES],
           "locationQuery": "Dallas-Fort Worth, TX",
           "maxCrawledPlacesPerSearch": per_search,
           "language": "en", "scrapeContacts": True,
           "skipClosedPlaces": True}
    r = requests.post("https://api.apify.com/v2/acts/compass~crawler-google-places/run-sync-get-dataset-items",
                      params={"token": apify_token}, json=inp, timeout=900)
    r.raise_for_status()
    return r.json()

def normalize(p):
    emails = p.get("emails") or []
    return {
        "company": p.get("title", "").strip(),
        "trade": (p.get("categoryName") or "contractor").lower(),
        "phone": p.get("phone") or "",
        "email": emails[0] if emails else "",
        "website": p.get("website") or "",
        "city": p.get("city") or "Dallas",
        "address": p.get("street") or "",
        "rating": p.get("totalScore"), "reviews": p.get("reviewsCount") or 0,
        "description": p.get("description") or "",
    }

def draft(l):
    subj, body = random.choice(TEMPLATES)
    review_line = (f" ({l['rating']} stars across {l['reviews']} reviews)"
                   if l["rating"] and l["reviews"] >= 10 else "")
    f = dict(first="there", company=l["company"], trade=l["trade"], city=l["city"],
             review_line=review_line, offer=OFFER, sender=SENDER)
    return subj.format(**f), body.format(**f)

def ghl(path, token, **kw):
    h = {"Authorization": f"Bearer {token}", "Version": "2021-07-28",
         "Content-Type": "application/json", "Accept": "application/json"}
    r = requests.post("https://services.leadconnectorhq.com" + path, headers=h, timeout=30, **kw)
    r.raise_for_status()
    return r.json()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--per-search", type=int, default=50)
    ap.add_argument("--min-reviews", type=int, default=5)
    ap.add_argument("--require-english", action="store_true",
                    help="skip listings whose own description reads as non-English")
    a = ap.parse_args()
    try:
        raw = scan(os.environ["APIFY_TOKEN"], a.per_search)
    except KeyError:
        sys.exit("Set APIFY_TOKEN")
    leads, seen = [], set()
    for p in raw:
        l = normalize(p)
        key = (l["phone"] or l["website"] or l["company"]).lower()
        if not l["company"] or key in seen or l["reviews"] < a.min_reviews:
            continue
        if not (l["email"] or l["phone"]):
            continue
        if a.require_english and looks_english(l["description"]) is False:
            continue
        seen.add(key)
        l["subject"], l["body"] = draft(l)
        leads.append(l)
    print(f"{len(raw)} scraped -> {len(leads)} usable leads")
    if a.dry_run:
        with open("leads_preview.csv", "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=leads[0].keys()); w.writeheader(); w.writerows(leads)
        print("wrote leads_preview.csv"); return
    tok, loc = os.environ["GHL_TOKEN"], os.environ["GHL_LOCATION_ID"]
    for l in leads:
        res = ghl("/contacts/upsert", tok, json={
            "locationId": loc, "companyName": l["company"], "name": l["company"],
            "email": l["email"] or None, "phone": l["phone"] or None,
            "website": l["website"] or None, "city": l["city"], "state": "TX",
            "address1": l["address"], "source": "DFW trade scan",
            "tags": ["dfw-trades", "to-review", l["trade"].replace(" ", "-")]})
        c = res["contact"]["id"]
        if res.get("new") is False:   # already in GHL: don't re-draft or re-add
            continue
        ghl(f"/contacts/{c}/notes", tok, json={
            "body": f"DRAFT EMAIL\nSubject: {l['subject']}\n\n{l['body']}\n\nSite: {l['website']}"})
        time.sleep(0.3)
    print("done: review contacts tagged 'to-review' in GHL")

if __name__ == "__main__":
    main()
