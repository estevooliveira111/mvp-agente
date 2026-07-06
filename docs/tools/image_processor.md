# Ferramenta: `image_processor`

## Descrição
Processa imagens de forma híbrida usando as bibliotecas Pillow e OpenCV. Converte formatos e aplica filtros (ex: grayscale, blur, edge_detect, resize).

## Parâmetros

| Nome | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `input_path` | `string` | ✅ Sim | Caminho da imagem de entrada (ex: 'imagem.jpg'). |
| `output_path` | `string` | ✅ Sim | Caminho onde a imagem processada será salva. A extensão (.png, .jpg) define o formato de conversão. |
| `operation` | `string` | ✅ Sim | Operação a ser realizada: 'grayscale', 'blur', 'edge_detect' ou 'resize'. |
| `width` | `integer` | ❌ Não | Largura em pixels (obrigatório somente se operation for 'resize'). |
| `height` | `integer` | ❌ Não | Altura em pixels (obrigatório somente se operation for 'resize'). |

## Como Funciona Internamente
```text
Recebe instruções para processar uma imagem. Utiliza OpenCV para operações 
    como detecção de bordas ou cores, e Pillow para manipulações mais fáceis de formatos e filtros.
```

---
*Arquivo fonte: `tools/image_processor.py`*