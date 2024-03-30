import requests
import time
import json

# 업비트 KRW 마켓에서 거래되는 코인 목록을 가져옵니다.
def get_upbit_krw_tickers():
    url = "https://api.upbit.com/v1/market/all?isDetails=false"
    response = requests.get(url)
    markets = response.json()
    krw_markets = [market['market'] for market in markets if market['market'].startswith('KRW-')]
    return krw_markets

# 바이낸스 USDT 마켓에서 거래되는 코인 목록을 가져옵니다.
def get_binance_usdt_tickers():
    url = "https://api.binance.com/api/v3/ticker/price"
    response = requests.get(url)
    prices = response.json()
    usdt_markets = [price['symbol'] for price in prices if price['symbol'].endswith('USDT')]
    return usdt_markets

# 업비트와 바이낸스에서 공통으로 거래되는 코인의 프리미엄을 계산합니다.
def calculate_premiums():
    upbit_tickers = get_upbit_krw_tickers()
    binance_tickers = get_binance_usdt_tickers()

    global exchange_rate

    max_premium_value = 0.0
    max_coin_name = ''

    # 업비트와 바이낸스에서 공통으로 거래되는 코인을 찾습니다.
    common_tickers = set([ticker.replace("KRW-", "") for ticker in upbit_tickers]) & set([ticker.replace("USDT", "") for ticker in binance_tickers])

    for ticker in common_tickers:
        # 업비트 가격 조회
        upbit_price_url = f"https://api.upbit.com/v1/ticker?markets=KRW-{ticker}"
        upbit_price = requests.get(upbit_price_url).json()[0]['trade_price']

        # 바이낸스 가격 조회
        binance_price_url = f"https://api.binance.com/api/v3/ticker/price?symbol={ticker}USDT"
        binance_price = requests.get(binance_price_url).json()['price']

        # 프리미엄 계산
        premium = (upbit_price - float(binance_price)*exchange_rate) / (float(binance_price)*exchange_rate) * 100

        if premium > max_premium_value and ticker != 'BTG':
            max_premium_value = premium
            max_coin_name = ticker
        print(f"{ticker}: 업비트 가격 = {upbit_price}, 바이낸스 가격 = {binance_price}, 프리미엄 = {premium:.2f}%")
    return {max_coin_name:max_premium_value}

# 사용자 액세스 토큰
access_token = 'uJrboorhlYtWzNGjK5ji4DjS-V67OIbRxUAKPXObAAABjZbrm56UJG13ldIf8A'
client_id = '6f8259fbd96e011565b64c6e4e9524bc'
refresh_token = 'r49RLbC_CfRkSwAQ1vheiGHpTTGeyZw8T2IKPXObAAABjZbrm5qUJG13ldIf8A'

def refresh_access_token():
    global access_token
    """
    리프레시 토큰을 사용하여 새 액세스 토큰을 요청합니다.

    :param client_id: 애플리케이션의 클라이언트 ID
    :param refresh_token: 사용자의 리프레시 토큰
    :return: 새로 발급된 액세스 토큰
    """
    url = 'https://kauth.kakao.com/oauth/token'
    payload = {
        'grant_type': 'refresh_token',
        'client_id': client_id,
        'refresh_token': refresh_token
    }
    response = requests.post(url, data=payload)
    response_data = response.json()

    if response.status_code == 200 and 'access_token' in response_data:
        access_token = response_data['access_token']
        # 필요한 경우, 새 리프레시 토큰도 저장할 수 있습니다.
        # new_refresh_token = response_data.get('refresh_token', refresh_token)
        # print("뉴 액세스 토큰 : {}".format(access_token))
    else:
        print("액세스 토큰 갱신 실패:", response_data.get("error_description", "Unknown error"))

def send_message_to_kakao(message):
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    data = {
        'template_object': json.dumps({
            'object_type': 'text',
            'text': message,
            'link': {
                'web_url': 'https://www.example.com',
                'mobile_web_url': 'https://www.example.com'
            },
            'button_title': '웹사이트 방문'
        })
    }
    response = requests.post('https://kapi.kakao.com/v2/api/talk/memo/default/send', headers=headers, data=data)

    if response.status_code != 200:
        print("메시지 전송 실패:", response.json())
    else:
        print("메시지가 성공적으로 전송되었습니다.")

def get_usdt_krw_price():
    import requests

    global exchange_rate

    url = "https://api.bithumb.com/public/ticker/usdt_KRW"
    try:
        response = requests.get(url)
        response_data = response.json()

        # 성공적으로 데이터를 받아왔다면 가격 정보 출력
        if response_data.get("status") == "0000":
            exchange_rate = (float)(response_data["data"]["closing_price"])
        else:
            print("가격 정보를 조회하는 데 실패했습니다.")
    except Exception as e:
        print(f"데이터 조회 중 오류가 발생했습니다: {e}")

# 프리미엄 계산 실행
while True:
    exchange_rate = 0
    get_usdt_krw_price()
    print(exchange_rate)

    a = calculate_premiums()
    coin_name = list(a.keys())
    coin_premium = list(a.values())

    message1 = "가장 프리미엄이 큰 코인 : {}".format(coin_name)
    message2 = "프리미엄 : {}%".format(coin_premium)
    message3 = "환율 : {}".format(exchange_rate)

    print(message1, message2, message3)
    
    refresh_access_token()

    send_message_to_kakao(message1)
    send_message_to_kakao(message2)
    send_message_to_kakao(message3)

    print("Waiting 60 seconds for the next update...\n")
    time.sleep(60)  # 60초 대기 후 다시 실행
