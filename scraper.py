from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from newspaper import Article, ArticleException
from urllib.parse import urlparse
import json

def extract_article_data_with_newspaper(url: str, html_content: str) -> dict:
    """
    Usa o newspaper3k para extrair dados estruturados do HTML de um artigo.
    """
    try:
        article = Article(url)
        article.download(input_html=html_content)
        article.parse()

        # Tenta extrair a data de publicação
        publish_date = article.publish_date if article.publish_date else None

        # Monta o dicionário com os dados extraídos
        data = {
            "title": article.title,
            "text": article.text,
            "authors": article.authors,
            "publish_date": publish_date.isoformat() if publish_date else None,
            "top_image": article.top_image,
            "movies": article.movies,
            "url": url,
            "domain": urlparse(url).netloc,
        }
        return data
    except ArticleException as e:
        print(f"Newspaper3k não conseguiu processar o artigo da URL {url}: {e}")
        # Retorna um dicionário de falha para ser tratado pelo chamador
        raise ValueError(f"Falha na extração com Newspaper3k: {e}")


def scrape_url(url: str) -> dict:
    """
    Realiza o scraping de uma URL usando Playwright para obter o HTML
    e o newspaper3k para extrair o conteúdo do artigo.

    Args:
        url (str): A URL a ser processada.

    Returns:
        dict: Um dicionário contendo os dados extraídos do artigo.

    Raises:
        PlaywrightTimeoutError: Se o Playwright exceder o tempo limite para carregar a página.
        ValueError: Se a extração do artigo falhar por outros motivos.
    """
    print(f"Iniciando scraping para a URL: {url}")
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            
            # Aumenta o timeout padrão para 60 segundos
            page.goto(url, timeout=60000, wait_until='domcontentloaded')
            
            # Aguarda um seletor comum para garantir que o corpo da página carregou
            page.wait_for_selector('body', timeout=30000)

            html_content = page.content()
            browser.close()

            if not html_content:
                raise ValueError("O conteúdo da página está vazio.")

            # Extrai os dados usando o newspaper3k
            article_data = extract_article_data_with_newspaper(url, html_content)
            
            # Validação simples: verifica se o título e o texto foram extraídos
            if not article_data.get("title") or not article_data.get("text"):
                raise ValueError("Scraping resultou em título ou texto vazio.")

            print(f"Scraping bem-sucedido para: {url}")
            return article_data

    except PlaywrightTimeoutError as e:
        print(f"Timeout ao tentar carregar a página {url}: {e}")
        raise PlaywrightTimeoutError(f"Timeout ao carregar a URL: {url}") from e
    
    except Exception as e:
        print(f"Ocorreu um erro inesperado durante o scraping da URL {url}: {e}")
        # Re-lança a exceção para ser tratada no main.py
        raise

# Exemplo de uso (pode ser removido ou comentado em produção)
if __name__ == '__main__':
    # Teste com uma URL de exemplo
    test_url = "https://www.wired.com/story/what-is-generative-ai/"
    
    try:
        data = scrape_url(test_url)
        print("\n--- DADOS EXTRAÍDOS ---")
        print(json.dumps(data, indent=2))
        print("-----------------------\n")

    except (PlaywrightTimeoutError, ValueError, Exception) as e:
        print("\n--- FALHA NO SCRAPING ---")
        print(f"Motivo: {e}")
        print("-------------------------")
