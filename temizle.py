from flask import Flask, render_template, request, send_file, session, redirect, url_for
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
import os
import json
import sqlite3
import shutil
import numpy as np
import soundfile as sf
from moviepy import AudioFileClip
import subprocess

app = Flask(__name__)
app.secret_key = "trafo_master_SaaS_key_2026"

# Flask-Login Ayarları
login_manager = LoginManager()
login_manager.init_app(app)

class User(UserMixin):
    def __init__(self, user_id, isim, eposta, hak, premium):
        self.id = user_id
        self.isim = isim
        self.eposta = eposta
        self.hak = hak
        self.premium = premium

@login_manager.user_loader
def load_user(user_id):
    conn = sqlite3.connect("kullanicilar.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM kullanicilar WHERE id = ?", (user_id,))
    u = cursor.fetchone()
    conn.close()
    if u:
        return User(u[0], u[1], u[2], u[3], u[4])
    return None

def dil_yukle(dil_kodu):
    yol = f"diller/{dil_kodu}.json"
    if os.path.exists(yol):
        with open(yol, "r", encoding="utf-8") as f:
            return json.load(f)
    with open("diller/en.json", "r", encoding="utf-8") as f:
        return json.load(f)

@app.route("/", methods=["GET"])
def ana_sayfa():
    secilen_dil = request.args.get("lang", "tr")
    dil_sozlugu = dil_yukle(secilen_dil)
    
    mevcut = None
    if current_user.is_authenticated:
        mevcut = {"isim": current_user.isim, "hak": current_user.hak}
        
    return render_template("index.html", dil=dil_sozlugu, seculi_dil=secilen_dil, mevcut_kullanici=mevcut)

@app.route("/login")
def login():
    conn = sqlite3.connect("kullanicilar.db")
    cursor = conn.cursor()
    test_id = "google_123456"
    cursor.execute("INSERT OR IGNORE INTO kullanicilar (id, isim, eposta) VALUES (?, ?, ?)", 
                   (test_id, "Test Kullanicisi", "test@gmail.com"))
    conn.commit()
    conn.close()
    
    user = load_user(test_id)
    login_user(user)
    return redirect(url_for("ana_sayfa"))

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("ana_sayfa"))

@app.route("/temizle", methods=["POST"])
@login_required
def ses_temizle_islemi():
    secilen_dil = request.args.get("lang", "tr")
    dil_sozlugu = dil_yukle(secilen_dil)
    
    if current_user.hak <= 0 and current_user.premium == 0:
        return render_template("index.html", dil=dil_sozlugu, seculi_dil=secilen_dil, mevcut_kullanici={"isim": current_user.isim, "hak": 0}, hata="Ücretsiz hakkınız bitti! Devam etmek için aylık 5$'lık Premium plana geçin.")

    file = request.files.get("ses_dosyası")
    if not file or file.filename == "":
        return render_template("index.html", dil=dil_sozlugu, seculi_dil=secilen_dil, mevcut_kullanici={"isim": current_user.isim, "hak": current_user.hak}, hata="Geçersiz dosya.")

    uzanti = os.path.splitext(file.filename)[1].lower()
    girdi_yolu = f"gecici_girdi{uzanti}"
    cikti_wav_yolu = "gecici_isleme.wav"
    nihai_cikti_yolu = "studyo_kalitesi.wav"
    
    file.save(girdi_yolu)

    try:
        if uzanti in [".mp3", ".mp4"]:
            ses_klibi = AudioFileClip(girdi_yolu)
            ses_klibi.write_audiofile(cikti_wav_yolu, fps=44100, logger=None)
            ses_klibi.close()
            isleme_dosyasi = cikti_wav_yolu
        else:
            isleme_dosyasi = girdi_yolu

        print("\n🤖 META AI DEMUCS MODELİ BAŞLADI...")
        command = ["demucs", "--two-stems=vocals", isleme_dosyasi]
        subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        klasor_adi = os.path.splitext(os.path.basename(isleme_dosyasi))[0]
        vokal_sirri = f"separated/htdemucs/{klasor_adi}/vocals.wav"

        if os.path.exists(vokal_sirri):
            data, rate = sf.read(vokal_sirri)
            maks_deger = np.max(np.abs(data))
            if maks_deger > 0:
                data = (data / maks_deger) * 0.9
            sf.write(nihai_cikti_yolu, data, rate)
            shutil.rmtree("separated", ignore_errors=True)
        else:
            raise Exception("Yapay zeka vokal kanalı üretemedi.")

        if os.path.exists(girdi_yolu): os.remove(girdi_yolu)
        if os.path.exists(cikti_wav_yolu): os.remove(cikti_wav_yolu)

        if current_user.premium == 0:
            conn = sqlite3.connect("kullanicilar.db")
            cursor = conn.cursor()
            cursor.execute("UPDATE kullanicilar SET kalan_hak = kalan_hak - 1 WHERE id = ?", (current_user.id,))
            conn.commit()
            conn.close()

        yenilenen_user = load_user(current_user.id)
        return render_template("index.html", dil=dil_sozlugu, seculi_dil=secilen_dil, mevcut_kullanici={"isim": yenilenen_user.isim, "hak": yenilenen_user.hak}, indirme_linki="/indir")

    except Exception as e:
        if os.path.exists(girdi_yolu): os.remove(girdi_yolu)
        if os.path.exists(cikti_wav_yolu): os.remove(cikti_wav_yolu)
        return render_template("index.html", dil=dil_sozlugu, seculi_dil=secilen_dil, mevcut_kullanici={"isim": current_user.isim, "hak": current_user.hak}, hata=f"Hata: {str(e)}")

@app.route("/indir", methods=["GET"])
@login_required
def indir():
    return send_file("studyo_kalitesi.wav", as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True, port=5000)