import json
import re
from datetime import datetime
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) "
        "AppleWebKit/605.1.15 Safari/604.1"
    )
}


def clean(text):
    return re.sub(r"\s+", " ", text or "").strip()


def load_sources():
    with open("sources.json", "r", encoding="utf-8") as f:
        return json.load(f)


def load_existing_jobs():
    try:
        with open("jobs.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except Exception:
        return []


def classify(title):
    text = title.lower()

    categories = {
        "리서치": ["리서치", "research", "analyst", "애널리스트"],
        "IB": ["ib", "investment banking", "기업금융", "ipo", "m&a"],
        "인프라·대체투자": [
            "인프라", "대체투자", "alternative", "infrastructure",
            "항공기", "에너지", "신재생"
        ],
        "PF·부동산": ["pf", "project finance", "부동산", "real estate"],
        "FICC": ["ficc", "채권", "fixed income", "외환", "fx", "credit"],
        "자산운용": ["자산운용", "운용", "portfolio", "fund manager"],
        "PE·VC": ["private equity", "venture capital", "pe", "vc"],
        "리스크": ["리스크", "risk", "준법", "compliance"],
    }

    for category, keywords in categories.items():
        if any(keyword in text for keyword in keywords):
            return category

    return "기타 금융"


def collect_source(source):
    url = source.get("url")
    company = source.get("company") or source.get("name") or "금융회사"

    if not url:
        return []

    response = requests.get(url, headers=HEADERS, timeout=20)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    jobs = []

    for link in soup.find_all("a", href=True):
        title = clean(link.get_text(" ", strip=True))

        if len(title) < 5:
            continue

        keywords = [
            "채용", "인턴", "경력", "신입", "리서치",
            "투자", "운용", "IB", "PF", "FICC",
            "analyst", "research"
        ]

        if not any(k.lower() in title.lower() for k in keywords):
            continue

        job_url = urljoin(url, link["href"])

        jobs.append({
            "company": company,
            "title": title,
            "category": classify(title),
            "url": job_url,
            "source": company + " 공식 채용",
            "collected_at": datetime.now().isoformat(timespec="seconds")
        })

    return jobs


def deduplicate(jobs):
    result = []
    seen = set()

    for job in jobs:
        key = (
            clean(job.get("company", "")).lower(),
            clean(job.get("title", "")).lower(),
            job.get("url", "")
        )

        if key in seen:
            continue

        seen.add(key)
        result.append(job)

    return result


def main():
    sources = load_sources()
    existing = load_existing_jobs()

    if isinstance(sources, dict):
        sources = sources.get("sources", [])

    collected = []

    for source in sources:
        try:
            jobs = collect_source(source)
            collected.extend(jobs)
            print(
                f"[OK] {source.get('company', source.get('name', 'source'))}: "
                f"{len(jobs)} jobs"
            )
        except Exception as e:
            print(
                f"[ERROR] {source.get('company', source.get('name', 'source'))}: {e}"
            )

    # 수집 실패로 기존 공고 전체가 사라지는 것을 방지
    if collected:
        final_jobs = deduplicate(collected)
    else:
        final_jobs = existing

    with open("jobs.json", "w", encoding="utf-8") as f:
        json.dump(final_jobs, f, ensure_ascii=False, indent=2)

    print(f"FINJOB update complete: {len(final_jobs)} jobs")


if __name__ == "__main__":
    main()
