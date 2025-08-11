# 🚀 한국투자증권 자동매매 시스템 (개선 버전)

## 📖 프로젝트 소개

이 프로젝트는 [조코딩 YouTube 채널](https://github.com/youtube-jocoding/koreainvestment-autotrade)의 한국투자증권 자동매매 강의 코드를 기반으로 개발된 **개선 버전**입니다.

### 🙏 원작자 크레딧
- **원작자**: [조코딩 (youtube-jocoding)](https://github.com/youtube-jocoding)
- **원본 저장소**: https://github.com/youtube-jocoding/koreainvestment-autotrade
- **YouTube 강의**: [한국투자증권 자동매매 시리즈](https://www.youtube.com/@jocoding)

## 📊 매매 전략: 동적 변동성 돌파 시스템

### 🎯 전략 개요
미국 주식 자동매매는 **동적 변동성 돌파 전략**을 사용합니다. 이는 래리 윌리엄스(Larry Williams)의 변동성 돌파 전략을 개선한 버전으로, 각 종목의 변동성에 따라 매수 타이밍을 조정합니다.

### 📈 전략 상세 분석

#### 1. 변동성 계산 (Volatility Calculation)
```python
# 최근 20일간의 일일 수익률 표준편차 계산
daily_return = (오늘종가 - 어제종가) / 어제종가
volatility = stdev(daily_returns) * √252  # 연율화
```

- **기간**: 최근 20거래일
- **방법**: 일일 수익률의 표준편차를 연율화
- **목적**: 종목별 위험도 측정

#### 2. 동적 승수 시스템 (Dynamic Multiplier System)
```python
if volatility > 40%:    multiplier = 0.3  # 초고변동성
elif volatility > 25%:  multiplier = 0.5  # 고변동성  
else:                   multiplier = 0.7  # 저변동성
```

| 변동성 구간 | 승수 | 전략 설명 |
|------------|------|----------|
| **40% 초과** | 0.3 | 극도로 불안정한 종목 → 보수적 접근 |
| **25~40%** | 0.5 | 변동성이 큰 종목 → 중간 수준 접근 |
| **25% 미만** | 0.7 | 안정적인 종목 → 적극적 접근 |

#### 3. 목표가 계산 공식
```
목표가 = 당일시가 + (전일고가 - 전일저가) × 동적승수
```

**예시 계산:**
- 당일 시가: $100
- 전일 고가: $105  
- 전일 저가: $95
- 변동성: 30% → 승수 0.5
- **목표가 = $100 + ($105 - $95) × 0.5 = $105**

#### 4. 매수 조건
- **기본 조건**: 현재가 ≥ 목표가
- **시간 조건**: 뉴욕시간 9:35 ~ 15:45
- **자금 조건**: 포트폴리오당 25% 배분
- **종목 수 제한**: 최대 4종목 동시 보유

### 🛡️ 위험 관리 시스템

#### 1. 손절매 (Stop Loss)
- **기준**: 매수가 대비 -2% 하락
- **특징**: 최우선 실행 (다른 조건보다 우선)

#### 2. 트레일링 스탑 (Trailing Stop)  
- **활성화 조건**: 매수가 대비 +2% 이상 수익
- **추적 방식**: 최고가 대비 -2% 하락 시 매도
- **장점**: 수익을 보호하면서 상승 여력 확보

#### 3. 고정 익절 (Take Profit)
- **기준**: 매수가 대비 +3% 상승
- **적용**: 트레일링 스탑 미활성화 구간에서만

### 📊 전략의 장단점

#### ✅ 장점
1. **적응형 시스템**: 종목별 변동성에 맞춤형 대응
2. **위험 최소화**: 고변동성 종목에 보수적 접근
3. **수익 극대화**: 저변동성 종목에 적극적 접근  
4. **체계적 관리**: 명확한 매수/매도 규칙

#### ⚠️ 단점
1. **횡보장 취약**: 방향성 없는 시장에서 손실 가능
2. **갭 리스크**: 시장 개장 전 악재 시 손절매 불가
3. **수수료 부담**: 잦은 매매로 인한 거래비용
4. **변동성 지연**: 과거 데이터 기반으로 현재 위험도 추정

### 🔬 백테스팅 고려사항

이 전략을 적용하기 전에 다음 사항을 검토하세요:

1. **과최적화 방지**: 다양한 시장 상황에서 테스트
2. **생존 편향**: 상장폐지 종목 데이터 포함 테스트  
3. **거래비용 포함**: 실제 수수료와 세금 반영
4. **슬리피지 고려**: 시장가 주문 시 가격 차이

## ✨ 주요 개선사항

### 🔧 안정성 향상
- **HTTP 세션 재사용**: `requests.Session()` 사용으로 연결 효율성 증대
- **자동 재시도 로직**: 네트워크 오류 시 3회 자동 재시도
- **타임아웃 설정**: 모든 API 호출에 30초 타임아웃 적용
- **ConnectionResetError 해결**: 재시도 메커니즘으로 연결 안정성 확보

### ☁️ 클라우드 배포 지원
- **Google Cloud Run 배포**: 서버리스 환경에서 24/7 실행
- **Docker 컨테이너화**: 일관된 실행 환경 보장
- **자동 배포 스크립트**: 원클릭 클라우드 배포
- **모니터링 대시보드**: 웹 기반 상태 모니터링

### 📊 모니터링 및 로깅
- **실시간 헬스체크**: HTTP 엔드포인트를 통한 상태 확인
- **상세 로깅**: 매수/매도 내역 및 오류 추적
- **Discord 알림 안정화**: 메시지 전송 실패 처리

### 🛡️ 보안 강화
- **환경 변수 지원**: API 키의 안전한 관리
- **Secret Manager 연동**: Google Cloud Secret Manager 사용 가능

## 🚀 배포 방법

### Google Cloud Run (추천)
```bash
# 자동 배포 스크립트 실행
./deploy_gcp.sh
```

**장점:**
- 💰 거의 무료 (월 200만 요청까지)
- 🔧 서버리스 (관리 불필요)
- 📈 자동 스케일링

### Docker 로컬 실행
```bash
# Docker 빌드 및 실행
docker build -f Dockerfile.gcp -t autotrade .
docker run -d --name autotrade -v $(pwd)/config.yaml:/app/config.yaml:ro autotrade
```

## 📋 설정 방법

### 1. API 키 설정
```yaml
# config.yaml
APP_KEY: "your_app_key_here"
APP_SECRET: "your_app_secret_here"
CANO: "your_account_number"
ACNT_PRDT_CD: "your_product_code"
DISCORD_WEBHOOK_URL: "your_discord_webhook_url"
URL_BASE: "https://openapi.koreainvestment.com:9443"
```

### 2. 의존성 설치
```bash
pip install -r requirements.txt
```

### 3. 프로그램 실행
```bash
# 한국 주식 자동매매
python KoreaStockAutoTrade.py

# 미국 주식 자동매매
python UsaStockAutoTrade.py

# 매수 테스트
python test_buy.py
```

## 📊 모니터링

배포 후 다음 엔드포인트로 상태를 확인할 수 있습니다:

- **대시보드**: `https://your-service-url/`
- **헬스체크**: `https://your-service-url/health`
- **상태 API**: `https://your-service-url/status`

## 💰 비용

### Google Cloud Run
- **무료 한도**: 월 200만 요청, 36만 GB-초
- **예상 비용**: $0~2/월 (대부분 무료)

## 📁 파일 구조

```
├── KoreaStockAutoTrade.py      # 한국 주식 자동매매 (원본 기반)
├── UsaStockAutoTrade.py        # 미국 주식 자동매매 (개선 버전)
├── test_buy.py                 # 매수 테스트 스크립트
├── start.py                    # Cloud Run 시작 스크립트
├── config.yaml                 # API 설정 파일
├── requirements.txt            # Python 의존성
├── Dockerfile.gcp             # Google Cloud Run용 Dockerfile
├── cloudbuild.yaml            # Google Cloud Build 설정
├── deploy_gcp.sh              # 자동 배포 스크립트
├── gcp_guide.md               # 상세 배포 가이드
└── README.md                  # 이 파일
```

## ⚠️ 주의사항

- **투자 위험**: 자동매매는 투자 손실 위험이 있습니다
- **API 제한**: 한국투자증권 API 사용 한도를 확인하세요
- **테스트 권장**: 모의투자로 충분히 테스트 후 실제 투자하세요
- **법적 책임**: 투자 손실에 대한 책임은 본인에게 있습니다

## 🤝 기여하기

1. 이 저장소를 Fork하세요
2. 새로운 기능을 개발하세요
3. Pull Request를 제출하세요

## 📄 라이선스

이 프로젝트는 원작자의 라이선스 정책을 따릅니다. 
교육 목적으로 사용하시고, 상업적 사용 시 원작자에게 문의하세요.

## 🔗 관련 링크

- **원본 저장소**: https://github.com/youtube-jocoding/koreainvestment-autotrade
- **조코딩 YouTube**: https://www.youtube.com/@jocoding
- **한국투자증권 OpenAPI**: https://apiportal.koreainvestment.com
- **Google Cloud Run**: https://cloud.google.com/run

---

**⚡ 개선 버전 개발자**: [G-hoon](https://github.com/G-hoon)
**🙏 원작자**: [조코딩](https://github.com/youtube-jocoding)

*이 프로젝트는 교육 목적으로 개발되었으며, 투자에 대한 책임은 사용자에게 있습니다.*
