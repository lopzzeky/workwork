from flask import Flask, render_template, request, session, redirect, url_for

app = Flask(__name__)
app.secret_key = 'clave_secreta_juego'

# Tus roles
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

# Preguntas basadas en el Reglamento Interno de Innova
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
            "pregunta": "Llegas a la oficina, dejas tus cosas y te vas directo a la sala de descanso. ¿Qué paso obligatorio te saltaste?",
            "opciones": [
                "A) Firmar la entrada junto con la hora en la que se llego.",
                "B) Pedir permiso para tomar café.",
                "C) Nada, así se hace siempre en Innova."
            ],
            "correcta": 0,
            "explicacion": "Es obligatorio firmar la entrada y salida diariamente (T3)."
        },
        {
            "pregunta": "Llega el ansiado viernes y decides venir con esa camisa manchada y desarreglado. Al llegar a la puerta...",
            "opciones": [
                "A) Entras triunfante porque los viernes todo se vale.",
                "B) Te devuelven: debes cuidar tu higiene y presentación.",
                "C) Entras sin que nadie note la camisa y pasas rápido."
            ],
            "correcta": 1,
            "explicacion": "Es de vital importancia cuidar la higiene y presentación personal, ademas de tener una vestimenta adecuada (T5)."
        },
        {
            "pregunta": "Antes de entregarle una herramienta o equipo a un cliente o a un compañero, ¿qué debes hacer primero?",
            "opciones": [
                "A) Envolverlo bonito para que se vea nuevo.",
                "B) Probarlo (testearlo) y limpiarlo para asegurarte de que funciona bien.",
                "C) Entregarlo tal cual salió del último trabajo, sin revisar nada."
            ],
            "correcta": 1,
            "explicacion": "Es obligatorio hacer testeo y limpieza de los equipos antes de entregarlos (T3)."
        },
        {
            "pregunta": "Terminaste tu turno y tu mesa de trabajo parece zona de guerra. ¿Qué corresponde hacer antes de irte?",
            "opciones": [
                "A) Dejarlo para el turno siguiente, que ellos se las arreglen.",
                "B) Ordenar y limpiar tu lugar de trabajo.",
                "C) Cerrar la puerta y que nadie lo note."
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
            "explicacion": "2 faltas sin avisar significan la suspensión inmediata de tu práctica."
        },
        {
            "pregunta": "Decides tener un 'martes de misterio' y faltas 2 veces seguidas sin avisar a nadie. ¿Qué pasa con tu práctica?",
            "opciones": [
                "A) Te ganas un premio a la desaparición del mes.",
                "B) Tu práctica se suspende.",
                "C) El líder de equipo te invita a un café para hablar de la vida."
            ],
           "correcta": 1,
            "explicacion": "2 faltas sin avisar significan la suspensión inmediata de tu práctica."
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
                "C) Solo el estuche de herramientas, el resto es opcional."
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
        }
    ]
}

# RUTA 1: Pantalla de inicio para elegir rol
@app.route('/')
def index():
    # Limpiamos cualquier juego anterior
    session.clear()
    return render_template('index.html', roles=ROLES)

# RUTA 2: Iniciar el juego
@app.route('/iniciar/<rol_id>')
def iniciar(rol_id):
    session['rol'] = rol_id
    session['puntaje'] = 0
    session['pregunta_actual'] = 0
    session['historial'] = []
    return redirect(url_for('pregunta'))

# RUTA 3: Mostrar y procesar las preguntas
@app.route('/pregunta', methods=['GET', 'POST'])
def pregunta():
    if 'rol' not in session:
        return redirect(url_for('index'))

    rol_actual = session['rol']
    preguntas_rol = PREGUNTAS.get(rol_actual, [])

    if session['pregunta_actual'] >= len(preguntas_rol):
        return render_template('intermedio.html') # <--- NUEVA LÍNEA

    pregunta_actual = preguntas_rol[session['pregunta_actual']]
    rol_info = next((r for r in ROLES if r['id'] == rol_actual), {})

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
        total=len(preguntas_rol)
    )
# RUTA JUEGO DE DADOS
@app.route('/reto_atencion')
def reto_atencion():
    return render_template('juego_dados.html')

# RUTA 4: Resultados
@app.route('/resultado')
def resultado():
    if 'rol' not in session: return redirect(url_for('index'))

    puntaje = session.get('puntaje', 0)
    total = len(PREGUNTAS.get(session['rol'], []))

    historial = session.get('historial', [])

    return render_template('resultado.html', puntaje=puntaje, total=total, historial=historial)

if __name__ == '__main__':
    app.run(debug=True)