# GitHub Actions 자동 배포 설정 가이드

이 가이드는 GitHub Actions를 사용하여 main 브랜치에 코드가 푸시될 때 자동으로 Google Cloud Run에 배포하는 방법을 설명합니다.

## 1. GitHub Secrets 설정

GitHub 리포지토리의 Settings > Secrets and variables > Actions에서 다음 시크릿을 추가하세요:

### 필수 시크릿

| 시크릿 이름 | 설명 | 예시 | 예상 길이 | 검증 방법 |
|------------|------|------|---------|----------|
| `GCP_PROJECT_ID` | Google Cloud 프로젝트 ID | `my-trading-project` | 6-30자 | 영문, 숫자, 하이픈만 |
| `GCP_SA_KEY` | Google Cloud 서비스 계정 키 (JSON) | `{"type": "service_account"...}` | 1000자+ | JSON 형식 검증 |
| `APP_KEY` | 한국투자증권 API 키 | `PSxxxxxxxxxxxxxxx` | 20-50자 | PS로 시작 |
| `APP_SECRET` | 한국투자증권 API 시크릿 | `xxxxxxxxxxxxxxxxxxxxxxx` | 30-100자 | 영문, 숫자, 특수문자 |
| `CANO` | 계좌번호 | `12345678901` | 8-15자 | 숫자만 |
| `ACNT_PRDT_CD` | 계좌상품코드 | `01` | 2-5자 | 숫자만 |
| `DISCORD_WEBHOOK_URL` | Discord 웹훅 URL (선택사항) | `https://discord.com/api/webhooks/...` | 50-200자 | HTTPS URL 형식 |

### ⚠️ 자주 발생하는 설정 오류

1. **복사/붙여넣기 시 공백 문제**
   - 값 앞뒤로 불필요한 공백이 포함되지 않도록 주의
   - 특히 JSON 키의 경우 줄바꿈 문자 포함 여부 확인

2. **JSON 형식 오류** (`GCP_SA_KEY`)
   - 반드시 `{`로 시작하고 `}`로 끝나야 함
   - 이스케이프 문자나 개행 문자 포함 시 문제 발생 가능

3. **계좌번호 형식** (`CANO`)
   - 하이픈(-)이나 공백 없이 숫자만 입력
   - 예: `1234567890` (O), `1234-567-890` (X)

### 🔍 설정 검증 방법

GitHub Actions에서 자동으로 다음을 검증합니다:
- 각 시크릿의 설정 여부 (YES/NO)
- 환경변수 길이 확인
- 기본적인 형식 검증

## 2. Google Cloud 서비스 계정 생성

### 2.1 서비스 계정 생성
```bash
# Google Cloud CLI로 서비스 계정 생성
gcloud iam service-accounts create github-actions-sa \
    --display-name "GitHub Actions Service Account"
```

### 2.2 권한 부여
```bash
# 프로젝트 ID 설정 (실제 프로젝트 ID로 변경)
export PROJECT_ID="YOUR_PROJECT_ID"
export SA_EMAIL="github-actions-sa@${PROJECT_ID}.iam.gserviceaccount.com"

# 필요한 권한 부여
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member "serviceAccount:${SA_EMAIL}" \
    --role "roles/cloudbuild.builds.editor"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member "serviceAccount:${SA_EMAIL}" \
    --role "roles/cloudbuild.builds.builder"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member "serviceAccount:${SA_EMAIL}" \
    --role "roles/run.admin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member "serviceAccount:${SA_EMAIL}" \
    --role "roles/run.developer"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member "serviceAccount:${SA_EMAIL}" \
    --role "roles/storage.admin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member "serviceAccount:${SA_EMAIL}" \
    --role "roles/iam.serviceAccountUser"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member "serviceAccount:${SA_EMAIL}" \
    --role "roles/serviceusage.serviceUsageAdmin"

# 권한 확인
gcloud projects get-iam-policy $PROJECT_ID \
    --flatten="bindings[].members" \
    --format="table(bindings.role)" \
    --filter="bindings.members:${SA_EMAIL}"
```

### 2.3 키 파일 다운로드
```bash
# 서비스 계정 키 생성 및 다운로드
gcloud iam service-accounts keys create github-actions-key.json \
    --iam-account github-actions-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com
```

## 3. GitHub Secrets에 키 등록

1. `github-actions-key.json` 파일의 전체 내용을 복사
2. GitHub 리포지토리 > Settings > Secrets and variables > Actions
3. "New repository secret" 클릭
4. Name: `GCP_SA_KEY`
5. Secret: JSON 파일의 전체 내용 붙여넣기

## 4. 자동 배포 테스트

### 4.1 코드 변경 후 푸시
```bash
# 코드 수정 후
git add .
git commit -m "feat: 자동매매 로직 개선"
git push origin main
```

### 4.2 배포 확인
1. GitHub 리포지토리의 "Actions" 탭에서 워크플로우 실행 확인
2. 배포 완료 후 Google Cloud Console에서 서비스 확인
3. 제공된 URL로 접속하여 대시보드 확인

## 5. 워크플로우 동작 방식

### 트리거 조건
- **main 브랜치에 push**: 자동 배포 실행
- **Pull Request**: 문법 검사만 실행 (배포 X)

### 배포 과정
1. 코드 체크아웃
2. Google Cloud CLI 설정
3. Docker 이미지 빌드 및 업로드
4. Cloud Run 서비스 배포 (환경변수 포함)
5. 배포 결과 확인

### 환경변수 주입
배포 시 GitHub Secrets의 값들이 Cloud Run 환경변수로 안전하게 주입됩니다:
- config.yaml 파일 없이도 동작
- 보안 정보가 컨테이너 이미지에 저장되지 않음

## 6. 로컬 개발 시

로컬에서는 여전히 `config.yaml` 파일을 사용할 수 있습니다:
1. `config.yaml.template`을 복사하여 `config.yaml` 생성
2. 실제 값으로 수정
3. **주의**: `config.yaml`은 `.gitignore`에 포함되어 GitHub에 업로드되지 않음

## 7. 트러블슈팅

### ❌ 환경변수 관련 오류 해결

#### "설정 검증 실패" 오류가 발생하는 경우

**단계별 해결 방법:**

1. **GitHub Actions 로그에서 디버깅 정보 확인**
   ```
   🔍 환경변수 디버깅...
   🔑 설정된 환경변수 확인:
   APP_KEY 설정됨: YES/NO
   APP_SECRET 설정됨: YES/NO
   📏 환경변수 길이 확인:
   APP_KEY 길이: XX
   ```

2. **"NO"로 표시되는 시크릿 재설정**
   - GitHub 리포지토리 > Settings > Secrets and variables > Actions
   - 해당 시크릿 삭제 후 다시 추가
   - 복사/붙여넣기 시 앞뒤 공백 제거

3. **길이가 비정상적인 경우**
   - APP_KEY: 20-50자 (보통 36자)
   - APP_SECRET: 30-100자 (보통 60-80자)
   - CANO: 8-15자 (보통 10-11자)
   - GCP_SA_KEY: 1000자 이상 (JSON 전체)

4. **한국투자증권 API 키 확인**
   - APP_KEY가 "PS"로 시작하는지 확인
   - 만료되지 않은 유효한 키인지 확인
   - 실제 거래용/모의투자용 구분 확인

### ❌ "You do not currently have an active account selected" 오류

**원인**: Google Cloud 인증 실패
**해결방법**:

1. **서비스 계정 키 확인**
```bash
# 서비스 계정 키 JSON 파일 검증
cat github-actions-key.json | jq .
```

2. **GitHub Secrets 재확인**
- `GCP_SA_KEY`: JSON 파일의 **전체 내용** (공백 포함)
- `GCP_PROJECT_ID`: 정확한 프로젝트 ID

3. **권한 재설정**
```bash
# 서비스 계정 삭제 후 재생성
gcloud iam service-accounts delete github-actions-sa@PROJECT_ID.iam.gserviceaccount.com
# 위의 2.1, 2.2 단계 다시 실행
```

### ❌ "Permission denied" 오류

**해결방법**: 추가 권한 부여
```bash
gcloud projects add-iam-policy-binding PROJECT_ID \
    --member "serviceAccount:github-actions-sa@PROJECT_ID.iam.gserviceaccount.com" \
    --role "roles/editor"
```

### ❌ API 비활성화 오류

**해결방법**: 필요한 API 수동 활성화
```bash
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com
```

### 배포 실패 시 체크리스트
1. ✅ 서비스 계정이 생성되었는가?
2. ✅ 필요한 권한이 모두 부여되었는가?
3. ✅ GitHub Secrets가 정확히 설정되었는가?
4. ✅ 프로젝트 ID가 일치하는가?
5. ✅ 필요한 Google Cloud API가 활성화되었는가?

### 로그 확인 방법
- **GitHub Actions**: Repository > Actions 탭
- **Cloud Build**: Google Cloud Console > Cloud Build > 빌드 기록
- **Cloud Run**: Google Cloud Console > Cloud Run > 서비스 로그

## 8. 비용 최적화

- **min-instances: 0**: 사용하지 않을 때 인스턴스 0개로 축소
- **max-instances: 1**: 최대 1개 인스턴스로 제한
- **메모리 512Mi**: 최소 필요 메모리만 할당

이 설정으로 월 비용이 거의 무료에 가깝게 유지됩니다.