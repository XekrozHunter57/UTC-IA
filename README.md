# UTC-IA

Aplicación educativa Android creada con Kivy, SQLite y Google Gemini.

## Compilación recomendada

La compilación debe hacerse en Linux (por ejemplo GitHub Actions), no desde Pydroid3/Termux.

### GitHub Actions

1. Sube este proyecto a un repositorio de GitHub.
2. Abre la pestaña **Actions**.
3. Ejecuta **Build UTC-IA APK** con **Run workflow**.
4. Cuando termine, descarga el artefacto `UTC-IA-debug-apk`.

## API de Gemini

En `main.py` la clave aparece como:

`API_KEY = "TU API AQUI"`

Para una versión real, no conviene publicar una clave personal dentro del código fuente. El proyecto conserva el marcador para que puedas configurarla de forma segura antes de compilar.

## Error original

El proyecto original fallaba durante `hostpython3` con Python 3.13/Termux:

`TypeError: Invalid special arguments: 'env': value None of env key 'PKG_CONFIG_PATH' must be a str`

Por eso esta versión está preparada para un entorno Linux de compilación con Python 3.11 y `PKG_CONFIG_PATH` definido.
