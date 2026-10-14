from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from pathlib import Path
import sqlite3
from datetime import date

app = Flask(__name__)
app.secret_key = "troque-esta-chave-por-uma-chave-secreta"

DATABASE = Path(__file__).resolve().parent / "database.db"


def conectar_banco():
    conexao = sqlite3.connect(DATABASE)
    conexao.row_factory = sqlite3.Row
    conexao.execute("PRAGMA foreign_keys = ON")
    return conexao


def inicializar_banco():
    with conectar_banco() as conexao:
        conexao.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario TEXT NOT NULL UNIQUE,
                email TEXT NOT NULL UNIQUE,
                senha TEXT NOT NULL
            )
        """)

        conexao.execute("""
            CREATE TABLE IF NOT EXISTS gastos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario_id INTEGER NOT NULL,
                descricao TEXT NOT NULL,
                categoria TEXT NOT NULL,
                valor REAL NOT NULL CHECK (valor > 0),
                mes INTEGER NOT NULL,
                ano INTEGER NOT NULL,
                FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
                    ON DELETE CASCADE
            )
        """)

        conexao.execute("""
            CREATE TABLE IF NOT EXISTS orcamentos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario_id INTEGER NOT NULL,
                mes INTEGER NOT NULL,
                ano INTEGER NOT NULL,
                valor REAL NOT NULL CHECK (valor >= 0),
                UNIQUE (usuario_id, mes, ano),
                FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
                    ON DELETE CASCADE
            )
        """)


def usuario_logado(funcao):
    @wraps(funcao)
    def decorada(*args, **kwargs):
        if "usuario_id" not in session:
            flash("Faça login para acessar essa página.", "error")
            return redirect(url_for("login"))
        return funcao(*args, **kwargs)
    return decorada


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/cadastro", methods=["GET", "POST"])
def cadastro():
    if request.method == "POST":
        usuario = request.form.get("usuario", "").strip()
        email = request.form.get("email", "").strip().lower()
        senha = request.form.get("senha", "")
        confirmar_senha = request.form.get("confirmar_senha", "")

        if not usuario or not email or not senha:
            flash("Preencha todos os campos.", "error")
            return redirect(url_for("cadastro"))

        if senha != confirmar_senha:
            flash("As senhas não coincidem.", "error")
            return redirect(url_for("cadastro"))

        if len(senha) < 8:
            flash("A senha deve ter pelo menos 8 caracteres.", "error")
            return redirect(url_for("cadastro"))

        senha_hash = generate_password_hash(senha)

        try:
            with conectar_banco() as conexao:
                conexao.execute("""
                    INSERT INTO usuarios (usuario, email, senha)
                    VALUES (?, ?, ?)
                """, (usuario, email, senha_hash))

            flash("Conta criada com sucesso! Faça login.", "success")
            return redirect(url_for("login"))

        except sqlite3.IntegrityError:
            flash("Esse nome de usuário ou e-mail já está cadastrado.", "error")
            return redirect(url_for("cadastro"))

    return render_template("cadastro.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        usuario = request.form.get("usuario", "").strip()
        senha = request.form.get("senha", "")

        with conectar_banco() as conexao:
            resultado = conexao.execute("""
                SELECT id, usuario, senha
                FROM usuarios
                WHERE usuario = ?
            """, (usuario,)).fetchone()

        if resultado and check_password_hash(resultado["senha"], senha):
            session.clear()
            session["usuario_id"] = resultado["id"]
            session["usuario"] = resultado["usuario"]
            flash("Login realizado com sucesso!", "success")
            return redirect(url_for("gastos"))

        flash("Usuário ou senha incorretos.", "error")
        return redirect(url_for("login"))

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("Você saiu da sua conta.", "info")
    return redirect(url_for("index"))


@app.route("/gastos")
@usuario_logado
def gastos():
    hoje = date.today()

    try:
        mes = int(request.args.get("mes", hoje.month))
        ano = int(request.args.get("ano", hoje.year))
        date(ano, mes, 1)
    except (ValueError, TypeError):
        mes, ano = hoje.month, hoje.year
        flash("Mês ou ano inválido.", "error")

    usuario_id = session["usuario_id"]

    with conectar_banco() as conexao:
        lista_gastos = conexao.execute("""
            SELECT id, descricao, categoria, valor
            FROM gastos
            WHERE usuario_id = ? AND mes = ? AND ano = ?
            ORDER BY id DESC
        """, (usuario_id, mes, ano)).fetchall()

        resultado_orcamento = conexao.execute("""
            SELECT valor
            FROM orcamentos
            WHERE usuario_id = ? AND mes = ? AND ano = ?
        """, (usuario_id, mes, ano)).fetchone()

        resumo = conexao.execute("""
            SELECT categoria, SUM(valor) AS total
            FROM gastos
            WHERE usuario_id = ? AND mes = ? AND ano = ?
            GROUP BY categoria
            ORDER BY total DESC
        """, (usuario_id, mes, ano)).fetchall()

    orcamento = resultado_orcamento["valor"] if resultado_orcamento else 0
    total_gastos = sum(gasto["valor"] for gasto in lista_gastos)
    saldo = orcamento - total_gastos
    categorias = {
        linha["categoria"]: linha["total"]
        for linha in resumo
    }

    meses = [
        (1, "Janeiro"),
        (2, "Fevereiro"),
        (3, "Março"),
        (4, "Abril"),
        (5, "Maio"),
        (6, "Junho"),
        (7, "Julho"),
        (8, "Agosto"),
        (9, "Setembro"),
        (10, "Outubro"),
        (11, "Novembro"),
        (12, "Dezembro")
    ]

    anos = list(range(hoje.year - 5, hoje.year + 6))

    return render_template(
        "gastos.html",
        meses=meses,
        anos=anos,
        mes_atual=mes,
        ano_atual=ano,
        orcamento=orcamento,
        total_gastos=total_gastos,
        saldo=saldo,
        categorias=categorias,
        gastos=lista_gastos
    )


@app.route("/definir_orcamento", methods=["POST"])
@usuario_logado
def definir_orcamento():
    try:
        valor = float(request.form.get("orcamento", "").replace(",", "."))
        mes = int(request.form.get("mes", date.today().month))
        ano = int(request.form.get("ano", date.today().year))

        if valor < 0 or not date(ano, mes, 1):
            raise ValueError

    except (ValueError, TypeError):
        flash("Informe um orçamento válido.", "error")
        return redirect(url_for("gastos"))

    with conectar_banco() as conexao:
        conexao.execute("""
            INSERT INTO orcamentos (usuario_id, mes, ano, valor)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(usuario_id, mes, ano)
            DO UPDATE SET valor = excluded.valor
        """, (session["usuario_id"], mes, ano, valor))

    flash("Orçamento atualizado!", "success")
    return redirect(url_for("gastos", mes=mes, ano=ano))


@app.route("/adicionar_gasto", methods=["POST"])
@usuario_logado
def adicionar_gasto():
    descricao = request.form.get("descricao", "").strip()
    categoria = request.form.get("categoria", "").strip()

    try:
        valor = float(request.form.get("valor", "").replace(",", "."))
        mes = int(request.form.get("mes", date.today().month))
        ano = int(request.form.get("ano", date.today().year))

        date(ano, mes, 1)

        if valor <= 0:
            raise ValueError

    except (ValueError, TypeError):
        flash("Informe um valor, mês e ano válidos.", "error")
        return redirect(url_for("gastos"))

    if not descricao or not categoria:
        flash("Preencha a descrição e a categoria.", "error")
        return redirect(url_for("gastos", mes=mes, ano=ano))

    with conectar_banco() as conexao:
        conexao.execute("""
            INSERT INTO gastos (
                usuario_id, descricao, categoria, valor, mes, ano
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            session["usuario_id"],
            descricao,
            categoria,
            valor,
            mes,
            ano
        ))

    flash("Gasto adicionado com sucesso!", "success")
    return redirect(url_for("gastos", mes=mes, ano=ano))


@app.route("/remover_gasto/<int:gasto_id>", methods=["POST"])
@usuario_logado
def remover_gasto(gasto_id):
    mes = request.form.get("mes", date.today().month)
    ano = request.form.get("ano", date.today().year)

    try:
        mes = int(mes)
        ano = int(ano)
        date(ano, mes, 1)
    except (ValueError, TypeError):
        mes, ano = date.today().month, date.today().year

    with conectar_banco() as conexao:
        resultado = conexao.execute("""
            DELETE FROM gastos
            WHERE id = ? AND usuario_id = ?
        """, (gasto_id, session["usuario_id"]))

    if resultado.rowcount:
        flash("Gasto removido.", "success")
    else:
        flash("Gasto não encontrado.", "error")

    return redirect(url_for("gastos", mes=mes, ano=ano))


inicializar_banco()


if __name__ == "__main__":
    app.run(debug=True)