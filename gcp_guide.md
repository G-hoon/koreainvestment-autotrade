# 🚀 Google Cloud Run 배포 가이드

## 🌟 Google Cloud Run의 장점

- **💰 비용**: 거의 무료 (월 200만 요청, 36만 GB-초 무료)
- **🔧 관리**: 서버리스, 자동 스케일링
- **⚡ 속도**: 빠른 배포, 즉시 시작
- **🌐 글로벌**: 전 세계 리전 지원

---

## 🚀 빠른 시작

### 1. 사전 준비
```bash
# Google Cloud CLI 설치 (macOS)
brew install --cask google-cloud-sdk

# 또는 다운로드: https://cloud.google.com/sdk/docs/install
```

### 2. 자동 배포
```bash
# 실행 권한 부여
chmod +x deploy_gcp.sh

# 배포 스크립트 실행
./deploy_gcp.sh
```

### 3. 완료!
배포가 완료되면 URL이 출력됩니다:
- **메인 페이지**: https://your-service-url/
- **헬스체크**: https://your-service-url/health
- **상태 확인**: https://your-service-url/status

---

## 🔧 수동 배포 (단계별)

### 1단계: Google Cloud 설정
```bash
# 로그인
gcloud auth login

# 프로젝트 선택 (없으면 생성)
gcloud projects create my-autotrade-project
gcloud config set project my-autotrade-project

# 필요한 API 활성화
gcloud services enable cloudbuild.googleapis.com run.googleapis.com
```

### 2단계: Docker 이미지 빌드
```bash
# 이미지 빌드
docker build -f Dockerfile.gcp -t gcr.io/[PROJECT_ID]/koreainvestment-autotrade .

# Container Registry에 푸시
gcloud auth configure-docker
docker push gcr.io/[PROJECT_ID]/koreainvestment-autotrade
```

### 3단계: Cloud Run 배포
```bash
gcloud run deploy koreainvestment-autotrade \
    --image gcr.io/[PROJECT_ID]/koreainvestment-autotrade \
    --region asia-northeast3 \
    --platform managed \
    --allow-unauthenticated \
    --memory 512Mi \
    --min-instances 1 \
    --max-instances 1
```

---

## 📊 모니터링 및 관리

### 로그 확인
```bash
# 실시간 로그
gcloud run logs tail koreainvestment-autotrade --region=asia-northeast3

# 최근 로그
gcloud run logs read koreainvestment-autotrade --region=asia-northeast3 --limit=50
```

### 서비스 상태 확인
```bash
# 서비스 정보
gcloud run services describe koreainvestment-autotrade --region=asia-northeast3

# 서비스 목록
gcloud run services list
```

### 웹 콘솔
- **Cloud Run 콘솔**: https://console.cloud.google.com/run
- **로그 뷰어**: https://console.cloud.google.com/logs
- **모니터링**: https://console.cloud.google.com/monitoring

---

## ⚙️ 설정 관리

### 환경 변수로 API 키 관리 (보안 강화)
```bash
# Secret Manager 사용 (권장)
gcloud secrets create app-key --data-file=<(echo -n "your_app_key")
gcloud secrets create app-secret --data-file=<(echo -n "your_app_secret")

# Cloud Run에서 Secret 사용
gcloud run services update koreainvestment-autotrade \
    --update-secrets APP_KEY=app-key:latest \
    --update-secrets APP_SECRET=app-secret:latest \
    --region=asia-northeast3
```

### 메모리 및 CPU 조정
```bash
# 리소스 증설
gcloud run services update koreainvestment-autotrade \
    --memory 1Gi \
    --cpu 2 \
    --region=asia-northeast3
```

---

## ⏰ 자동 실행 스케줄러 설정

### Cloud Scheduler로 미국 장시간 자동 실행

미국 장 시작시간(9:30 EST)에 자동으로 프로그램을 실행하도록 설정할 수 있습니다.

#### 1. Cloud Scheduler API 활성화
```bash
# Cloud Scheduler API 활성화
gcloud services enable cloudscheduler.googleapis.com
```

#### 2. 스케줄러 작업 생성
```bash
# 매일 평일 9:30 EST에 자동 실행
gcloud scheduler jobs create http usa-trading-scheduler \
  --schedule="30 14 * * 1-5" \
  --uri="https://your-cloud-run-url/" \
  --http-method=GET \
  --time-zone="America/New_York" \
  --location="us-central1" \
  --description="미국 장 시작시간(9:30 EST)에 자동매매 실행"
```

#### 3. 스케줄 설명
- `30 14 * * 1-5`: 매일 평일(월~금) 14:30 UTC (= 9:30 EST)
- `time-zone="America/New_York"`: EST/EDT 자동 적용
- 프로그램은 15:50 EST에 자동으로 종료됩니다

#### 4. 스케줄러 관리
```bash
# 스케줄러 목록 확인
gcloud scheduler jobs list --location=us-central1

# 스케줄러 일시 중지
gcloud scheduler jobs pause usa-trading-scheduler --location=us-central1

# 스케줄러 재시작
gcloud scheduler jobs resume usa-trading-scheduler --location=us-central1

# 스케줄러 삭제
gcloud scheduler jobs delete usa-trading-scheduler --location=us-central1
```

#### 5. 수동 실행 테스트
```bash
# 스케줄러 즉시 실행 (테스트용)
gcloud scheduler jobs run usa-trading-scheduler --location=us-central1
```

### Discord 알림 기능

프로그램이 시작하고 종료할 때 Discord로 알림을 받을 수 있습니다:

- **장 시작 시**: 잔고 정보, 보유 종목, 평가 손익 표시
- **장 종료 시**: 최종 잔고 및 수익률 결과 표시
- **실시간**: 매수/매도 체결 내역, 위험관리 알림

---

## 🔄 업데이트 및 재배포

### 코드 변경 후 재배포
```bash
# 1. 이미지 다시 빌드
docker build -f Dockerfile.gcp -t gcr.io/[PROJECT_ID]/koreainvestment-autotrade .
docker push gcr.io/[PROJECT_ID]/koreainvestment-autotrade

# 2. 서비스 업데이트 (자동으로 새 버전 배포)
gcloud run services update koreainvestment-autotrade --region=asia-northeast3
```

### 롤백 (이전 버전으로 복구)
```bash
# 이전 리비전으로 롤백
gcloud run services update-traffic koreainvestment-autotrade \
    --to-revisions=REVISION-NAME=100 \
    --region=asia-northeast3
```

---

## 💰 비용 최적화

### 무료 한도
- **요청**: 월 200만 건까지 무료
- **컴퓨팅**: 월 36만 GB-초까지 무료
- **아웃바운드 트래픽**: 월 1GB까지 무료

### 비용 절약 팁
```bash
# 최소 인스턴스를 0으로 설정 (트래픽이 없을 때 완전히 중지)
gcloud run services update koreainvestment-autotrade \
    --min-instances 0 \
    --region=asia-northeast3
```

### 예상 비용 (무료 한도 초과 시)
- **CPU**: $0.00002400/vCPU-초
- **메모리**: $0.00000250/GB-초  
- **요청**: $0.40/100만 요청

대부분의 자동매매 프로그램은 **월 $0~2 수준**입니다.

---

## 🚨 문제 해결

### 자주 발생하는 문제

#### 1. "Permission denied" 오류
```bash
# IAM 권한 확인
gcloud projects add-iam-policy-binding [PROJECT_ID] \
    --member="user:your-email@gmail.com" \
    --role="roles/run.admin"
```

#### 2. Docker 빌드 실패
```bash
# Docker Desktop이 실행 중인지 확인
# M1/M2 Mac의 경우 플랫폼 지정
docker build -f Dockerfile.gcp --platform linux/amd64 -t gcr.io/[PROJECT_ID]/koreainvestment-autotrade .
```

#### 3. 프로그램이 바로 종료됨
```bash
# 로그에서 오류 확인
gcloud run logs read koreainvestment-autotrade --region=asia-northeast3

# config.yaml 설정 확인
kubectl create configmap config --from-file=config.yaml
```

#### 4. API 연결 실패
- config.yaml의 API 키 확인
- 한국투자증권 API 서버 상태 확인
- 방화벽 설정 확인

---

## 🔒 보안 고려사항

### API 키 보호
1. **Secret Manager 사용** (강력 권장)
2. **환경 변수로 전달**
3. **config.yaml 파일에 하드코딩 지양**

### 접근 제한
```bash
# 인증 필요하도록 변경
gcloud run services remove-iam-policy-binding koreainvestment-autotrade \
    --member="allUsers" \
    --role="roles/run.invoker" \
    --region=asia-northeast3
```

---

## 📞 지원 및 도움말

- **Google Cloud 지원**: https://cloud.google.com/support
- **Cloud Run 문서**: https://cloud.google.com/run/docs
- **커뮤니티**: https://stackoverflow.com/questions/tagged/google-cloud-run

---

*Google Cloud Run으로 안정적이고 경제적인 자동매매 서비스를 운영하세요! 🚀*