# Ferramenta: `crypto_manager`

## Descrição
Ferramenta de segurança para gerenciar criptografia simétrica. Pode gerar chaves, criptografar e descriptografar metadados de processamento de forma segura.

## Parâmetros

| Nome | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `operation` | `string` | ✅ Sim | A operação que deseja realizar. Valores permitidos: 'generate_key', 'encrypt' ou 'decrypt'. |
| `data` | `string` | ❌ Não | Os metadados, string ou JSON que devem ser criptografados/descriptografados. (Opcional se operation = 'generate_key'). |
| `key` | `string` | ❌ Não | A chave simétrica (gerada pelo Fernet) em Base64. Obrigatório para 'encrypt' e 'decrypt'. |

## Como Funciona Internamente
```text
Controla o ciclo de criptografia.
    - generate_key: Cria uma chave simétrica de 32 bytes.
    - encrypt: Transforma texto puro em token cifrado ilegível (url-safe).
    - decrypt: Reverte o token cifrado para o texto puro (usando a mesma chave).
```

---
*Arquivo fonte: `tools/crypto_manager.py`*