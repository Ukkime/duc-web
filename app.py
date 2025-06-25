import os
import subprocess
import threading
import datetime
from flask import Flask, render_template_string, request, jsonify, send_from_directory
import socket # Used for printing local IP in __main__

app = Flask(__name__)

# --- Configuration ---
# Directorio donde se guardarán los gráficos generados y los logs de los escaneos
# Asegúrate de que este directorio exista y sea escribible por el usuario de Flask
GRAPH_DIR = os.path.join(os.getcwd(), 'static', 'graphs')
os.makedirs(GRAPH_DIR, exist_ok=True)

# Archivo para guardar el log de los escaneos
SCAN_LOG_FILE = os.path.join(os.getcwd(), 'scan_log.txt')

# Lista para almacenar el estado de los escaneos en curso
# {scan_id: {'thread': thread_obj, 'status': 'running'/'finished'/'error', 'path': 'ruta', 'output_file': 'ruta_grafico', 'error_msg': ''}}
running_scans = {}

# Rutas predefinidas para el desplegable (al menos dos niveles)
# ¡Asegúrate de que estas rutas existan en tu sistema!
SCAN_PATHS = [
    {'display': '/', 'path': '/'},
    {'display': '/home', 'path': '/home'},
    {'display': '/home/administrador', 'path': '/home/administrador'}, # Assuming 'administrador' is a common user directory
    {'display': '/var', 'path': '/var'},
    {'display': '/var/log', 'path': '/var/log'},
    {'display': '/usr', 'path': '/usr'},
    {'display': '/usr/local', 'path': '/usr/local'},
    # Puedes añadir más rutas aquí
]

# --- Funciones de Utilidad ---

def _run_duc_command(command, log_file, error_message):
    """Ejecuta un comando duc y redirige la salida a un archivo de log."""
    try:
        # Usamos `sudo` para `duc index` y `duc graph`
        # Asegúrate de que el usuario de Flask tenga permisos en sudoers (ver advertencia en explicaciones previas)
        process = subprocess.run(command, check=True, capture_output=True, text=True)
        with open(log_file, 'a') as f:
            f.write(f"\n--- {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} --- Comando: {' '.join(command)} ---\n")
            f.write(process.stdout)
            f.write(process.stderr)
            f.write(f"--- Fin Comando ---\n")
        return True, ""
    except subprocess.CalledProcessError as e:
        error_msg = f"{error_message}: Comando '{' '.join(e.cmd)}' falló con código {e.returncode}.\nStdout: {e.stdout}\nStderr: {e.stderr}"
        with open(log_file, 'a') as f:
            f.write(f"\n--- {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} --- ERROR en Comando: {' '.join(command)} ---\n")
            f.write(error_msg)
            f.write(f"--- Fin Error ---\n")
        return False, error_msg
    except Exception as e:
        error_msg = f"Error inesperado al ejecutar duc: {e}"
        with open(log_file, 'a') as f:
            f.write(f"\n--- {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} --- ERROR Inesperado: {' '.join(command)} ---\n")
            f.write(error_msg)
            f.write(f"--- Fin Error ---\n")
        return False, error_msg

def _scan_disk_task(scan_id, scan_path, output_filename):
    """
    Función que ejecuta el escaneo de disco en un hilo separado.
    """
    error_msg = ""
    graph_path = os.path.join(GRAPH_DIR, output_filename)

    try:
        # 1. Ejecutar duc index
        app.logger.info(f"[{scan_id}] Iniciando duc index para: {scan_path}")
        index_command = ['sudo', 'duc', 'index', scan_path]
        index_success, error_msg = _run_duc_command(index_command, SCAN_LOG_FILE, "Error al indexar con duc")

        if index_success:
            app.logger.info(f"[{scan_id}] duc index completado para: {scan_path}. Generando gráfico...")
            # 2. Generar duc graph
            graph_command = ['sudo', 'duc', 'graph', '-o', graph_path, scan_path]
            graph_success, error_msg = _run_duc_command(graph_command, SCAN_LOG_FILE, "Error al generar gráfico con duc")

            if graph_success:
                app.logger.info(f"[{scan_id}] Gráfico generado exitosamente: {graph_path}")
                running_scans[scan_id]['status'] = 'finished'
                running_scans[scan_id]['output_file'] = output_filename
            else:
                app.logger.error(f"[{scan_id}] ERROR al generar gráfico para {scan_path}: {error_msg}")
                running_scans[scan_id]['status'] = 'error'
                running_scans[scan_id]['error_msg'] = error_msg
        else:
            app.logger.error(f"[{scan_id}] ERROR al indexar para {scan_path}: {error_msg}")
            running_scans[scan_id]['status'] = 'error'
            running_scans[scan_id]['error_msg'] = error_msg

    except Exception as e:
        error_msg = f"Excepción inesperada en _scan_disk_task: {e}"
        app.logger.error(f"[{scan_id}] {error_msg}")
        running_scans[scan_id]['status'] = 'error'
        running_scans[scan_id]['error_msg'] = error_msg

# --- Flask Routes ---

# HTML content with embedded CSS and JavaScript
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Disk Usage Analyzer with DUC</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background-color: #f4f4f4; color: #333; }
        .container { max-width: 900px; margin: auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 0 10px rgba(0, 0, 0, 0.1); }
        h1, h2 { color: #0056b3; }
        .form-section, .status-section, .graph-section { margin-bottom: 30px; padding: 15px; border: 1px solid #ddd; border-radius: 5px; background-color: #fff; }
        label { display: block; margin-bottom: 5px; font-weight: bold; }
        select, button { padding: 10px; border-radius: 4px; border: 1px solid #ddd; margin-right: 10px; }
        button { background-color: #007bff; color: white; cursor: pointer; border: none; }
        button:hover { background-color: #0056b3; }
        #scan-status-list { list-style: none; padding: 0; }
        #scan-status-list li { background-color: #e9e9e9; margin-bottom: 8px; padding: 10px; border-radius: 4px; display: flex; flex-wrap: wrap; justify-content: space-between; align-items: center; }
        #scan-status-list li span { margin-right: 15px; }
        .status-running { color: orange; font-weight: bold; }
        .status-finished { color: green; font-weight: bold; }
        .status-error { color: red; font-weight: bold; }
        #latest-graph-container { text-align: center; margin-top: 20px; }
        #latest-graph { max-width: 100%; height: auto; border: 1px solid #ccc; }
        .error-message { color: red; font-size: 0.9em; margin-top: 5px; width: 100%; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Disk Usage Analyzer with DUC</h1>

        <div class="form-section">
            <h2>Launch New Scan</h2>
            <form id="scan-form">
                <label for="scan_path">Select path to scan:</label>
                <select id="scan_path" name="scan_path">
                    {% for path_info in scan_paths %}
                        <option value="{{ path_info.path }}">{{ path_info.display }}</option>
                    {% endfor %}
                </select>
                <button type="submit">Start Scan</button>
            </form>
            <div id="scan-message" style="margin-top: 10px;"></div>
        </div>

        <div class="status-section">
            <h2>Scan Status</h2>
            <ul id="scan-status-list">
                </ul>
        </div>

        <div class="graph-section">
            <h2>Most Recent Disk Usage Graph</h2>
            <div id="latest-graph-container">
                {% if latest_graph %}
                    <img id="latest-graph" src="{{ url_for('serve_graph', filename=latest_graph) }}?_t={{ now_timestamp }}" alt="Disk Usage Graph">
                {% else %}
                    <p>No graphs available. Launch a scan to generate one!</p>
                {% endif %}
            </div>
        </div>
    </div>

    <script>
        const scanForm = document.getElementById('scan-form');
        const scanMessage = document.getElementById('scan-message');
        const scanStatusList = document.getElementById('scan-status-list');
        const latestGraphContainer = document.getElementById('latest-graph-container');

        // Function to update scan status
        async function updateScanStatus() {
            try {
                const response = await fetch('/scan_status');
                const scans = await response.json();

                scanStatusList.innerHTML = ''; // Clear current list
                let foundLatestGraph = false;
                // Get filename without query param for comparison
                let currentLatestGraphFilename = latestGraphContainer.querySelector('#latest-graph')?.src.split('/').pop().split('?')[0];

                // Iterate over scans in reverse order to prioritize most recent ones
                for (let i = scans.length - 1; i >= 0; i--) {
                    const scan = scans[i];
                    const li = document.createElement('li');
                    let statusClass = '';
                    if (scan.status === 'running') {
                        statusClass = 'status-running';
                    } else if (scan.status === 'finished') {
                        statusClass = 'status-finished';
                    } else if (scan.status === 'error') {
                        statusClass = 'status-error';
                    }

                    li.innerHTML = `
                        <span>Scan ID: <strong>${scan.id.substring(0, 15)}...</strong></span>
                        <span>Path: <strong>${scan.path}</strong></span>
                        <span>Status: <span class="${statusClass}">${scan.status.toUpperCase()}</span></span>
                        ${scan.error_msg ? `<div class="error-message">Error: ${scan.error_msg}</div>` : ''}
                    `;
                    scanStatusList.prepend(li); // Add to the beginning so most recent are at the top

                    // If a scan has finished and we haven't found a more recent graph yet, update
                    if (scan.status === 'finished' && scan.output_file && !foundLatestGraph) {
                        // Add cache busting here!
                        const newGraphSrc = `/static/graphs/${scan.output_file}?_t=${new Date().getTime()}`;
                        if (currentLatestGraphFilename !== scan.output_file) {
                            latestGraphContainer.innerHTML = `<img id="latest-graph" src="${newGraphSrc}" alt="Disk Usage Graph">`;
                            currentLatestGraphFilename = scan.output_file; // Update the current graph filename
                        }
                        foundLatestGraph = true; // We found and potentially updated with the most recent
                    }
                }
                // If after checking all scans, there's no graph, show message
                if (!foundLatestGraph && !latestGraphContainer.querySelector('#latest-graph')) {
                     latestGraphContainer.innerHTML = '<p>No graphs available. Launch a scan to generate one!</p>';
                }

            } catch (error) {
                console.error('Error fetching scan status:', error);
            }
        }

        // Submit scan form
        scanForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const formData = new FormData(scanForm);
            const scanPath = formData.get('scan_path');

            scanMessage.textContent = 'Starting scan...';
            scanMessage.style.color = 'blue';

            try {
                const response = await fetch('/scan', {
                    method: 'POST',
                    body: formData
                });
                const result = await response.json();

                if (result.status === 'scan_started') {
                    scanMessage.textContent = result.message;
                    scanMessage.style.color = 'green';
                    updateScanStatus(); // Update status immediately
                } else {
                    scanMessage.textContent = `Error: ${result.message}`;
                    scanMessage.style.color = 'red';
                }
            } catch (error) {
                scanMessage.textContent = `Error connecting to server: ${error}`;
                scanMessage.style.color = 'red';
                console.error('Error:', error);
            }
        });

        // Update scan status every 5 seconds
        setInterval(updateScanStatus, 5000);

        // Update status on page load for the first time
        document.addEventListener('DOMContentLoaded', updateScanStatus);
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    """Main route that displays the most recent graph and the form for new scans."""
    # Find the most recent graph
    latest_graph = None
    graph_files = [f for f in os.listdir(GRAPH_DIR) if f.endswith('.png')]
    if graph_files:
        # Sort by modification date to find the most recent
        graph_files.sort(key=lambda x: os.path.getmtime(os.path.join(GRAPH_DIR, x)), reverse=True)
        latest_graph = graph_files[0]

    # Pass a timestamp to the template for the initial image loading to ensure fresh load
    now_timestamp = datetime.datetime.now().timestamp() * 1000 # Convert to milliseconds for JS compatibility

    # Use render_template_string to render HTML from a string
    return render_template_string(HTML_TEMPLATE,
                                  latest_graph=latest_graph,
                                  scan_paths=SCAN_PATHS,
                                  now_timestamp=int(now_timestamp)) # Pass as integer

@app.route('/scan', methods=['POST'])
def start_scan():
    """Launches a new disk scan."""
    scan_path = request.form.get('scan_path', '/')
    if not os.path.exists(scan_path):
        return jsonify({'status': 'error', 'message': f'The path {scan_path} does not exist.'}), 400

    # Generate a unique ID for this scan
    # Use timestamp and a portion of the path for the ID
    scan_id = datetime.datetime.now().strftime("%Y%m%d%H%M%S") + "_" + scan_path.replace('/', '_').strip('_').replace('.', '_')
    output_filename = f"disk_usage_{scan_id}.png"

    # Start the scan in a separate thread
    scan_thread = threading.Thread(target=_scan_disk_task, args=(scan_id, scan_path, output_filename))
    scan_thread.daemon = True # Allows the program to exit even if the thread is running
    scan_thread.start()

    running_scans[scan_id] = {
        'thread': scan_thread,
        'status': 'running',
        'path': scan_path,
        'output_file': None, # Will be updated when finished
        'error_msg': ''
    }

    return jsonify({'status': 'scan_started', 'scan_id': scan_id, 'message': f'Scan initiated for {scan_path}.'})

@app.route('/scan_status')
def get_scan_status():
    """Returns the status of ongoing scans."""
    status_list = []
    # Use list() to copy keys, avoiding issues if running_scans is modified during iteration
    for scan_id in list(running_scans.keys()):
        data = running_scans[scan_id]

        # Clean up references to finished threads and handle final status
        if not data['thread'].is_alive() and data['status'] == 'running':
            # If the thread is not alive and still in 'running', it means it finished
            # but the main thread hasn't yet updated its status to 'finished' or 'error'.
            # This can happen if the thread completes right between checks.
            # Ideally, _scan_disk_task should have set the final status.
            # For robustness, you can add a check for `data['error_msg']` here
            # to see if _scan_disk_task has already marked an error.
            if not data['error_msg']: # If no error message, assume it finished successfully
                 data['status'] = 'finished'
            else: # If there's an error message, it's an error
                 data['status'] = 'error'

        status_list.append({
            'id': scan_id,
            'path': data['path'],
            'status': data['status'],
            'output_file': data['output_file'],
            'error_msg': data['error_msg']
        })

        # Optional: Remove finished scans to avoid accumulating too many in memory
        # Only do this if you don't need the full history in the interface.
        # if data['status'] == 'finished' or data['status'] == 'error':
        #     del running_scans[scan_id]

    # Sort the list by ID (which contains the timestamp) to show most recent first
    status_list.sort(key=lambda x: x['id'], reverse=True)
    return jsonify(status_list)

@app.route('/static/graphs/<filename>')
def serve_graph(filename):
    """Serves graph files."""
    return send_from_directory(GRAPH_DIR, filename)

if __name__ == '__main__':
    # Get local IP for user display
    try:
        # This is for informational purposes only when starting the app.
        # It may not work in all complex network environments.
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
    except Exception:
        local_ip = "127.0.0.1 (or your network IP)"

    print(f"Flask application started at http://{local_ip}:8888")
    print(f"Graph directory: {GRAPH_DIR}")
    print(f"Scan log file: {SCAN_LOG_FILE}")
    print("\nIMPORTANT! Ensure the user running this application has sudo permissions for 'duc index' and 'duc graph' WITHOUT PASSWORD PROMPT.")
    print("Example in /etc/sudoers (using 'sudo visudo'):")
    print(f"  <your_user> ALL=(ALL) NOPASSWD: /usr/bin/duc index *, /usr/bin/duc graph *")
    print("-" * 50)

    app.run(host='0.0.0.0', port=8888, debug=True) # debug=True for development, set to False in production