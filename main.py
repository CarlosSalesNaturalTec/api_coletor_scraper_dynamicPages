import uvicorn
from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel
from typing import List
import traceback
from datetime import datetime

# Importações locais
from firestore_client import get_firestore_client, log_error
from scraper import scrape_url

# Inicializa a aplicação FastAPI
app = FastAPI(
    title="API Coletor Scraper",
    description="Uma API para orquestrar o scraping de páginas web dinâmicas com Playwright.",
    version="1.0.0"
)

class ScrapeRequest(BaseModel):
    urls: List[str] = []

def run_scraping_jobs(urls_to_scrape: List[str]):
    """
    Função executada em background que itera sobre as URLs,
    tenta fazer o scraping e salva o resultado ou o erro no Firestore.
    """
    print(f"Iniciando processo de scraping para {len(urls_to_scrape)} URLs.")
    db = get_firestore_client()

    if not db:
        # Se não houver conexão com o DB, não há como prosseguir.
        # O erro já foi logado por get_firestore_client e log_error lida com isso.
        log_error(
            "Falha crítica em 'run_scraping_jobs': não foi possível conectar ao Firestore.",
            {"urls_count": len(urls_to_scrape)}
        )
        return

    for url in urls_to_scrape:
        try:
            # 1. Tenta fazer o scraping
            scraped_data = scrape_url(url)
            
            # 2. Adiciona metadados do processo
            scraped_data['scraped_by'] = 'Playwright'
            scraped_data['scraped_at'] = datetime.now()
            
            # 3. Salva o resultado na coleção 'scraped_articles'
            db.collection('scraped_articles').add(scraped_data)
            print(f"Dados de '{url}' salvos com sucesso em 'scraped_articles'.")

        except Exception as e:
            # 4. Se ocorrer qualquer erro durante o scraping, registra a falha
            print(f"Falha ao processar a URL: {url}. Motivo: {e}")
            
            # Monta o log de falha
            failure_log = {
                "url": url,
                "reason": str(e),
                "scraped_by": "Playwright",
                "failed_at": datetime.now()
            }
            
            # Salva na coleção 'urls_com_falha_playwright'
            db.collection('urls_com_falha_playwright').add(failure_log)
            print(f"URL '{url}' salva em 'urls_com_falha_playwright'.")
            
            # Salva o erro detalhado na coleção de erros de execução
            log_error(
                error_message=f"Erro no scraping da URL: {url}",
                details={"error": str(e), "traceback": traceback.format_exc()}
            )

@app.post("/scrape/start-jobs", status_code=202)
async def start_scraping(background_tasks: BackgroundTasks):
    """
    Endpoint para iniciar o processo de scraping.
    Ele busca as URLs da coleção 'urls_com_falha' e inicia o trabalho em background.
    """
    print("Recebida requisição para iniciar os trabalhos de scraping.")
    db = get_firestore_client()
    
    if not db:
        # Se não há DB, não podemos buscar as URLs.
        log_error("Falha ao iniciar o processo de scraping: sem conexão com o banco de dados.", 
                  {"traceback": traceback.format_exc()})
        raise HTTPException(status_code=500, detail="Não foi possível conectar ao banco de dados.")

    try:
        urls_ref = db.collection('urls_com_falha')
        
        # Limita a 100 URLs por execução para não sobrecarregar
        docs = urls_ref.limit(100).stream()
        
        urls_to_process = [doc.to_dict().get('url') for doc in docs if doc.to_dict().get('url')]

        if not urls_to_process:
            return {"message": "Nenhuma URL encontrada em 'urls_com_falha' para processar."}

        # Inicia a tarefa em background para não bloquear a resposta da API
        background_tasks.add_task(run_scraping_jobs, urls_to_process)
        
        return {"message": f"Processo de scraping iniciado em background para {len(urls_to_process)} URLs."}

    except Exception as e:
        log_error("Falha ao iniciar o processo de scraping.", 
                  {"error": str(e), "traceback": traceback.format_exc()})
        raise HTTPException(status_code=500, detail="Erro interno ao tentar iniciar os trabalhos de scraping.")

@app.get("/", include_in_schema=False)
async def root():
    return {"message": "API Coletor Scraper está no ar. Acesse /docs para a documentação."}

# Permite a execução direta do servidor com 'python main.py'
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)