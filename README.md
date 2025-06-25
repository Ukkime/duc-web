
# DUC Web Application (Disk Usage Checker)
Small web interface for DUC - https://duc.zevv.nl/

This Flask application lets you scan your system's disk usage using `duc` and visualize the results in a graph directly from your web browser. You can also launch new scans and monitor their status.

---

## ⚠️ IMPORTANT! Security Considerations

This application requires the user running Flask to have `sudo` permissions to execute `duc index` and `duc graph` commands without a password.  
This poses a **significant security risk** if not handled properly.

**Production Recommendations:**

- Restrict `sudo` commands to specific paths.  
- Use a dedicated user with minimal permissions.  
- Implement a task queue system (Celery, Redis Queue) that runs commands under a controlled user.

---

## 1. Requirements

Make sure the following are installed:

- **Python 3**  
  ```bash
  python3 --version
  ```

- **Flask**  
  ```bash
  pip install Flask
  ```

- **DUC (Disk Usage Checker)**  
  ```bash
  sudo apt-get install duc           # Debian/Ubuntu  
  # sudo yum install duc             # CentOS/RHEL  
  # sudo pacman -S duc               # Arch Linux  
  # brew install duc                 # macOS (Homebrew)  
  ```

---

## 2. Configuring `sudoers` (Critical Step!)

Edit the `sudoers` file:

```bash
sudo visudo
```

Add the following line, replacing `<your_user>` with your Linux username:

```bash
<your_user> ALL=(ALL) NOPASSWD: /usr/bin/duc index *, /usr/bin/duc graph *
```

Save and exit:

- In `nano`: Ctrl+X, then `Y` to confirm, and Enter to save.

**Verify the configuration (optional but recommended):**

```bash
sudo duc index /
sudo duc graph -o /tmp/test_duc_graph.png /
```

---

## 3. Application File Setup

Create a file called `app.py` in a directory (e.g., `~/duc_app/`) and paste the provided Python code.

---

## 4. Directory Structure

```plaintext
.
└── app.py
└── static/
    └── graphs/
```

```bash
mkdir -p static/graphs
```

Ensure the user running `app.py` has write permissions in `static/graphs`.

---

## 5. Running the Application

```bash
cd ~/duc_app/
python app.py
```

You will see something like:

```
Flask app started at http://127.0.0.1:8888
Graph directory: /home/your_user/duc_app/static/graphs
Scan log: /home/your_user/duc_app/scan_log.txt
```

---

## 6. Accessing the Web Application

Open your browser and go to: [http://localhost:8888](http://localhost:8888)

From another machine: [http://192.168.X.X:8888](http://192.168.X.X:8888)

---

## 7. Using the Application

### Latest Graph

The most recent graph in `static/graphs` will be shown automatically.

### Launching a New Scan

1. Select a path (e.g., `/`, `/home`, etc.)
2. Click **Start Scan**
3. It will be added to the scan status list.

### Scan Status

- **RUNNING**: scan in progress  
- **FINISHED**: completed successfully  
- **ERROR**: there was an issue (check logs)

### Log Files

`scan_log.txt` logs all `duc` command outputs and errors for debugging.

---

# Aplicación Web DUC (Disk Usage Checker)

Esta aplicación Flask te permite escanear el uso de disco de tu sistema usando `duc` y visualizar los resultados en un gráfico directamente desde tu navegador web. También puedes lanzar nuevos escaneos y ver su estado.

---

## ⚠️ ¡IMPORTANTE! Consideraciones de Seguridad

Esta aplicación requiere que el usuario bajo el que se ejecuta Flask tenga permisos `sudo` para ejecutar los comandos `duc index` y `duc graph` sin pedir contraseña.  
Esto representa un **riesgo de seguridad significativo** si no se gestiona adecuadamente.

**Recomendaciones para producción:**

- Limitar los comandos `sudo` a rutas específicas.  
- Usar un usuario dedicado con permisos mínimos.  
- Implementar un sistema de cola de tareas (Celery, Redis Queue) que ejecute los comandos con un usuario controlado.

---

## 1. Requisitos

Antes de empezar, asegúrate de tener instalado:

- **Python 3**  
  ```bash
  python3 --version
  ```

- **Flask**  
  ```bash
  pip install Flask
  ```

- **DUC (Disk Usage Checker)**  
  ```bash
  sudo apt-get install duc           # Debian/Ubuntu  
  # sudo yum install duc             # CentOS/RHEL  
  # sudo pacman -S duc               # Arch Linux  
  # brew install duc                 # macOS (Homebrew)  
  ```

---

## 2. Configuración de `sudoers` (¡Paso Crítico!)

Edita el archivo `sudoers`:

```bash
sudo visudo
```

Añade la siguiente línea, reemplazando `<tu_usuario>` con tu nombre de usuario:

```bash
<tu_usuario> ALL=(ALL) NOPASSWD: /usr/bin/duc index *, /usr/bin/duc graph *
```

Guarda y sal:

- En `nano`: Ctrl+X, luego `Y` para confirmar, y Enter para guardar.

**Verifica la configuración (opcional):**

```bash
sudo duc index /
sudo duc graph -o /tmp/test_duc_graph.png /
```

---

## 3. Preparación del Archivo de la Aplicación

Crea un archivo `app.py` en un directorio (ej. `~/duc_app/`) y copia el código Python correspondiente.

---

## 4. Estructura de Directorios

```plaintext
.
└── app.py
└── static/
    └── graphs/
```

```bash
mkdir -p static/graphs
```

---

## 5. Ejecución de la Aplicación

```bash
cd ~/duc_app/
python app.py
```

Verás algo como:

```
Aplicación Flask iniciada en http://127.0.0.1:8888
Directorio de gráficos: /home/tu_usuario/duc_app/static/graphs
Log de escaneos: /home/tu_usuario/duc_app/scan_log.txt
```

---

## 6. Acceso a la Aplicación Web

Abre tu navegador en: [http://localhost:8888](http://localhost:8888)

Desde otra máquina: [http://192.168.X.X:8888](http://192.168.X.X:8888)

---

## 7. Uso de la Aplicación

### Gráfico más Reciente

Se muestra automáticamente al cargar la página.

### Lanzar Nuevo Escaneo

1. Selecciona una ruta (ej. `/`, `/home`, etc.)
2. Haz clic en **Iniciar Escaneo**
3. Aparecerá en la lista de estado.

### Estado de los Escaneos

- **RUNNING**: en curso  
- **FINISHED**: completado correctamente  
- **ERROR**: ha fallado (ver logs)

### Archivos de Log

`scan_log.txt` contiene resultados y errores para depuración.
