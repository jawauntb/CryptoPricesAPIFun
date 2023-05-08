from pycoingecko import CoinGeckoAPI
cg = CoinGeckoAPI()
cg.ping()

def getUSDPriceByID(tid):
  vs_currencies=['usd']
  return cg.get_price(tid, vs_currencies)

def getTokenFromContract(contract):
  id='ethereum'
  return cg.get_coin_info_from_contract_address_by_id(id, contract)

vs_currencies=['usd']
token = getTokenFromContract('0xfca59cd816ab1ead66534d82bc21e7515ce441cf')

token_id = token['id']
alldays = [1,2,5,10,20,40,80]

# cg.get_coin_market_chart_from_contract_address_by_id()
# chart = cg.get_coin_market_chart_by_id(token_id, vs_currencies, 2)
# print(chart['prices'])
# ohlc are candles
ohlc = cg.get_coin_ohlc_by_id(token_id, vs_currencies, 1)
# print(ohlc)

def getCandlesFromOHLC(ohlc):
  candles = []
  for row in ohlc:
    candle = {
      'ts':row[0], 
      'open':row[1],
      'high':row[2],
      'low':row[3],
      'close': row[4]}
    candles.append(candle)
  return candles
  
candles = getCandlesFromOHLC(ohlc)

from functools import reduce
# Calculates the SMA of an array of candles using the `source` price.
def calculate_sma(candles, source):
    length = len(candles)
    sum = reduce((lambda last, x: { source: last[source] + x[source] }), candles)
    sma = sum[source] / length
    return sma

# Calculates the EMA of an array of candles using the `source` price.
def calculate_ema(candles, source):
    length = len(candles)
    target = candles[0]
    previous = candles[1]
    # if there is no previous EMA calculated, then EMA=SMA
    if 'ema' not in previous or previous['ema'] == None:
        return calculate_sma(candles, source)
    else:
        # multiplier: (2 / (length + 1))
        # EMA: (close * multiplier) + ((1 - multiplier) * EMA(previous))
        multiplier = 2 / (length + 1)
        ema = (target[source] * multiplier) + (previous['ema'] * (1 - multiplier))

        return ema


# Calculates the EMA(EMA) of an array of candles.
def calculate_ema_ema(candles):
    length = len(candles)
    target = candles[0]
    previous = candles[1]
    # all previous candles need to have an EMA already, otherwise we can't calculate EMA(EMA)
    have_ema = list(filter(lambda a: 'ema' in a and a['ema'] != None, candles[1:]))
    if len(have_ema) >= length - 1:
        # if there is no previous EMA(EMA) calculated yet, then EMA(EMA)=SMA(EMA)
        if 'ema_ema' not in previous or previous['ema_ema'] == None:
            return calculate_sma(candles, 'ema')
        # if there is a previous EMA(EMA), it is used
        else:
            # multiplier: (2 / (length + 1))
            # EMA(EMA): (EMA * multiplier) + ((1 - multiplier) * EMA(EMA, previous))
            multiplier = 2 / (length + 1)
            ema_ema = (target['ema'] * multiplier) + (previous['ema_ema'] * (1 - multiplier))

            return ema_ema
    else:
        return None

# Calculates the DEMA of an array of candles.
def calculate_dema(candles):
    target = candles[0]
    # can only calculate the DEMA if we have the EMA and the EMA(EMA) if the target candle
    if 'ema' not in target or 'ema_ema' not in target or target['ema'] == None or target['ema_ema'] == None:
        return None
    else:
        # DEMA = 2*EMA – EMA(EMA)
        dema = (2 * target['ema']) - target['ema_ema']
        return dema

def calculate(candles, source):
    candles[0]['sma'] = calculate_sma(candles, source)
    candles[0]['ema'] = calculate_ema(candles, source)
    candles[0]['ema_ema'] = calculate_ema_ema(candles)
    candles[0]['dema'] = calculate_dema(candles)

EMA_LENGTH = 10
EMA_SOURCE = 'close'
position = 0
while position + EMA_LENGTH <= len(candles):
    current_candles = candles[position:(position+EMA_LENGTH)]
    current_candles = list(reversed(current_candles))
    calculate(current_candles, EMA_SOURCE)
    position += 1

for candle in candles:
    if 'sma' in candle:
        print('{}: sma={} ema={} ema(ema)={} dema={}'.format(candle['ts'], candle['sma'], candle['ema'], candle['ema_ema'], candle['dema']))
