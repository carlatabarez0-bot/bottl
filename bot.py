import os
import logging
import sqlite3
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)

# ---------------------------------------------------------------------------
# CONFIGURACIÓN
# ---------------------------------------------------------------------------

# El token se lee de una variable de entorno (NUNCA lo escribas directo en el código)
TOKEN = os.environ.get("8637656121:AAEVZjQLTddCEUxyw91OsjGvz8vKjUS48nE")

# Si quieres que SOLO tú puedas usar el bot, pon aquí tu ID numérico de Telegram.
# Déjalo como None si no quieres restringir el acceso.
# (Puedes obtener tu ID hablando con @userinfobot en Telegram)
ALLOWED_USER_ID = os.environ.get("ALLOWED_USER_ID")
ALLOWED_USER_ID = int(ALLOWED_USER_ID) if ALLOWED_USER_ID else None

DB_PATH = os.environ.get("DB_PATH", "clientes.db")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Estados de la conversación para /agregar
NOMBRE, NUMERO, DIRECCION, NOTAS = range(4)


# ---------------------------------------------------------------------------
# BASE DE DATOS
# ---------------------------------------------------------------------------

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            numero TEXT,
            direccion TEXT,
            notas TEXT,
            creado_por INTEGER,
            fecha_creacion TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.commit()
    conn.close()


def agregar_cliente(nombre, numero, direccion, notas, user_id):
    conn = get_conn()
    conn.execute(
        "INSERT INTO clientes (nombre, numero, direccion, notas, creado_por) VALUES (?, ?, ?, ?, ?)",
        (nombre, numero, direccion, notas, user_id),
    )
    conn.commit()
    conn.close()


def buscar_clientes(texto):
    conn = get_conn()
    like = f"%{texto}%"
    rows = conn.execute(
        "SELECT * FROM clientes WHERE nombre LIKE ? OR numero LIKE ? OR direccion LIKE ? ORDER BY nombre",
        (like, like, like),
    ).fetchall()
    conn.close()
    return rows


def listar_clientes():
    conn = get_conn()
    rows = conn.execute("SELECT * FROM clientes ORDER BY nombre").fetchall()
    conn.close()
    return rows


def eliminar_cliente(cliente_id):
    conn = get_conn()
    cur = conn.execute("DELETE FROM clientes WHERE id = ?", (cliente_id,))
    conn.commit()
    afectados = cur.rowcount
    conn.close()
    return afectados > 0


def formatear_cliente(row):
    texto = f"🆔 {row['id']} — 👤 *{row['nombre']}*"
    if row["numero"]:
        texto += f"\n📞 {row['numero']}"
    if row["direccion"]:
        texto += f"\n📍 {row['direccion']}"
    if row["notas"]:
        texto += f"\n📝 {row['notas']}"
    return texto


# ---------------------------------------------------------------------------
# CONTROL DE ACCESO
# ---------------------------------------------------------------------------

async def acceso_permitido(update: Update) -> bool:
    if ALLOWED_USER_ID is None:
        return True
    user_id = update.effective_user.id
    if user_id != ALLOWED_USER_ID:
        await update.message.reply_text(
            "⛔ No tienes permiso para usar este bot."
        )
        return False
    return True


# ---------------------------------------------------------------------------
# COMANDOS BÁSICOS
# ---------------------------------------------------------------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await acceso_permitido(update):
        return
    await update.message.reply_text(
        "👋 Hola, soy tu bot de clientes.\n\n"
        "Comandos disponibles:\n"
        "/agregar - Agregar un nuevo cliente\n"
        "/buscar <texto> - Buscar por nombre, número o dirección\n"
        "/listar - Ver todos los clientes\n"
        "/eliminar <id> - Eliminar un cliente\n"
        "/cancelar - Cancelar la acción actual"
    )


async def buscar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await acceso_permitido(update):
        return
    if not context.args:
        await update.message.reply_text("Uso: /buscar <nombre, número o dirección>")
        return
    texto = " ".join(context.args)
    resultados = buscar_clientes(texto)
    if not resultados:
        await update.message.reply_text("No encontré ningún cliente con ese dato.")
        return
    mensaje = "\n\n".join(formatear_cliente(r) for r in resultados)
    await update.message.reply_text(mensaje, parse_mode="Markdown")


async def listar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await acceso_permitido(update):
        return
    resultados = listar_clientes()
    if not resultados:
        await update.message.reply_text("Todavía no tienes clientes guardados.")
        return
    mensaje = "\n\n".join(formatear_cliente(r) for r in resultados)
    # Telegram limita los mensajes a 4096 caracteres; si tienes muchos clientes
    # esto se puede paginar más adelante.
    await update.message.reply_text(mensaje, parse_mode="Markdown")


async def eliminar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await acceso_permitido(update):
        return
    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text("Uso: /eliminar <id>  (usa /listar para ver los IDs)")
        return
    ok = eliminar_cliente(int(context.args[0]))
    if ok:
        await update.message.reply_text("✅ Cliente eliminado.")
    else:
        await update.message.reply_text("No encontré un cliente con ese ID.")


# ---------------------------------------------------------------------------
# CONVERSACIÓN /agregar
# ---------------------------------------------------------------------------

async def agregar_inicio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await acceso_permitido(update):
        return ConversationHandler.END
    await update.message.reply_text(
        "Vamos a agregar un cliente nuevo.\n\n¿Cuál es su *nombre*?",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove(),
    )
    return NOMBRE


async def recibir_nombre(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["nombre"] = update.message.text.strip()
    await update.message.reply_text("¿Cuál es su *número* de teléfono? (o escribe - para omitir)", parse_mode="Markdown")
    return NUMERO


async def recibir_numero(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = update.message.text.strip()
    context.user_data["numero"] = None if texto == "-" else texto
    await update.message.reply_text("¿Cuál es su *dirección*? (o escribe - para omitir)", parse_mode="Markdown")
    return DIRECCION


async def recibir_direccion(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = update.message.text.strip()
    context.user_data["direccion"] = None if texto == "-" else texto
    await update.message.reply_text("¿Alguna *nota* adicional? (o escribe - para omitir)", parse_mode="Markdown")
    return NOTAS


async def recibir_notas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = update.message.text.strip()
    notas = None if texto == "-" else texto

    agregar_cliente(
        context.user_data["nombre"],
        context.user_data.get("numero"),
        context.user_data.get("direccion"),
        notas,
        update.effective_user.id,
    )

    await update.message.reply_text(
        f"✅ Cliente *{context.user_data['nombre']}* guardado correctamente.",
        parse_mode="Markdown",
    )
    context.user_data.clear()
    return ConversationHandler.END


async def cancelar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("Operación cancelada.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

def main():
    if not TOKEN:
        raise RuntimeError(
            "Falta la variable de entorno TELEGRAM_BOT_TOKEN. "
            "Consigue un token hablando con @BotFather en Telegram."
        )

    init_db()

    app = Application.builder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("agregar", agregar_inicio)],
        states={
            NOMBRE: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_nombre)],
            NUMERO: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_numero)],
            DIRECCION: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_direccion)],
            NOTAS: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_notas)],
        },
        fallbacks=[CommandHandler("cancelar", cancelar)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("buscar", buscar))
    app.add_handler(CommandHandler("listar", listar))
    app.add_handler(CommandHandler("eliminar", eliminar))
    app.add_handler(conv_handler)

    logger.info("Bot iniciado, escuchando mensajes...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
