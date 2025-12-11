import os
from uuid import uuid4

from flask import (
    Flask, render_template, request, redirect,
    url_for, session, jsonify, flash
)
from werkzeug.utils import secure_filename
from PyPDF2 import PdfReader
from dotenv import load_dotenv

from openai import OpenAI

# Carregar .env
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "change-this-secret-key")

# Chave do OpenRouter
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
if not OPENROUTER_API_KEY:
    raise RuntimeError("Defina OPENROUTER_API_KEY no arquivo .env")

# Cliente OpenRouter (OpenAI-compatible)
client = OpenAI(
    api_key=OPENROUTER_API_KEY,
    base_url="https://openrouter.ai/api/v1"
)

# Modelo (pode trocar se quiser)
MODEL = "mistralai/mistral-7b-instruct"

# Credenciais padrão da área admin
ADMIN_USER = "chatbot"
ADMIN_PASS = "@chatbot0123"

# Upload
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
ALLOWED_EXTENSIONS = {"txt", "pdf"}
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Histórico dos usuários em memória
conversations = {}

# 🔐 Configuração específica do ADMIN (persistente enquanto o app estiver rodando)
# Agora com suporte a vários arquivos de contexto
admin_config = {
    "persona_text": None,
    "mode": "no_context",       # "no_context", "context" ou "both"
    "contexts": [],             # lista de dicts: [{"id", "name", "text"}, ...]
}


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def get_user_id() -> str:
    if "user_id" not in session:
        session["user_id"] = str(uuid4())
    return session["user_id"]


def get_default_persona() -> str:
    return (
        "Você é o Chatbot Zezim, um assistente virtual amigável, educado, útil e objetivo. "
        "Responda sempre em português do Brasil de forma clara."
    )


def build_instruction_text() -> str:
    """
    Monta a mensagem de sistema com base em:
      - personalidade
      - modo escolhido
      - contexto(s) da empresa/documento (um ou mais arquivos)

    Regras:
      - Se NÃO estiver logado, sempre usa personalidade padrão, SEM contexto.
      - Se estiver logado como admin, usa admin_config (persona/mode/contexts).
    """
    if session.get("logged_in"):
        # 🔐 Admin logado: usa config personalizada
        persona = admin_config.get("persona_text") or get_default_persona()
        mode = admin_config.get("mode", "no_context")
        contexts = admin_config.get("contexts") or []
    else:
        # 🔓 Público: sempre padrão, sem arquivo
        persona = get_default_persona()
        mode = "no_context"
        contexts = []

    # Junta todos os textos de contexto em um bloco só
    combined_context = None
    if contexts:
        partes = []
        for ctx in contexts:
            name = ctx.get("name", "arquivo sem nome")
            text = ctx.get("text", "")
            partes.append(f"ARQUIVO: {name}\n\n{text}")
        combined_context = "\n\n-----\n\n".join(partes)

    textos = []

    # Sempre começa pela personalidade
    textos.append("INSTRUÇÕES DE PERSONALIDADE:\n" + persona)

    # Adiciona contexto dependendo do modo (apenas quando há contexto e modo permite)
    if combined_context and mode in ("context", "both"):
        if mode == "context":
            # Modo restrito: só responde com base nos arquivos
            textos.append(
                "INSTRUÇÕES DE CONTEXTO (MODO RESTRITO):\n"
                "Você deve responder SOMENTE com base nas informações dos textos abaixo. "
                "Se a pergunta não puder ser respondida com essas informações, diga "
                "claramente que o conteúdo não está disponível ou que não sabe.\n\n"
                + combined_context
            )
        elif mode == "both":
            # Modo complementar: usa os arquivos como base, mas pode complementar
            textos.append(
                "INSTRUÇÕES DE CONTEXTO (PERSONALIDADE + EMPRESA/ARQUIVOS):\n"
                "Use as informações dos textos abaixo como referência principal para "
                "responder perguntas relacionadas à empresa/arquivos. "
                "Você PODE usar conhecimento geral para complementar, desde que "
                "não entre em contradição com o conteúdo abaixo. "
                "Se precisar extrapolar, deixe claro que está completando com "
                "conhecimento geral.\n\n"
                + combined_context
            )

    return "\n\n".join(textos)


def get_history():
    """
    Retorna o histórico de conversa do usuário atual.
    Sempre que marcamos session["reset_history"] = True
    ou ainda não existir histórico, reconstruímos a mensagem de sistema
    com build_instruction_text().
    """
    user_id = get_user_id()
    history = conversations.get(user_id)

    if history is None or session.get("reset_history"):
        history = [
            {"role": "system", "content": build_instruction_text()}
        ]
        conversations[user_id] = history
        session.pop("reset_history", None)

    return history


def extract_text_from_file(file) -> str:
    filename = secure_filename(file.filename)
    ext = filename.rsplit(".", 1)[1].lower()

    if ext == "txt":
        return file.read().decode("utf-8", errors="ignore")

    if ext == "pdf":
        reader = PdfReader(file)
        return "\n".join(page.extract_text() or "" for page in reader.pages)

    return ""


@app.route("/")
def index():
    """
    Renderiza a página principal.
    Para o admin logado, mostramos a config real (admin_config).
    Para o público, mostramos apenas os valores padrão.
    """
    if session.get("logged_in"):
        persona_text = admin_config.get("persona_text") or get_default_persona()
        mode = admin_config.get("mode", "no_context")
        context_files = admin_config.get("contexts", [])
        has_context = bool(context_files)
    else:
        persona_text = get_default_persona()
        mode = "no_context"
        context_files = []
        has_context = False

    return render_template(
        "index.html",
        logged_in=session.get("logged_in", False),
        persona_text=persona_text,
        mode=mode,
        has_context=has_context,
        context_files=context_files,
    )


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = request.form.get("username", "")
        pwd = request.form.get("password", "")

        if user == ADMIN_USER and pwd == ADMIN_PASS:
            session["logged_in"] = True
            session["reset_history"] = True  # reseta histórico ao entrar no admin
            flash("Login realizado com sucesso!", "success")
            return redirect(url_for("index"))

        flash("Credenciais inválidas", "error")

    return render_template("login.html", logged_in=session.get("logged_in", False))


@app.route("/logout")
def logout():
    """
    Ao sair do admin:
      - saímos do modo logged_in
      - limpamos o histórico da sessão atual
      - marcamos reset_history para criar um novo sistema padrão (público)
      - MAS mantemos admin_config intacto (para usar num próximo login)
    """
    session.pop("logged_in", None)
    conversations.pop(get_user_id(), None)
    session["reset_history"] = True
    flash("Você saiu do painel admin.", "info")
    return redirect(url_for("index"))


@app.route("/config", methods=["POST"])
def config():
    """
    Rota de configuração do painel admin.
    Agora:
      - Atualiza personalidade
      - Atualiza modo
      - Permite subir UM ou VÁRIOS arquivos de contexto
        (sem apagar os anteriores automaticamente)
    """
    if not session.get("logged_in"):
        flash("Acesso negado: faça login.", "error")
        return redirect(url_for("login"))

    persona = request.form.get("persona_text", "").strip()
    mode = request.form.get("mode", "no_context")

    if mode not in ("no_context", "context", "both"):
        mode = "no_context"

    # Atualiza config do admin (global)
    admin_config["persona_text"] = persona or get_default_persona()
    admin_config["mode"] = mode

    # Garante a lista de contextos
    if "contexts" not in admin_config or admin_config["contexts"] is None:
        admin_config["contexts"] = []

    # Recebe UM ou VÁRIOS arquivos de contexto
    files = request.files.getlist("context_files")
    added_any = False

    for file in files:
        if file and file.filename:
            if allowed_file(file.filename):
                content = extract_text_from_file(file)
                context_entry = {
                    "id": str(uuid4()),
                    "name": secure_filename(file.filename),
                    "text": content[:8000],  # limite simples por arquivo
                }
                admin_config["contexts"].append(context_entry)
                added_any = True
            else:
                flash(
                    f"Formato inválido para o arquivo: {file.filename}. Use .txt ou .pdf.",
                    "error",
                )

    if added_any:
        flash("Arquivo(s) de contexto carregado(s) com sucesso!", "success")

    # Ao alterar config, reseta histórico da sessão atual (admin)
    session["reset_history"] = True

    return redirect(url_for("index"))


@app.route("/remove_context", methods=["POST"])
def remove_context():
    """
    Remove UM arquivo de contexto selecionado pelo admin.
    A lista continua com os outros arquivos.
    """
    if not session.get("logged_in"):
        flash("Acesso negado: faça login.", "error")
        return redirect(url_for("login"))

    file_id = request.form.get("file_id")
    contexts = admin_config.get("contexts", [])

    if not file_id:
        flash("Nenhum arquivo selecionado para remover.", "error")
        return redirect(url_for("index"))

    before = len(contexts)
    contexts = [c for c in contexts if c.get("id") != file_id]

    if len(contexts) < before:
        admin_config["contexts"] = contexts
        flash("Arquivo de contexto removido com sucesso!", "success")
        session["reset_history"] = True
    else:
        flash("Arquivo de contexto não encontrado.", "error")

    return redirect(url_for("index"))


@app.route("/reset_chat", methods=["POST"])
def reset_chat():
    conversations.pop(get_user_id(), None)
    session["reset_history"] = True
    return jsonify({"status": "ok"})


@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json() or {}
    msg = data.get("message", "").strip()

    if not msg:
        return jsonify({"error": "Mensagem vazia"}), 400

    history = get_history()
    history.append({"role": "user", "content": msg})

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=history,
        )

        reply = response.choices[0].message.content

        # Remover tokens especiais (<s>, </s>, etc.)
        tokens_remover = ["<s>", "</s>", "<pad>", "<unk>"]
        for t in tokens_remover:
            reply = reply.replace(t, "")
        reply = reply.strip()

        history.append({"role": "assistant", "content": reply})
        conversations[get_user_id()] = history

        return jsonify({"reply": reply})

    except Exception as e:
        erro_str = repr(e)
        print("ERRO AO CHAMAR OPENROUTER:", erro_str)
        return jsonify({"error": f"Erro ao chamar o modelo: {e}"}), 500


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
