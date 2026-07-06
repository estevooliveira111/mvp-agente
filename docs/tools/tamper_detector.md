# Ferramenta: `tamper_detector`

## Descrição
Verifica se uma imagem foi adulterada usando Error Level Analysis (ELA) com OpenCV para buscar inconsistências de pixels e texturas. Também gera um Hash criptográfico seguro (SHA-256) da imagem para garantir sua integridade.

## Parâmetros

| Nome | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `image_path` | `string` | ✅ Sim | O caminho (absoluto ou relativo) da imagem a ser analisada contra adulterações. |

## Como Funciona Internamente
```text
1. Lê a imagem crua e usa Cryptography (SHA-256) para criar um registro de integridade.
    2. Utiliza ELA (Error Level Analysis) via OpenCV para comparar artefatos de compressão.
    3. Analisa as texturas e inconsistências nas bordas (Laplacian variance) para detectar adulterações.
```

---
*Arquivo fonte: `tools/tamper_detector.py`*