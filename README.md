# Bot de Telegram — Gestión de Clientes

Bot personal para guardar y consultar clientes (nombre, número, dirección, notas)
directamente desde Telegram. Usa SQLite (un solo archivo, sin servidor de base
de datos que mantener).

## Comandos

- `/start` — mensaje de bienvenida
- `/agregar` — inicia una conversación paso a paso para guardar un cliente
- `/buscar <texto>` — busca por nombre, número o dirección
- `/listar` — muestra todos los clientes guardados
- `/eliminar <id>` — elimina un cliente por su ID (el ID lo ves con `/listar`)
- `/cancelar` — cancela el flujo de `/agregar` si te equivocas

## 1. Crear el bot en Telegram

1. Abre Telegram y busca **@BotFather**.
2. Envía `/newbot` y sigue las instrucciones (nombre y username del bot).
3. BotFather te va a dar un **token** parecido a `123456789:AAExxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`.
   Guárdalo, lo vas a necesitar en el paso 3.

## 2. (Opcional pero recomendado) Restringir el bot solo a ti

1. Busca **@userinfobot** en Telegram y envíale cualquier mensaje.
2. Te va a devolver tu **ID numérico** (algo como `987654321`).
3. Guárdalo, lo vas a usar como `ALLOWED_USER_ID` en el siguiente paso.

Si no configuras esto, cualquier persona que encuentre tu bot podrá usarlo.

## 3. Desplegar en Railway (recomendado — gratis para este uso, y queda 24/7)

1. Crea una cuenta en [railway.app](https://railway.app) (puedes entrar con tu
   cuenta de GitHub).
2. Sube esta carpeta a un repositorio de GitHub (puede ser privado).
3. En Railway: **New Project → Deploy from GitHub repo** y elige el repositorio.
4. Railway va a detectar el `Procfile` y desplegar automáticamente un
   **worker** (proceso en segundo plano, no necesita puerto web).
5. Ve a la pestaña **Variables** del proyecto y agrega:
   - `TELEGRAM_BOT_TOKEN` = el token que te dio BotFather
   - `ALLOWED_USER_ID` = tu ID numérico (si quieres restringirlo, paso 2)
6. **Importante — persistencia de datos:** por defecto, el sistema de archivos
   de Railway se reinicia con cada nuevo despliegue, y perderías tu base
   `clientes.db`. Para evitar esto:
   - En el proyecto, ve a **Settings → Volumes** y crea un volumen (por
     ejemplo, móntalo en `/data`).
   - Agrega la variable `DB_PATH` = `/data/clientes.db`.
   - Así la base de datos vive en el volumen y sobrevive a los redeploys.
7. Guarda las variables; Railway reinicia el servicio solo y el bot queda
   corriendo 24/7. Si el proceso llega a caerse, Railway lo reinicia
   automáticamente.

Railway tiene un plan gratuito con horas incluidas al mes; para un bot
personal de bajo uso normalmente alcanza. Si algún mes te pasas, cuesta
centavos (cobra por uso real de CPU/RAM, no por "plan fijo").

### Alternativa: VPS propio

Si en algún momento prefieres tener control total (por ejemplo un droplet de
DigitalOcean o una instancia de Contabo/Hetzner), el despliegue es:

```bash
git clone <tu-repo>
cd bot-clientes
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
export TELEGRAM_BOT_TOKEN="tu_token"
export ALLOWED_USER_ID="tu_id"
```

Y para que quede corriendo 24/7 y se reinicie solo si el servidor reinicia,
usa `systemd`:

```ini
# /etc/systemd/system/bot-clientes.service
[Unit]
Description=Bot de Telegram - Clientes
After=network.target

[Service]
WorkingDirectory=/ruta/a/bot-clientes
Environment="TELEGRAM_BOT_TOKEN=tu_token"
Environment="ALLOWED_USER_ID=tu_id"
ExecStart=/ruta/a/bot-clientes/venv/bin/python bot.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable bot-clientes
sudo systemctl start bot-clientes
```

## 4. Probar localmente antes de desplegar (opcional)

```bash
pip install -r requirements.txt
export TELEGRAM_BOT_TOKEN="tu_token"
python bot.py
```

Abre tu bot en Telegram y prueba `/start`, `/agregar`, `/buscar`, `/listar`.

## Próximos pasos posibles

- Comando `/editar` para modificar un cliente existente.
- Exportar todos los clientes a un archivo Excel/CSV.
- Paginar `/listar` cuando tengas muchos clientes (Telegram limita cada
  mensaje a 4096 caracteres).
- Respaldos automáticos del archivo `clientes.db`.

Si quieres cualquiera de estos, dímelo y lo agrego.
