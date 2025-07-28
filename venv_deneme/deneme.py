import matplotlib.pyplot as plt

# Veriler
x = [1, 2, 3, 4, 5]
y = [2, 4, 1, 8, 7]

# Grafik oluşturma
plt.plot(x, y, label="Veri", marker='o', color='blue')

# Başlık ve etiketler
plt.title("Basit Çizgi Grafiği")
plt.xlabel("X ekseni")
plt.ylabel("Y ekseni")

# Efsane (legend) ve grid
plt.legend()
plt.grid(True)

# Göster
plt.show()
