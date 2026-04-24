# Lambda container image — Python 3.11
FROM public.ecr.aws/lambda/python:3.11

# TA-Lib C kütüphanesini kaynak koddan derle (Lambda'da pip install yetmez)
RUN yum install -y gcc gcc-c++ make wget tar gzip && \
    wget -q https://sourceforge.net/projects/ta-lib/files/ta-lib/0.4.0/ta-lib-0.4.0-src.tar.gz && \
    tar -xzf ta-lib-0.4.0-src.tar.gz && \
    cd ta-lib && ./configure --prefix=/usr && make && make install && \
    cd .. && rm -rf ta-lib ta-lib-0.4.0-src.tar.gz

# Python bağımlılıklarını kur
COPY requirements.txt .
RUN pip install --no-cache-dir numpy==1.24.2 && \
    pip install --no-cache-dir --no-build-isolation TA-Lib==0.4.28 && \
    pip install --no-cache-dir pymongo==4.5.0 requests==2.28.2 pandas==1.5.3 python-dotenv==1.0.0

# Uygulama dosyalarını kopyala
COPY . ${LAMBDA_TASK_ROOT}

# Lambda handler: main.py içindeki handler fonksiyonu
CMD ["main.handler"]
