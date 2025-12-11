Chatbot Zezim – Assistente Virtual com Contexto Inteligente 🤖📄
Projeto autoral desenvolvido para demonstrar a aplicação de IA generativa integrada a sistemas web, permitindo interação com usuários, leitura de documentos e personalização de comportamento.

Descrição do Projeto 🧠
O Chatbot Zezim é uma aplicação web criada em Python (Flask) que utiliza modelos de linguagem através da API OpenRouter.
Ele foi desenvolvido para ser altamente flexível, simples de operar e adaptável a diferentes cenários.

Entre suas funcionalidades:
• Conversação livre com personalidade configurável
• Upload de um ou vários arquivos de contexto (TXT e PDF)
• Modo restrito baseado unicamente nos arquivos enviados
• Modo híbrido: personalidade + contexto
• Painel administrativo com login
• Tema claro e escuro
• Entrada por voz (speech to text)
• Remoção individual de arquivos de contexto
• Deploy completo na nuvem via Render

Aplicação em Empresas e Organizações 🏢🤝
O Chatbot Zezim foi projetado para ser facilmente implementado em empresas, instituições e organizações que desejam:

• Atender clientes de forma mais rápida
• Responder dúvidas frequentes automaticamente
• Centralizar informações internas em um assistente virtual
• Reduzir carga do atendimento humano
• Disponibilizar respostas 24 horas por dia

Ao adicionar documentos com informações internas (como tabelas, serviços, políticas, preços, procedimentos ou orientações), o chatbot passa a responder qualquer dúvida relacionada à empresa de maneira precisa e instantânea.

É como ter um funcionário disponível 24 horas por dia, sem intervalo, sem folgas e sempre preparado para atender o cliente com agilidade.

Demonstração Online 🌐
Você pode acessar a versão hospedada no Render:
[https://chatbot-zezim.onrender.com/](https://chatbot-zezim.onrender.com/)

Acesso ao Painel Administrativo 🔐
Usuário: chatbot
Senha: @chatbot0123

Instalação e Execução Local (VS Code + venv) 💻🛠️

1. Clonar o repositório
   git clone [https://github.com/ulissesoliveiraa/chatbot-app.git](https://github.com/ulissesoliveiraa/chatbot-app.git)

2. Acessar a pasta do projeto
   cd chatbot-app

3. Criar o ambiente virtual
   python -m venv venv

4. Ativar o ambiente virtual (PowerShell)
   venv\Scripts\activate

   No CMD:
   venv\Scripts\activate.bat

5. Instalar dependências
   pip install -r requirements.txt

6. Criar um arquivo .env na raiz contendo:
   OPENROUTER_API_KEY=sua_chave_aqui
   FLASK_SECRET_KEY=chave_segura_de_sessao

7. Iniciar o servidor Flask
   python app.py

8. Acessar no navegador
   [http://127.0.0.1:5000/](http://127.0.0.1:5000/)

Estrutura do Projeto 📂
static/
style.css

templates/
base.html
index.html
login.html

uploads/
arquivos enviados para contexto

app.py
Código principal da aplicação

requirements.txt
Bibliotecas necessárias

Procfile
Arquivo de inicialização usado pelo Render

Tecnologias Utilizadas 🧩
• Python 3
• Flask
• HTML/CSS
• JavaScript
• OpenRouter API
• Render (deploy)

Aviso Legal ⚠️
Este é um projeto autoral criado por Ulisses Oliveira.
Não é permitido copiar, publicar, redistribuir, utilizar ou adaptar este código, total ou parcialmente, sem autorização expressa do autor.

Contato 📬
Para dúvidas, parcerias, implementação empresarial ou solicitação de autorização, entre em contato diretamente com o autor.
- email: j.ulisses1312@gmail.com
- email: ulisses9@hotmail.com.br

