import numpy as np
from scipy.io import wavfile

print("🔊 Test için cızırtılı/gürültülü ses dosyası üretiliyor...")

ornekleme_hizi = 44100
sure = 5.0
t = np.linspace(0, sure, int(ornekleme_hizi * sure), endpoint=False)
temiz_ses = np.sin(2 * np.pi * 440 * t) * 0.5
gurultu = np.random.normal(0, 0.3, temiz_ses.shape)
gurultulu_ses = temiz_ses + gurultu

wavfile.write("gurultulu.wav", ornekleme_hizi, gurultulu_ses.astype(np.float32))
print("✅ 'gurultulu.wav' başarıyla oluşturuldu!")