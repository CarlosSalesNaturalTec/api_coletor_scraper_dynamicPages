import firebase_admin
from firebase_admin import credentials, firestore
from dotenv import load_dotenv
import os
import threading

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

# Objeto para garantir que a inicialização do Firebase seja thread-safe
app_lock = threading.Lock()

def get_firestore_client():
    """
    Inicializa o Firebase Admin SDK se ainda não foi inicializado e retorna 
    uma instância do cliente Firestore.

    A inicialização é feita de forma thread-safe para garantir que seja executada apenas uma vez.
    """
    with app_lock:
        if not firebase_admin._apps:
            try:
                # Carrega as credenciais a partir da variável de ambiente
                cred = credentials.ApplicationDefault()
                firebase_admin.initialize_app(cred)
                print("Firebase App inicializado com sucesso.")
            except Exception as e:
                print(f"Erro ao inicializar o Firebase App: {e}")
                # Se a inicialização falhar, não podemos continuar.
                # Lançar a exceção permite que o chamador saiba da falha.
                raise
    
    return firestore.client()

def log_error(error_message: str, details: dict = None):
    """
    Salva uma mensagem de erro na coleção 'erros_de_execucao' no Firestore.

    Args:
        error_message (str): A mensagem de erro principal.
        details (dict, optional): Um dicionário com detalhes adicionais sobre o erro.
    """
    try:
        db = get_firestore_client()
        error_log = {
            "message": error_message,
            "details": details or {},
            "timestamp": firestore.SERVER_TIMESTAMP
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
        print("Cliente Firestore obtido com sucesso.")
        # Teste de log de erro
        log_error("Teste de log de erro a partir do firestore_client.", {"component": "initialization"})
    except Exception as e:
        print(f"Falha ao obter o cliente Firestore ou logar erro: {e}")
