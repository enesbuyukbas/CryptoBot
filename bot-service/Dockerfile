# Python için temel imaj
FROM python:3.9

# Çalışma dizinini oluşturun
WORKDIR /app

# Gereksinimler dosyasını kopyalayın
COPY requirements.txt /app/

# Bağımlılıkları yükleyin
RUN pip install --no-cache-dir -r requirements.txt

# Uygulama dosyalarını kopyalayın
COPY . /app/

# Uygulamayı çalıştırın
CMD ["python", "main.py"]
