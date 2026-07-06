# Ferramenta: `audio_sensitive_detector`

## Descrição
Analisa áudios buscando conteúdos sensíveis. Extrai features (MFCC, espectrograma) usando Librosa para classificar padrões de voz/ruído, retornando um laudo criptografado para fins de auditoria segura.

## Parâmetros

| Nome | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `audio_path` | `string` | ✅ Sim | Caminho do arquivo de áudio a ser inspecionado. |
| `encryption_key` | `string` | ❌ Não | (Opcional) Chave Fernet em Base64. Se não fornecida, uma será gerada. |

## Como Funciona Internamente
```text
1. Lê o áudio com Librosa e extrai MFCC, Spectral Bandwidth e Zero Crossing Rate.
    2. Aplica um modelo heurístico MVP para classificar entre voz, silêncio e ruído agressivo (ex: gritos, explosões).
    3. Gera um relatório em JSON contendo essas métricas e a classificação.
    4. Criptografa estritamente esse relatório usando Cryptography para auditoria protegida.
```

---
*Arquivo fonte: `tools/audio_sensitive_detector.py`*