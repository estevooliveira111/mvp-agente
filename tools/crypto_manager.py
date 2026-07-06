import json
from cryptography.fernet import Fernet

# 1. Metadados: Define como a IA enxerga esta ferramenta
tool_metadata = {
    "name": "crypto_manager",
    "description": "Ferramenta de segurança para gerenciar criptografia simétrica. Pode gerar chaves, criptografar e descriptografar metadados de processamento de forma segura.",
    "parameters": {
        "type": "object",
        "properties": {
            "operation": {
                "type": "string",
                "description": "A operação que deseja realizar. Valores permitidos: 'generate_key', 'encrypt' ou 'decrypt'."
            },
            "data": {
                "type": "string",
                "description": "Os metadados, string ou JSON que devem ser criptografados/descriptografados. (Opcional se operation = 'generate_key')."
            },
            "key": {
                "type": "string",
                "description": "A chave simétrica (gerada pelo Fernet) em Base64. Obrigatório para 'encrypt' e 'decrypt'."
            }
        },
        "required": ["operation"]
    }
}

# 2. Execução: O que roda quando a IA chama a ferramenta
def execute(**kwargs):
    """
    Controla o ciclo de criptografia.
    - generate_key: Cria uma chave simétrica de 32 bytes.
    - encrypt: Transforma texto puro em token cifrado ilegível (url-safe).
    - decrypt: Reverte o token cifrado para o texto puro (usando a mesma chave).
    """
    operation = kwargs.get("operation")
    data = kwargs.get("data")
    key_str = kwargs.get("key")
    
    if not operation:
        return json.dumps({"status": "error", "message": "O parâmetro 'operation' é obrigatório."})
        
    try:
        # GERAR CHAVE =======================================
        if operation == "generate_key":
            new_key = Fernet.generate_key()
            return json.dumps({
                "status": "success",
                "data": {
                    "action": "Key generated",
                    "key": new_key.decode('utf-8'),
                    "instructions": "Guarde esta chave. Sem ela, não será possível descriptografar os dados cifrados com a mesma."
                }
            })
            
        # CRIPTOGRAFAR =======================================
        elif operation == "encrypt":
            if not data or not key_str:
                return json.dumps({"status": "error", "message": "Para a operação 'encrypt', os parâmetros 'data' e 'key' são obrigatórios."})
                
            f = Fernet(key_str.encode('utf-8'))
            # O Fernet requer bytes para encriptar
            encrypted_data = f.encrypt(data.encode('utf-8'))
            
            return json.dumps({
                "status": "success",
                "data": {
                    "action": "Data encrypted",
                    "encrypted_content": encrypted_data.decode('utf-8')
                }
            })
            
        # DESCRIPTOGRAFAR =======================================
        elif operation == "decrypt":
            if not data or not key_str:
                return json.dumps({"status": "error", "message": "Para a operação 'decrypt', os parâmetros 'data' (o texto cifrado) e 'key' são obrigatórios."})
                
            f = Fernet(key_str.encode('utf-8'))
            decrypted_data = f.decrypt(data.encode('utf-8'))
            
            return json.dumps({
                "status": "success",
                "data": {
                    "action": "Data decrypted",
                    "decrypted_content": decrypted_data.decode('utf-8')
                }
            })
            
        # OPERAÇÃO INVÁLIDA =======================================
        else:
            return json.dumps({"status": "error", "message": f"Operação '{operation}' desconhecida. Use 'generate_key', 'encrypt' ou 'decrypt'."})
            
    except ValueError:
        return json.dumps({
            "status": "error",
            "message": "A chave fornecida ('key') é inválida. O Fernet requer uma chave Base64 (url-safe) de 32 bytes."
        })
    except Exception as e:
        # Captura erros gerais de descriptografia (ex: Token inválido, dados corrompidos)
        return json.dumps({
            "status": "error",
            "message": f"Falha na operação criptográfica: {str(e)}. (Verifique se a chave corresponde aos dados cifrados e se os dados estão corretos)"
        })
