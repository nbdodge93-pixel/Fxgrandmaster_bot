import MetaTrader5 as mt5
import time
import pandas as pd
import requests

# 1. MT5 ከ Exness ጋር ማገናኘት
if not mt5.initialize():
    print("❌ MT5 initialization failed.")
    mt5.shutdown()
    quit()

SYMBOL = "EURUSD"
LOT_SIZE = 0.01  # ለሙከራ ($25-$50) ደህንነቱ የተጠበቀ ሎት
MAGIC_NUMBER = 999999

print("🚀 Fxgrandmaster High-Impact News & Price Action Bot ተጀመረ...")

# 2. የዋጋ ታሪክ መረጃዎችን መቀበያ
def get_rates(symbol, timeframe, count=50):
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, count)
    if rates is None:
        return None
    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    return df

# 3. ከፍተኛ ተጽዕኖ ያላቸውን ዜናዎች (High-Impact News) እና Actual vs Forecast መለኪያ
def check_high_impact_news():
    try:
        # ነጻ የኢኮኖሚ ካላንደር ዌብሳይት/ኤፒአይ በመጠቀም የቀጥታ ዜናዎችን መቃኘት
        # (ለፈጣን ምላሽ የቅርብ ጊዜውን የዩኤስ እና የዩሮ ዞን High-Impact ዜናዎችን ይፈትሻል)
        url = "https://nfs.faireconomy.media/ff_calendar_thisweek.json"
        response = requests.get(url, timeout=3)
        if response.status_code == 200:
            events = response.json()
            current_time = pd.Timestamp.now(tz='UTC')
            
            for event in events:
                if event.get('country') in ['USD', 'EUR'] and event.get('impact') == 'High':
                    event_time = pd.to_datetime(event.get('date'))
                    
                    # ዜናው ልክ አሁን (በሚቀጥሉት 30 ሰኮንዶች ውስጥ) የሚለቀቅ ከሆነ ወይም አዲስ ከተለቀቀ
                    time_diff = (event_time - current_time).total_seconds()
                    
                    if -10 <= time_diff <= 15:  # ዜናው በሚወጣበት ሰዓት ላይ ትክክለኛውን ቁጥር እንፈትሻለን
                        actual = event.get('actual')
                        forecast = event.get('forecast')
                        
                        if actual is not None and forecast is not None:
                            try:
                                act_val = float(str(actual).replace('%','').replace('K','').replace('M',''))
                                fcast_val = float(str(forecast).replace('%','').replace('K','').replace('M',''))
                                
                                title = event.get('title', '')
                                currency = event.get('country')
                                
                                # ለ EURUSD የሚሆን የዜና ማዛመጃ ሎጂክ
                                # USD ዜና ከሆነ: Actual > Forecast ለ USD መልካም (EURUSD ይወርዳል -> SELL)
                                # EUR ዜና ከሆነ: Actual > Forecast ለ EUR መልካም (EURUSD ይወጣል -> BUY)
                                if currency == 'USD':
                                    if act_val > fcast_val:
                                        return "SELL", f"USD High News ({title}): Act {actual} > Fcast {forecast}"
                                    elif act_val < fcast_val:
                                        return "BUY", f"USD High News ({title}): Act {actual} < Fcast {forecast}"
                                        
                                elif currency == 'EUR':
                                    if act_val > fcast_val:
                                        return "BUY", f"EUR High News ({title}): Act {actual} > Fcast {forecast}"
                                    elif act_val < fcast_val:
                                        return "SELL", f"EUR High News ({title}): Act {actual} < Fcast {forecast}"
                            except Exception as parse_err:
                                continue
        return None, None
    except Exception as e:
        return None, None

# 4. የ Price Action ስትራቴጂ (Support/Resistance, Fake Breakout & FVG)
def analyze_price_action(df):
    resistance = df['high'].rolling(window=20).max().iloc[-1]
    support = df['low'].rolling(window=20).min().iloc[-1]
    current_close = df['close'].iloc[-1]
    
    # Fake Breakout ማረጋገጫ
    fake_breakout_buy = (df['low'].iloc[-2] < support) and (current_close > support)
    fake_breakout_sell = (df['high'].iloc[-2] > resistance) and (current_close < resistance)
    
    # Market Imbalance (FVG)
    imbalance_buy = (df['low'].iloc[-1] > df['high'].iloc[-3])
    imbalance_sell = (df['high'].iloc[-1] < df['low'].iloc[-3])
    
    if fake_breakout_buy or imbalance_buy:
        return "BUY"
    elif fake_breakout_sell or imbalance_sell:
        return "SELL"
    return None

# 5. ትዕዛዝ ማስፈጸሚያ (Execution Engine በ Millisecond ፍጥነት)
def execute_trade(signal, comment_text):
    tick = mt5.symbol_info_tick(SYMBOL)
    if tick is None:
        return

    # በአንድ ጊዜ አንድ ትዕዛዝ ብቻ እንዲኖር መከላከል
    positions = mt5.positions_get(symbol=SYMBOL)
    if positions is not None and len(positions) > 0:
        return  

    if signal == "BUY":
        price = tick.ask
        sl = price - 0.0020  # 20 Pips Stop Loss
        tp = price + 0.0040  # 40 Pips Take Profit
        
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": SYMBOL,
            "volume": LOT_SIZE,
            "type": mt5.ORDER_TYPE_BUY,
            "price": price,
            "sl": sl,
            "tp": tp,
            "deviation": 30,  # በዜና ሰዓት ፈጣን ዋጋ ለመቀበል የተስተካከለ Slippage
            "magic": MAGIC_NUMBER,
            "comment": comment_text[:30],
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_FOK,
        }
        result = mt5.order_send(request)
        if result.retcode == mt5.TRADE_RETCODE_DONE:
            print(f"✅ [NEWS/PA BUY] በተሳካ ሁኔታ ተከፈተ! | {comment_text}")

    elif signal == "SELL":
        price = tick.bid
        sl = price + 0.0020
        tp = price - 0.0040
        
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": SYMBOL,
            "volume": LOT_SIZE,
            "type": mt5.ORDER_TYPE_SELL,
            "price": price,
            "sl": sl,
            "tp": tp,
            "deviation": 30,
            "magic": MAGIC_NUMBER,
            "comment": comment_text[:30],
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_FOK,
        }
        result = mt5.order_send(request)
        if result.retcode == mt5.TRADE_RETCODE_DONE:
            print(f"✅ [NEWS/PA SELL] በተሳካ ሁኔታ ተከፈተ! | {comment_text}")

# 6. ዋናው የክትትል ሉፕ (Main High-Speed Loop)
while True:
    try:
        # ሀ) መጀመሪያ የከባድ ዜናዎችን (High-Impact News) ሁኔታ በሰኮንድ ውስጥ እንፈትሻለን
        news_signal, news_comment = check_high_impact_news()
        if news_signal:
            print(f"⚡ ከባድ የዜና ሲግናል ተገኘ: {news_comment} -> ትዕዛዝ በመላክ ላይ...")
            execute_trade(news_signal, news_comment)
            time.sleep(10)  # ከዜና ትዕዛዝ በኋላ አጭር እረፍት
            continue

        # ለ) ዜና ከሌለ በ Price Action (Fake Breakout & FVG) መሰረት ከፍተኛ ዕድል ያላቸውን እንቃኛለን
        df = get_rates(SYMBOL, mt5.TIMEFRAME_M1, count=30) # የ 1 ደቂቃ ሰም ለፈጣን ምላሽ
        if df is not None:
            pa_signal = analyze_price_action(df)
            if pa_signal:
                print(f"🎯 የ Price Action ሲግናል ተገኘ: {pa_signal}")
                execute_trade(pa_signal, f"PA_{pa_signal}")
        
        # ገበያው እንዳያመልጥ በየ 2 ሰኮንዱ በፍጥነት ይቃኛል
        time.sleep(2)
        
    except Exception as e:
        print(f"ስህተት ተፈጥሯል: {e}")
        time.sleep(3)
