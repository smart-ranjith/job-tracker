import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime, timezone
import time
import random
import hashlib
import os
from urllib.parse import quote_plus

# ── SCRAPERAPI ─────────────────────────────────────────────────────
SCRAPER_KEY      = os.environ.get("SCRAPER_API_KEY", "")

# ── TELEGRAM ───────────────────────────────────────────────────────
TELEGRAM_TOKEN   = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")

def send_telegram(msg):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        return
    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            json={"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "HTML"},
            timeout=10
        )
        print("  📱 Telegram sent!")
    except Exception as e:
        print(f"  ⚠ Telegram failed: {e}")

# ── HEADERS ────────────────────────────────────────────────────────
HEADERS_POOL = [
    {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Referer": "https://www.google.com/",
    },
    {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
        "Accept-Language": "en-GB,en;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Referer": "https://www.bing.com/",
    },
    {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.8",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.7",
        "Referer": "https://www.google.co.in/",
    },
]

def get_headers():
    return random.choice(HEADERS_POOL)

# ── PROFILE ────────────────────────────────────────────────────────
PROFILE = {
    "skills": ["python", "java", "mysql", "html", "css", "firebase",
               "git", "excel", "data analytics", "automation", "tailwind",
               "sql", "rest api", "backend", "web"],
    "strong": ["mysql", "excel", "python", "html", "css", "sql", "automation"],
    "weak":   ["react", "rest api", "machine learning", "vite", "django", "flask"],
    "keywords": ["python", "java", "full stack", "data", "backend", "embedded",
                 "software", "developer", "intern", "fresher", "automation",
                 "web", "mysql", "analytics", "sql", "business analyst",
                 "data engineer", "api", "engineer"],
    "avoid": ["hr", "sales", "marketing", "content writer", "accountant",
              "finance", "legal", "graphic design", "video editor",
              "telecaller", "bpo", "receptionist"]
}

# All skills to check for match/missing
ALL_SKILLS = [
    "python", "java", "mysql", "sql", "html", "css", "javascript",
    "react", "node", "django", "flask", "fastapi", "spring", "git",
    "github", "rest api", "firebase", "excel", "power bi", "tableau",
    "pandas", "numpy", "machine learning", "deep learning", "aws",
    "docker", "linux", "mongodb", "postgresql", "tailwind", "automation",
    "selenium", "data analytics", "backend", "full stack"
]

KNOWN_SKILLS = set([
    "python", "java", "mysql", "sql", "html", "css", "git",
    "github", "firebase", "excel", "tailwind", "automation",
    "backend", "data analytics"
])

# ── LOCATION ───────────────────────────────────────────────────────
CHENNAI_KEYWORDS = [
    "chennai", "tambaram", "sholinganallur", "adyar", "anna nagar",
    "t nagar", "kodambakkam", "velachery", "chengalpattu", "perambur",
    "ambattur", "avadi", "porur", "maduravoyal", "chromepet", "pallavaram",
    "guindy", "teynampet", "nungambakkam", "mylapore"
]
ONLINE_KEYWORDS = ["remote", "work from home", "wfh", "online",
                   "hybrid", "virtual", "anywhere", "pan india"]

NEARBY_CITIES = [
    "bangalore", "bengaluru", "hyderabad", "pune", "coimbatore",
    "trichy", "madurai", "salem", "vellore"
]

def is_location_allowed(location, desc=""):
    loc  = location.lower()
    text = (location + " " + desc).lower()
    if any(c in loc for c in CHENNAI_KEYWORDS):
        return True, "chennai"
    if any(o in text for o in ONLINE_KEYWORDS):
        return True, "online"
    if loc.strip() in ["", "india", "pan india", "across india"]:
        return True, "remote"
    if any(c in loc for c in NEARBY_CITIES):
        return True, "nearby"
    return False, "skip"

# ── JOB ID (for dedup across runs) ────────────────────────────────
def job_id(title, company):
    key = f"{title.lower().strip()[:40]}-{company.lower().strip()[:25]}"
    return hashlib.md5(key.encode()).hexdigest()[:12]

# ── SEEN JOBS ──────────────────────────────────────────────────────
def load_seen():
    try:
        with open("data/seen_jobs.json") as f:
            return set(json.load(f).get("ids", []))
    except:
        return set()

def save_seen(seen_ids):
    os.makedirs("data", exist_ok=True)
    with open("data/seen_jobs.json", "w") as f:
        json.dump({
            "ids": list(seen_ids),
            "updated": datetime.now().strftime("%Y-%m-%d")
        }, f)


# ── FAKE JOB FILTER ────────────────────────────────────────────────
SUSPICIOUS = [
    "urgent hiring", "no experience needed", "earn from home",
    "data entry", "copy paste", "whatsapp", "telegram",
    "guaranteed job", "100% placement", "fees required",
    "registration fee", "processing fee", "pay to apply"
]

def is_fake(title, company, desc=""):
    text = (title + " " + company + " " + desc).lower()
    if any(s in text for s in SUSPICIOUS):
        return True
    if company.strip().lower() in ["", "unknown", "n/a"]:
        return True
    return False

# ── RESUME MATCH ───────────────────────────────────────────────────
def resume_match(title, desc=""):
    text = (title + " " + desc).lower()
    required = [s for s in ALL_SKILLS if s in text]
    if not required:
        return 50, []  # neutral if no skills mentioned
    matched = [s for s in required if s in KNOWN_SKILLS]
    missing = [s for s in required if s not in KNOWN_SKILLS]
    pct = int((len(matched) / len(required)) * 100) if required else 50
    return pct, missing[:5]  # cap missing at 5

# ── RESUME SCORE X/10 ──────────────────────────────────────────────
def resume_score(title, desc=""):
    pct, missing = resume_match(title, desc)
    score = round(pct / 10, 1)
    tips = []
    if missing:
        tips.append(f"Add {', '.join(missing[:3])} to resume")
    if pct < 50:
        tips.append("Highlight automation internship experience")
    if "intern" in (title + desc).lower() and pct >= 60:
        tips.append("Strong match — apply immediately")
    return score, tips

# ── 5D FIT EVALUATION ──────────────────────────────────────────────
def fit_evaluation(title, desc="", location="", date=None):
    text = (title + " " + desc).lower()
    scores = {}

    # 1. Skills match
    pct, _ = resume_match(title, desc)
    scores["skills"] = round(pct / 10, 1)

    # 2. Experience match
    exp_score = 5
    if any(w in text for w in ["fresher", "0-1", "0 year", "intern", "trainee", "entry"]):
        exp_score = 9
    elif any(w in text for w in ["2 year", "3 year", "senior", "lead", "manager"]):
        exp_score = 2
    elif any(w in text for w in ["1 year", "1-2"]):
        exp_score = 6
    scores["experience"] = exp_score

    # 3. Location fit
    _, loc_type = is_location_allowed(location)
    scores["location"] = {"chennai":10,"online":8,"remote":7,"skip":1}.get(loc_type, 5)

    # 4. Career alignment
    targets = ["python","software","full stack","data","backend",
               "java","automation","analyst","engineer","developer"]
    hits = sum(1 for r in targets if r in text)
    scores["career"] = min(10, round(4 + hits * 1.5, 1))

    # 5. Role freshness
    fresh_score = 5
    if date:
        try:
            days = (datetime.now() - datetime.strptime(date, "%Y-%m-%d")).days
            fresh_score = 10 if days<=1 else 9 if days<=2 else 7 if days<=7 else 4 if days<=10 else 2
        except: pass
    scores["freshness"] = fresh_score

    overall = round(sum(scores.values()) / len(scores), 1)
    return scores, overall

# ── STALENESS ──────────────────────────────────────────────────────
def staleness(date):
    try:
        days = (datetime.now() - datetime.strptime(date, "%Y-%m-%d")).days
        if days > 10: return "dead"
        if days > 7:  return "stale"
        return "fresh"
    except:
        return "unknown"

# ── SCORING ────────────────────────────────────────────────────────
def score_job(title, desc="", location="", posted_date=None):
    text = (title + " " + desc).lower()
    score = 0

    for bad in PROFILE["avoid"]:
        if bad in text:
            return 0, "skip"

    for skill in PROFILE["strong"]:
        if skill in text:
            score += 3

    for kw in PROFILE["keywords"]:
        if kw in text:
            score += 1

    if any(w in text for w in ["fresher", "intern", "trainee", "entry level", "graduate", "0-1", "0 - 1"]):
        score += 5

    for skill in PROFILE["weak"]:
        if skill in text:
            score -= 1

    # Date boost — newer = higher score
    if posted_date:
        try:
            now = datetime.now()
            pd  = datetime.strptime(posted_date, "%Y-%m-%d")
            days_old = (now - pd).days
            if days_old <= 1:
                score += 6
            elif days_old <= 2:
                score += 4
            elif days_old <= 7:
                score += 2
        except:
            pass

    if score >= 10:
        prob = "high"
    elif score >= 5:
        prob = "medium"
    elif score > 0:
        prob = "low"
    else:
        return 0, "skip"

    return score, prob

# ── CATEGORIZE ─────────────────────────────────────────────────────
def categorize(title):
    t = title.lower()
    if any(x in t for x in ["full stack","fullstack","mern","mean","react","frontend","web dev"]):
        return "fullstack"
    elif any(x in t for x in ["backend","api developer","server"]):
        return "backend"
    elif any(x in t for x in ["python","django","flask","fastapi","automation"]):
        return "python"
    elif any(x in t for x in ["data engineer","etl","pipeline","big data"]):
        return "dataeng"
    elif any(x in t for x in ["data analyst","analytics","sql analyst","bi analyst","business analyst","power bi"]):
        return "data"
    elif any(x in t for x in ["java","spring","android","mobile","kotlin"]):
        return "java"
    elif any(x in t for x in ["ml","machine learning","ai","deep learning","nlp"]):
        return "ml"
    elif any(x in t for x in ["software","developer","engineer","programmer"]):
        return "software"
    else:
        return "general"

# ── BUILD JOB OBJECT ───────────────────────────────────────────────
def make_job(title, company, location, source, url, desc="", posted_date=None):
    if is_fake(title, company, desc):
        return None

    allowed, loc_type = is_location_allowed(location, desc)
    if not allowed:
        return None

    today = datetime.now().strftime("%Y-%m-%d")
    date  = posted_date or today
    score, prob = score_job(title, desc, location, date)
    if prob == "skip":
        return None

    match_pct, missing      = resume_match(title, desc)
    res_score, res_tips     = resume_score(title, desc)
    fit_scores, fit_overall = fit_evaluation(title, desc, location, date)
    days_old = (datetime.now() - datetime.strptime(date, "%Y-%m-%d")).days if date else 99
    fresh = days_old <= 2
    stale = staleness(date)

    return {
        "id":          job_id(title, company),
        "title":       title.strip(),
        "company":     company.strip(),
        "location":    location.strip(),
        "loc_type":    loc_type,
        "source":      source,
        "url":         url,
        "prob":        prob,
        "score":       score,
        "match_pct":   match_pct,
        "missing":     missing,
        "res_score":   res_score,
        "res_tips":    res_tips,
        "fit":         fit_scores,
        "fit_overall": fit_overall,
        "domain":      categorize(title),
        "date":        date,
        "fresh":       fresh,
        "stale":       stale,
        "is_new":      False,  # set in main() after seen check
    }

# ── SAFE GET (ScraperAPI → bypasses IP blocks) ────────────────────
def safe_get(url, timeout=30, retries=2):
    # Try ScraperAPI first (residential IPs bypass anti-bot)
    if SCRAPER_KEY:
        api_url = f"http://api.scraperapi.com?api_key={SCRAPER_KEY}&url={quote_plus(url)}&country_code=in&render=true"
        for attempt in range(retries):
            try:
                r = requests.get(api_url, timeout=timeout)
                if r.status_code == 200:
                    return r
                time.sleep(2)
            except Exception as e:
                if attempt == retries - 1:
                    print(f"  ✗ ScraperAPI failed: {url[:50]} → {e}")
                time.sleep(random.uniform(2, 4))

    # Fallback: direct request
    for attempt in range(retries):
        try:
            r = requests.get(url, headers=get_headers(), timeout=20)
            r.raise_for_status()
            return r
        except Exception as e:
            if attempt == retries - 1:
                print(f"  ✗ Direct failed: {url[:50]}")
            time.sleep(random.uniform(1, 3))
    return None

def sleep():
    time.sleep(random.uniform(1.5, 3.0))

# ── INTERNSHALA ────────────────────────────────────────────────────
def scrape_internshala():
    jobs, searches = [], [
        "python-developer", "software-developer", "web-developer",
        "data-analytics", "java-developer", "full-stack-developer",
        "backend-developer", "sql-developer", "business-analyst",
        "data-engineer", "automation-testing"
    ]
    for search in searches:
        r = safe_get(f"https://internshala.com/internships/{search}-internship/")
        if not r: sleep(); continue
        soup  = BeautifulSoup(r.text, "html.parser")
        cards = soup.select(".individual_internship") or soup.select(".internship_meta")
        for card in cards[:6]:
            try:
                title   = (card.select_one(".profile") or card.select_one("h3") or card.select_one(".title")).get_text(strip=True)
                company = (card.select_one(".company_name") or card.select_one(".company-name")).get_text(strip=True)
                loc_el  = card.select_one(".location_link") or card.select_one(".location")
                location= loc_el.get_text(strip=True) if loc_el else "India"
                link_el = card.select_one("a[href]")
                url     = ("https://internshala.com" + link_el["href"]) if link_el and link_el["href"].startswith("/") else link_el["href"] if link_el else ""
                j = make_job(title, company, location, "Internshala", url)
                if j: jobs.append(j)
            except: continue
        sleep()
    return jobs

# ── NAUKRI ─────────────────────────────────────────────────────────
def scrape_naukri():
    jobs, searches = [], [
        "python-developer", "software-developer", "data-analyst",
        "java-developer", "web-developer", "full-stack-developer",
        "backend-developer", "sql-developer", "business-analyst",
        "data-engineer", "automation-engineer"
    ]
    for kw in searches:
        r = safe_get(f"https://www.naukri.com/{kw}-jobs-in-chennai?experience=0")
        if not r: sleep(); continue
        soup  = BeautifulSoup(r.text, "html.parser")
        cards = soup.select(".jobTuple") or soup.select("article") or soup.select("[class*='job-container']")
        for card in cards[:6]:
            try:
                title_el   = card.select_one(".title") or card.select_one("a.title") or card.select_one("[class*='title']")
                company_el = card.select_one(".companyInfo span") or card.select_one("[class*='company']")
                loc_el     = card.select_one(".location") or card.select_one("[class*='location']")
                link_el    = card.select_one("a[href]")
                title      = title_el.get_text(strip=True) if title_el else kw.replace("-"," ").title()
                company    = company_el.get_text(strip=True) if company_el else "Unknown"
                location   = loc_el.get_text(strip=True) if loc_el else "Chennai"
                url        = link_el["href"] if link_el else ""
                j = make_job(title, company, location, "Naukri", url)
                if j: jobs.append(j)
            except: continue
        sleep()
    return jobs

# ── LINKEDIN ───────────────────────────────────────────────────────
def scrape_linkedin():
    jobs, searches = [], [
        ("python developer intern", "Chennai"),
        ("software engineer intern", "Chennai"),
        ("data analyst intern", "Chennai"),
        ("full stack developer intern", "Chennai"),
        ("java developer intern", "Chennai"),
        ("backend developer intern", "India"),
        ("business analyst intern", "Chennai"),
        ("data engineer intern", "India"),
        ("sql developer intern", "India"),
    ]
    for kw, loc in searches:
        url = f"https://www.linkedin.com/jobs/search/?keywords={kw.replace(' ','%20')}&location={loc.replace(' ','%20')}&f_JT=I&f_E=1"
        r   = safe_get(url)
        if not r: sleep(); continue
        soup  = BeautifulSoup(r.text, "html.parser")
        cards = soup.select(".base-card") or soup.select(".jobs-search__results-list li")
        for card in cards[:6]:
            try:
                title   = (card.select_one(".base-search-card__title") or card.select_one("h3")).get_text(strip=True)
                company = (card.select_one(".base-search-card__subtitle") or card.select_one("h4")).get_text(strip=True)
                loc_el  = card.select_one(".job-search-card__location")
                location= loc_el.get_text(strip=True) if loc_el else loc
                link_el = card.select_one("a.base-card__full-link") or card.select_one("a")
                url2    = link_el["href"] if link_el else ""
                j = make_job(title, company, location, "LinkedIn", url2)
                if j: jobs.append(j)
            except: continue
        sleep()
    return jobs

# ── UNSTOP ─────────────────────────────────────────────────────────
def scrape_unstop():
    jobs = []
    r    = safe_get("https://unstop.com/api/public/opportunity/search-result?opportunity=jobs&per_page=30&filters[type][]=1")
    if not r: return jobs
    try:
        items = r.json().get("data", {}).get("data", [])
        for item in items:
            title    = item.get("title", "")
            company  = item.get("organisation", {}).get("name", "Unknown")
            location = item.get("city", "India")
            url      = f"https://unstop.com/jobs/{item.get('public_url','')}"
            j = make_job(title, company, location, "Unstop", url)
            if j: jobs.append(j)
    except: pass
    return jobs

# ── SHINE ──────────────────────────────────────────────────────────
def scrape_shine():
    jobs, searches = [], [
        "python-developer", "software-engineer", "data-analyst",
        "java-developer", "full-stack-developer", "backend-developer",
        "business-analyst", "sql-developer"
    ]
    for kw in searches:
        r = safe_get(f"https://www.shine.com/job-search/{kw}-jobs-in-chennai/")
        if not r: sleep(); continue
        soup  = BeautifulSoup(r.text, "html.parser")
        cards = soup.select(".jobCard") or soup.select("[class*='job-card']") or soup.select("article")
        for card in cards[:5]:
            try:
                title_el   = card.select_one("h2") or card.select_one(".title") or card.select_one("a")
                company_el = card.select_one(".company") or card.select_one("[class*='company']")
                loc_el     = card.select_one(".location") or card.select_one("[class*='location']")
                link_el    = card.select_one("a[href]")
                title      = title_el.get_text(strip=True) if title_el else kw.replace("-"," ").title()
                company    = company_el.get_text(strip=True) if company_el else "Unknown"
                location   = loc_el.get_text(strip=True) if loc_el else "Chennai"
                url        = link_el["href"] if link_el else ""
                if url and not url.startswith("http"):
                    url = "https://www.shine.com" + url
                j = make_job(title, company, location, "Shine", url)
                if j: jobs.append(j)
            except: continue
        sleep()
    return jobs

# ── FOUNDIT ────────────────────────────────────────────────────────
def scrape_foundit():
    jobs, searches = [], [
        "python-developer", "software-engineer", "data-analyst",
        "java-developer", "full-stack-developer", "backend-developer",
        "business-analyst", "data-engineer"
    ]
    for kw in searches:
        r = safe_get(f"https://www.foundit.in/search?query={kw.replace('-','+')}+fresher&location=Chennai")
        if not r: sleep(); continue
        soup  = BeautifulSoup(r.text, "html.parser")
        cards = soup.select(".jobCard") or soup.select("[class*='cardContainer']") or soup.select("article")
        for card in cards[:5]:
            try:
                title_el = card.select_one("h3") or card.select_one(".title") or card.select_one("a")
                co_el    = card.select_one(".company") or card.select_one("[class*='company']")
                loc_el   = card.select_one(".location") or card.select_one("[class*='location']")
                link_el  = card.select_one("a[href]")
                title    = title_el.get_text(strip=True) if title_el else kw.replace("-"," ").title()
                company  = co_el.get_text(strip=True) if co_el else "Unknown"
                location = loc_el.get_text(strip=True) if loc_el else "Chennai"
                url      = link_el["href"] if link_el else ""
                if url and not url.startswith("http"):
                    url = "https://www.foundit.in" + url
                j = make_job(title, company, location, "Foundit", url)
                if j: jobs.append(j)
            except: continue
        sleep()
    return jobs

# ── TIMESJOBS ──────────────────────────────────────────────────────
def scrape_timesjobs():
    jobs, searches = [], [
        "python", "software+engineer", "data+analyst",
        "java", "full+stack", "backend+developer", "business+analyst"
    ]
    for kw in searches:
        r = safe_get(f"https://www.timesjobs.com/candidate/job-search.html?searchType=Home_Search&sequence=0&startPage=1&textKeywords={kw}&cboWorkExp1=0&cboWorkExp2=0&txtLocation=Chennai")
        if not r: sleep(); continue
        soup  = BeautifulSoup(r.text, "html.parser")
        cards = soup.select(".job-bx") or soup.select(".clearfix.job")
        for card in cards[:5]:
            try:
                title_el = card.select_one("h2") or card.select_one(".job-title")
                co_el    = card.select_one(".joblist-comp-name") or card.select_one(".company")
                loc_el   = card.select_one(".job-locations") or card.select_one(".location")
                link_el  = card.select_one("h2 a") or card.select_one("a[href]")
                title    = title_el.get_text(strip=True) if title_el else kw
                company  = co_el.get_text(strip=True) if co_el else "Unknown"
                location = loc_el.get_text(strip=True) if loc_el else "Chennai"
                url      = link_el["href"] if link_el else ""
                j = make_job(title, company, location, "TimesJobs", url)
                if j: jobs.append(j)
            except: continue
        sleep()
    return jobs

# ── FRESHERSWORLD ──────────────────────────────────────────────────
def scrape_freshersworld():
    jobs, searches = [], [
        "python", "software-engineer", "java",
        "full-stack", "data-analyst", "backend", "business-analyst"
    ]
    for kw in searches:
        r = safe_get(f"https://www.freshersworld.com/jobs/jobsearch/{kw}-jobs-for-freshers-in-Chennai")
        if not r: sleep(); continue
        soup  = BeautifulSoup(r.text, "html.parser")
        cards = soup.select(".joblist") or soup.select("[class*='job-container']") or soup.select("li.job")
        for card in cards[:5]:
            try:
                title_el = card.select_one("h3") or card.select_one(".title") or card.select_one("a")
                co_el    = card.select_one(".company-name") or card.select_one(".company")
                loc_el   = card.select_one(".location")
                link_el  = card.select_one("a[href]")
                title    = title_el.get_text(strip=True) if title_el else kw
                company  = co_el.get_text(strip=True) if co_el else "Unknown"
                location = loc_el.get_text(strip=True) if loc_el else "Chennai"
                url      = link_el["href"] if link_el else ""
                if url and not url.startswith("http"):
                    url = "https://www.freshersworld.com" + url
                j = make_job(title, company, location, "Freshersworld", url)
                if j: jobs.append(j)
            except: continue
        sleep()
    return jobs

# ── HIRIST ─────────────────────────────────────────────────────────
def scrape_hirist():
    jobs, searches = [], [
        "python", "java", "full-stack", "data-analyst",
        "backend", "sql", "software-engineer"
    ]
    for kw in searches:
        r = safe_get(f"https://www.hirist.tech/search?q={kw}&l=Chennai&exp=0-1")
        if not r: sleep(); continue
        soup  = BeautifulSoup(r.text, "html.parser")
        cards = soup.select(".job-card") or soup.select("[class*='jobCard']") or soup.select("article")
        for card in cards[:5]:
            try:
                title_el = card.select_one("h2") or card.select_one(".title") or card.select_one("a")
                co_el    = card.select_one(".company") or card.select_one("[class*='company']")
                loc_el   = card.select_one(".location")
                link_el  = card.select_one("a[href]")
                title    = title_el.get_text(strip=True) if title_el else kw
                company  = co_el.get_text(strip=True) if co_el else "Unknown"
                location = loc_el.get_text(strip=True) if loc_el else "Chennai"
                url      = link_el["href"] if link_el else ""
                if url and not url.startswith("http"):
                    url = "https://www.hirist.tech" + url
                j = make_job(title, company, location, "Hirist", url)
                if j: jobs.append(j)
            except: continue
        sleep()
    return jobs

# ── WELLFOUND ──────────────────────────────────────────────────────
def scrape_wellfound():
    jobs, searches = [], [
        "python", "software-engineer", "data",
        "full-stack", "backend", "java"
    ]
    for kw in searches:
        r = safe_get(f"https://wellfound.com/jobs?q={kw}&l=India&jobType=internship")
        if not r: sleep(); continue
        soup  = BeautifulSoup(r.text, "html.parser")
        cards = soup.select("[class*='JobListing']") or soup.select("div[data-test='JobListing']") or soup.select("article")
        for card in cards[:5]:
            try:
                title_el = card.select_one("h2") or card.select_one("a") or card.select_one("[class*='title']")
                co_el    = card.select_one("[class*='company']") or card.select_one("h3")
                loc_el   = card.select_one("[class*='location']")
                link_el  = card.select_one("a[href]")
                title    = title_el.get_text(strip=True) if title_el else kw
                company  = co_el.get_text(strip=True) if co_el else "Unknown"
                location = loc_el.get_text(strip=True) if loc_el else "India"
                url      = link_el["href"] if link_el else ""
                if url and not url.startswith("http"):
                    url = "https://wellfound.com" + url
                j = make_job(title, company, location, "Wellfound", url)
                if j: jobs.append(j)
            except: continue
        sleep()
    return jobs

# ── DEDUP (by job ID across platforms) ────────────────────────────
def dedup(jobs):
    seen, result = set(), []
    for j in jobs:
        if j["id"] not in seen:
            seen.add(j["id"])
            result.append(j)
    return result

# ── TRENDS ─────────────────────────────────────────────────────────
def compute_trends(jobs):
    skill_count  = {}
    domain_count = {}
    source_count = {}

    for j in jobs:
        text = (j["title"] + " " + " ".join(j.get("missing", []))).lower()

        # Count skills mentioned in job titles
        for s in ALL_SKILLS:
            if s in text:
                skill_count[s] = skill_count.get(s, 0) + 1

        # Count domains
        d = j.get("domain", "general")
        domain_count[d] = domain_count.get(d, 0) + 1

        # Count sources
        src = j.get("source", "Unknown")
        source_count[src] = source_count.get(src, 0) + 1

    top_skills  = sorted(skill_count.items(),  key=lambda x: x[1], reverse=True)[:15]
    top_domains = sorted(domain_count.items(), key=lambda x: x[1], reverse=True)

    # Skills gap — most requested skills you DON'T have
    gap_skills = [(s, c) for s, c in top_skills if s not in KNOWN_SKILLS][:8]

    return {
        "updated":    datetime.now().strftime("%Y-%m-%d"),
        "top_skills": [{"skill": k, "count": v} for k, v in top_skills],
        "gap_skills": [{"skill": k, "count": v} for k, v in gap_skills],
        "domains":    [{"domain": k, "count": v} for k, v in top_domains],
        "sources":    source_count,
    }

# ── INDEED ─────────────────────────────────────────────────────────
def scrape_indeed():
    jobs, searches = [], [
        ("python developer intern", "Chennai"),
        ("software engineer intern", "Chennai"),
        ("data analyst intern", "Chennai"),
        ("full stack developer intern", "Chennai"),
        ("java developer intern", "Chennai"),
        ("backend developer intern", "Chennai"),
        ("business analyst intern", "Chennai"),
        ("python intern fresher", "India"),
        ("software developer fresher", "Chennai"),
        ("web developer intern", "Chennai"),
    ]
    for kw, loc in searches:
        url = f"https://in.indeed.com/jobs?q={quote_plus(kw)}&l={quote_plus(loc)}&fromage=14"
        r   = safe_get(url)
        if not r: sleep(); continue
        soup  = BeautifulSoup(r.text, "html.parser")
        cards = soup.select(".job_seen_beacon") or soup.select(".tapItem") or soup.select("[class*='job_']")
        for card in cards[:8]:
            try:
                t_el = card.select_one(".jobTitle") or card.select_one("h2")
                c_el = card.select_one(".companyName") or card.select_one("[class*='company']")
                l_el = card.select_one(".companyLocation") or card.select_one("[class*='location']")
                a_el = card.select_one("a[href]")
                title    = t_el.get_text(strip=True) if t_el else kw
                company  = c_el.get_text(strip=True) if c_el else "Unknown"
                location = l_el.get_text(strip=True) if l_el else loc
                href     = a_el["href"] if a_el else ""
                url2     = f"https://in.indeed.com{href}" if href.startswith("/") else href
                j = make_job(title, company, location, "Indeed", url2)
                if j: jobs.append(j)
            except: continue
        sleep()
    return jobs

# ── MAIN ───────────────────────────────────────────────────────────
SCRAPERS = [
    ("Internshala",   scrape_internshala),
    ("Naukri",        scrape_naukri),
    ("LinkedIn",      scrape_linkedin),
    ("Indeed",        scrape_indeed),
    ("Unstop",        scrape_unstop),
    ("Shine",         scrape_shine),
    ("Foundit",       scrape_foundit),
    ("TimesJobs",     scrape_timesjobs),
    ("Freshersworld", scrape_freshersworld),
    ("Hirist",        scrape_hirist),
    ("Wellfound",     scrape_wellfound),
]

def main():
    os.makedirs("data", exist_ok=True)
    # Debug secrets
    print(f"🔑 ScraperAPI: {'✅ LOADED' if SCRAPER_KEY else '❌ NOT FOUND'}")
    print(f"🔑 Telegram:   {'✅ LOADED' if TELEGRAM_TOKEN else '❌ NOT FOUND'}")

    seen_ids     = load_seen()
    all_jobs     = []
    source_stats = {}

    for name, fn in SCRAPERS:
        print(f"🔍 Scraping {name}...")
        try:
            jobs = fn()
            source_stats[name] = len(jobs)
            all_jobs += jobs
            print(f"   → {len(jobs)} jobs")
        except Exception as e:
            source_stats[name] = 0
            print(f"   ✗ {name} failed: {e}")

    all_jobs = dedup(all_jobs)

    chennai_count = len([j for j in all_jobs if j["loc_type"] == "chennai"])
    print(f"\n📍 Chennai jobs: {chennai_count} | Nearby/Remote: {len(all_jobs)-chennai_count}")

    # Mark new vs seen
    new_count = 0
    for j in all_jobs:
        j["is_new"] = j["id"] not in seen_ids
        if j["is_new"]:
            new_count += 1

    all_ids = seen_ids | {j["id"] for j in all_jobs}
    save_seen(all_ids)

    all_jobs.sort(key=lambda x: (x["score"], x["match_pct"]), reverse=True)

    high  = [j for j in all_jobs if j["prob"] == "high"]
    medium= [j for j in all_jobs if j["prob"] == "medium"]
    low   = [j for j in all_jobs if j["prob"] == "low"]
    fresh = [j for j in all_jobs if j["fresh"]]

    print(f"\n✅ Total unique: {len(all_jobs)}")
    print(f"   🟢 High:      {len(high)}")
    print(f"   🟡 Medium:    {len(medium)}")
    print(f"   🔴 Low:       {len(low)}")
    print(f"   ⚡ Fresh<48h: {len(fresh)}")
    print(f"   🆕 New today: {new_count}")
    print(f"\n🔌 Source health: {source_stats}")

    with open("data/jobs.json", "w") as f:
        json.dump({
            "updated":      datetime.now().strftime("%Y-%m-%d %H:%M UTC"),
            "total":        len(all_jobs),
            "source_stats": source_stats,
            "jobs":         all_jobs
        }, f, indent=2)

    trends = compute_trends(all_jobs)
    with open("data/trends.json", "w") as f:
        json.dump(trends, f, indent=2)

    print("💾 Saved → data/jobs.json + data/seen_jobs.json + data/trends.json")

    # ── TELEGRAM ALERT ─────────────────────────────────────────────
    new_high = [j for j in all_jobs if j["is_new"] and j["prob"] == "high"]
    if new_high:
        lines = [f"🎯 <b>{len(new_high)} NEW High-Match Jobs!</b>\n📅 {datetime.now().strftime('%d %b %Y')}\n"]
        for j in new_high[:5]:
            ref = " 🤝" if j.get("referral") else ""
            loc = {"chennai":"🏙","online":"💻","remote":"🌐","nearby":"📍"}.get(j["loc_type"],"📍")
            lines.append(f"• <b>{j['title']}</b>{ref}\n  {j['company']} | {loc}\n  Match: {j['match_pct']}% | {j['url']}\n")
        if len(new_high) > 5:
            lines.append(f"...+{len(new_high)-5} more")
        lines.append(f"\n🔗 https://smart-ranjith.github.io/job-tracker")
        send_telegram("\n".join(lines))
    else:
        send_telegram(
            f"📊 Daily Update — {datetime.now().strftime('%d %b %Y')}\n"
            f"Total: {len(all_jobs)} | High: {len(high)} | New: {new_count}\n"
            f"🔗 https://smart-ranjith.github.io/job-tracker"
        )

if __name__ == "__main__":
    main()