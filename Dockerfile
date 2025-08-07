# Estágio 1: Imagem base com Python
FROM python:3.9-slim as base

# Define o diretório de trabalho
WORKDIR /app

# Variáveis de ambiente
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Instala as dependências do sistema para o Playwright
# O comando 'playwright install --with-deps' fará isso automaticamente,
# mas é uma boa prática ter as dependências listadas explicitamente.
RUN apt-get update && apt-get install -y \
    build-essential \
    libglib2.0-0 \
    libnss3 \
    libnspr4 \
    libdbus-1-3 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    && rm -rf /var/lib/apt/lists/*

# Copia o arquivo de dependências
COPY requirements.txt .

# Instala as dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Instala o Playwright e seus navegadores
# O '--with-deps' garante que todas as dependências do SO sejam instaladas
RUN playwright install --with-deps chromium

# Estágio 2: Imagem final de produção
FROM base as final

# Define o diretório de trabalho
WORKDIR /app

# Copia as dependências instaladas do estágio 'base'
COPY --from=base /usr/local/lib/python3.9/site-packages/ /usr/local/lib/python3.9/site-packages/
COPY --from=base /root/.cache/ms-playwright/ /root/.cache/ms-playwright/

# Copia o código da aplicação
COPY . .

# Expõe a porta que a aplicação irá rodar
EXPOSE 8000

# Comando para iniciar a aplicação
# Usa o Uvicorn para rodar a aplicação FastAPI
# O host 0.0.0.0 é necessário para que a aplicação seja acessível de fora do container
# O Gunicorn é recomendado para produção, mas Uvicorn é suficiente para muitos casos no Cloud Run.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]