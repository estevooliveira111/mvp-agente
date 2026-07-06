import json
import os
import librosa
import numpy as np
from cryptography.fernet import Fernet

# 1. Metadados: Define como a IA enxerga esta ferramenta
tool_metadata = {
    "name": "audio_sensitive_detector",
    "description": "Analisa áudios buscando conteúdos sensíveis. Extrai features (MFCC, espectrograma) usando Librosa para classificar padrões de voz/ruído, retornando um laudo criptografado para fins de auditoria segura.",
    "parameters": {
        "type": "object",
        "properties": {
            "audio_path": {
                "type": "string",
                "description": "Caminho do arquivo de áudio a ser inspecionado."
            },
            "encryption_key": {
                "type": "string",
                "description": "(Opcional) Chave Fernet em Base64. Se não fornecida, uma será gerada."
            }
        },
        "required": ["audio_path"]
    }
}

# 2. Execução: O que roda quando a IA chama a ferramenta
def execute(**kwargs):
    """
    1. Lê o áudio com Librosa e extrai MFCC, Spectral Bandwidth e Zero Crossing Rate.
    2. Aplica um modelo heurístico MVP para classificar entre voz, silêncio e ruído agressivo (ex: gritos, explosões).
    3. Gera um relatório em JSON contendo essas métricas e a classificação.
    4. Criptografa estritamente esse relatório usando Cryptography para auditoria protegida.
    """
    audio_path = kwargs.get("audio_path")
    encryption_key = kwargs.get("encryption_key")
    
    if not audio_path:
        return json.dumps({"status": "error", "message": "O parâmetro 'audio_path' é obrigatório."})
        
    try:
        target_path = os.path.abspath(audio_path)
        
        if not os.path.exists(target_path):
            return json.dumps({"status": "error", "message": f"Arquivo de áudio não encontrado: {audio_path}"})
            
        # ==========================================
        # 1. EXTRAÇÃO DE FEATURES (LIBROSA)
        # ==========================================
        y, sr = librosa.load(target_path, sr=None)
        
        # MFCC (Mel-frequency cepstral coefficients)
        # Captura muito bem as propriedades do trato vocal, excelente para detectar fala.
        mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
        mfcc_var = np.var(mfccs, axis=1) # Variância do MFCC (Sons caóticos têm alta variância)
        
        # Spectral Bandwidth (Largura de banda do espectro)
        # Ajuda a diferenciar tons puros e vozes de ruídos brancos ou estática aguda.
        bandwidth = librosa.feature.spectral_bandwidth(y=y, sr=sr)
        mean_bandwidth = float(np.mean(bandwidth))
        
        # Zero Crossing Rate (Taxa de cruzamento por zero)
        # Ruídos agressivos (gritos agudos, sons percussivos estourados) cruzam o zero constantemente.
        zcr = librosa.feature.zero_crossing_rate(y)
        mean_zcr = float(np.mean(zcr))
        
        # Root Mean Square Energy (Energia)
        # Mede o quão "alto" ou enérgico o áudio é.
        energy = float(np.mean(librosa.feature.rms(y=y)))
        
        # ==========================================
        # 2. MODELO DE CLASSIFICAÇÃO MVP
        # ==========================================
        classification = "Padrão Indefinido"
        risk_level = "Baixo"
        
        # Regras Heurísticas baseadas em processamento de sinais analógicos
        if energy < 0.005:
            classification = "Silêncio / Fundo Estático"
            risk_level = "Baixo"
        elif mean_zcr > 0.12 and mean_bandwidth > 2400:
            classification = "Ruído Agressivo (Possível Grito / Alarme / Som Sensível)"
            risk_level = "Alto"
        elif 0.02 < mean_zcr < 0.09 and 1200 < mean_bandwidth < 2500:
            classification = "Voz Humana Padrão / Diálogo"
            risk_level = "Baixo"
        else:
            classification = "Música ou Ruído Ambiente Complexo"
            risk_level = "Médio"
            
        # ==========================================
        # 3. RELATÓRIO E CRIPTOGRAFIA DE AUDITORIA
        # ==========================================
        audit_report = {
            "file_analyzed": audio_path,
            "classification_result": classification,
            "sensitive_risk_level": risk_level,
            "signal_metrics": {
                "energy_rms": round(energy, 4),
                "mean_zero_crossing_rate": round(mean_zcr, 4),
                "mean_spectral_bandwidth": round(mean_bandwidth, 2),
                "avg_mfcc_variance": round(float(np.mean(mfcc_var)), 2)
            }
        }
        
        # Converte para string
        report_json_str = json.dumps(audit_report, ensure_ascii=False)
        
        # Criptografa
        if not encryption_key:
            encryption_key = Fernet.generate_key().decode('utf-8')
            
        fernet = Fernet(encryption_key.encode('utf-8'))
        encrypted_audit = fernet.encrypt(report_json_str.encode('utf-8'))
        
        return json.dumps({
            "status": "success",
            "data": {
                "message": "Análise sensível concluída. O laudo de auditoria foi gerado e criptografado com sucesso.",
                "encrypted_audit_report": encrypted_audit.decode('utf-8'),
                "encryption_key": encryption_key,
                "instructions": "O conteúdo analítico está criptografado acima. Utilize a ferramenta 'crypto_manager' com esta chave caso precise decriptar o laudo."
            }
        })
        
    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": f"Falha na detecção sensível de áudio: {str(e)}"
        })
