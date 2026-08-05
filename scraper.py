import requests
from bs4 import BeautifulSoup
import json
import re
from datetime import datetime
import time
import random

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

# ── PROFILE ─────────────────────────────────────────────────────────
PROFILE = {
    "skills": ["python", "java", "mysql", "html", "css", "iot", "firebase",
               "git", "excel", "data analytics", "automation", "tailwind",
               "embedded", "sql", "rest api"],
    "strong": ["mysql", "excel", "python automation", "iot", "html", "css"],
    "weak":   ["react", "rest api", "machine learning", "vite"],
    "keywords": ["python", "java", "full stack", "data", "iot", "embedded",
                 "software", "developer", "intern", "fresher", "automation",
                 "backend", "web", "mysql", "analytics"],
    "avoid": ["hr", "sales", "marketing", "content writer", "accountant",
              "finance", "legal", "graphic design", "video editor"]
}

# ── SCORING ─────────────────────────────────────────────────────────
def score_job(title, desc=""):
    text = (title + " " + desc).lower()
    score = 0
    matched = []

    # Avoid irrelevant roles
    for bad in PROFILE["avoid"]:
        if bad in text:
            return 0, "irrelevant"

    # Strong skill match
    for skill in PROFILE["strong"]:
        if skill in text:
            score += 3
            matched.append(skill)

    # General keyword match
    for kw in PROFILE["keywords"]:
        if kw in text:
            score += 1

    # Fresher bonus
    if any(w in text for w in ["fresher", "intern", "trainee", "entry level", "graduate"]):
        score += 5

    # Weak skills — lower score
    for skill in PROFILE["weak"]:
        if skill in text and skill not in matched:
            score -= 1

    if score >= 8:
        prob = "high"
    elif score >= 4:
        prob = "medium"
    elif score > 0:
        prob = "low"
    else:
        return 0, "skip"

    return score, prob

# ── INTERNSHALA ─────────────────────────────────────────────────────
def scrape_internshala():
    jobs = []
    searches = [
        "python-developer", "software-developer", "web-developer",
        "data-analytics", "iot", "java-developer", "full-stack-developer"
    ]
    for search in searches:
        try:
            url = f"https://internshala.com/internships/{search}-internship/"
            r = requests.get(url, headers=HEADERS, timeout=10)
            soup = BeautifulSoup(r.text, "html.parser")
            cards = soup.select(".internship_meta") or soup.select(".individual_internship")
            for card in cards[:5]:
                try:
                    title_el = card.select_one(".profile") or card.select_one("h3")
                    company_el = card.select_one(".company_name") or card.select_one(".company-name")
                    location_el = card.select_one(".location_link") or card.select_one(".location")
                    link_el = card.select_one("a")

                    title = title_el.get_text(strip=True) if title_el else search.replace("-", " ").title()
                    company = company_el.get_text(strip=True) if company_el else "Unknown"
                    location = location_el.get_text(strip=True) if location_el else "India"
                    link = "https://internshala.com" + link_el["href"] if link_el and link_el.get("href","").startswith("/") else (link_el["href"] if link_el else url)

                    score, prob = score_job(title)
                    if prob == "skip":
                        continue

                    jobs.append({
                        "title": title,
                        "company": company,
                        "location": location,
                        "source": "Internshala",
                        "url": link,
                        "prob": prob,
                        "score": score,
                        "domain": categorize(title),
                        "date": datetime.now().strftime("%Y-%m-%d")
                    })
                except:
                    continue
            time.sleep(random.uniform(1, 2))
        except Exception as e:
            print(f"Internshala error ({search}): {e}")
    return jobs

# ── NAUKRI ──────────────────────────────────────────────────────────
def scrape_naukri():
    jobs = []
    searches = [
        ("python-developer", "0-1"),
        ("software-developer", "0-1"),
        ("data-analyst", "0-1"),
        ("java-developer", "0-1"),
        ("web-developer", "0-1"),
        ("iot-developer", "0-1"),
        ("full-stack-developer", "0-1"),
    ]
    for keyword, exp in searches:
        try:
            url = f"https://www.naukri.com/{keyword}-jobs-in-chennai?experience={exp}"
            r = requests.get(url, headers=HEADERS, timeout=12)
            soup = BeautifulSoup(r.text, "html.parser")
            cards = soup.select(".jobTuple") or soup.select("article.jobTupleHeader") or soup.select("[class*='job-container']")
            for card in cards[:5]:
                try:
                    title_el = card.select_one(".title") or card.select_one("a.title") or card.select_one("[class*='title']")
                    company_el = card.select_one(".companyInfo") or card.select_one("[class*='company']")
                    location_el = card.select_one(".location") or card.select_one("[class*='location']")
                    link_el = card.select_one("a.title") or card.select_one("a")

                    title = title_el.get_text(strip=True) if title_el else keyword.replace("-", " ").title()
                    company = company_el.get_text(strip=True) if company_el else "Unknown"
                    location = location_el.get_text(strip=True) if location_el else "Chennai"
                    link = link_el["href"] if link_el and link_el.get("href") else url

                    score, prob = score_job(title)
                    if prob == "skip":
                        continue

                    jobs.append({
                        "title": title,
                        "company": company,
                        "location": location,
                        "source": "Naukri",
                        "url": link,
                        "prob": prob,
                        "score": score,
                        "domain": categorize(title),
                        "date": datetime.now().strftime("%Y-%m-%d")
                    })
                except:
                    continue
            time.sleep(random.uniform(1.5, 3))
        except Exception as e:
            print(f"Naukri error ({keyword}): {e}")
    return jobs

# ── LINKEDIN PUBLIC ──────────────────────────────────────────────────
def scrape_linkedin():
    jobs = []
    searches = [
        ("python developer intern", "Chennai"),
        ("software engineer intern", "Chennai"),
        ("data analyst intern", "Chennai"),
        ("full stack developer intern", "Chennai"),
        ("IoT intern", "Chennai"),
        ("java developer intern", "India"),
    ]
    for keyword, location in searches:
        try:
            kw_enc = keyword.replace(" ", "%20")
            loc_enc = location.replace(" ", "%20")
            url = f"https://www.linkedin.com/jobs/search/?keywords={kw_enc}&location={loc_enc}&f_JT=I&f_E=1"
            r = requests.get(url, headers=HEADERS, timeout=12)
            soup = BeautifulSoup(r.text, "html.parser")
            cards = soup.select(".jobs-search__results-list li") or soup.select(".base-card")
            for card in cards[:5]:
                try:
                    title_el = card.select_one(".base-search-card__title") or card.select_one("h3")
                    company_el = card.select_one(".base-search-card__subtitle") or card.select_one("h4")
                    location_el = card.select_one(".job-search-card__location") or card.select_one("[class*='location']")
                    link_el = card.select_one("a.base-card__full-link") or card.select_one("a")

                    title = title_el.get_text(strip=True) if title_el else keyword
                    company = company_el.get_text(strip=True) if company_el else "Unknown"
                    location_text = location_el.get_text(strip=True) if location_el else location
                    link = link_el["href"] if link_el and link_el.get("href") else url

                    score, prob = score_job(title)
                    if prob == "skip":
                        continue

                    jobs.append({
                        "title": title,
                        "company": company,
                        "location": location_text,
                        "source": "LinkedIn",
                        "url": link,
                        "prob": prob,
                        "score": score,
                        "domain": categorize(title),
                        "date": datetime.now().strftime("%Y-%m-%d")
                    })
                except:
                    continue
            time.sleep(random.uniform(2, 3))
        except Exception as e:
            print(f"LinkedIn error ({keyword}): {e}")
    return jobs

# ── UNSTOP ──────────────────────────────────────────────────────────
def scrape_unstop():
    jobs = []
    try:
        url = "https://unstop.com/api/public/opportunity/search-result?opportunity=jobs&per_page=20&filters[type][]=1&filters[eligible][]=1"
        r = requests.get(url, headers=HEADERS, timeout=10)
        data = r.json()
        items = data.get("data", {}).get("data", [])
        for item in items[:15]:
            try:
                title = item.get("title", "")
                company = item.get("organisation", {}).get("name", "Unknown")
                location = item.get("city", "India")
                link = f"https://unstop.com/jobs/{item.get('public_url','')}"
                score, prob = score_job(title)
                if prob == "skip":
                    continue
                jobs.append({
                    "title": title,
                    "company": company,
                    "location": location,
                    "source": "Unstop",
                    "url": link,
                    "prob": prob,
                    "score": score,
                    "domain": categorize(title),
                    "date": datetime.now().strftime("%Y-%m-%d")
                })
            except:
                continue
    except Exception as e:
        print(f"Unstop error: {e}")
    return jobs

# ── CATEGORIES ──────────────────────────────────────────────────────
def categorize(title):
    t = title.lower()
    if any(x in t for x in ["full stack","fullstack","mern","mean","react","frontend","backend","web dev"]):
        return "fullstack"
    elif any(x in t for x in ["python","django","flask","fastapi","automation"]):
        return "python"
    elif any(x in t for x in ["data","analyst","analytics","sql","mysql","bi","power bi"]):
        return "data"
    elif any(x in t for x in ["iot","embedded","hardware","firmware","arduino","raspberry","sensor"]):
        return "iot"
    elif any(x in t for x in ["java","spring","android","mobile","kotlin"]):
        return "java"
    elif any(x in t for x in ["ml","machine learning","ai","deep learning","nlp"]):
        return "ml"
    else:
        return "general"

# ── DEDUP ───────────────────────────────────────────────────────────
def dedup(jobs):
    seen = set()
    result = []
    for j in jobs:
        key = (j["title"].lower()[:30], j["company"].lower()[:20])
        if key not in seen:
            seen.add(key)
            result.append(j)
    return result

# ── MAIN ────────────────────────────────────────────────────────────
def main():
    print("🔍 Scraping Internshala...")
    all_jobs = scrape_internshala()
    print(f"   → {len(all_jobs)} jobs")

    print("🔍 Scraping Naukri...")
    n = scrape_naukri()
    all_jobs += n
    print(f"   → {len(n)} jobs")

    print("🔍 Scraping LinkedIn...")
    l = scrape_linkedin()
    all_jobs += l
    print(f"   → {len(l)} jobs")

    print("🔍 Scraping Unstop...")
    u = scrape_unstop()
    all_jobs += u
    print(f"   → {len(u)} jobs")

    # Dedup + sort by score
    all_jobs = dedup(all_jobs)
    all_jobs.sort(key=lambda x: x["score"], reverse=True)

    print(f"\n✅ Total unique jobs: {len(all_jobs)}")
    print(f"   High: {len([j for j in all_jobs if j['prob']=='high'])}")
    print(f"   Medium: {len([j for j in all_jobs if j['prob']=='medium'])}")
    print(f"   Low: {len([j for j in all_jobs if j['prob']=='low'])}")

    # Save JSON
    with open("data/jobs.json", "w") as f:
        json.dump({
            "updated": datetime.now().strftime("%Y-%m-%d %H:%M UTC"),
            "total": len(all_jobs),
            "jobs": all_jobs
        }, f, indent=2)

    print("💾 Saved to data/jobs.json")

if __name__ == "__main__":
    main()
