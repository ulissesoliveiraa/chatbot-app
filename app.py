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


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def get_user_id():
    if "user_id" not in session:
        session["user_id"] = str(uuid4())
    return session["user_id"]


def get_default_persona():
    return (
        "Você é o Chatbot Zezim, um assistente virtual amigável, educado, útil e objetivo. "
        "Responda sempre em português do Brasil de forma clara."
    )


def build_instruction_text():
    persona = session.get("persona_text", get_default_persona())
    mode = session.get("mode", "no_context")
    context_text = session.get("context_text")

    textos = []

    textos.append("INSTRUÇÕES DE PERSONALIDADE:\n" + persona)

    if mode == "context" and context_text:
        textos.append(
            "INSTRUÇÕES DE CONTEXTO:\n"
            "Você deve responder SOMENTE com base no texto abaixo. "
            "Se a resposta não estiver no texto, diga que não tem informação.\n\n"
            + context_text
        )

    return "\n\n".join(textos)


def get_history():
    user_id = get_user_id()
    history = conversations.get(user_id)

    if history is None or session.get("reset_history"):
        history = [
            {"role": "system", "content": build_instruction_text()}
        ]
        conversations[user_id] = history
        session.pop("reset_history", None)

    return history


def extract_text_from_file(file):
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
    return render_template(
        "index.html",
        logged_in=session.get("logged_in", False),
        persona_text=session.get("persona_text", get_default_persona()),
        mode=session.get("mode", "no_context"),
        has_context=bool(session.get("context_text"))
    )


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = request.form.get("username", "")
        pwd = request.form.get("password", "")

        if user == ADMIN_USER and pwd == ADMIN_PASS:
            session["logged_in"] = True
            flash("Login realizado com sucesso!", "success")
            return redirect(url_for("index"))

        flash("Credenciais inválidas", "error")

    return render_template("login.html", logged_in=session.get("logged_in", False))


@app.route("/logout")
def logout():
    session.pop("logged_in", None)
    flash("Você saiu do painel admin.", "info")
    return redirect(url_for("index"))


@app.route("/config", methods=["POST"])
def config():
    if not session.get("logged_in"):
        flash("Acesso negado: faça login.", "error")
        return redirect(url_for("login"))

    persona = request.form.get("persona_text", "").strip()
    mode = request.form.get("mode", "no_context")

    session["persona_text"] = persona or get_default_persona()
    session["mode"] = mode

    file = request.files.get("context_file")
    if file and file.filename:
        if allowed_file(file.filename):
            content = extract_text_from_file(file)
            session["context_text"] = content[:8000]
            flash("Arquivo de contexto carregado!", "success")
        else:
            flash("Formato inválido. Use .txt ou .pdf", "error")

    session["reset_history"] = True

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

        # 🔥 Remover tokens especiais (<s>, </s>, etc.)
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
