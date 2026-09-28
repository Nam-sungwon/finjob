import json
import re
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


# --------------------------------------------------
# 경로 설정
# collect_jobs.py 위치:
# finjob/.github/workflows/collect_jobs.py
#
# 실제 데이터 파일 위치:
# finjob/sources.json
# finjob/jobs.json
# --------------------------------------------------

ROOT_DIR = Path(__file__).resolve().parents[2]

SOURCES_FILE = ROOT_DIR / "sources.json"
JOBS_FILE = ROOT_DIR / "jobs.json"


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) "
        "AppleWebKit/605.1.15 Safari/604.1"
    )
}


def clean(text):
    return re.sub(r"\s+", " ", text or "").strip()


def load_sources():
    if not SOURCES_FILE.exists():
        print(f"[ERROR] sources.json not found: {SOURCES_FILE}")
        return []

    with open(SOURCES_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, dict):
        return data.get("sources", [])

    if isinstance(data, list):
        return data

    return []


def load_existing_jobs():
    if not JOBS_FILE.exists():
        return []

    try:
        with open(JOBS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        if isinstance(data, list):
            return data

    except Exception as e:
        print(f"[WARNING] Could not read existing jobs.json: {e}")

    return []


def classify(title):
    text = title.lower()

    categories = {
        "리서치": [
            "리서치",
            "research",
            "analyst",
            "애널리스트",
        ],
        "IB": [
            "ib",
            "investment banking",
            "기업금융",
            "ipo",
            "m&a",
        ],
        "인프라·대체투자": [
            "인프라",
            "대체투자",
            "alternative",
            "infrastructure",
            "항공기",
            "에너지",
            "신재생",
        ],
        "PF·부동산": [
            "pf",
            "project finance",
            "부동산",
            "real estate",
        ],
        "FICC": [
            "ficc",
            "채권",
            "fixed income",
            "외환",
            "fx",
            "credit",
        ],
        "자산운용": [
            "자산운용",
            "운용",
            "portfolio",
            "fund manager",
        ],
        "PE·VC": [
            "private equity",
            "venture capital",
            "pe",
            "vc",
        ],
        "리스크": [
            "리스크",
            "risk",
            "준법",
            "compliance",
        ],
    }

    for category, keywords in categories.items():
        if any(keyword in text for keyword in keywords):
            return category

    return "기타 금융"


def collect_source(source):
    url = source.get("url")
    company = (
        source.get("company")
        or source.get("name")
        or "금융회사"
    )

    if not url:
        print(f"[SKIP] URL 없음: {company}")
        return []

    response = requests.get(
        url,
        headers=HEADERS,
        timeout=20,
    )

    response.raise_for_status()

    soup = BeautifulSoup(
        response.text,
        "html.parser",
    )

    jobs = []

    keywords = [
        "채용",
        "인턴",
        "경력",
        "신입",
        "리서치",
        "투자",
        "운용",
        "IB",
        "PF",
        "FICC",
        "analyst",
        "research",
    ]

    for link in soup.find_all("a", href=True):

        title = clean(
            link.get_text(
                " ",
                strip=True,
            )
        )

        if len(title) < 5:
            continue

        if not any(
            keyword.lower() in title.lower()
            for keyword in keywords
        ):
            continue

        job_url = urljoin(
            url,
            link["href"],
        )

        jobs.append(
            {
                "company": company,
                "title": title,
                "category": classify(title),
                "url": job_url,
                "source": f"{company} 공식 채용",
                "collected_at": datetime.now().isoformat(
                    timespec="seconds"
                ),
            }
        )

    return jobs


def deduplicate(jobs):
    result = []
    seen = set()

    for job in jobs:

        key = (
            clean(
                job.get(
                    "company",
                    "",
                )
            ).lower(),
            clean(
                job.get(
                    "title",
                    "",
                )
            ).lower(),
            job.get(
                "url",
                "",
            ),
        )

        if key in seen:
            continue

        seen.add(key)
        result.append(job)

    return result


def save_jobs(jobs):
    with open(
        JOBS_FILE,
        "w",
        encoding="utf-8",
    ) as f:

        json.dump(
            jobs,
            f,
            ensure_ascii=False,
            indent=2,
        )


def main():

    print("=" * 50)
    print("FINJOB collector start")
    print(f"Repository root: {ROOT_DIR}")
    print(f"Sources file: {SOURCES_FILE}")
    print(f"Jobs file: {JOBS_FILE}")
    print("=" * 50)

    sources = load_sources()
    existing_jobs = load_existing_jobs()

    print(f"Sources: {len(sources)}")
    print(f"Existing jobs: {len(existing_jobs)}")

    collected_jobs = []

    for source in sources:

        company = (
            source.get("company")
            or source.get("name")
            or "source"
        )

        try:

            jobs = collect_source(source)

            collected_jobs.extend(jobs)

            print(
                f"[OK] {company}: "
                f"{len(jobs)} jobs"
            )

        except Exception as e:

            print(
                f"[ERROR] {company}: {e}"
            )

    # 모든 사이트 수집 실패 시
    # 기존 jobs.json을 보존
    if collected_jobs:

        final_jobs = deduplicate(
            collected_jobs
        )

    else:

        print(
            "[WARNING] 새 공고를 수집하지 못했습니다. "
            "기존 jobs.json을 유지합니다."
        )

        final_jobs = existing_jobs

    save_jobs(final_jobs)

    print("=" * 50)
    print(
        f"FINJOB update complete: "
        f"{len(final_jobs)} jobs"
    )
    print("=" * 50)


if __name__ == "__main__":
    main()
