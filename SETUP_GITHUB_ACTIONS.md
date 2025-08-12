# GitHub Actions 자동 배포 설정 가이드

이 가이드는 GitHub Actions를 사용하여 main 브랜치에 코드가 푸시될 때 자동으로 Google Cloud Run에 배포하는 방법을 설명합니다.

## 1. GitHub Secrets 설정

GitHub 리포지토리의 Settings > Secrets and variables > Actions에서 다음 시크릿을 추가하세요:

### 필수 시크릿

| 시크릿 이름 | 설명 | 예시 |
|------------|------|------|
| `GCP_PROJECT_ID` | Google Cloud 프로젝트 ID | `my-trading-project` |
| `GCP_SA_KEY` | Google Cloud 서비스 계정 키 (JSON) | `{"type": "service_account"...}` |
| `APP_KEY` | 한국투자증권 API 키 | `PSxxxxxxxxxxxxxxx` |
| `APP_SECRET` | 한국투자증권 API 시크릿 | `xxxxxxxxxxxxxxxxxxxxxxx` |
| `CANO` | 계좌번호 | `12345678901` |
| `ACNT_PRDT_CD` | 계좌상품코드 | `01` |
| `DISCORD_WEBHOOK_URL` | Discord 웹훅 URL | `https://discord.com/api/webhooks/...` |

## 2. Google Cloud 서비스 계정 생성

### 2.1 서비스 계정 생성
```bash
# Google Cloud CLI로 서비스 계정 생성
gcloud iam service-accounts create github-actions-sa \
    --display-name "GitHub Actions Service Account"
```

### 2.2 권한 부여
```bash
# 필요한 권한 부여
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member "serviceAccount:github-actions-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role "roles/cloudbuild.builds.editor"

gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member "serviceAccount:github-actions-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role "roles/run.admin"

gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member "serviceAccount:github-actions-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role "roles/storage.admin"

gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member "serviceAccount:github-actions-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role "roles/iam.serviceAccountUser"
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

### 배포 실패 시
1. GitHub Actions 로그 확인
2. Google Cloud Build 로그 확인
3. Cloud Run 서비스 로그 확인

### 자주 발생하는 문제
- **권한 부족**: 서비스 계정에 필요한 권한이 있는지 확인
- **시크릿 오타**: GitHub Secrets의 키 이름과 값 확인
- **프로젝트 ID 불일치**: `GCP_PROJECT_ID` 시크릿 값 확인

## 8. 비용 최적화

- **min-instances: 0**: 사용하지 않을 때 인스턴스 0개로 축소
- **max-instances: 1**: 최대 1개 인스턴스로 제한
- **메모리 512Mi**: 최소 필요 메모리만 할당

이 설정으로 월 비용이 거의 무료에 가깝게 유지됩니다.