import requests
import json
import datetime
from pytz import timezone
import time
import yaml
import statistics
import math
import os
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import subprocess

def get_version_info():
    """버전 정보와 배포 날짜 가져오기"""
    try:
        # Git 커밋 해시와 날짜 가져오기
        commit_hash = subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD'], 
                                            stderr=subprocess.DEVNULL).decode('utf-8').strip()
        commit_date = subprocess.check_output(['git', 'log', '-1', '--format=%cd', '--date=format:%Y-%m-%d %H:%M:%S'], 
                                            stderr=subprocess.DEVNULL).decode('utf-8').strip()
        return f"🚀 버전: {commit_hash} | 배포일: {commit_date}"
    except:
        # Git 정보를 가져올 수 없는 경우 현재 시간 사용
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return f"🚀 배포일: {current_time}"

def get_stock_balance_quiet():
    """주식 잔고조회 (메시지 전송 없이)"""
    PATH = "uapi/overseas-stock/v1/trading/inquire-balance"
    URL = f"{URL_BASE}/{PATH}"
    headers = {"Content-Type":"application/json", 
        "authorization":f"Bearer {ACCESS_TOKEN}",
        "appKey":APP_KEY,
        "appSecret":APP_SECRET,
        "tr_id":"JTTT3012R",
        "custtype":"P"
    }
    params = {
        "CANO": CANO,
        "ACNT_PRDT_CD": ACNT_PRDT_CD,
        "OVRS_EXCG_CD": "NASD",
        "TR_CRCY_CD": "USD",
        "CTX_AREA_FK200": "",
        "CTX_AREA_NK200": ""
    }
    res = session.get(URL, headers=headers, params=params, timeout=30)
    stock_list = res.json()['output1']
    evaluation = res.json()['output2']
    stock_dict = {}
    for stock in stock_list:
        if int(stock['ovrs_cblc_qty']) > 0:
            stock_dict[stock['ovrs_pdno']] = {
                'qty': stock['ovrs_cblc_qty'],
                'name': stock['ovrs_item_name']
            }
    return stock_dict, evaluation

def send_balance_info():
    """잔고 정보를 Discord로 전송"""
    try:
        # 현금 잔고 정보
        cash_balance = get_balance()
        exchange_rate = get_exchange_rate()
        usd_balance = cash_balance / exchange_rate
        
        send_message("💰 ===== 계좌 정보 =====", force_discord=True)
        send_message(f"💵 현금 잔고: ₩{cash_balance:,.0f} (${usd_balance:,.2f})", force_discord=True)
        
        # 보유 주식 정보
        stock_dict, evaluation = get_stock_balance_quiet()
        if stock_dict:
            send_message("📈 보유 종목:", force_discord=True)
            for symbol, info in stock_dict.items():
                send_message(f"  • {info['name']}({symbol}): {info['qty']}주", force_discord=True)
            send_message(f"💎 주식 평가 금액: ${evaluation['tot_evlu_pfls_amt']}", force_discord=True)
            send_message(f"📊 평가 손익: ${evaluation['ovrs_tot_pfls']}", force_discord=True)
        else:
            send_message("📈 보유 종목: 없음", force_discord=True)
        
        send_message("========================", force_discord=True)
    except Exception as e:
        send_message(f"❌ 잔고 정보 조회 오류: {str(e)}", force_discord=True)

# 환경변수 우선, config.yaml 파일을 백업으로 사용
def validate_config_value(key, value, expected_type=str, min_length=None, max_length=None):
    """설정값 유효성 검증"""
    if not value:
        raise ValueError(f"❌ {key}가 설정되지 않았습니다.")
    
    if not isinstance(value, expected_type):
        raise ValueError(f"❌ {key}의 타입이 올바르지 않습니다. 예상: {expected_type}, 실제: {type(value)}")
    
    if min_length and len(str(value)) < min_length:
        raise ValueError(f"❌ {key}의 길이가 너무 짧습니다. 최소 {min_length}자 필요, 현재: {len(str(value))}자")
    
    if max_length and len(str(value)) > max_length:
        raise ValueError(f"❌ {key}의 길이가 너무 깁니다. 최대 {max_length}자, 현재: {len(str(value))}자")
    
    print(f"✅ {key}: 검증 완료 (길이: {len(str(value))}자)")

def load_config():
    """환경변수나 config.yaml에서 설정 로드 및 검증"""
    config = {}
    config_source = ""
    
    # 환경변수에서 우선 로드
    if os.getenv('APP_KEY'):
        print("🔍 환경변수에서 설정을 로드하는 중...")
        config['APP_KEY'] = os.getenv('APP_KEY')
        config['APP_SECRET'] = os.getenv('APP_SECRET')
        config['CANO'] = os.getenv('CANO')
        config['ACNT_PRDT_CD'] = os.getenv('ACNT_PRDT_CD')
        config['DISCORD_WEBHOOK_URL'] = os.getenv('DISCORD_WEBHOOK_URL')
        config['URL_BASE'] = os.getenv('URL_BASE', 'https://openapi.koreainvestment.com:9443')
        config_source = "환경변수"
    else:
        # config.yaml 파일에서 로드 (로컬 개발용)
        try:
            print("🔍 config.yaml 파일에서 설정을 로드하는 중...")
            with open('config.yaml', encoding='UTF-8') as f:
                config = yaml.load(f, Loader=yaml.FullLoader)
            config_source = "config.yaml 파일"
        except FileNotFoundError:
            print("❌ config.yaml 파일이 없고 환경변수도 설정되지 않았습니다.")
            raise Exception("설정 파일이나 환경변수가 필요합니다.")
    
    # 설정값 검증
    print(f"🔑 {config_source}에서 로드한 설정을 검증하는 중...")
    try:
        validate_config_value('APP_KEY', config.get('APP_KEY'), str, 20, 50)
        validate_config_value('APP_SECRET', config.get('APP_SECRET'), str, 30, 200)
        validate_config_value('CANO', config.get('CANO'), str, 8, 15)
        validate_config_value('ACNT_PRDT_CD', config.get('ACNT_PRDT_CD'), str, 2, 5)
        validate_config_value('URL_BASE', config.get('URL_BASE'), str, 10, 100)
        
        # DISCORD_WEBHOOK_URL은 선택사항
        if config.get('DISCORD_WEBHOOK_URL'):
            validate_config_value('DISCORD_WEBHOOK_URL', config.get('DISCORD_WEBHOOK_URL'), str, 50, 200)
            print("✅ DISCORD_WEBHOOK_URL: 설정됨")
        else:
            print("⚠️  DISCORD_WEBHOOK_URL: 설정되지 않음 (Discord 알림 비활성화)")
        
        print(f"✅ 모든 설정이 {config_source}에서 성공적으로 로드되고 검증되었습니다.")
        
    except ValueError as e:
        print(f"❌ 설정 검증 실패: {e}")
        print("\n🔧 설정 문제 해결 방법:")
        print("1. GitHub Secrets (리포지토리 > Settings > Secrets and variables > Actions)에서 값 확인")
        print("2. 로컬 개발 시 config.yaml 파일의 값 확인")
        print("3. 한국투자증권 API 키/시크릿이 올바른지 확인")
        raise Exception(f"설정 검증 실패: {e}")
    
    return config

_cfg = load_config()
APP_KEY = _cfg['APP_KEY']
APP_SECRET = _cfg['APP_SECRET']
ACCESS_TOKEN = ""
CANO = _cfg['CANO']
ACNT_PRDT_CD = _cfg['ACNT_PRDT_CD']
DISCORD_WEBHOOK_URL = _cfg['DISCORD_WEBHOOK_URL']
URL_BASE = _cfg['URL_BASE']

# HTTP 세션 및 재시도 설정
session = requests.Session()
retry_strategy = Retry(
    total=3,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["HEAD", "GET", "PUT", "DELETE", "OPTIONS", "TRACE", "POST"]
)
adapter = HTTPAdapter(max_retries=retry_strategy)
session.mount("http://", adapter)
session.mount("https://", adapter)

# 매수 가격 및 트레일링 스탑 추적용 딕셔너리
buy_prices = {}  # {종목코드: 매수가격}
trailing_stops = {}  # {종목코드: 최고가}

def send_message(msg, force_discord=False):
    """디스코드 메세지 전송"""
    now = datetime.datetime.now()
    message = {"content": f"[{now.strftime('%Y-%m-%d %H:%M:%S')}] {str(msg)}"}
    
    # 매수/매도 관련 메시지만 Discord로 전송 (force_discord=True인 경우 예외)
    is_trading_message = any(keyword in str(msg) for keyword in 
                           ["매수 성공", "매도 성공", "손절매 신호", "이익실현 신호", "트레일링스탑"])
    
    if DISCORD_WEBHOOK_URL and (is_trading_message or force_discord):
        try:
            session.post(DISCORD_WEBHOOK_URL, data=message, timeout=10)
        except Exception as e:
            print(f"Discord 메시지 전송 실패: {e}")
    print(message)

def get_access_token():
    """토큰 발급"""
    headers = {"content-type":"application/json"}
    body = {"grant_type":"client_credentials",
    "appkey":APP_KEY, 
    "appsecret":APP_SECRET}
    PATH = "oauth2/tokenP"
    URL = f"{URL_BASE}/{PATH}"
    try:
        res = session.post(URL, headers=headers, data=json.dumps(body), timeout=30)
        result = res.json()
        
        if 'access_token' in result:
            return result["access_token"]
        else:
            send_message(f"❌ 토큰 발급 실패: access_token 없음 - {result}", force_discord=True)
            raise Exception(f"토큰 응답에 access_token 없음: {result}")
            
    except Exception as e:
        send_message(f"❌ API 토큰 발급 오류: {str(e)}", force_discord=True)
        raise
    
def hashkey(datas):
    """암호화"""
    PATH = "uapi/hashkey"
    URL = f"{URL_BASE}/{PATH}"
    headers = {
    'content-Type' : 'application/json',
    'appKey' : APP_KEY,
    'appSecret' : APP_SECRET,
    }
    res = session.post(URL, headers=headers, data=json.dumps(datas), timeout=30)
    hashkey = res.json()["HASH"]
    return hashkey

def get_current_price(market="NAS", code="AAPL"):
    """현재가 조회"""
    PATH = "uapi/overseas-price/v1/quotations/price"
    URL = f"{URL_BASE}/{PATH}"
    headers = {"Content-Type":"application/json", 
            "authorization": f"Bearer {ACCESS_TOKEN}",
            "appKey":APP_KEY,
            "appSecret":APP_SECRET,
            "tr_id":"HHDFS00000300"}
    params = {
        "AUTH": "",
        "EXCD":market,
        "SYMB":code,
    }
    res = session.get(URL, headers=headers, params=params, timeout=30)
    return float(res.json()['output']['last'])

def calculate_volatility(market="NAS", code="AAPL", days=20):
    """최근 N일간의 변동성 계산 (수정된 최종 버전)"""
    PATH = "uapi/overseas-price/v1/quotations/dailyprice"
    URL = f"{URL_BASE}/{PATH}"
    headers = {
        "Content-Type": "application/json", 
        "authorization": f"Bearer {ACCESS_TOKEN}",
        "appKey": APP_KEY,
        "appSecret": APP_SECRET,
        "tr_id": "HHDFS76240000"
    }
    params = {
        "AUTH": "",
        "EXCD": market,
        "SYMB": code,
        "GUBN": "0",
        "BYMD": "",
        "MODP": "0"
    }
    
    res = session.get(URL, headers=headers, params=params, timeout=30)
    prices = res.json().get('output2', [])

    if not prices:
        send_message(f"[{code}] 일봉 데이터 조회 실패. 변동성 계산을 건너뜁니다.")
        return 0.2

    daily_returns = []
    for i in range(min(days, len(prices)-1)):
        try:
            today_price_data = prices[i]
            yesterday_price_data = prices[i+1]

            # 'clos', 'last', 'base', 'close' 순서로 종가를 찾도록 수정
            # 진단 결과 'clos'가 정확한 키 이름임을 확인했습니다.
            today_close = float(today_price_data.get('clos', today_price_data.get('last', today_price_data.get('base', today_price_data.get('close', 0)))))
            yesterday_close = float(yesterday_price_data.get('clos', yesterday_price_data.get('last', yesterday_price_data.get('base', yesterday_price_data.get('close', 0)))))
            
            if today_close == 0 or yesterday_close == 0:
                continue

            daily_return = (today_close - yesterday_close) / yesterday_close
            daily_returns.append(daily_return)
        except Exception as e:
            send_message(f"[{code}] 변동성 계산 중 일부 데이터 오류: {e}")
            continue
    
    if len(daily_returns) > 1:
        volatility = statistics.stdev(daily_returns) * math.sqrt(252)
        return volatility
    
    # 계산에 실패한 경우 기본값 반환
    send_message(f"[{code}] 유효한 데이터 부족으로 변동성 계산 실패. 기본값을 사용합니다.")
    return 0.2

def get_target_price(market="NAS", code="AAPL"):
    """동적 승수를 적용한 변동성 돌파 전략으로 매수 목표가 조회"""
    PATH = "uapi/overseas-price/v1/quotations/dailyprice"
    URL = f"{URL_BASE}/{PATH}"
    headers = {"Content-Type":"application/json", 
        "authorization": f"Bearer {ACCESS_TOKEN}",
        "appKey":APP_KEY,
        "appSecret":APP_SECRET,
        "tr_id":"HHDFS76240000"}
    params = {
        "AUTH":"",
        "EXCD":market,
        "SYMB":code,
        "GUBN":"0",
        "BYMD":"",
        "MODP":"0"
    }
    res = session.get(URL, headers=headers, params=params, timeout=30)
    stck_oprc = float(res.json()['output2'][0]['open']) #오늘 시가
    stck_hgpr = float(res.json()['output2'][1]['high']) #전일 고가
    stck_lwpr = float(res.json()['output2'][1]['low']) #전일 저가
    
    # 변동성 기반 동적 승수 계산
    volatility = calculate_volatility(market, code, days=20)
    
    # 변동성에 따른 승수 조정
    if volatility > 0.4:
        multiplier = 0.3
    elif volatility > 0.25:
        multiplier = 0.5
    else:
        multiplier = 0.7
    
    target_price = stck_oprc + (stck_hgpr - stck_lwpr) * multiplier
    
    # <<< [수정] 아래 로직으로 변경 >>>
    # 아직 이 종목의 목표가를 보낸 적이 없다면 메시지를 보내고 기록
    if code not in target_price_message_sent:
        send_message(f"{code} 변동성: {volatility:.2%}, 승수: {multiplier}, 목표가: ${target_price:.2f}", force_discord=True)
        target_price_message_sent.add(code) # 메시지를 보냈다고 기록
    
    return target_price

def get_stock_balance():
    """주식 잔고조회"""
    PATH = "uapi/overseas-stock/v1/trading/inquire-balance"
    URL = f"{URL_BASE}/{PATH}"
    headers = {"Content-Type":"application/json", 
        "authorization":f"Bearer {ACCESS_TOKEN}",
        "appKey":APP_KEY,
        "appSecret":APP_SECRET,
        "tr_id":"JTTT3012R",
        "custtype":"P"
    }
    params = {
        "CANO": CANO,
        "ACNT_PRDT_CD": ACNT_PRDT_CD,
        "OVRS_EXCG_CD": "NASD",
        "TR_CRCY_CD": "USD",
        "CTX_AREA_FK200": "",
        "CTX_AREA_NK200": ""
    }
    res = session.get(URL, headers=headers, params=params, timeout=30)
    stock_list = res.json()['output1']
    evaluation = res.json()['output2']
    stock_dict = {}
    send_message(f"====주식 보유잔고====")
    for stock in stock_list:
        if int(stock['ovrs_cblc_qty']) > 0:
            stock_dict[stock['ovrs_pdno']] = stock['ovrs_cblc_qty']
            send_message(f"{stock['ovrs_item_name']}({stock['ovrs_pdno']}): {stock['ovrs_cblc_qty']}주")
            time.sleep(0.1)
    send_message(f"주식 평가 금액: ${evaluation['tot_evlu_pfls_amt']}")
    time.sleep(0.1)
    send_message(f"평가 손익 합계: ${evaluation['ovrs_tot_pfls']}")
    time.sleep(0.1)
    send_message(f"=================")
    return stock_dict

def get_balance():
    """현금 잔고조회"""
    PATH = "uapi/domestic-stock/v1/trading/inquire-psbl-order"
    URL = f"{URL_BASE}/{PATH}"
    headers = {"Content-Type":"application/json", 
        "authorization":f"Bearer {ACCESS_TOKEN}",
        "appKey":APP_KEY,
        "appSecret":APP_SECRET,
        "tr_id":"TTTC8908R",
        "custtype":"P",
    }
    params = {
        "CANO": CANO,
        "ACNT_PRDT_CD": ACNT_PRDT_CD,
        "PDNO": "005930",
        "ORD_UNPR": "65500",
        "ORD_DVSN": "01",
        "CMA_EVLU_AMT_ICLD_YN": "Y",
        "OVRS_ICLD_YN": "Y"
    }
    res = session.get(URL, headers=headers, params=params, timeout=30)
    cash = res.json()['output']['ord_psbl_cash']
    send_message(f"주문 가능 현금 잔고: {cash}원")
    return int(cash)

def buy(market="NASD", code="AAPL", qty="1", price="0"):
    """미국 주식 시장가 매수"""
    PATH = "uapi/overseas-stock/v1/trading/order"
    URL = f"{URL_BASE}/{PATH}"
    data = {
        "CANO": CANO,
        "ACNT_PRDT_CD": ACNT_PRDT_CD,
        "OVRS_EXCG_CD": market,
        "PDNO": code,
        "ORD_DVSN": "00", # 해외주식 주문 구분 '00'이 지정가와 시장가 모두 포함 가능
        "ORD_QTY": str(int(qty)),
        "OVRS_ORD_UNPR": str(float(price)), # 시장가 주문이지만 현재가 입력
        "ORD_SVR_DVSN_CD": "0"
    }
    headers = {"Content-Type":"application/json", 
        "authorization":f"Bearer {ACCESS_TOKEN}",
        "appKey":APP_KEY,
        "appSecret":APP_SECRET,
        "tr_id":"TTTT1002U",
        "custtype":"P",
        "hashkey" : hashkey(data)
    }
    res = session.post(URL, headers=headers, data=json.dumps(data), timeout=30)
    if res.json()['rt_cd'] == '0':
        # 매수 성공 시 매수 가격 저장 (실제 체결가는 아니지만 로직상 기록)
        # 실제 체결가는 별도로 조회해야 가장 정확함
        buy_prices[code] = price
        trailing_stops[code] = price  # 트레일링 스탑 초기화
        send_message(f"[매수 성공] {code}: 시장가 주문, 수량: {qty}, 기준가: ${price:.2f}")
        return True
    else:
        send_message(f"[매수 실패]{str(res.json())}")
        return False

def sell(market="NASD", code="AAPL", qty="1", price="0"):
    """미국 주식 시장가 매도"""
    PATH = "uapi/overseas-stock/v1/trading/order"
    URL = f"{URL_BASE}/{PATH}"
    data = {
        "CANO": CANO,
        "ACNT_PRDT_CD": ACNT_PRDT_CD,
        "OVRS_EXCG_CD": market,
        "PDNO": code,
        "ORD_DVSN": "00",
        "ORD_QTY": str(int(qty)),
        "OVRS_ORD_UNPR": str(float(price)), # 시장가 주문이지만 현재가 입력
        "ORD_SVR_DVSN_CD": "0"
    }
    headers = {"Content-Type":"application/json", 
        "authorization":f"Bearer {ACCESS_TOKEN}",
        "appKey":APP_KEY,
        "appSecret":APP_SECRET,
        "tr_id":"TTTT1006U",
        "custtype":"P",
        "hashkey" : hashkey(data)
    }
    res = session.post(URL, headers=headers, data=json.dumps(data), timeout=30)
    if res.json()['rt_cd'] == '0':
        # 매도 성공 시 해당 종목의 기록 삭제
        if code in buy_prices:
            del buy_prices[code]
        if code in trailing_stops:
            del trailing_stops[code]
        send_message(f"[매도 성공] {code}: 시장가 주문, 수량: {qty}, 기준가: ${price:.2f}")
        return True
    else:
        send_message(f"[매도 실패]{str(res.json())}")
        return False

def check_stop_loss(code, current_price, stop_loss_pct=0.05):
    """손절매 조건 확인"""
    if code not in buy_prices:
        return False
    
    buy_price = buy_prices[code]
    stop_loss_price = buy_price * (1 - stop_loss_pct)
    
    if current_price <= stop_loss_price:
        loss_pct = (current_price - buy_price) / buy_price
        send_message(f"[손절매 신호] {code}: 매수가 ${buy_price:.2f} → 현재가 ${current_price:.2f} (손실 {loss_pct:.2%})")
        return True
    return False

def check_take_profit(code, current_price, profit_pct=0.1):
    """이익 실현 조건 확인"""
    if code not in buy_prices:
        return False
    
    buy_price = buy_prices[code]
    take_profit_price = buy_price * (1 + profit_pct)
    
    if current_price >= take_profit_price:
        profit_pct_actual = (current_price - buy_price) / buy_price
        send_message(f"[이익실현 신호] {code}: 매수가 ${buy_price:.2f} → 현재가 ${current_price:.2f} (수익 {profit_pct_actual:.2%})")
        return True
    return False

def update_trailing_stop(code, current_price):
    """트레일링 스탑 업데이트"""
    if code not in trailing_stops:
        trailing_stops[code] = current_price
    else:
        # 현재가가 기록된 최고가보다 높으면 업데이트
        if current_price > trailing_stops[code]:
            trailing_stops[code] = current_price

def check_trailing_stop(code, current_price, trailing_pct=0.02):
    """트레일링 스탑 조건 확인"""
    if code not in trailing_stops or code not in buy_prices:
        return False
    
    highest_price = trailing_stops[code]
    buy_price = buy_prices[code]
    
    # 매수가 대비 최소 2% 이상 수익이 있을 때만 트레일링 스탑 적용
    if highest_price > buy_price * 1.02:
        trailing_stop_price = highest_price * (1 - trailing_pct)
        
        if current_price <= trailing_stop_price:
            profit_pct = (current_price - buy_price) / buy_price
            send_message(f"[트레일링스탑] {code}: 최고가 ${highest_price:.2f} → 현재가 ${current_price:.2f} (수익 {profit_pct:.2%})")
            return True
    
    return False

def check_positions_for_risk_management(stock_dict, bought_list, nasd_symbol_list, nyse_symbol_list, amex_symbol_list):
    """보유 종목들의 손절매/이익실현/트레일링스탑 조건 검사 (수정된 로직)"""
    for code in list(bought_list):  # list()로 복사해서 순회 중 수정 방지
        if code in buy_prices:
            # 해당 종목의 시장 구분
            market1 = "NASD"
            market2 = "NAS"
            if code in nyse_symbol_list:
                market1 = "NYSE"
                market2 = "NYS"
            if code in amex_symbol_list:
                market1 = "AMEX"
                market2 = "AMS"
            
            try:
                current_price = get_current_price(market2, code)
                
                # <<<< 로직 수정 파트 >>>>

                # 1. 최고가(트레일링 스탑 기준)를 항상 업데이트
                update_trailing_stop(code, current_price)
                
                # 2. 손절매는 최우선으로, 다른 조건보다 먼저 확인
                if check_stop_loss(code, current_price, stop_loss_pct=0.02):
                    if code in stock_dict:
                        qty = stock_dict[code]
                        if sell(market=market1, code=code, qty=qty, price=current_price):
                            bought_list.remove(code)
                            if code in stock_dict:
                                del stock_dict[code]
                        continue # 매도 후 다음 종목으로 넘어감
                
                # 3. 트레일링 스탑이 활성화된 경우 (2% 이상 수익), 트레일링 스탑으로만 매도 판단
                if check_trailing_stop(code, current_price, trailing_pct=0.02):
                    if code in stock_dict:
                        qty = stock_dict[code]
                        if sell(market=market1, code=code, qty=qty, price=current_price):
                            bought_list.remove(code)
                            if code in stock_dict:
                                del stock_dict[code]
                        continue # 매도 후 다음 종목으로 넘어감
                
                # 4. 트레일링 스탑이 활성화되지 않은 초기 수익 구간에서만 고정 익절 실행
                elif check_take_profit(code, current_price, profit_pct=0.03):
                    if code in stock_dict:
                        qty = stock_dict[code]
                        if sell(market=market1, code=code, qty=qty, price=current_price):
                            bought_list.remove(code)
                            if code in stock_dict:
                                del stock_dict[code]
                        continue # 매도 후 다음 종목으로 넘어감
                
                # <<<< 로직 수정 종료 >>>>
                            
            except Exception as e:
                send_message(f"[위험관리 오류] {code}: {str(e)}")
                time.sleep(1)

def get_exchange_rate():
    """환율 조회"""
    PATH = "uapi/overseas-stock/v1/trading/inquire-present-balance"
    URL = f"{URL_BASE}/{PATH}"
    headers = {"Content-Type":"application/json", 
            "authorization": f"Bearer {ACCESS_TOKEN}",
            "appKey":APP_KEY,
            "appSecret":APP_SECRET,
            "tr_id":"CTRP6504R"}
    params = {
        "CANO": CANO,
        "ACNT_PRDT_CD": ACNT_PRDT_CD,
        "OVRS_EXCG_CD": "NASD",
        "WCRC_FRCR_DVSN_CD": "01",
        "NATN_CD": "840",
        "TR_MKET_CD": "01",
        "INQR_DVSN_CD": "00"
    }
    res = session.get(URL, headers=headers, params=params, timeout=30)
    exchange_rate = 1270.0
    if len(res.json()['output2']) > 0:
        exchange_rate = float(res.json()['output2'][0]['frst_bltn_exrt'])
    return exchange_rate

# 장시간 체크 함수
def is_market_open():
    """미국 주식 시장 개장 시간 체크"""
    t_now = datetime.datetime.now(timezone('America/New_York'))
    today = t_now.weekday()
    
    # 주말이면 휴장
    if today == 5 or today == 6:  # 토요일, 일요일
        return False
    
    # 평일 9:30 ~ 16:00 (EST) 개장
    market_open = t_now.replace(hour=9, minute=30, second=0, microsecond=0)
    market_close = t_now.replace(hour=16, minute=0, second=0, microsecond=0)
    
    return market_open <= t_now <= market_close

# 자동매매 시작
try:
    ACCESS_TOKEN = get_access_token()

    nasd_symbol_list = ["PLTR", "AVGO", "LRCX", "NVDA", "AAPL", "MU", "LYFT", "MSFT", "AMD"] # 매수 희망 종목 리스트 (NASD)
    nyse_symbol_list = [] 
    amex_symbol_list = [] 
    symbol_list = nasd_symbol_list + nyse_symbol_list + amex_symbol_list
    
    bought_list = [] # 매수 완료된 종목 리스트
    target_price_message_sent = set() # <<< [추가] 목표가 메시지를 보냈는지 기록하는 용도
    daily_message_sent = False  # 일일 초기 메시지 전송 여부

    # 장시간이 아니면 프로그램 종료
    if not is_market_open():
        send_message("현재 장시간이 아닙니다. 프로그램을 종료합니다.", force_discord=True)
        exit()

    total_cash = get_balance() # 보유 현금 조회
    exchange_rate = get_exchange_rate() # 환율 조회
    stock_dict = get_stock_balance() # 보유 주식 조회
    for sym in stock_dict.keys():
        bought_list.append(sym)
    target_buy_count = 4 # 매수할 종목 수
    buy_percent = 0.25 # 종목당 매수 금액 비율
    buy_amount = total_cash * buy_percent / exchange_rate # 종목별 주문 금액 계산 (달러)
    soldout = False

    # 초기 메시지는 한 번만 전송 (Discord에도 전송)
    if not daily_message_sent:
        # 버전 정보 가져오기
        version_info = get_version_info()
        
        send_message("===해외 주식 자동매매 프로그램을 시작합니다===", force_discord=True)
        send_message(version_info, force_discord=True)
        send_message(f"목표 매수 종목 수: {target_buy_count}, 종목당 투자 비율: {buy_percent:.0%}", force_discord=True)
        send_message(f"위험관리: 손절매 -5%, 이익실현 +10%, 트레일링스탑 -2%", force_discord=True)
        
        # 현재 잔고 및 보유 종목 정보 전송
        send_balance_info()
        
        # 모든 종목의 목표가를 한 번에 계산하고 메시지 전송
        for sym in symbol_list:
            market2 = "NAS"
            if sym in nyse_symbol_list:
                market2 = "NYS"
            if sym in amex_symbol_list:
                market2 = "AMS"
            try:
                target_price = get_target_price(market2, sym)
                # get_target_price 내부에서 목표가 메시지가 전송됨
            except Exception as e:
                send_message(f"[목표가 계산 오류] {sym}: {str(e)}")
        
        daily_message_sent = True
    
    while True:
        t_now = datetime.datetime.now(timezone('America/New_York')) # 뉴욕 기준 현재 시간
        t_9 = t_now.replace(hour=9, minute=30, second=0, microsecond=0)
        t_start = t_now.replace(hour=9, minute=35, second=0, microsecond=0)
        t_sell = t_now.replace(hour=15, minute=45, second=0, microsecond=0)
        t_exit = t_now.replace(hour=15, minute=50, second=0,microsecond=0)
        today = t_now.weekday()
        
        # 장시간이 아니면 프로그램 종료
        if not is_market_open():
            send_message("장시간이 종료되어 프로그램을 종료합니다.", force_discord=True)
            break
            
        if t_9 < t_now < t_start and soldout == False: # 잔여 수량 매도
            for sym, qty in stock_dict.items():
                market1 = "NASD"
                market2 = "NAS"
                if sym in nyse_symbol_list:
                    market1 = "NYSE"
                    market2 = "NYS"
                if sym in amex_symbol_list:
                    market1 = "AMEX"
                    market2 = "AMS"
                sell(market=market1, code=sym, qty=qty, price=get_current_price(market=market2, code=sym))
            soldout = True
            bought_list = []
            time.sleep(1)
            stock_dict = get_stock_balance()
            
        if t_start < t_now < t_sell:  # AM 09:35 ~ PM 03:45 : 매수 및 위험관리
            # 1. 기존 포지션 위험관리 (손절/익절/트레일링스탑)
            check_positions_for_risk_management(stock_dict, bought_list, nasd_symbol_list, nyse_symbol_list, amex_symbol_list)
            
            # 2. 새로운 매수 기회 탐색
            for sym in symbol_list:
                if len(bought_list) < target_buy_count:
                    if sym in bought_list:
                        continue
                    market1 = "NASD"
                    market2 = "NAS"
                    if sym in nyse_symbol_list:
                        market1 = "NYSE"
                        market2 = "NYS"
                    if sym in amex_symbol_list:
                        market1 = "AMEX"
                        market2 = "AMS"
                    
                    try:
                        # 동적 목표가 계산 적용
                        target_price = get_target_price(market2, sym)
                        current_price = get_current_price(market2, sym)
                        
                        if target_price < current_price:
                            buy_qty = 0  # 매수할 수량 초기화
                            buy_qty = int(buy_amount // current_price)
                            if buy_qty > 0:
                                send_message(f"{sym} 목표가 달성({target_price:.2f} < {current_price:.2f}) 매수를 시도합니다.")
                                # 시장가 매수를 위해 price 에는 체결 기준용 현재가를 넘겨줌
                                result = buy(market=market1, code=sym, qty=buy_qty, price=current_price) 
                                time.sleep(1)
                                if result:
                                    soldout = False
                                    bought_list.append(sym)
                                    get_stock_balance()
                    except Exception as e:
                        send_message(f"[매수 시도 오류] {sym}: {str(e)}")
                        time.sleep(5)  # 오류 시 더 긴 대기시간
                        
            time.sleep(10)  # 10초마다 체크
            
            # 30분마다 잔고 확인
            if t_now.minute == 30 and t_now.second <= 10: 
                get_stock_balance()
                time.sleep(5)
                
        if t_sell < t_now < t_exit:  # PM 03:45 ~ PM 03:50 : 일괄 매도
            if soldout == False:
                stock_dict = get_stock_balance()
                for sym, qty in stock_dict.items():
                    market1 = "NASD"
                    market2 = "NAS"
                    if sym in nyse_symbol_list:
                        market1 = "NYSE"
                        market2 = "NYS"
                    if sym in amex_symbol_list:
                        market1 = "AMEX"
                        market2 = "AMS"
                    # 시장가 매도를 위해 price 에는 참고용 현재가를 넘겨줌
                    sell(market=market1, code=sym, qty=qty, price=get_current_price(market=market2, code=sym))
                soldout = True
                bought_list = []
                time.sleep(1)
                
        if t_exit < t_now:  # PM 03:50 ~ :프로그램 종료
            # 장 종료 전 최종 잔고 정보 전송
            send_message("📊 ===== 장 마감 결과 =====", force_discord=True)
            send_balance_info()
            send_message("🔔 미국 장시간이 종료되었습니다. 프로그램을 종료합니다.", force_discord=True)
            break
            
        time.sleep(5)  # 5초 대기
        
except Exception as e:
    send_message(f"[오류 발생]{e}")
    time.sleep(1)
