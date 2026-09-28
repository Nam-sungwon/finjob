import json
import re
import hashlib
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


ROOT_DIR = Path(__file__).resolve().parents[2]

JOBS_FILE = ROOT_DIR / "jobs.json"


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) "
        "AppleWebKit/605.1.15 Safari/604.1"
    )
}


SHINHAN_URL = "https://recruit.shinhansec.com/recruit/list.do"


def clean(text):
    return re.sub(r"\s+", " ", text or "").strip()


def make_id(company, title, url):
    value = f"{company}|{title}|{url}"
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:14]


def classify_role(title):
    text = title.lower()

    categories = [
        (
            "리서치",
            [
                "리서치",
                "research",
                "ra ",
                "ra공개채용",
                "research assistant",
            ],
        ),
        (
            "IB",
            [
                "기업금융",
                "investment banking",
                " ib",
                "ib ",
                "ipo",
                "m&a",
                "인수금융",
            ],
        ),
        (
            "PF·부동산",
            [
                "pf",
                "부동산",
                "project finance",
                "구조화금융",
            ],
        ),
        (
            "FICC",
            [
                "채권",
                "ficc",
                "fixed income",
                "외환",
                "fx",
                "크레딧",
                "credit",
            ],
        ),
        (
            "인프라·대체투자",
            [
                "인프라",
                "대체투자",
                "alternative",
                "infrastructure",
                "신재생",
                "에너지",
            ],
        ),
        (
            "자산운용",
            [
                "운용",
                "패시브",
                "portfolio",
                "랩",
                "신탁",
            ],
        ),
        (
            "리스크",
            [
                "리스크",
                "risk",
                "준법",
                "compliance",
                "내부통제",
            ],
        ),
        (
            "디지털자산",
            [
                "디지털자산",
                "digital asset",
                "가상자산",
            ],
        ),
    ]

    for category, keywords in categories:
        if any(keyword in text for keyword in keywords):
            return category

    return "기타 금융"


def classify_type(text):
    text = text.lower()

    if "인턴" in text:
        return "인턴"

    if "신입" in text:
        return "신입"

    if "경력" in text:
        return "경력"

    return "기타"


def extract_deadline(text):
    match = re.search(
        r"(20\d{2})[.\-/](\d{1,2})[.\-/](\d{1,2})",
        text,
    )

    if not match:
        return None

    year, month, day = match.groups()

    return f"{year}-{int(month):02d}-{int(day):02d}"


def collect_shinhan():
    response = requests.get(
        SHINHAN_URL,
        headers=HEADERS,
        timeout=30,
    )

    response.raise_for_status()

    soup = BeautifulSoup(
        response.text,
        "html.parser",
    )

    jobs = []
    seen = set()

    for link in soup.find_all("a", href=True):

        href = link.get("href", "")

        # 실제 채용 상세 페이지 링크만 허용
        if "view.do" not in href:
            continue

        text = clean(
            link.get_text(
                " ",
                strip=True,
            )
        )

        if not text:
            continue

        # 공고 상세 URL
        url = urljoin(
            SHINHAN_URL,
            href,
        )

        # URL 기준 중복 제거
        if url in seen:
            continue

        seen.add(url)

        # 부모 영역 전체 텍스트 확보
        parent = link

        for _ in range(4):
            if parent.parent:
                parent = parent.parent

        full_text = clean(
            parent.get_text(
                " ",
                strip=True,
            )
        )

        title = text

        # 지나치게 긴 링크 텍스트 방지
        if len(title) > 120:
            title = title[:120]

        job_type = classify_type(full_text)
        deadline = extract_deadline(full_text)

        jobs.append(
            {
                "id": make_id(
                    "신한투자증권",
                    title,
                    url,
                ),
                "company": "신한투자증권",
                "title": title,
                "role": classify_role(title),
                "type": job_type,
                "deadline": deadline,
                "posted": None,
                "source": "신한투자증권 공식 채용",
                "url": url,
                "fresh": True,
            }
        )

    return jobs


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
    print("=" * 50)

    all_jobs = []

    try:

        shinhan_jobs = collect_shinhan()

        all_jobs.extend(
            shinhan_jobs
        )

        print(
            f"[OK] 신한투자증권: "
            f"{len(shinhan_jobs)} jobs"
        )

    except Exception as e:

        print(
            f"[ERROR] 신한투자증권: {e}"
        )

    if not all_jobs:

        print(
            "[WARNING] 실제 채용공고를 수집하지 못했습니다."
        )

        return

    # URL 기준 최종 중복 제거
    final_jobs = []
    seen_urls = set()

    for job in all_jobs:

        url = job["url"]

        if url in seen_urls:
            continue

        seen_urls.add(url)
        final_jobs.append(job)

    save_jobs(final_jobs)

    print("=" * 50)
    print(
        f"FINJOB update complete: "
        f"{len(final_jobs)} jobs"
    )
    print("=" * 50)


if __name__ == "__main__":
    main()
