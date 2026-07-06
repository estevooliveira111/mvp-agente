# Ferramenta: `audio_analyzer`

## Descrição
Analisa arquivos de áudio usando Librosa. Detecta o BPM (tempo/batidas por minuto) e a frequência dominante média (usando spectral centroid).

## Parâmetros

| Nome | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `audio_path` | `string` | ✅ Sim | Caminho do arquivo de áudio (.wav, .mp3, etc) a ser analisado. |

## Como Funciona Internamente
```text
Carrega o arquivo de áudio e extrai informações matemáticas (Tempo/BPM e Centroide Espectral).
```

---
*Arquivo fonte: `tools/audio_analyzer.py`*