import os
import sqlite3
import random
from functools import wraps
from flask import (
    Flask, render_template, request, session, redirect,
    url_for, jsonify, flash, g
)
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
# En producción, usa una variable de entorno real para esto.
app.secret_key = os.environ.get('SECRET_KEY', 'clave_secreta_juego')

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'innova.db')

# ============================================================
#  CONTENIDO DEL JUEGO (roles del cuestionario y preguntas)
# ============================================================
ROLES = [
    {
        "id": "nuevo_ingreso",
        "titulo": "Practicante",
        "descripcion": "Acabas de unirte al equipo. Conoce lo esencial.",
        "emoji": "",
        "color": "#2A9D8F",
    },
    {
        "id": "Trabajador",
        "titulo": "Trabajador",
        "descripcion": "Ya formas parte del equipo. Pon a prueba tu conocimiento.",
        "emoji": "",
        "color": "#E63946",
    },
    {
        "id": "lider",
        "titulo": "Líder de Equipo",
        "descripcion": "Guías a otros. Demuestra tu dominio de la empresa.",
        "emoji": "",
        "color": "#457B9D",
    }
]

# Mapeo entre el ROL DE CUENTA (login) y el ROL DE JUEGO (banco de preguntas)
CUENTA_A_JUEGO = {
    "practicante": "nuevo_ingreso",
    "trabajador": "Trabajador",
    "jefe": "lider",
}

PREGUNTAS = {
    "nuevo_ingreso": [
        {
            "pregunta": "Te entregan tus EPP y herramientas el primer día. ¿Qué se espera de ti con ellas?",
            "opciones": [
                "A) Dejarlas donde sea, para eso están los casilleros.",
                "B) Cuidarlas, ya que son de la empresa y las necesitarás para trabajar.",
                "C) Prestárselas a un amigo que también hace pega de vez en cuando."
            ],
            "correcta": 1,
            "explicacion": "Es obligatorio cuidar los EPP y herramientas entregadas para trabajar (T3)."
        },
        {
            "pregunta": "Llegas a la oficina, dejas tus cosas y como no tienes nada que hacer, empiezas a jugar con el celular. ¿Qué paso obligatorio te saltaste?",
            "imagen": "oficina.png",
            "opciones": [
                "A) Saludar a la mascota de la empresa.",
                "B) Anotarme en el libro de asistencia.",
                "C) Pedir permiso para tomar desayuno"
            ],
            "correcta": 1,
            "explicacion": "Es obligatorio firmar la entrada y salida diariamente (T3)."
        },
        {
            "pregunta": "Llega el ansiado viernes y decides venir con esa camisa manchada y desarreglado/a. Al llegar a la puerta...",
            "imagen": "camisa.png",
            "opciones": [
                "A) Entras triunfante porque los viernes todo se vale.",
                "B) Te llaman la atención: debes cuidar tu higiene y presentación.",
                "C) Entras sin que nadie note la camisa y pasas rápido."
            ],
            "correcta": 1,
            "explicacion": "Es de vital importancia cuidar la higiene y presentación personal, ademas de tener una vestimenta adecuada (T5)."
        },
        {
            "pregunta": "Antes de entregarle una herramienta o equipo a un cliente o a un compañero, ¿qué debes hacer primero?",
            "opciones": [
                "A) Revizar si funciona para entregarlo lo mas rapido posible.",
                "B) Probarlo (testearlo) y limpiarlo para asegurarte de que funciona bien.",
                "C) Entregarlo tal cual salió del último trabajo, sin revisar nada."
            ],
            "correcta": 1,
            "explicacion": "Es obligatorio hacer testeo y limpieza de los equipos antes de entregarlos (T3)."
        },
        {
            "pregunta": "Terminaste tu turno y tu mesa de trabajo es un desorden. ¿Qué corresponde hacer antes de irte?",
            "opciones": [
                "A) Dejarlo para el turno siguiente, que ellos se las arreglen.",
                "B) Ordenar y limpiar, ya que espero lo mismo para mi.",
                "C) Dejar tal cual como me lo dejaron."
            ],
            "correcta": 1,
            "explicacion": "Mantener orden y limpieza en el lugar de trabajo es obligatorio (T5)."
        },
        {
            "pregunta": "Decides tener un 'martes de misterio' y faltas 2 veces seguidas sin avisar a nadie. ¿Qué pasa con tu práctica?",
            "opciones": [
                "A) Te ganas un premio a la desaparición del mes.",
                "B) Tu práctica se suspende.",
                "C) El líder de equipo te invita a un café para hablar de la vida."
            ],
            "correcta": 1,
            "explicacion": "2 faltas sin avisar significan la suspensión inmediata de tu práctica. La clave es la comunicación: ante cualquier problema o emergencia que te impida asistir con normalidad, debes avisar de inmediato."
        },
        {
            "pregunta": "Para un buen control de los equipos, la honestidad es clave. Si se pierde una herramienta, tú fuiste el último en usarla y alguien reporta su pérdida, ¿cuál es tu deber?",
            "opciones": [
                "A) Guardar silencio y esperar que aparezca sola.",
                "B) Disimular, total nadie puede probar que fui yo.",
                "C) Dar un paso al frente, reportar que la usé y detallar dónde la dejé por última vez."
            ],
            "correcta": 2,
            "explicacion": "Avisar en caso de pérdida de alguna herramienta o equipo de trabajo es obligatorio. Dar el aviso oportuno evita retrasos en la operación (T3)."
        },
        {
            "pregunta": "Es tu primer día y traes tu mochila favorita con todas tus cosas. Al llegar a la entrada de la empresa...",
            "opciones": [
                "A) Entras con ella, total es pequeña.",
                "B) Debes dejarla afuera o en un casillero: no se permite el ingreso con mochila al interior.",
                "C) La escondes bajo el escritorio para que nadie la vea."
            ],
            "correcta": 1,
            "explicacion": "Está prohibido ingresar con mochila al interior de la empresa (T3)."
        },
        {
            "pregunta": "Necesitas el próximo viernes libre para un trámite personal. ¿Cuándo deberías avisar como máximo?",
            "opciones": [
                "A) El mismo viernes en la mañana, avisando por si acaso.",
                "B) Con 24 horas de anticipación como mínimo.",
                "C) No hace falta avisar, total es solo un día."
            ],
            "correcta": 1,
            "explicacion": "Los permisos se piden con 24 horas de anticipación."
        },
        {
            "pregunta": "Un compañero llega un lunes con evidente olor a alcohol. Según el reglamento, esta situación es:",
            "opciones": [
                "A) Normal si fue un fin de semana largo.",
                "B) Una falta grave: está prohibido llegar al trabajo en estado de ebriedad.",
                "C) Algo que solo importa si maneja un vehículo."
            ],
            "correcta": 1,
            "explicacion": "Está prohibido llegar a trabajar en estado de ebriedad (T3)."
        }
    ],
    "Trabajador": [
        {
            "pregunta": "Estás en terreno y te das cuenta de que el Alicate Universal desapareció de tu cinturón. ¿Qué haces?",
            "opciones": [
                "A) Comprar uno igual en la ferretería de la esquina y no decir nada.",
                "B) Culpar al practicante nuevo, siempre funciona.",
                "C) Avisar inmediatamente al supervisor sobre la pérdida de la herramienta."
            ],
            "correcta": 2,
            "explicacion": "Es obligatorio avisar en caso de pérdida de alguna herramienta o equipo de trabajo (T3)."
        },
        {
            "pregunta": "Un cliente muy simpático te pide tu WhatsApp personal para 'coordinar más rápido'. Tu respuesta correcta es:",
            "opciones": [
                "A) '¡Claro! Aquí tiene, y le paso mi Instagram también'.",
                "B) 'Pásame el tuyo y te llamo cuando pueda'.",
                "C) 'Por políticas de la empresa está prohibido usar teléfonos personales para hablar con clientes'."
            ],
            "correcta": 2,
            "explicacion": "Está estrictamente prohibido utilizar los teléfonos personales para hablar con los clientes (T5)."
        },
        {
            "pregunta": "Vas manejando el vehículo de la empresa y tu canción favorita suena en la radio. ¿Cuál es el límite para no convertirte en un peligro?",
            "opciones": [
                "A) Máximo 60 km/h en ciudad, con cinturón puesto y sin tocar el teléfono.",
                "B) Lo que marque el velocímetro si voy atrasado a la instalación.",
                "C) 100 km/h, pero solo si no hay policías cerca."
            ],
            "correcta": 0,
            "explicacion": "Es obligatorio el uso de cinturón, está prohibido el teléfono al volante y la velocidad máxima en ciudad es 60 km/h (T3)."
        },
        {
            "pregunta": "Un compañero te cuenta que un cliente le ofreció trabajo extra 'por fuera', pagado en efectivo y fuera del horario de Innova. ¿Qué corresponde hacer?",
            "opciones": [
                "A) Aceptar también, total es plata extra.",
                "B) Recordarle que está prohibido tomar trabajos particulares con los clientes de la empresa.",
                "C) Pedirle que te incluya a ti también."
            ],
            "correcta": 1,
            "explicacion": "Está prohibido tomar trabajos particulares con nuestros clientes (T1)."
        },
        {
            "pregunta": "Antes de salir a terreno, el supervisor revisa tu vehículo de trabajo. ¿Cuál de estos SÍ debe llevar obligatoriamente?",
            "opciones": [
                "A) Chaleco reflectante, botiquín, triángulo y cable para traspaso de corriente.",
                "B) Un parlante bluetooth y snacks para el camino.",
                "C) Alicates, Llaves, Destornillador, cables para traspaso de corriente."
            ],
            "correcta": 0,
            "explicacion": "Los vehículos deben portar chaleco reflectante, botiquín, triángulo y cable para traspaso de corriente (T3)."
        },
        {
            "pregunta": "Sufres un pequeño accidente en el trayecto al trabajo. ¿Qué debes hacer apenas puedas?",
            "opciones": [
                "A) No decir nada para no preocupar a nadie.",
                "B) Avisar de inmediato, sea accidente laboral o de trayecto.",
                "C) Esperar a que alguien pregunte por qué llegaste distinto."
            ],
            "correcta": 1,
            "explicacion": "Es obligatorio avisar en caso de accidente laboral o de trayecto (T2)."
        },
        {
            "pregunta": "En el grupo de WhatsApp de terreno, un compañero hace comentarios subidos de tono sobre una colega. Según el reglamento, esto es:",
            "opciones": [
                "A) Una falta gravísima: el acoso sexual y laboral está prohibido.",
                "B) Algo que se debe resolver 'entre ellos'.",
                "C) Aceptable si es 'solo una talla'."
            ],
            "correcta": 0,
            "explicacion": "Está prohibido el acoso sexual y laboral (T0)."
        },
        {
            "pregunta": "Estás reparando una instalación y notas un cable pelado cerca de tu zona de trabajo. Tienes un alicate con mango metálico a mano. ¿Qué haces?",
            "opciones": [
                "A) Lo usas igual, total tienes experiencia.",
                "B) Evitas cualquier elemento conductor de electricidad y usas herramientas aisladas o cortas la energía primero.",
                "C) Le pides a un compañero sin experiencia que lo intente."
            ],
            "correcta": 1,
            "explicacion": "Está prohibido el uso de elementos que sean conductores de electricidad en contextos de riesgo eléctrico (T3)."
        },
        {
            "pregunta": "Llegas a hacer un trabajo y el cliente coordinado no aparece. ¿Cuánto tiempo esperas como máximo antes de actuar?",
            "opciones": [
                "A) Todo el día, hasta que llegue.",
                "B) 15 minutos como máximo, y si no llega, avisar al supervisor.",
                "C) Te vas de inmediato sin avisar a nadie."
            ],
            "correcta": 1,
            "explicacion": "Se debe esperar 15 minutos como máximo al cliente con visita coordinada; si no llega, avisar al supervisor."
        },
        {
            "pregunta": "Un colega sin licencia de conducir te pide las llaves del vehículo de trabajo para 'mover el auto no más'. ¿Qué haces?",
            "opciones": [
                "A) Se las prestas, es solo un movimiento corto.",
                "B) Te niegas: no se puede entregar el vehículo a quien no tiene licencia de conducir.",
                "C) Lo mueves tú pero dejas que él maneje de regreso."
            ],
            "correcta": 1,
            "explicacion": "No se debe entregar el vehículo de trabajo a personas sin licencia de conducir (T3)."
        }
    ],
    "lider": [
        {
            "pregunta": "Tu mejor técnico resolvió un problema épico, pero ha llegado tarde tres días seguidos sin avisar. ¿Cómo manejas esta situación?",
            "opciones": [
                "A) Lo retas frente a todo el equipo para dar el ejemplo.",
                "B) Lo felicitas en público por su logro, y en privado hablas con él sobre sus atrasos.",
                "C) Ignoras el atraso porque es tu mejor técnico."
            ],
            "correcta": 1,
            "explicacion": "Las felicitaciones son siempre en público y los llamados de atención en privado."
        },
        {
            "pregunta": "Notas que dos trabajadores le hacen 'bromas' pesadas y recurrentes a un compañero nuevo. ¿Cuánta tolerancia aplicas?",
            "opciones": [
                "A) Les dices que al menos inviten al resto del equipo a las bromas.",
                "B) Tolerancia de 15 minutos, como con los atrasos.",
                "C) Tolerancia cero. Detienes la situación de inmediato."
            ],
            "correcta": 2,
            "explicacion": "En Innova hay tolerancia cero con el bullying y está prohibido el acoso laboral (T0)."
        },
        {
            "pregunta": "Uno de tus técnicos llega 10 minutos tarde, pero avisó por WhatsApp con anticipación que el bus se demoró. ¿Qué corresponde?",
            "opciones": [
                "A) Aplicar tolerancia, ya que hay 15 minutos de margen con aviso previo.",
                "B) Descontarle el día completo por principio.",
                "C) Ignorar el aviso, las reglas son las reglas sin excepción."
            ],
            "correcta": 0,
            "explicacion": "Habrá tolerancia de 15 minutos por atrasos, siempre con aviso previo."
        },
        {
            "pregunta": "Decides ordenar el taller: separas lo que sirve de lo que no, y luego organizas cada herramienta en su lugar. ¿Qué pasos de la metodología 5S acabas de aplicar?",
            "opciones": [
                "A) Seiri (Clasificación) y Seiton (Organización).",
                "B) Shitsuke (Disciplina) únicamente.",
                "C) Ninguno, eso no forma parte de las 5S."
            ],
            "correcta": 0,
            "explicacion": "Seiri es clasificar y descartar lo innecesario, y Seiton es organizar lo que queda: dos de los cinco pilares de la metodología 5S."
        },
        {
            "pregunta": "Un miembro de tu equipo viene a contarte un problema personal que afecta su rendimiento. ¿Qué habilidad de liderazgo es clave en ese momento?",
            "opciones": [
                "A) Escucha activa y empatía: entender antes de responder.",
                "B) Cambiar de tema rápido para volver al trabajo.",
                "C) Resolverlo tú mismo sin dejarlo hablar."
            ],
            "correcta": 0,
            "explicacion": "La escucha activa y la empatía son habilidades clave de comunicación efectiva que se esperan de un líder en Innova."
        },
        {
            "pregunta": "Dos técnicos de tu equipo no logran ponerse de acuerdo en cómo dividirse una tarea urgente. ¿Qué habilidad de liderazgo necesitas aplicar?",
            "opciones": [
                "A) Poder de negociación: mediar y encontrar un acuerdo que funcione para ambos.",
                "B) Ignorarlo, que ellos lo resuelvan solos sin importar el resultado.",
                "C) Asignar la tarea al azar para evitar el conflicto."
            ],
            "correcta": 0,
            "explicacion": "El poder de negociación es una competencia clave para resolver conflictos dentro del equipo."
        },
        {
            "pregunta": "Al dar feedback a tu equipo, mezclas comentarios positivos y negativos en la misma frase frente a todos. ¿Qué principio de liderazgo no estás respetando?",
            "opciones": [
                "A) Las felicitaciones son en público y los llamados de atención en privado.",
                "B) Ninguno, así se hace siempre.",
                "C) La comunicación efectiva no tiene relación con esto."
            ],
            "correcta": 0,
            "explicacion": "Las felicitaciones deben darse en público y los llamados de atención en privado, para mantener el respeto y la motivación del equipo."
        }
    ]
}

# ============================================================
#  BASE DE DATOS (SQLite - persiste en disco como innova.db)
# ============================================================
def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def cerrar_db(exception=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()


def init_db():
    """Crea las tablas si no existen y siembra un usuario admin por defecto."""
    db = sqlite3.connect(DB_PATH)
    db.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            rut TEXT UNIQUE,
            usuario TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            rol_cuenta TEXT NOT NULL,
            fecha_creacion TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    db.execute('''
        CREATE TABLE IF NOT EXISTS resultados (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
            rol_juego TEXT NOT NULL,
            puntaje_teoria INTEGER NOT NULL,
            total_teoria INTEGER NOT NULL,
            puntaje_dados INTEGER NOT NULL DEFAULT 0,
            total_dados INTEGER NOT NULL DEFAULT 0,
            puntaje_final INTEGER NOT NULL,
            total_final INTEGER NOT NULL,
            fecha TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(usuario_id) REFERENCES usuarios(id)
        )
    ''')

    existe_admin = db.execute(
        "SELECT id FROM usuarios WHERE rol_cuenta = 'admin' LIMIT 1"
    ).fetchone()

    if not existe_admin:
        db.execute(
            "INSERT INTO usuarios (nombre, usuario, password_hash, rol_cuenta) VALUES (?, ?, ?, ?)",
            ("Administrador", "admin", generate_password_hash("admin123"), "admin")
        )
        print("Usuario admin creado -> usuario: admin / contraseña: admin123 (¡cámbiala!)")

    db.commit()
    db.close()


# ============================================================
#  DECORADORES DE CONTROL DE ACCESO
# ============================================================
def login_requerido(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if 'usuario_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return wrapper


def rol_requerido(*roles_permitidos):
    def decorador(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if 'usuario_id' not in session:
                return redirect(url_for('login'))
            if session.get('rol_cuenta') not in roles_permitidos:
                return "No autorizado", 403
            return f(*args, **kwargs)
        return wrapper
    return decorador


# ============================================================
#  AUTENTICACIÓN
# ============================================================
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario = request.form.get('usuario', '').strip()
        password = request.form.get('password', '')

        db = get_db()
        fila = db.execute(
            "SELECT * FROM usuarios WHERE usuario = ?", (usuario,)
        ).fetchone()

        if fila and check_password_hash(fila['password_hash'], password):
            session.clear()
            session['usuario_id'] = fila['id']
            session['nombre'] = fila['nombre']
            session['rol_cuenta'] = fila['rol_cuenta']

            if fila['rol_cuenta'] in ('admin', 'jefe'):
                return redirect(url_for('ranking'))
            return redirect(url_for('index'))
        else:
            flash('Usuario o contraseña incorrectos.')
            return redirect(url_for('login'))

    return render_template('login.html', modo_admin=False)


@app.route('/crear_usuario', methods=['GET', 'POST'])
@rol_requerido('admin')
def crear_usuario():
    if request.method == 'POST':
        nombre = request.form.get('nombre', '').strip()
        rut = request.form.get('rut', '').strip() # <- NUEVO
        usuario = request.form.get('usuario', '').strip()
        password = request.form.get('password', '')
        rol_cuenta = request.form.get('rol_cuenta')

        if rol_cuenta not in ('practicante', 'trabajador', 'jefe'):
            flash('Rol de cuenta inválido.')
            return redirect(url_for('crear_usuario'))

        if not nombre or not rut or not usuario or not password:
            flash('Todos los campos son obligatorios.')
            return redirect(url_for('crear_usuario'))

        db = get_db()
        existe = db.execute(
            "SELECT id FROM usuarios WHERE usuario = ? OR rut = ?", (usuario, rut)
        ).fetchone()

        if existe:
            flash('Ese nombre de usuario o RUT ya está registrado.')
            return redirect(url_for('crear_usuario'))

        # Se guarda con el RUT incluido
        db.execute(
            "INSERT INTO usuarios (nombre, rut, usuario, password_hash, rol_cuenta) VALUES (?, ?, ?, ?, ?)",
            (nombre, rut, usuario, generate_password_hash(password), rol_cuenta)
        )
        db.commit()
        flash(f'¡Cuenta creada exitosamente para {nombre} (RUT: {rut})!')
        return redirect(url_for('crear_usuario'))

    return render_template('crear_usuario.html')


@app.route('/login_admin', methods=['GET', 'POST'])
def login_admin():
    """Login exclusivo para administradores. A diferencia de /login,
    exige que la cuenta tenga rol_cuenta = 'admin'; las credenciales
    siempre se verifican, nunca se saltan el paso."""
    if request.method == 'POST':
        usuario = request.form.get('usuario', '').strip()
        password = request.form.get('password', '')

        db = get_db()
        fila = db.execute(
            "SELECT * FROM usuarios WHERE usuario = ? AND rol_cuenta = 'admin'",
            (usuario,)
        ).fetchone()

        if fila and check_password_hash(fila['password_hash'], password):
            session.clear()
            session['usuario_id'] = fila['id']
            session['nombre'] = fila['nombre']
            session['rol_cuenta'] = fila['rol_cuenta']
            return redirect(url_for('ranking'))
        else:
            flash('Usuario o contraseña de administrador incorrectos.')
            return redirect(url_for('login_admin'))

    return render_template('login.html', modo_admin=True)


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


# ============================================================
#  RUTAS DEL JUEGO
# ============================================================
@app.route('/')
@login_requerido
def index():
    if session['rol_cuenta'] in ('admin', 'jefe'):
        return redirect(url_for('ranking'))

    rol_juego_id = CUENTA_A_JUEGO.get(session['rol_cuenta'])
    rol_info = next((r for r in ROLES if r['id'] == rol_juego_id), None)
    return render_template('index.html', rol=rol_info)


@app.route('/iniciar')
@login_requerido
def iniciar():
    if session['rol_cuenta'] in ('admin', 'jefe'):
        return redirect(url_for('ranking'))

    rol_juego_id = CUENTA_A_JUEGO.get(session['rol_cuenta'])
    preguntas_rol = PREGUNTAS.get(rol_juego_id, [])

    # Orden aleatorio de las preguntas para esta partida (sin repetir ninguna)
    orden = list(range(len(preguntas_rol)))
    random.shuffle(orden)

    session['rol_juego'] = rol_juego_id
    session['orden_preguntas'] = orden
    session['puntaje'] = 0
    session['pregunta_actual'] = 0
    session['historial'] = []
    session['puntaje_dados'] = 0
    session['total_dados'] = 0
    session['resultado_guardado'] = False
    return redirect(url_for('pregunta'))


@app.route('/pregunta', methods=['GET', 'POST'])
@login_requerido
def pregunta():
    if 'rol_juego' not in session:
        return redirect(url_for('index'))

    rol_juego = session['rol_juego']
    preguntas_rol = PREGUNTAS.get(rol_juego, [])
    orden = session['orden_preguntas']

    if session['pregunta_actual'] >= len(orden):
        return render_template('intermedio.html')

    indice_real = orden[session['pregunta_actual']]
    pregunta_actual = preguntas_rol[indice_real]
    rol_info = next((r for r in ROLES if r['id'] == rol_juego), {})

    if request.method == 'POST':
        respuesta_idx = int(request.form.get('opcion'))
        es_correcta = (respuesta_idx == pregunta_actual['correcta'])
        if es_correcta:
            session['puntaje'] += 1

        registro = {
            "pregunta": pregunta_actual["pregunta"],
            "tu_respuesta": pregunta_actual["opciones"][respuesta_idx],
            "respuesta_correcta": pregunta_actual["opciones"][pregunta_actual["correcta"]],
            "es_correcta": es_correcta,
            "explicacion": pregunta_actual.get("explicacion", "")
        }

        historial = session.get('historial', [])
        historial.append(registro)
        session['historial'] = historial
        session['pregunta_actual'] += 1
        return redirect(url_for('pregunta'))

    return render_template(
        'pregunta.html',
        pregunta=pregunta_actual,
        rol=rol_info,
        numero=session['pregunta_actual'] + 1,
        total=len(orden)
    )


@app.route('/reto_atencion')
@login_requerido
def reto_atencion():
    return render_template('juego_dados.html')


@app.route('/api/guardar_reto_dados', methods=['POST'])
@login_requerido
def guardar_reto_dados():
    """El JS del reto de dados llama a esta ruta por fetch() al terminar las 3 rondas."""
    data = request.get_json(force=True, silent=True) or {}
    correctas = int(data.get('correctas', 0))
    total = int(data.get('total', 0))

    session['puntaje_dados'] = correctas
    session['total_dados'] = total
    return jsonify({"ok": True})


@app.route('/resultado')
@login_requerido
def resultado():
    if 'rol_juego' not in session:
        return redirect(url_for('index'))

    puntaje_teoria = session.get('puntaje', 0)
    total_teoria = len(PREGUNTAS.get(session['rol_juego'], []))
    puntaje_dados = session.get('puntaje_dados', 0)
    total_dados = session.get('total_dados', 0)

    puntaje_final = puntaje_teoria + puntaje_dados
    total_final = total_teoria + total_dados

    historial = session.get('historial', [])

    # Se guarda en la base de datos una sola vez por partida jugada
    if not session.get('resultado_guardado'):
        db = get_db()
        db.execute('''
            INSERT INTO resultados
                (usuario_id, rol_juego, puntaje_teoria, total_teoria,
                 puntaje_dados, total_dados, puntaje_final, total_final)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            session['usuario_id'], session['rol_juego'],
            puntaje_teoria, total_teoria,
            puntaje_dados, total_dados,
            puntaje_final, total_final
        ))
        db.commit()
        session['resultado_guardado'] = True

    return render_template(
        'resultado.html',
        puntaje=puntaje_final,
        total=total_final,
        puntaje_teoria=puntaje_teoria,
        total_teoria=total_teoria,
        puntaje_dados=puntaje_dados,
        total_dados=total_dados,
        historial=historial
    )


# ============================================================
#  RANKING (solo admin y jefe)
# ============================================================
@app.route('/ranking')
@rol_requerido('admin', 'jefe')
def ranking():
    db = get_db()
    filas = db.execute('''
        SELECT u.nombre, u.usuario, r.rol_juego,
               r.puntaje_final, r.total_final, r.fecha
        FROM resultados r
        JOIN usuarios u ON u.id = r.usuario_id
        ORDER BY (CAST(r.puntaje_final AS FLOAT) / r.total_final) DESC, r.fecha ASC
        LIMIT 20
    ''').fetchall()
    return render_template('ranking.html', resultados=filas)


# ============================================================
#  LISTADO DE USUARIOS (solo admin)
# ============================================================
@app.route('/usuarios')
@rol_requerido('admin')
def usuarios():
    db = get_db()
    filas = db.execute('''
        SELECT id, nombre, rut, usuario, rol_cuenta, fecha_creacion
        FROM usuarios
        ORDER BY fecha_creacion DESC
    ''').fetchall()
    return render_template('usuarios.html', usuarios=filas)


@app.route('/usuarios/<int:usuario_id>/editar', methods=['GET', 'POST'])
@rol_requerido('admin')
def editar_usuario(usuario_id):
    db = get_db()
    fila = db.execute("SELECT * FROM usuarios WHERE id = ?", (usuario_id,)).fetchone()

    if not fila:
        flash('Usuario no encontrado.')
        return redirect(url_for('usuarios'))

    if request.method == 'POST':
        nombre = request.form.get('nombre', '').strip()
        rut = request.form.get('rut', '').strip()
        usuario = request.form.get('usuario', '').strip()
        password = request.form.get('password', '')
        rol_cuenta = request.form.get('rol_cuenta')

        if rol_cuenta not in ('practicante', 'trabajador', 'jefe', 'admin'):
            flash('Rol de cuenta inválido.')
            return redirect(url_for('editar_usuario', usuario_id=usuario_id))

        if not nombre or not usuario:
            flash('Nombre y usuario son obligatorios.')
            return redirect(url_for('editar_usuario', usuario_id=usuario_id))

        # Verifica que el nuevo usuario/rut no choque con OTRA cuenta distinta a esta
        choque = db.execute(
            "SELECT id FROM usuarios WHERE (usuario = ? OR (rut = ? AND rut != '')) AND id != ?",
            (usuario, rut, usuario_id)
        ).fetchone()
        if choque:
            flash('Ese nombre de usuario o RUT ya está en uso por otra cuenta.')
            return redirect(url_for('editar_usuario', usuario_id=usuario_id))

        if password:
            db.execute(
                "UPDATE usuarios SET nombre=?, rut=?, usuario=?, password_hash=?, rol_cuenta=? WHERE id=?",
                (nombre, rut, usuario, generate_password_hash(password), rol_cuenta, usuario_id)
            )
        else:
            db.execute(
                "UPDATE usuarios SET nombre=?, rut=?, usuario=?, rol_cuenta=? WHERE id=?",
                (nombre, rut, usuario, rol_cuenta, usuario_id)
            )
        db.commit()

        # Si el admin se edita a sí mismo, refresca los datos de su sesión
        if usuario_id == session.get('usuario_id'):
            session['nombre'] = nombre
            session['rol_cuenta'] = rol_cuenta

        flash(f'Datos de {nombre} actualizados correctamente.')
        return redirect(url_for('usuarios'))

    return render_template('editar_usuario.html', usuario=fila)


@app.route('/usuarios/<int:usuario_id>/eliminar', methods=['POST'])
@rol_requerido('admin')
def eliminar_usuario(usuario_id):
    db = get_db()

    if usuario_id == session.get('usuario_id'):
        flash('No puedes eliminar tu propia cuenta mientras tienes la sesión iniciada.')
        return redirect(url_for('usuarios'))

    fila = db.execute("SELECT * FROM usuarios WHERE id = ?", (usuario_id,)).fetchone()
    if not fila:
        flash('Usuario no encontrado.')
        return redirect(url_for('usuarios'))

    if fila['rol_cuenta'] == 'admin':
        total_admins = db.execute(
            "SELECT COUNT(*) AS c FROM usuarios WHERE rol_cuenta = 'admin'"
        ).fetchone()['c']
        if total_admins <= 1:
            flash('No puedes eliminar la única cuenta de administrador restante.')
            return redirect(url_for('usuarios'))

    # Borra también los resultados asociados a ese usuario para no dejar registros huérfanos
    db.execute("DELETE FROM resultados WHERE usuario_id = ?", (usuario_id,))
    db.execute("DELETE FROM usuarios WHERE id = ?", (usuario_id,))
    db.commit()

    flash(f'Usuario "{fila["usuario"]}" eliminado correctamente.')
    return redirect(url_for('usuarios'))


if __name__ == '__main__':
    init_db()
    app.run(debug=True)