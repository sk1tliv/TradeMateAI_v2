from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import yfinance as yf
import os
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

app = Flask(__name__)
CORS(app)

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def get_price_change(symbol):
    try:
        df = yf.Ticker(symbol).history(period="30d")['Close']
        return round(((df.iloc[-1] - df.iloc[0]) / df.iloc[0]) * 100, 2)
    except Exception as e:
        print(f"Hata: {symbol} için veri alınamadı - {e}")
        return 0.0

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/invest", methods=["POST"])
def invest():
    data = request.get_json()
    income = data.get("income")
    duration = data.get("duration")
    risk = data.get("risk")

    if income is None or duration is None or risk is None:
        return {"advice": "Gelir, süre veya risk tercihi eksik!"}, 400

    btc = get_price_change("BTC-USD")
    eur = get_price_change("EURUSD=X")
    gold = get_price_change("XAUUSD=X")

    prompt = f""" 
Sen finans danışmanı bir yapay zekasın. 
Kullanıcının bilgileri: 
- Aylık gelir: {income} TL 
- Yatırım süresi: {duration} yıl 
- Risk tercihi: {risk} 
Son 30 günlük piyasa değişimleri: 
- Bitcoin: %{btc} 
- Euro/Dolar: %{eur} 
- Altın: %{gold} 
Bu verilere dayanarak kullanıcıya 4-5 satırdan oluşan kısa bir yatırım önerisi ver. 
"""

    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.7,
                top_p=0.95,
                top_k=40,
                max_output_tokens=150
            )
        )
        advice = response.text.strip()
        return {"advice": advice}

    except Exception as e:
        print(f"Gemini API hatası: {e}")
        return {"advice": "Üzgünüm, şu anda öneri oluşturulamıyor. Lütfen daha sonra tekrar deneyin."}, 500

if __name__ == '__main__':
    app.run(debug=True)
