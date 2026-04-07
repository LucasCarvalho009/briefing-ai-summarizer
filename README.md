# 📝 Resumidor de Texto com IA

Uma aplicação web completa para gerar resumos inteligentes de textos usando IA (Hugging Face) com fallback local para garantir funcionamento em qualquer situação.

## 🎯 Funcionalidades

- ✍️ **Colar Texto**: Cole qualquer texto diretamente na interface
- 📄 **Upload de Arquivos**: Suporte para PDF e TXT (até 10MB)
- 🤖 **IA Avançada**: Usa modelo BART da Hugging Face para resumos de alta qualidade
- ⚡ **Fallback Local**: Sistema de backup que sempre funciona, mesmo sem IA
- 🎯 **Pontos-Chave**: Extração automática de bullet points
- 📋 **Copiar Resultados**: Copie resumo e pontos-chave facilmente
- 🎨 **Interface Moderna**: Design responsivo e intuitivo
- 🔄 **Drag & Drop**: Arraste arquivos diretamente para a interface

## 🏗️ Estrutura do Projeto

```
text-summarizer/
├── backend/
│   ├── main.py                  # API FastAPI
│   ├── summarizer.py            # Lógica de IA com Hugging Face
│   ├── fallback_summarizer.py  # Resumidor local de backup
│   ├── pdf_extractor.py         # Extração de texto de PDF
│   └── requirements.txt         # Dependências Python
├── frontend/
│   ├── index.html              # Interface principal
│   ├── styles.css              # Estilos
│   └── script.js               # Lógica do cliente
├── .gitignore
├── .env.example
├── PLAN.md
└── README.md
```

## 🚀 Como Executar

### Pré-requisitos

- Python 3.8 ou superior
- pip (gerenciador de pacotes Python)
- Navegador web moderno

### Passo 1: Instalar Dependências

```bash
# Navegar para o diretório backend
cd backend

# Criar ambiente virtual (recomendado)
python -m venv venv

# Ativar ambiente virtual
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Instalar dependências
pip install -r requirements.txt
```

**Nota**: A primeira execução irá baixar o modelo BART (~1.6GB). Isso pode levar alguns minutos dependendo da sua conexão.

### Passo 2: Iniciar o Backend

```bash
# Ainda no diretório backend
uvicorn main:app --reload --port 8000
```

Você verá uma mensagem indicando que o servidor está rodando:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
```

### Passo 3: Abrir o Frontend

1. Abra o arquivo `frontend/index.html` no seu navegador
2. Ou use um servidor local:

```bash
# Opção 1: Python
cd frontend
python -m http.server 3000

# Opção 2: Node.js (se tiver instalado)
npx serve frontend
```

3. Acesse `http://localhost:3000` no navegador

## 📖 Como Usar

### Método 1: Colar Texto

1. Clique na aba "Colar Texto"
2. Cole ou digite seu texto (mínimo 50 caracteres)
3. Clique em "Gerar Resumo"
4. Aguarde o processamento (5-30 segundos)
5. Veja o resumo e pontos-chave gerados

### Método 2: Upload de Arquivo

1. Clique na aba "Upload de Arquivo"
2. Arraste um arquivo PDF ou TXT, ou clique para selecionar
3. Clique em "Gerar Resumo"
4. Aguarde o processamento
5. Veja os resultados

### Copiar Resultados

- Clique no ícone 📋 ao lado de cada seção para copiar
- Use o botão "Copiar Tudo" para copiar resumo e pontos-chave juntos

## 🔧 Configuração Avançada

### Variáveis de Ambiente

Copie `.env.example` para `.env` e ajuste conforme necessário:

```bash
cp .env.example .env
```

Configurações disponíveis:
- `API_PORT`: Porta do servidor (padrão: 8000)
- `MODEL_NAME`: Modelo Hugging Face a usar
- `FORCE_FALLBACK`: Forçar uso do fallback local
- `MAX_FILE_SIZE_MB`: Tamanho máximo de arquivo

### Forçar Modo Fallback

Para testar sem baixar o modelo de IA:

```python
# Em backend/main.py, adicione após as importações:
from summarizer import get_summarizer
summarizer = get_summarizer()
summarizer.force_fallback(True)
```

## 🎨 Tecnologias Utilizadas

### Backend
- **FastAPI**: Framework web moderno e rápido
- **Uvicorn**: Servidor ASGI de alta performance
- **Transformers**: Biblioteca Hugging Face para IA
- **PyTorch**: Framework de deep learning
- **PyPDF2**: Extração de texto de PDF

### Frontend
- **HTML5**: Estrutura semântica
- **CSS3**: Estilos modernos com gradientes e animações
- **JavaScript Vanilla**: Sem dependências externas

### Modelo de IA
- **BART (facebook/bart-large-cnn)**: Modelo otimizado para resumos

## 📊 Endpoints da API

### GET /
Informações básicas da API

### GET /health
Verifica status da API e do modelo
```json
{
  "status": "healthy",
  "model_status": {
    "model_loaded": true,
    "using_fallback": false
  }
}
```

### POST /summarize
Gera resumo de texto ou arquivo

**Parâmetros**:
- `text` (form-data): Texto direto
- `file` (form-data): Arquivo PDF ou TXT

**Resposta**:
```json
{
  "summary": "Resumo do texto...",
  "bullet_points": [
    "Ponto 1",
    "Ponto 2",
    "Ponto 3"
  ],
  "method": "ai",
  "success": true,
  "error": null
}
```

## 🛡️ Tratamento de Erros

A aplicação trata diversos cenários de erro:

- ❌ Arquivo muito grande (>10MB)
- ❌ Formato não suportado
- ❌ PDF corrompido ou sem texto
- ❌ Texto muito curto (<50 caracteres)
- ❌ Erro no modelo de IA → **Usa fallback automaticamente**
- ❌ API offline → Indicador visual no rodapé

## 🔄 Sistema de Fallback

O sistema de fallback garante que a aplicação sempre funcione:

1. **Tentativa Principal**: Usa modelo BART da Hugging Face
2. **Fallback Automático**: Se a IA falhar, usa algoritmo local baseado em:
   - Extração de sentenças importantes
   - Pontuação por posição, comprimento e palavras-chave
   - Seleção das top 5 sentenças mais relevantes

**Vantagens do Fallback**:
- ⚡ Processamento instantâneo (<1 segundo)
- 💾 Não requer download de modelos
- 🔧 Funciona offline
- 📦 Baixo uso de memória

## 📝 Exemplos de Uso

### Exemplo 1: Texto Curto
```
Input: "A inteligência artificial está transformando o mundo..."
Output: Resumo de 2-3 sentenças + 3-5 pontos-chave
```

### Exemplo 2: Artigo Longo
```
Input: Artigo de 5000 palavras
Output: Resumo conciso + principais insights
```

### Exemplo 3: PDF Técnico
```
Input: Documento PDF de 20 páginas
Output: Resumo executivo + pontos principais
```

## 🐛 Solução de Problemas

### Erro: "Import transformers could not be resolved"
```bash
pip install transformers torch
```

### Erro: "API não responde"
- Verifique se o backend está rodando na porta 8000
- Verifique o firewall
- Tente acessar http://localhost:8000/health

### Erro: "Modelo não carrega"
- Primeira execução demora (download do modelo)
- Verifique conexão com internet
- Use modo fallback se necessário

### PDF não extrai texto
- Verifique se o PDF não é apenas imagem
- Use PDF com texto selecionável
- Tente converter para TXT primeiro

## 🚀 Melhorias Futuras

- [ ] Suporte para mais idiomas
- [ ] Histórico de resumos
- [ ] Exportar resultados em PDF
- [ ] Ajuste de comprimento do resumo
- [ ] Suporte para DOCX
- [ ] API de autenticação
- [ ] Modo escuro
- [ ] PWA (Progressive Web App)

## 📄 Licença

Este projeto é de código aberto e está disponível sob a licença MIT.

## 👨‍💻 Autor

Desenvolvido com ❤️ usando FastAPI e Hugging Face

## 🤝 Contribuindo

Contribuições são bem-vindas! Sinta-se à vontade para:

1. Fazer fork do projeto
2. Criar uma branch para sua feature
3. Commit suas mudanças
4. Push para a branch
5. Abrir um Pull Request

## 📞 Suporte

Se encontrar problemas ou tiver dúvidas:

1. Verifique a seção de Solução de Problemas
2. Consulte os logs do backend
3. Abra uma issue no repositório

---

**Nota**: Este projeto usa modelos de IA que requerem recursos computacionais. Para melhor performance, recomenda-se:
- 8GB+ de RAM
- Conexão estável com internet (primeira execução)
- Processador moderno

Para ambientes com recursos limitados, o modo fallback oferece uma alternativa eficiente e rápida.