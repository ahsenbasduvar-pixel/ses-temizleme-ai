import sqlite3

def veritabanini_kur():
    conn = sqlite3.connect("kullanicilar.db")
    cursor = conn.cursor()
    
    # Kullanıcılar tablosunu oluşturuyoruz
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS kullanicilar (
        id TEXT PRIMARY KEY,
        isim TEXT,
        eposta TEXT UNIQUE,
        kalan_hak INTEGER DEFAULT 3,
        premium_durumu INTEGER DEFAULT 0
    )
    """)
    
    conn.commit()
    conn.close()
    print("💾 SQLite Veritabanı başarıyla kuruldu ve hazır!")

if __name__ == "__main__":
    veritabanini_kur()