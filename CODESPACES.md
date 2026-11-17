# Probar Fuel Route Optimizer en GitHub Codespaces desde Android

Esta configuración está preparada para el repositorio `AgustinWojtyszyn/fuel-route-optimizer`, rama `main`.

> **Importante:** GitHub Codespaces exige cuota disponible. Si ya agotaste las horas o el almacenamiento gratuitos, GitHub no permite abrir ni crear el entorno sin que se renueve tu cuota o habilites facturación. Este archivo no evita esa restricción.

## Abrir desde el celular

1. En Chrome, abrí https://github.com/AgustinWojtyszyn/fuel-route-optimizer
2. Entrá en **Code → Codespaces → Create codespace on main**. Activá **Sitio para computadoras** si el menú no aparece en Android.
3. Codespaces instalará los paquetes de `requirements.txt`, ejecutará migraciones, importará ciudades y comprobará Django.
4. Al conectarte se iniciará un servidor de desarrollo en el puerto **8000**. En **Ports**, abrí el enlace privado correspondiente.
5. Visitá `/` para la presentación, `/demo/` para el planificador y `/health/` para verificar los datos cargados.

La vista web no requiere introducir tarjetas de crédito en la aplicación. La URL privada del puerto está disponible solamente mientras el Codespace está activo y tu cuenta tiene acceso.

## Importar el CSV de evaluación

El archivo `fuel-prices-for-be-assessment.csv` **no está en el repositorio** y no debe publicarse (contiene datos de precios cuyo permiso de redistribución no está acreditado).

Desde el explorador de archivos de VS Code en el navegador, utilizá **Upload...** para subir el CSV a la carpeta de trabajo del Codespace. Luego, en la terminal:

```bash
python manage.py import_stations ./fuel-prices-for-be-assessment.csv
python manage.py check
```

Si el archivo se llama distinto, adaptá la ruta. Mantenelo fuera de Git y no lo subas al repositorio.

## Activar rutas reales con HeiGIT

Antes de crear el Codespace, guardá tu clave en **GitHub → Settings → Codespaces → Secrets → New secret** con nombre `ORS_API_KEY`, y autorizá este repositorio. Si ya está creado, detenelo y volvé a iniciarlo tras asignar el secreto para que el proceso Django lo reciba.

Si no configurás `ORS_API_KEY`, podrás inspeccionar la interfaz pero no calcular rutas reales. El CSV y la clave son dos requisitos distintos.

## Comprobaciones

```bash
python -m unittest discover -s tests -v
python manage.py test routes -v 1
python manage.py makemigrations --check --dry-run
python manage.py check
```

Para comprobar el proveedor real, con el secreto disponible y el CSV importado:

```bash
python scripts/run_live_checks.py
```

El endpoint `/health/` puede responder 503 mientras el CSV no esté importado o no haya estaciones localizables. Esto no implica que falle la página de presentación.

## Seguridad y costos

- El puerto 8000 se reenvía en modo **privado**.
- La configuración usa `DJANGO_DEBUG=1` solamente para desarrollo privado, no para publicar en producción.
- No subas claves, datos privados ni `db.sqlite3` a GitHub.
- Si tu cuota está agotada, **esta preparación no te dará más horas**. Para probar sin cuota de Codespaces, utilizá Termux o desplegá en Render Free con una estrategia específica para cargar datos sin exponer el CSV.
