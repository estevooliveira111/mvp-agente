import hashlib
import secrets
from cryptography.fernet import Fernet
from core.exceptions import SecurityException

class SecurityManager:
    """
    Gerenciador centralizado de rotinas de segurança do Core.
    Responsável por hashs, validações e fornecimento seguro de instâncias criptográficas.
    """
    
    @staticmethod
    def get_fernet_instance(key_base64: str) -> Fernet:
        """
        Retorna uma instância validada do Fernet para criptografia simétrica.
        Lança SecurityException clara caso a chave seja inválida.
        """
        try:
            return Fernet(key_base64.encode('utf-8'))
        except ValueError:
            raise SecurityException("Chave criptográfica inválida. O Fernet requer uma chave Base64 (url-safe) de 32 bytes.")
            
    @staticmethod
    def generate_new_symmetric_key() -> str:
        """Gera uma nova chave simétrica segura."""
        return Fernet.generate_key().decode('utf-8')

    @staticmethod
    def hash_sensitive_data(text: str, salt: str = None) -> dict:
        """
        Gera um hash SHA-256 unidirecional usando um salt.
        Útil para mascarar dados sensíveis, PIIs, senhas ou tokens que não precisam ser decifrados.
        """
        if not salt:
            # Gera um salt criptograficamente seguro de 16 bytes
            salt = secrets.token_hex(16)
            
        hashed = hashlib.sha256((text + salt).encode('utf-8')).hexdigest()
        
        return {
            "hash": hashed,
            "salt": salt
        }
        
    @staticmethod
    def verify_hash(text: str, salt: str, expected_hash: str) -> bool:
        """Verifica se um texto em claro corresponde ao hash armazenado usando seu respectivo salt."""
        computed = hashlib.sha256((text + salt).encode('utf-8')).hexdigest()
        return secrets.compare_digest(computed, expected_hash)
