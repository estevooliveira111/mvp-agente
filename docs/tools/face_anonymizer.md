# Ferramenta: `face_anonymizer`

## Descrição
Pipeline avançado: Detecta rostos (OpenCV), aplica blur seletivo (Pillow) para anonimização e criptografa a imagem original (Fernet) como backup seguro antes da exportação.

## Parâmetros

| Nome | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `input_path` | `string` | ✅ Sim | Caminho da imagem original a ser processada. |
| `output_path` | `string` | ✅ Sim | Caminho onde a imagem com os rostos borrados (anonimizada) será salva. |
| `encryption_key` | `string` | ❌ Não | (Opcional) Chave Fernet em Base64. Se não for passada, a ferramenta gerará uma nova automaticamente. |
| `delete_original` | `boolean` | ❌ Não | (Opcional) Se verdadeiro, apaga a imagem original após gerar o backup criptografado. Padrão: false. |

## Como Funciona Internamente
```text
1. Criptografa a imagem original (salva como .enc).
    2. Lê a imagem e usa Haar Cascades do OpenCV para achar as coordenadas dos rostos.
    3. Passa para o Pillow recortar, borrar (Gaussian Blur) e colar de volta os rostos.
    4. Salva a versão segura e, opcionalmente, apaga a original.
```

---
*Arquivo fonte: `tools/face_anonymizer.py`*