#!/bin/bash

# Google Cloud Run 배포 스크립트
set -e

# 색상 코드
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Google Cloud Run 자동매매 프로그램 배포 스크립트${NC}"

# 변수 설정
PROJECT_ID=""
SERVICE_NAME="koreainvestment-autotrade"
REGION="asia-northeast3"  # 서울 리전
IMAGE_NAME=""  # 나중에 설정

echo -e "${YELLOW}📋 배포 설정:${NC}"
echo "  - 서비스 이름: $SERVICE_NAME"
echo "  - 리전: $REGION (서울)"
echo "  - 이미지: $IMAGE_NAME"

# Google Cloud CLI 설치 확인
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}❌ Google Cloud CLI가 설치되어 있지 않습니다.${NC}"
    echo "설치 방법: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# 프로젝트 ID 자동 감지 또는 입력 받기
if [ -z "$PROJECT_ID" ]; then
    # 현재 설정된 프로젝트 ID 가져오기
    CURRENT_PROJECT=$(gcloud config get-value project 2>/dev/null || echo "")
    
    if [ -n "$CURRENT_PROJECT" ]; then
        echo -e "${YELLOW}현재 프로젝트: $CURRENT_PROJECT${NC}"
        read -p "이 프로젝트를 사용하시겠습니까? [Y/n]: " -r
        if [[ $REPLY =~ ^[Nn]$ ]]; then
            read -p "사용할 프로젝트 ID를 입력하세요: " PROJECT_ID
        else
            PROJECT_ID=$CURRENT_PROJECT
        fi
    else
        read -p "Google Cloud 프로젝트 ID를 입력하세요: " PROJECT_ID
    fi
    
    # 이미지 이름 업데이트
    IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"
fi

# 이미지 이름 설정
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

echo -e "${GREEN}✅ 프로젝트 ID: $PROJECT_ID${NC}"
echo -e "${GREEN}✅ 이미지 이름: $IMAGE_NAME${NC}"

# Google Cloud 인증 확인
echo -e "${BLUE}🔐 Google Cloud 인증 확인 중...${NC}"
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | head -n1 > /dev/null; then
    echo -e "${YELLOW}⚠️  Google Cloud에 로그인이 필요합니다.${NC}"
    gcloud auth login
fi

# 프로젝트 설정
gcloud config set project $PROJECT_ID

# 필요한 API 활성화
echo -e "${BLUE}🔧 필요한 Google Cloud API 활성화 중...${NC}"
gcloud services enable \
    cloudbuild.googleapis.com \
    run.googleapis.com \
    containerregistry.googleapis.com \
    artifactregistry.googleapis.com

echo -e "${GREEN}✅ API 활성화 완료${NC}"

# config.yaml 존재 확인
if [ ! -f "config.yaml" ]; then
    echo -e "${RED}❌ config.yaml 파일이 없습니다.${NC}"
    echo "config.yaml 파일을 생성하거나 복사해주세요."
    
    cat > config.yaml << EOF
# 한국투자증권 API 설정
APP_KEY: "your_app_key_here"
APP_SECRET: "your_app_secret_here"
CANO: "your_account_number_here"
ACNT_PRDT_CD: "your_product_code_here"
DISCORD_WEBHOOK_URL: "your_discord_webhook_url_here"
URL_BASE: "https://openapi.koreainvestment.com:9443"
EOF
    
    echo -e "${YELLOW}⚠️  config.yaml 템플릿이 생성되었습니다. 실제 값을 입력하고 다시 실행해주세요.${NC}"
    exit 1
fi

# Google Cloud Build로 이미지 빌드 및 푸시 (Docker 없이도 가능)
echo -e "${BLUE}🐳 Google Cloud Build로 이미지 빌드 중...${NC}"
gcloud builds submit --config cloudbuild.yaml .

echo -e "${GREEN}✅ 이미지 업로드 완료${NC}"

# Cloud Run 서비스 배포
echo -e "${BLUE}🚀 Cloud Run 서비스 배포 중...${NC}"
gcloud run deploy $SERVICE_NAME \
    --image $IMAGE_NAME \
    --region $REGION \
    --platform managed \
    --allow-unauthenticated \
    --memory 512Mi \
    --cpu 1 \
    --timeout 3600 \
    --concurrency 1 \
    --min-instances 1 \
    --max-instances 1 \
    --set-env-vars "TZ=Asia/Seoul" \
    --port 8080

# 서비스 URL 가져오기
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region=$REGION --format="value(status.url)")

echo ""
echo -e "${GREEN}🎉 배포 완료!${NC}"
echo -e "${BLUE}📊 서비스 정보:${NC}"
echo "  - 서비스 URL: $SERVICE_URL"
echo "  - 헬스체크: $SERVICE_URL/health"
echo "  - 상태 확인: $SERVICE_URL/status"
echo "  - 대시보드: $SERVICE_URL/"

echo ""
echo -e "${BLUE}📝 다음 단계:${NC}"
echo "  1. 브라우저에서 $SERVICE_URL 접속하여 상태 확인"
echo "  2. 로그 확인: gcloud run logs tail $SERVICE_NAME --region=$REGION"
echo "  3. 서비스 관리: https://console.cloud.google.com/run"

echo ""
echo -e "${BLUE}💰 예상 비용:${NC}"
echo "  - Cloud Run: 거의 무료 (월 200만 요청, 36만 GB-초까지 무료)"
echo "  - Container Registry: 스토리지 비용 미미"

echo ""
echo -e "${BLUE}🔧 유용한 명령어:${NC}"
echo "  - 로그 실시간 확인: gcloud run logs tail $SERVICE_NAME --region=$REGION"
echo "  - 서비스 삭제: gcloud run services delete $SERVICE_NAME --region=$REGION"
echo "  - 트래픽 확인: gcloud run services describe $SERVICE_NAME --region=$REGION"