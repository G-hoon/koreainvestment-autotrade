# 🔄 GitHub Fork 설정 가이드

## 1단계: GitHub에서 Fork 생성

1. 브라우저에서 https://github.com/youtube-jocoding/koreainvestment-autotrade 접속
2. 우측 상단 "Fork" 버튼 클릭
3. 본인 계정에 저장소 생성

## 2단계: 리모트 저장소 변경

아래 명령어를 실행하세요 ([your-username]을 실제 GitHub 사용자명으로 교체):

```bash
# 본인 Fork로 origin 변경
git remote set-url origin https://github.com/[your-username]/koreainvestment-autotrade.git

# 원본 저장소를 upstream으로 추가
git remote add upstream https://github.com/youtube-jocoding/koreainvestment-autotrade.git

# 리모트 확인
git remote -v
```

## 3단계: GitHub에 푸시

```bash
# 변경사항을 본인 Fork에 푸시
git push origin main
```

## 4단계: config.yaml 설정

```bash
# 템플릿을 복사하여 설정 파일 생성
cp config.yaml.template config.yaml

# 에디터로 실제 API 키 입력
nano config.yaml
```

config.yaml에 다음 정보를 입력하세요:
- APP_KEY: 한국투자증권 OpenAPI 키
- APP_SECRET: 한국투자증권 OpenAPI 시크릿
- CANO: 계좌번호
- ACNT_PRDT_CD: 상품코드 (보통 "01")
- DISCORD_WEBHOOK_URL: Discord 웹훅 URL (선택사항)

## 5단계: 로컬 테스트

```bash
# 의존성 설치
pip install -r requirements.txt

# 프로그램 실행 테스트
python UsaStockAutoTrade.py
```

## 6단계: Google Cloud Run 배포 (선택사항)

```bash
# Google Cloud CLI 설치 후
./deploy_gcp.sh
```

## ✅ 완료!

이제 본인의 GitHub 저장소에서 자동매매 시스템을 관리할 수 있습니다.

- 📊 **로컬 실행**: `python UsaStockAutoTrade.py`
- ☁️ **클라우드 배포**: `./deploy_gcp.sh`
- 📖 **상세 가이드**: `gcp_guide.md` 참고