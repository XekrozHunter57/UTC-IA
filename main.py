import sqlite3
import threading
from datetime import datetime

from kivy.app import App
from kivy.clock import Clock
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.metrics import dp
from kivy.core.window import Window

from google import genai


# =========================================================
# CONFIGURACIÓN GENERAL
# =========================================================

APP_NAME = "UTC-IA"
APP_VERSION = "1.1"

DB_NAME = "utc_ia.db"

API_KEY = "TU API AQUI"


# =========================================================
# COLORES
# =========================================================

AZUL = (0.05, 0.25, 0.55, 1)
AZUL_CLARO = (0.90, 0.94, 1, 1)
BLANCO = (1, 1, 1, 1)
NEGRO = (0.08, 0.08, 0.08, 1)
GRIS = (0.45, 0.45, 0.45, 1)

Window.clearcolor = BLANCO


# =========================================================
# CONFIGURACIÓN DE GEMINI
# =========================================================

cliente = None

if API_KEY and API_KEY != "TU API AQUI":

    try:

        cliente = genai.Client(
            api_key=API_KEY
        )

    except Exception:

        cliente = None


# =========================================================
# BASE DE DATOS SQLITE
# =========================================================

def obtener_conexion():

    return sqlite3.connect(
        DB_NAME,
        check_same_thread=False
    )


def inicializar_base_datos():

    conexion = obtener_conexion()
    cursor = conexion.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS consultas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            estudiante TEXT,
            asignatura TEXT,
            tipo_consulta TEXT,
            pregunta TEXT,
            respuesta TEXT,
            fecha TEXT,
            valoracion TEXT
        )
    """)

    conexion.commit()
    conexion.close()


inicializar_base_datos()


# =========================================================
# GUARDAR CONSULTA
# =========================================================

def guardar_consulta(
    estudiante,
    asignatura,
    tipo_consulta,
    pregunta,
    respuesta
):

    conexion = obtener_conexion()
    cursor = conexion.cursor()

    fecha = datetime.now().strftime(
        "%d/%m/%Y %H:%M"
    )

    cursor.execute("""
        INSERT INTO consultas
        (
            estudiante,
            asignatura,
            tipo_consulta,
            pregunta,
            respuesta,
            fecha,
            valoracion
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        estudiante,
        asignatura,
        tipo_consulta,
        pregunta,
        respuesta,
        fecha,
        None
    ))

    consulta_id = cursor.lastrowid

    conexion.commit()
    conexion.close()

    return consulta_id


# =========================================================
# GUARDAR VALORACIÓN
# =========================================================

def guardar_valoracion(
    consulta_id,
    valoracion
):

    conexion = obtener_conexion()
    cursor = conexion.cursor()

    cursor.execute("""
        UPDATE consultas
        SET valoracion = ?
        WHERE id = ?
    """, (
        valoracion,
        consulta_id
    ))

    conexion.commit()
    conexion.close()


# =========================================================
# OBTENER CONSULTA
# =========================================================

def obtener_consulta(
    consulta_id
):

    conexion = obtener_conexion()
    cursor = conexion.cursor()

    cursor.execute("""
        SELECT
            id,
            estudiante,
            asignatura,
            tipo_consulta,
            pregunta,
            respuesta,
            fecha,
            valoracion
        FROM consultas
        WHERE id = ?
    """, (
        consulta_id,
    ))

    resultado = cursor.fetchone()

    conexion.close()

    return resultado


# =========================================================
# TOTAL CONSULTAS
# =========================================================

def obtener_total_consultas():

    conexion = obtener_conexion()
    cursor = conexion.cursor()

    cursor.execute("""
        SELECT COUNT(*)
        FROM consultas
    """)

    total = cursor.fetchone()[0]

    conexion.close()

    return total


# =========================================================
# TOTAL ESTUDIANTES
# =========================================================

def obtener_total_estudiantes():

    conexion = obtener_conexion()
    cursor = conexion.cursor()

    cursor.execute("""
        SELECT COUNT(DISTINCT estudiante)
        FROM consultas
        WHERE estudiante IS NOT NULL
        AND TRIM(estudiante) != ''
    """)

    total = cursor.fetchone()[0]

    conexion.close()

    return total


# =========================================================
# POR ASIGNATURA
# =========================================================

def obtener_por_asignatura():

    conexion = obtener_conexion()
    cursor = conexion.cursor()

    cursor.execute("""
        SELECT
            asignatura,
            COUNT(*)
        FROM consultas
        GROUP BY asignatura
        ORDER BY COUNT(*) DESC
    """)

    resultado = cursor.fetchall()

    conexion.close()

    return resultado


# =========================================================
# POR TIPO
# =========================================================

def obtener_por_tipo():

    conexion = obtener_conexion()
    cursor = conexion.cursor()

    cursor.execute("""
        SELECT
            tipo_consulta,
            COUNT(*)
        FROM consultas
        GROUP BY tipo_consulta
        ORDER BY COUNT(*) DESC
    """)

    resultado = cursor.fetchall()

    conexion.close()

    return resultado


# =========================================================
# VALORACIONES
# =========================================================

def obtener_valoraciones():

    conexion = obtener_conexion()
    cursor = conexion.cursor()

    cursor.execute("""
        SELECT
            COALESCE(valoracion, 'No especificada'),
            COUNT(*)
        FROM consultas
        GROUP BY COALESCE(valoracion, 'No especificada')
    """)

    resultado = cursor.fetchall()

    conexion.close()

    return resultado


# =========================================================
# PORCENTAJE DE UTILIDAD
# =========================================================

def obtener_porcentaje_utilidad():

    conexion = obtener_conexion()
    cursor = conexion.cursor()

    cursor.execute("""
        SELECT COUNT(*)
        FROM consultas
        WHERE valoracion IN ('Sí', 'No')
    """)

    total_valoradas = cursor.fetchone()[0]

    if total_valoradas == 0:

        conexion.close()

        return 0

    cursor.execute("""
        SELECT COUNT(*)
        FROM consultas
        WHERE valoracion = 'Sí'
    """)

    positivas = cursor.fetchone()[0]

    conexion.close()

    porcentaje = (
        positivas / total_valoradas
    ) * 100

    return round(
        porcentaje,
        1
    )


# =========================================================
# ÚLTIMAS CONSULTAS
# =========================================================

def obtener_ultimas_consultas(
    limite=5
):

    conexion = obtener_conexion()
    cursor = conexion.cursor()

    cursor.execute("""
        SELECT
            id,
            estudiante,
            asignatura,
            tipo_consulta,
            pregunta,
            fecha
        FROM consultas
        ORDER BY id DESC
        LIMIT ?
    """, (
        limite,
    ))

    resultado = cursor.fetchall()

    conexion.close()

    return resultado


# =========================================================
# HISTORIAL
# =========================================================

def obtener_historial():

    conexion = obtener_conexion()
    cursor = conexion.cursor()

    cursor.execute("""
        SELECT
            id,
            estudiante,
            asignatura,
            tipo_consulta,
            pregunta,
            fecha
        FROM consultas
        ORDER BY id DESC
    """)

    resultado = cursor.fetchall()

    conexion.close()

    return resultado


# =========================================================
# VALIDACIÓN
# =========================================================

def validar_consulta(
    nombre,
    asignatura,
    tipo,
    pregunta
):

    nombre = nombre.strip()
    asignatura = asignatura.strip()
    tipo = tipo.strip()
    pregunta = pregunta.strip()

    if not nombre:

        return False, (
            "Ingrese el nombre del estudiante."
        )

    if not asignatura:

        return False, (
            "Ingrese la asignatura."
        )

    if not tipo or tipo == "Seleccionar tipo de consulta":

        return False, (
            "Seleccione el tipo de consulta."
        )

    if not pregunta:

        return False, (
            "Escriba la pregunta que desea realizar."
        )

    if len(pregunta) < 3:

        return False, (
            "La pregunta es demasiado corta."
        )

    return True, ""


# =========================================================
# TÍTULO
# =========================================================

def crear_titulo(texto):

    return Label(
        text=texto,
        font_size="22sp",
        bold=True,
        color=AZUL,
        size_hint_y=None,
        height=dp(58)
    )


# =========================================================
# BOTÓN
# =========================================================

def crear_boton(
    texto,
    funcion
):

    boton = Button(
        text=texto,
        size_hint_y=None,
        height=dp(52),
        font_size="16sp",
        bold=True,
        color=BLANCO,
        background_normal="",
        background_color=AZUL
    )

    boton.bind(
        on_release=funcion
    )

    return boton


# =========================================================
# PANTALLA DE INICIO
# =========================================================

class Inicio(Screen):

    def __init__(self, **kwargs):

        super().__init__(**kwargs)

        layout = BoxLayout(
            orientation="vertical",
            padding=dp(20),
            spacing=dp(14)
        )

        layout.add_widget(
            Label(
                text="UTC-IA",
                font_size="34sp",
                bold=True,
                color=AZUL,
                size_hint_y=None,
                height=dp(65)
            )
        )

        layout.add_widget(
            Label(
                text="Asistente Académico Inteligente",
                font_size="18sp",
                bold=True,
                color=NEGRO,
                size_hint_y=None,
                height=dp(42)
            )
        )

        subtitulo = Label(
            text=(
                "Sistema de apoyo al aprendizaje "
                "mediante Inteligencia Artificial"
            ),
            color=GRIS,
            halign="center",
            valign="middle"
        )

        subtitulo.bind(
            size=lambda instance, value:
            setattr(
                instance,
                "text_size",
                (instance.width - dp(10), None)
            )
        )

        layout.add_widget(
            subtitulo
        )

        layout.add_widget(
            crear_boton(
                "📝  Nueva consulta",
                self.nueva_consulta
            )
        )

        layout.add_widget(
            crear_boton(
                "📚  Historial",
                self.historial
            )
        )

        layout.add_widget(
            crear_boton(
                "📊  Estadísticas",
                self.estadisticas
            )
        )

        layout.add_widget(
            crear_boton(
                "⚙️  Configuración",
                self.configuracion
            )
        )

        layout.add_widget(
            Label(
                text="UTC-IA • Prototipo académico",
                color=GRIS,
                size_hint_y=None,
                height=dp(40)
            )
        )

        self.add_widget(layout)


    def nueva_consulta(self, instance):

        self.manager.current = "nueva"


    def historial(self, instance):

        self.manager.get_screen(
            "historial"
        ).cargar_historial()

        self.manager.current = "historial"


    def estadisticas(self, instance):

        self.manager.get_screen(
            "estadisticas"
        ).cargar_estadisticas()

        self.manager.current = "estadisticas"


    def configuracion(self, instance):

        pantalla = self.manager.get_screen(
            "configuracion"
        )

        pantalla.actualizar_estado()

        self.manager.current = "configuracion"


# =========================================================
# NUEVA CONSULTA
# =========================================================

class NuevaConsulta(Screen):

    def __init__(self, **kwargs):

        super().__init__(**kwargs)

        layout = BoxLayout(
            orientation="vertical",
            padding=dp(15),
            spacing=dp(10)
        )

        layout.add_widget(
            crear_titulo(
                "📝 NUEVA CONSULTA"
            )
        )

        self.nombre = TextInput(
            hint_text="Nombre del estudiante",
            multiline=False,
            size_hint_y=None,
            height=dp(48),
            background_color=BLANCO,
            foreground_color=NEGRO
        )

        self.asignatura = TextInput(
            hint_text="Asignatura",
            multiline=False,
            size_hint_y=None,
            height=dp(48),
            background_color=BLANCO,
            foreground_color=NEGRO
        )

        self.tipo = Spinner(
            text="Seleccionar tipo de consulta",
            values=[
                "Explicación",
                "Ejercicio",
                "Investigación",
                "Concepto",
                "Otro"
            ],
            size_hint_y=None,
            height=dp(48),
            background_normal="",
            background_color=AZUL,
            color=BLANCO
        )

        self.pregunta = TextInput(
            hint_text="Escriba aquí su pregunta...",
            multiline=True,
            background_color=BLANCO,
            foreground_color=NEGRO
        )

        layout.add_widget(self.nombre)
        layout.add_widget(self.asignatura)
        layout.add_widget(self.tipo)
        layout.add_widget(self.pregunta)

        layout.add_widget(
            crear_boton(
                "🤖  CONSULTAR A UTC-IA",
                self.consultar
            )
        )

        layout.add_widget(
            crear_boton(
                "⬅️  Regresar",
                self.regresar
            )
        )

        self.add_widget(layout)


    def consultar(self, instance):

        nombre = self.nombre.text.strip()
        asignatura = self.asignatura.text.strip()
        tipo = self.tipo.text.strip()
        pregunta = self.pregunta.text.strip()

        valido, mensaje = validar_consulta(
            nombre,
            asignatura,
            tipo,
            pregunta
        )

        if not valido:

            self.mostrar_aviso(
                "⚠️ Campo requerido",
                mensaje
            )

            return

        pantalla = self.manager.get_screen(
            "procesando"
        )

        pantalla.iniciar()

        self.manager.current = "procesando"

        hilo = threading.Thread(
            target=self.consultar_gemini,
            args=(
                nombre,
                asignatura,
                tipo,
                pregunta
            ),
            daemon=True
        )

        hilo.start()


    def consultar_gemini(
        self,
        nombre,
        asignatura,
        tipo,
        pregunta
    ):

        try:

            if cliente is None:

                Clock.schedule_once(
                    lambda dt:
                    self.mostrar_error(
                        "⚠️ API NO CONFIGURADA\n\n"
                        "UTC-IA está preparado para conectarse "
                        "con Gemini, pero todavía no existe "
                        "una API Key con cuota disponible."
                    ),
                    0
                )

                return


            instruccion = f"""
Actúa como UTC-IA, un asistente académico
para estudiantes universitarios.

Estudiante: {nombre}
Asignatura: {asignatura}
Tipo de consulta: {tipo}

Pregunta:
{pregunta}

INSTRUCCIONES:

1. Responde directamente la pregunta.

2. Explica de manera clara, académica,
comprensible y ordenada.

3. Mantén la respuesta enfocada
en la consulta realizada.

4. Si es un ejercicio, explica el procedimiento
paso a paso para favorecer el aprendizaje.

5. Si es un concepto, proporciona una definición
clara y posteriormente su explicación.

6. Si es una investigación, organiza la información
mediante apartados cuando sea necesario.

7. No inventes datos ni fuentes.

8. Si la información proporcionada no es suficiente,
indícalo claramente.

9. La inteligencia artificial debe apoyar
el aprendizaje y no sustituir el esfuerzo
académico del estudiante.

10. No agregues saludos.

11. No agregues despedidas.

12. No agregues frases motivacionales.

13. No escribas frases como:
"mucho éxito en tus estudios",
"espero haberte ayudado",
"sigue adelante",
"éxitos",
o expresiones similares.

14. No agregues información que no esté
relacionada directamente con la pregunta.

15. Utiliza un tono académico,
neutral y profesional.

16. Utiliza ejemplos cuando ayuden
a comprender el contenido.

17. Cuando la respuesta requiera varios puntos,
utiliza una estructura ordenada.

18. No finalices prematuramente.
Desarrolla todos los puntos necesarios
para responder completamente.

19. Termina únicamente después de haber
respondido la consulta.
"""
            # =================================================
            # CONSULTAR GEMINI
            # =================================================

            respuesta_ia = cliente.interactions.create(
                model="gemini-3.8-flash",
                input=instruccion
            )

            respuesta = respuesta_ia.output_text


            # =================================================
            # VALIDAR RESPUESTA
            # =================================================

            if not respuesta:

                raise Exception(
                    "Gemini no devolvió contenido."
                )


            respuesta = respuesta.strip()


            # =================================================
            # GUARDAR SQLITE
            # =================================================

            consulta_id = guardar_consulta(
                nombre,
                asignatura,
                tipo,
                pregunta,
                respuesta
            )


            Clock.schedule_once(
                lambda dt:
                self.mostrar_respuesta(
                    consulta_id
                ),
                0
            )


        except Exception as error:

            mensaje = str(error)

            if (
                "429" in mensaje
                or
                "Rate limit exceeded" in mensaje
                or
                "quota" in mensaje.lower()
            ):

                texto = (
                    "⚠️ SERVICIO NO DISPONIBLE\n\n"
                    "Gemini alcanzó el límite de consultas "
                    "o no existe cuota disponible "
                    "para este proyecto.\n\n"
                    "Inténtelo nuevamente más tarde."
                )

            else:

                texto = (
                    "⚠️ NO SE PUDO OBTENER UNA RESPUESTA\n\n"
                    "Revise la conexión a Internet "
                    "o la configuración del servicio."
                )


            Clock.schedule_once(
                lambda dt:
                self.mostrar_error(texto),
                0
            )


    def mostrar_respuesta(
        self,
        consulta_id
    ):

        pantalla = self.manager.get_screen(
            "respuesta"
        )

        pantalla.cargar(
            consulta_id
        )

        self.manager.current = "respuesta"


    def mostrar_error(
        self,
        mensaje
    ):

        pantalla = self.manager.get_screen(
            "error"
        )

        pantalla.mensaje.text = mensaje

        self.manager.current = "error"


    def mostrar_aviso(
        self,
        titulo,
        mensaje
    ):

        contenido = BoxLayout(
            orientation="vertical",
            padding=dp(15),
            spacing=dp(10)
        )

        contenido.add_widget(
            Label(
                text=mensaje,
                halign="center",
                color=NEGRO
            )
        )

        boton = Button(
            text="Aceptar",
            size_hint_y=None,
            height=dp(45),
            color=BLANCO,
            background_normal="",
            background_color=AZUL
        )

        contenido.add_widget(
            boton
        )

        popup = Popup(
            title=titulo,
            content=contenido,
            size_hint=(0.85, 0.35)
        )

        boton.bind(
            on_release=popup.dismiss
        )

        popup.open()


    def regresar(
        self,
        instance
    ):

        self.manager.current = "inicio"


# =========================================================
# PROCESANDO
# =========================================================

class Procesando(Screen):

    def __init__(self, **kwargs):

        super().__init__(**kwargs)

        layout = BoxLayout(
            orientation="vertical",
            padding=dp(30),
            spacing=dp(20)
        )

        layout.add_widget(
            Label(
                text="UTC-IA",
                font_size="30sp",
                bold=True,
                color=AZUL
            )
        )

        self.estado = Label(
            text="⏳ Procesando consulta...",
            font_size="18sp",
            color=NEGRO,
            halign="center"
        )

        layout.add_widget(
            self.estado
        )

        layout.add_widget(
            Label(
                text=(
                    "Espere mientras UTC-IA "
                    "procesa la información."
                ),
                color=GRIS,
                halign="center"
            )
        )

        self.add_widget(layout)


    def iniciar(self):

        self.estado.text = (
            "⏳ Procesando consulta..."
        )


# =========================================================
# RESPUESTA DE IA
# =========================================================

class RespuestaIA(Screen):

    def __init__(self, **kwargs):

        super().__init__(**kwargs)

        layout = BoxLayout(
            orientation="vertical",
            padding=dp(12),
            spacing=dp(8)
        )

        layout.add_widget(
            crear_titulo(
                "🤖 RESPUESTA DE UTC-IA"
            )
        )


        # -------------------------------------------------
        # SCROLL DE RESPUESTA
        # -------------------------------------------------

        self.scroll_respuesta = ScrollView(
            do_scroll_x=False,
            do_scroll_y=True,
            bar_width=dp(8),
            bar_color=AZUL,
            bar_inactive_color=AZUL_CLARO,
            scroll_type=[
                "bars",
                "content"
            ]
        )


        self.respuesta = Label(
            text="",
            color=NEGRO,
            halign="left",
            valign="top",
            size_hint_y=None,
            padding=(dp(8), dp(8))
        )


        self.respuesta.bind(
            width=lambda instance, value:
            setattr(
                instance,
                "text_size",
                (value - dp(16), None)
            )
        )


        self.respuesta.bind(
            texture_size=lambda instance, value:
            setattr(
                instance,
                "height",
                max(value[1] + dp(16), dp(100))
            )
        )


        self.scroll_respuesta.add_widget(
            self.respuesta
        )


        layout.add_widget(
            self.scroll_respuesta
        )


        layout.add_widget(
            Label(
                text="¿La respuesta fue útil?",
                color=NEGRO,
                size_hint_y=None,
                height=dp(35)
            )
        )


        botones = BoxLayout(
            size_hint_y=None,
            height=dp(48),
            spacing=dp(8)
        )


        boton_si = Button(
            text="👍 Sí",
            color=BLANCO,
            background_normal="",
            background_color=AZUL
        )


        boton_no = Button(
            text="👎 No",
            color=BLANCO,
            background_normal="",
            background_color=AZUL
        )


        boton_si.bind(
            on_release=lambda x:
            self.valorar("Sí")
        )


        boton_no.bind(
            on_release=lambda x:
            self.valorar("No")
        )


        botones.add_widget(
            boton_si
        )

        botones.add_widget(
            boton_no
        )


        layout.add_widget(
            botones
        )


        self.estado = Label(
            text="",
            color=GRIS,
            size_hint_y=None,
            height=dp(30)
        )


        layout.add_widget(
            self.estado
        )


        layout.add_widget(
            crear_boton(
                "⬅️  Regresar al inicio",
                self.regresar
            )
        )


        self.add_widget(layout)

        self.consulta_id = None


    def cargar(
        self,
        consulta_id
    ):

        self.consulta_id = consulta_id

        registro = obtener_consulta(
            consulta_id
        )


        if not registro:

            self.respuesta.text = (
                "No se encontró la consulta."
            )

            return


        (
            id_,
            estudiante,
            asignatura,
            tipo,
            pregunta,
            respuesta,
            fecha,
            valoracion
        ) = registro


        self.respuesta.text = (
            f"👤 Estudiante: {estudiante}\n\n"
            f"📚 Asignatura: {asignatura}\n"
            f"🧠 Tipo: {tipo}\n"
            f"📅 Fecha: {fecha}\n\n"
            f"❓ Pregunta:\n"
            f"{pregunta}\n\n"
            f"🤖 Respuesta:\n"
            f"{respuesta}"
        )


        self.estado.text = ""


        Clock.schedule_once(
            self.ir_arriba,
            0
        )


        if valoracion:

            self.estado.text = (
                f"Valoración registrada: "
                f"{valoracion}"
            )


    def ir_arriba(self, dt):

        self.scroll_respuesta.scroll_y = 1


    def valorar(
        self,
        valoracion
    ):

        if self.consulta_id is None:

            return


        guardar_valoracion(
            self.consulta_id,
            valoracion
        )


        self.estado.text = (
            "✅ Valoración registrada"
        )


    def regresar(
        self,
        instance
    ):

        self.manager.current = "inicio"


# =========================================================
# ERROR
# =========================================================

class ErrorScreen(Screen):

    def __init__(self, **kwargs):

        super().__init__(**kwargs)

        layout = BoxLayout(
            orientation="vertical",
            padding=dp(25),
            spacing=dp(20)
        )

        layout.add_widget(
            Label(
                text="⚠️ UTC-IA",
                font_size="28sp",
                bold=True,
                color=AZUL
            )
        )

        self.mensaje = Label(
            text="",
            color=NEGRO,
            halign="center",
            valign="middle"
        )

        self.mensaje.bind(
            size=lambda instance, value:
            setattr(
                instance,
                "text_size",
                (instance.width - dp(20), None)
            )
        )

        layout.add_widget(
            self.mensaje
        )

        layout.add_widget(
            crear_boton(
                "⬅️  Regresar",
                self.regresar
            )
        )

        self.add_widget(layout)


    def regresar(
        self,
        instance
    ):

        self.manager.current = "inicio"


# =========================================================
# HISTORIAL
# =========================================================

class Historial(Screen):

    def __init__(self, **kwargs):

        super().__init__(**kwargs)

        layout = BoxLayout(
            orientation="vertical",
            padding=dp(12),
            spacing=dp(8)
        )


        layout.add_widget(
            crear_titulo(
                "📚 HISTORIAL DE CONSULTAS"
            )
        )


        scroll = ScrollView(
            do_scroll_x=False,
            do_scroll_y=True,
            bar_width=dp(8),
            bar_color=AZUL,
            bar_inactive_color=AZUL_CLARO,
            scroll_type=[
                "bars",
                "content"
            ]
        )


        self.contenedor = GridLayout(
            cols=1,
            spacing=dp(10),
            padding=dp(5),
            size_hint_y=None
        )


        self.contenedor.bind(
            minimum_height=self.contenedor.setter(
                "height"
            )
        )


        scroll.add_widget(
            self.contenedor
        )


        layout.add_widget(
            scroll
        )


        layout.add_widget(
            crear_boton(
                "⬅️  Regresar al inicio",
                self.regresar
            )
        )


        self.add_widget(layout)


    def cargar_historial(self):

        self.contenedor.clear_widgets()


        historial = obtener_historial()


        if not historial:

            self.contenedor.add_widget(
                Label(
                    text=(
                        "📭 No existen consultas "
                        "registradas todavía."
                    ),
                    color=GRIS,
                    size_hint_y=None,
                    height=dp(70)
                )
            )

            return


        for registro in historial:

            (
                consulta_id,
                estudiante,
                asignatura,
                tipo,
                pregunta,
                fecha
            ) = registro


            tarjeta = BoxLayout(
                orientation="vertical",
                padding=dp(10),
                spacing=dp(5),
                size_hint_y=None,
                height=dp(180),
            )


            informacion = Label(
                text=(
                    f"👤 {estudiante}\n"
                    f"📚 {asignatura}\n"
                    f"🧠 {tipo}\n"
                    f"📅 {fecha}"
                ),
                color=NEGRO,
                halign="left",
                valign="middle",
                size_hint_y=None,
                height=dp(82)
            )


            tarjeta.add_widget(
                informacion
            )


            pregunta_label = Label(
                text=f"❓ {pregunta}",
                color=NEGRO,
                halign="left",
                valign="top",
                size_hint_y=None
            )


            pregunta_label.bind(
                width=lambda instance, value:
                setattr(
                    instance,
                    "text_size",
                    (value - dp(4), None)
                )
            )


            pregunta_label.bind(
                texture_size=lambda instance, value:
                setattr(
                    instance,
                    "height",
                    max(value[1], dp(45))
                )
            )


            tarjeta.add_widget(
                pregunta_label
            )


            boton = Button(
                text="👁️  Ver respuesta",
                size_hint_y=None,
                height=dp(42),
                color=BLANCO,
                background_normal="",
                background_color=AZUL
            )


            boton.bind(
                on_release=lambda btn,
                cid=consulta_id:
                self.ver_respuesta(cid)
            )


            tarjeta.add_widget(
                boton
            )


            def actualizar_altura(
                instancia,
                valor
            ):

                tarjeta.height = (
                    dp(82)
                    + pregunta_label.height
                    + dp(42)
                    + dp(20)
                )


            pregunta_label.bind(
                height=actualizar_altura
            )


            self.contenedor.add_widget(
                tarjeta
            )


    def ver_respuesta(
        self,
        consulta_id
    ):

        pantalla = self.manager.get_screen(
            "respuesta"
        )


        pantalla.cargar(
            consulta_id
        )


        self.manager.current = "respuesta"


    def regresar(
        self,
        instance
    ):

        self.manager.current = "inicio"
        # =========================================================
# ESTADÍSTICAS
# =========================================================

class Estadisticas(Screen):

    def __init__(self, **kwargs):

        super().__init__(**kwargs)

        layout = BoxLayout(
            orientation="vertical",
            padding=dp(12),
            spacing=dp(8)
        )


        layout.add_widget(
            crear_titulo(
                "📊 ESTADÍSTICAS DEL SISTEMA"
            )
        )


        scroll = ScrollView(
            do_scroll_x=False,
            do_scroll_y=True,
            bar_width=dp(8),
            bar_color=AZUL,
            bar_inactive_color=AZUL_CLARO,
            scroll_type=[
                "bars",
                "content"
            ]
        )


        self.contenedor = BoxLayout(
            orientation="vertical",
            spacing=dp(10),
            padding=dp(5),
            size_hint_y=None
        )


        self.contenedor.bind(
            minimum_height=self.contenedor.setter(
                "height"
            )
        )


        scroll.add_widget(
            self.contenedor
        )


        layout.add_widget(
            scroll
        )


        layout.add_widget(
            crear_boton(
                "⬅️  Regresar al inicio",
                self.regresar
            )
        )


        self.add_widget(layout)


    def cargar_estadisticas(self):

        self.contenedor.clear_widgets()


        total = obtener_total_consultas()

        estudiantes = obtener_total_estudiantes()


        self.agregar_seccion(
            "📌 RESUMEN GENERAL"
        )


        self.agregar_dato(
            f"📚 Total de consultas: {total}"
        )


        self.agregar_dato(
            f"👥 Estudiantes registrados: {estudiantes}"
        )


        self.agregar_seccion(
            "📚 CONSULTAS POR ASIGNATURA"
        )


        asignaturas = obtener_por_asignatura()


        if asignaturas:

            for asignatura, cantidad in asignaturas:

                self.agregar_dato(
                    f"• {asignatura}: {cantidad}"
                )

        else:

            self.agregar_dato(
                "No existen datos."
            )


        self.agregar_seccion(
            "🧠 CONSULTAS POR TIPO"
        )


        tipos = obtener_por_tipo()


        if tipos:

            for tipo, cantidad in tipos:

                self.agregar_dato(
                    f"• {tipo}: {cantidad}"
                )

        else:

            self.agregar_dato(
                "No existen datos."
            )


        self.agregar_seccion(
            "👍 VALORACIONES"
        )


        valoraciones = obtener_valoraciones()


        if valoraciones:

            for valoracion, cantidad in valoraciones:

                self.agregar_dato(
                    f"• {valoracion}: {cantidad}"
                )

        else:

            self.agregar_dato(
                "No existen valoraciones."
            )


        porcentaje = obtener_porcentaje_utilidad()


        self.agregar_seccion(
            "📈 UTILIDAD"
        )


        self.agregar_dato(
            f"Porcentaje de respuestas "
            f"valoradas como útiles: {porcentaje}%"
        )


        self.agregar_seccion(
            "🕐 ÚLTIMAS CONSULTAS"
        )


        ultimas = obtener_ultimas_consultas(5)


        if ultimas:

            for registro in ultimas:

                (
                    consulta_id,
                    estudiante,
                    asignatura,
                    tipo,
                    pregunta,
                    fecha
                ) = registro


                texto = (
                    f"• {fecha}\n"
                    f"  {estudiante} — "
                    f"{asignatura}\n"
                    f"  {tipo}: {pregunta}"
                )


                self.agregar_dato(
                    texto,
                    altura=dp(80)
                )

        else:

            self.agregar_dato(
                "No existen consultas."
            )


    def agregar_seccion(
        self,
        texto
    ):

        self.contenedor.add_widget(
            Label(
                text=texto,
                font_size="18sp",
                bold=True,
                color=AZUL,
                size_hint_y=None,
                height=dp(45)
            )
        )


    def agregar_dato(
        self,
        texto,
        altura=dp(45)
    ):

        self.contenedor.add_widget(
            Label(
                text=texto,
                color=NEGRO,
                halign="left",
                valign="middle",
                size_hint_y=None,
                height=altura
            )
        )


    def regresar(
        self,
        instance
    ):

        self.manager.current = "inicio"


# =========================================================
# CONFIGURACIÓN
# =========================================================

class Configuracion(Screen):

    def __init__(self, **kwargs):

        super().__init__(**kwargs)

        layout = BoxLayout(
            orientation="vertical",
            padding=dp(20),
            spacing=dp(12)
        )


        layout.add_widget(
            crear_titulo(
                "⚙️ CONFIGURACIÓN"
            )
        )


        self.estado_ia = Label(
            text="",
            color=NEGRO,
            halign="center",
            valign="middle",
            size_hint_y=None,
            height=dp(80)
        )


        layout.add_widget(
            self.estado_ia
        )


        layout.add_widget(
            Label(
                text=(
                    "🤖 Sistema de Inteligencia Artificial\n\n"
                    "UTC-IA utiliza Gemini como servicio "
                    "de procesamiento de consultas.\n\n"
                    "La API se encuentra preparada para "
                    "ser configurada cuando exista cuota "
                    "disponible."
                ),
                color=NEGRO,
                halign="center"
            )
        )


        layout.add_widget(
            Label(
                text=(
                    f"📱 Aplicación: {APP_NAME}\n"
                    f"🔢 Versión: {APP_VERSION}\n"
                    f"🗄️ Base de datos: SQLite\n"
                    f"🤖 Motor IA: Gemini"
                ),
                color=GRIS,
                halign="center"
            )
        )


        layout.add_widget(
            crear_boton(
                "⬅️  Regresar al inicio",
                self.regresar
            )
        )


        self.add_widget(
            layout
        )


    def actualizar_estado(self):

        if cliente is not None:

            self.estado_ia.text = (
                "🟢 ESTADO DE IA\n\n"
                "API configurada"
            )

        else:

            self.estado_ia.text = (
                "🟡 ESTADO DE IA\n\n"
                "API pendiente de configuración"
            )


    def regresar(
        self,
        instance
    ):

        self.manager.current = "inicio"


# =========================================================
# ADMINISTRADOR DE PANTALLAS
# =========================================================

class UTCIA(App):

    def build(self):

        self.title = "UTC-IA"


        administrador = ScreenManager()


        administrador.add_widget(
            Inicio(
                name="inicio"
            )
        )


        administrador.add_widget(
            NuevaConsulta(
                name="nueva"
            )
        )


        administrador.add_widget(
            Procesando(
                name="procesando"
            )
        )


        administrador.add_widget(
            RespuestaIA(
                name="respuesta"
            )
        )


        administrador.add_widget(
            ErrorScreen(
                name="error"
            )
        )


        administrador.add_widget(
            Historial(
                name="historial"
            )
        )


        administrador.add_widget(
            Estadisticas(
                name="estadisticas"
            )
        )


        administrador.add_widget(
            Configuracion(
                name="configuracion"
            )
        )


        return administrador


# =========================================================
# EJECUCIÓN
# =========================================================

if __name__ == "__main__":

    UTCIA().run()