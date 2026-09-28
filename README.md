# FINJOB — Release Candidate

금융권 채용공고를 공식 소스 중심으로 수집·분류·표시하는 웹앱의 앱 패키징 직전 개발본입니다.

## 포함 기능
- 금융투자협회 회원사 채용 Collector
- 신한투자증권 공식 채용 Collector
- KB증권 공식 GreetingHR Collector
- 삼성증권 공식 진입점 health adapter
- 회사별 수집 실패 격리 및 `collector_status.json`
- 공고 표준 스키마: `company/title/career/deadline/posted/tags/url/source/collected_at`
- 복수 태그 자동 분류: 리서치, IB, 인프라·대체투자, PF·부동산, FICC, 자산운용, PE·VC, 리스크, 디지털자산
- 중복 공고 병합
- 마감 공고 자동 비노출
- 최근 3일 NEW 표시
- 검색 / 직무 / 경력 / 정렬
- MY RADAR 관심직무 저장
- 관심공고 저장
- Collector 상태 UI
- GitHub Actions 일 3회 자동 갱신
- Supabase 테이블 스키마 및 환경변수 예시
- Windows/macOS/Linux 로컬 실행 스크립트

## 바로 실행
### Windows
`run_local.bat` 실행 후 브라우저에서 `http://localhost:8000`

### macOS / Linux
```bash
./run_local.sh
```

## 수동 실행
```bash
pip install -r requirements.txt
python collector/collector.py
python -m http.server 8000
```

## 배포 직전 남은 외부 작업
코드가 아니라 계정 권한이 필요한 작업만 남겨두었습니다.
1. GitHub 저장소 생성 후 프로젝트 업로드
2. 정적 호스팅(Vercel/Cloudflare Pages/GitHub Pages) 연결
3. Supabase를 사용할 경우 프로젝트 생성 후 `.env` 값 입력
4. 필요 시 iOS/Android 패키징(Capacitor/Expo 등) 및 스토어 계정 연결

## 주의
채용사이트의 HTML/JS 구조는 변경될 수 있습니다. 어댑터는 독립되어 있어 한 소스의 파싱 실패가 전체 수집을 중단시키지 않습니다. 개별 공고를 안정적으로 추출할 수 없는 공식 페이지는 임의 데이터를 만들지 않습니다.
