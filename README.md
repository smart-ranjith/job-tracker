# 🎯 Ranjith G — Automated Job Tracker

Auto-scrapes **Internshala, Naukri, LinkedIn, Unstop** daily.
Scores jobs against your profile. Hosts a live dashboard on GitHub Pages.

## ⚡ Setup (5 minutes)

### Step 1 — Create GitHub repo
1. Go to [github.com](https://github.com) → **New repository**
2. Name it: `job-tracker`
3. Set to **Public** (required for GitHub Pages free hosting)
4. Click **Create repository**

### Step 2 — Upload these files
Upload all files from this zip into the repo:
- `scraper.py`
- `index.html`
- `requirements.txt`
- `data/jobs.json`
- `.github/workflows/scrape.yml`

### Step 3 — Enable GitHub Pages
1. Repo → **Settings** → **Pages**
2. Source → **Deploy from branch**
3. Branch → `main` → folder `/root`
4. Click **Save**
5. Your dashboard URL: `https://YOUR_USERNAME.github.io/job-tracker`

### Step 4 — Enable GitHub Actions
1. Repo → **Actions** tab
2. Click **"I understand my workflows, enable them"**
3. Go to **Actions → Daily Job Scraper → Run workflow**
4. Click **Run workflow** (manual first run)

### Step 5 — Done!
- Scraper runs **every day at 8:30 AM IST** automatically
- Dashboard updates live at your GitHub Pages URL
- Just open the URL anytime to see fresh jobs

## 🔧 Customize
Edit `scraper.py` → `PROFILE` section to update your skills anytime.

## 📊 What it scrapes
| Platform | Type |
|---|---|
| Internshala | Internships (best for freshers) |
| Naukri | Jobs 0-1 year experience |
| LinkedIn | Public internship listings |
| Unstop | Competitions + jobs |
