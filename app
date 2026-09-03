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

# Tus preguntas (Completé los datos vacíos como ejemplo)
PREGUNTAS = {
    "nuevo_ingreso": [
        {
            "pregunta": "Guia, reglamentos de la empresa, cada actividad tiene cierta cantidad de tolerancia. !TENER EN CUENTA¡",
            "opciones": ["Entendido"],
            "correcta": 0, # Corresponde a "Okey"
        },
        {
            "pregunta": "Utilizarias tu numero personal para hablar con un cliente?",
            "opciones": ["Si", "No"],
            "correcta": 1, # Corresponde a "No"
            "explicacion": "Es esencial separar la informacion personal con el trabajo, con esto evitamos situaciones incomodas",
        },
        {
            "pregunta": "Es importante mantener el respeto y la responzabilidad en el area de trabajo. A continuacion, faltar 2 veces a la practica sin avisar corresponde a: ",
            "opciones": ["1 tolerancia menos", "Suspencion de Practica Profesional"],
            "correcta": 1, # Corresponde a "No"
            "explicacion": "La practica nos ayuda a formar profesionales, por lo que debe haber compromiso ",
        },
        {
            "pregunta": "La comunicacion efectiva es importante en las empresas?",
            "opciones": ["Si", "No"],
            "correcta": 0, # Corresponde a "Si"
            "explicacion": "Comunicarse de forma efectiva facilita el trabajo y mejora el ambiente laboral",
        }
        
    ],
    "Trabajador": [
        {
            "pregunta": "",
            "opciones": [""],
            "correcta": 0, 
            "explicacion": "",
        },
        {
            "pregunta": "Cual es la que menos tolerancia tiene, dentro de las reglas?",
            "opciones": ["A: Acoso laboral", "B: Problemas de salud", "Estado de ebriedad", "Realizar instalacion a un cliente sin aprobración del jefe"],
            "correcta": 0, # Corresponde al "A"
            "explicacion": "Segun corresponde el reglamento, el acoso laboral no esta permitido en ninguna instancia y es la opcion con tolerancia 0",
        },
        {
            "pregunta": "",
            "opciones": [""],
            "correcta": 0, # Corresponde a ""
            "explicacion": "",
        }
    ],
    "lider": [
         {
            "pregunta": "¿Cuál es la principal métrica de éxito del equipo?",
            "opciones": ["Horas trabajadas", "Proyectos entregados a tiempo", "Cantidad de reuniones"],
            "correcta": 1,
            "explicacion": "Medimos la eficiencia por los proyectos entregados a tiempo.",
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
    # NUEVO: Creamos una lista vacía para guardar el historial de respuestas
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
        return redirect(url_for('resultado'))

    pregunta_actual = preguntas_rol[session['pregunta_actual']]

    if request.method == 'POST':
        respuesta_idx = int(request.form.get('opcion'))
        
        # Evaluamos si acertó o falló
        es_correcta = (respuesta_idx == pregunta_actual['correcta'])
        if es_correcta:
            session['puntaje'] += 1
            
        # NUEVO: Guardamos el detalle de esta jugada
        registro = {
            "pregunta": pregunta_actual["pregunta"],
            "tu_respuesta": pregunta_actual["opciones"][respuesta_idx],
            "respuesta_correcta": pregunta_actual["opciones"][pregunta_actual["correcta"]],
            "es_correcta": es_correcta,
            "explicacion": pregunta_actual.get("explicacion", "")
        }
        
        # Recuperamos la lista de la memoria, agregamos el registro y lo volvemos a guardar
        historial = session.get('historial', [])
        historial.append(registro)
        session['historial'] = historial
            
        session['pregunta_actual'] += 1
        return redirect(url_for('pregunta'))

    return render_template('pregunta.html', pregunta=pregunta_actual)

# RUTA 4: Resultados
@app.route('/resultado')
def resultado():
    if 'rol' not in session: return redirect(url_for('index'))
    
    puntaje = session.get('puntaje', 0)
    total = len(PREGUNTAS.get(session['rol'], []))
    
    # NUEVO: Extraemos el historial para enviarlo al HTML
    historial = session.get('historial', []) 
    
    return render_template('resultado.html', puntaje=puntaje, total=total, historial=historial)
if __name__ == '__main__':
    app.run(debug=True)
