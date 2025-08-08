import os
from google.cloud import firestore
from dotenv import load_dotenv
from datetime import datetime

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

_db = None

def get_firestore_client():
    """
    Inicializa e retorna um cliente Firestore, garantindo uma instância única.
    """
    global _db
    if _db is None:
        try:
            # Verifica se a variável de ambiente essencial está configurada
            if not os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
                raise ValueError("A variável de ambiente GOOGLE_APPLICATION_CREDENTIALS não está definida.")
            
            _db = firestore.Client()
            print("Cliente Firestore inicializado com sucesso.")
        except Exception as e:
            print(f"Erro ao conectar ao Firestore: {e}")
            # Retorna None para indicar que a conexão falhou
            return None
    return _db

def log_error(error_message: str, details: dict = None):
    """
    Salva uma mensagem de erro na coleção 'erros_de_execucao' no Firestore.

    Args:
        error_message (str): A mensagem de erro principal.
        details (dict, optional): Um dicionário com detalhes adicionais sobre o erro.
    """
    db = get_firestore_client()
    if not db:
        print("Não foi possível salvar o log de erro: sem conexão com o banco de dados.")
        print(f"Erro original que não pôde ser salvo: {error_message}")
        return

    try:
        error_log = {
            "message": error_message,
            "details": details or {},
            "timestamp": datetime.now()
        }
        db.collection('erros_de_execucao').add(error_log)
        print(f"Erro '{error_message}' salvo no Firestore.")
    except Exception as e:
        # Se o logging no Firestore falhar, imprime o erro original e o erro do log
        print(f"Falha ao salvar o log de erro no Firestore: {e}")
        print(f"Erro original que não pôde ser salvo: {error_message}")

# Exemplo de uso (pode ser removido ou comentado em produção)
if __name__ == '__main__':
    try:
        db_client = get_firestore_client()
        if db_client:
            print("Cliente Firestore obtido com sucesso.")
            # Teste de log de erro
            log_error("Teste de log de erro a partir do firestore_client.", {"component": "initialization"})
        else:
            print("Falha ao obter o cliente Firestore.")
    except Exception as e:
        print(f"Falha ao obter o cliente Firestore ou logar erro: {e}")