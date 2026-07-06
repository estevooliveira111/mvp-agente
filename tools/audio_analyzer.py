import json
import os
import librosa
import numpy as np

# 1. Metadados: Define como a IA enxerga esta ferramenta
tool_metadata = {
    "name": "audio_analyzer",
    "description": "Analisa arquivos de áudio usando Librosa. Detecta o BPM (tempo/batidas por minuto) e a frequência dominante média (usando spectral centroid).",
    "parameters": {
        "type": "object",
        "properties": {
            "audio_path": {
                "type": "string",
                "description": "Caminho do arquivo de áudio (.wav, .mp3, etc) a ser analisado."
            }
        },
        "required": ["audio_path"]
    }
}

# 2. Execução: O que roda quando a IA chama a ferramenta
def execute(**kwargs):
    """
    Carrega o arquivo de áudio e extrai informações matemáticas (Tempo/BPM e Centroide Espectral).
    """
    audio_path = kwargs.get("audio_path")
    
    if not audio_path:
        return json.dumps({"status": "error", "message": "O parâmetro 'audio_path' é obrigatório."})
        
    try:
        # Resolve caminhos relativos
        target_path = os.path.abspath(audio_path)
        
        if not os.path.exists(target_path):
            return json.dumps({"status": "error", "message": f"Arquivo de áudio não encontrado: {audio_path}"})
            
        # ==========================================
        # ANÁLISE DE ÁUDIO COM LIBROSA
        # ==========================================
        # sr=None carrega o áudio na taxa de amostragem (Sample Rate) original dele
        y, sr = librosa.load(target_path, sr=None)
        
        # 1. Extração do BPM (Tempo)
        # O beat_track retorna uma tupla. Queremos apenas o tempo (BPM estimado).
        tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
        
        # Garantir que bpm é um float, pois librosa pode retornar array 1D dependendo da versão
        bpm_val = float(tempo[0]) if isinstance(tempo, np.ndarray) else float(tempo)
        
        # 2. Frequência Dominante (Spectral Centroid)
        # Indica onde está localizado o "centro de massa" do espectro (o tom médio).
        # Retorna um array com o valor do centroide para cada frame do áudio.
        cent = librosa.feature.spectral_centroid(y=y, sr=sr)
        
        # Tiramos a média do array para ter uma noção geral da frequência dominante de toda a música/áudio
        mean_centroid = float(np.mean(cent))
        
        # Também pegamos a duração total para enriquecer os dados
        duration = float(librosa.get_duration(y=y, sr=sr))
        
        resultado = {
            "bpm": round(bpm_val, 2),
            "dominant_frequency_hz": round(mean_centroid, 2),
            "sample_rate_hz": sr,
            "duration_seconds": round(duration, 2)
        }
        
        return json.dumps({
            "status": "success",
            "data": resultado
        })
        
    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": f"Erro ao analisar o áudio: {str(e)}"
        })
