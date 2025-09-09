# Importation des modules Flask nécessaires
from flask import Flask, render_template, request, jsonify, send_file   # Pour le serveur web et les API
from flask_socketio import SocketIO  # Pour la communication en temps réel
from datetime import datetime, timedelta
import json
import os
from collections import deque # Pour stocker l'historique des données
import statistics # Pour les calculs statistiques
import csv
import io
from datetime import datetime

# Initialisation de l'application Flask
app = Flask(__name__)  
app.config['SECRET_KEY'] = 'cle_secrete_de_mon_projet_iot'

# Configuration SocketIO
socketio = SocketIO(
    app,
    cors_allowed_origins="*", 
    async_mode='threading',
    logger=True,  # Activer les logs pour debug
    engineio_logger=True
)

# Configuration des fichiers de données
DATA_FILE = 'iot_data.json'
ALERTS_FILE = 'alerts_config.json'

# Stockage des données en mémoire (les 1000 dernières mesures)
sensor_history = deque(maxlen=1000)

# Données capteur actuelles
latest_data = {
    'temperature': None,
    'humidity': None,
    'timestamp': None
}

# État de la LED (éteinte par défaut)
led_state = False

# Configuration des alertes par défaut
default_alerts_config = {
    'temperature_min': 15.0,
    'temperature_max': 35.0,
    'humidity_min': 30.0,
    'humidity_max': 80.0,
    'alerts_enabled': True
}

# Charger la configuration des alertes
def load_alerts_config():
    if os.path.exists(ALERTS_FILE):
        try:
            with open(ALERTS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return default_alerts_config.copy()

# Sauvegarder la configuration des alertes
def save_alerts_config(config):
    try:
        with open(ALERTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2)
    except Exception as e:
        print(f"Erreur sauvegarde config alertes: {e}")

alerts_config = load_alerts_config()

# Clients connectés
connected_clients = set()

# Statistiques
def calculate_stats():
    if len(sensor_history) < 2:
        return None
    
    temps = [d['temperature'] for d in sensor_history if d['temperature'] is not None]
    humidity = [d['humidity'] for d in sensor_history if d['humidity'] is not None]
    
    if not temps or not humidity:
        return None
    
    return {
        'temperature': {
            'current': temps[-1],
            'min': min(temps),
            'max': max(temps),
            'avg': round(statistics.mean(temps), 1),
            'median': round(statistics.median(temps), 1)
        },
        'humidity': {
            'current': humidity[-1],
            'min': min(humidity),
            'max': max(humidity),
            'avg': round(statistics.mean(humidity), 1),
            'median': round(statistics.median(humidity), 1)
        },
        'total_readings': len(sensor_history),
        'time_span_hours': round((datetime.now() - datetime.fromisoformat(sensor_history[0]['timestamp'])).total_seconds() / 3600, 1) if sensor_history else 0
    }

# Vérifier les alertes
def check_alerts(temperature, humidity):
    if not alerts_config['alerts_enabled']:
        return []
    
    alerts = []
    
    if temperature < alerts_config['temperature_min']:
        alerts.append({
            'type': 'temperature_low',
            'message': f'Température trop basse: {temperature}°C (seuil: {alerts_config["temperature_min"]}°C)',
            'severity': 'warning',
            'value': temperature,
            'threshold': alerts_config['temperature_min']
        })
    elif temperature > alerts_config['temperature_max']:
        alerts.append({
            'type': 'temperature_high',
            'message': f'Température trop élevée: {temperature}°C (seuil: {alerts_config["temperature_max"]}°C)',
            'severity': 'danger',
            'value': temperature,
            'threshold': alerts_config['temperature_max']
        })
    
    if humidity < alerts_config['humidity_min']:
        alerts.append({
            'type': 'humidity_low',
            'message': f'Humidité trop faible: {humidity}% (seuil: {alerts_config["humidity_min"]}%)',
            'severity': 'warning',
            'value': humidity,
            'threshold': alerts_config['humidity_min']
        })
    elif humidity > alerts_config['humidity_max']:
        alerts.append({
            'type': 'humidity_high',
            'message': f'Humidité trop élevée: {humidity}% (seuil: {alerts_config["humidity_max"]}%)',
            'severity': 'danger',
            'value': humidity,
            'threshold': alerts_config['humidity_max']
        })
    
    return alerts

# Sauvegarder les données dans un fichier JSON
def save_data_to_file():
    try:
        data_to_save = {
            'last_updated': datetime.now().isoformat(),
            'total_readings': len(sensor_history),
            'data': list(sensor_history)
        }
        
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data_to_save, f, indent=2)
    except Exception as e:
        print(f"Erreur sauvegarde données: {e}")

# Charger les données depuis le fichier
def load_data_from_file():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                saved_data = json.load(f)
                for item in saved_data.get('data', [])[-1000:]:
                    sensor_history.append(item)
                print(f"Chargé {len(sensor_history)} mesures depuis {DATA_FILE}")
        except Exception as e:
            print(f"Erreur chargement données: {e}")

# Charger les données au démarrage
load_data_from_file()

# Routes Flask
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/status')
def status():
    return jsonify({
        'status': 'running',
        'timestamp': datetime.now().isoformat(),
        'latest_data': latest_data,
        'clients_connected': len(connected_clients),
        'led_state': led_state,
        'total_readings': len(sensor_history),
        'alerts_config': alerts_config,
        'stats': calculate_stats()
    })

@app.route('/history')
def get_history():
    limit = request.args.get('limit', 100, type=int)
    limit = min(limit, 1000)
    
    history_data = list(sensor_history)[-limit:] if sensor_history else []
    
    return jsonify({
        'data': history_data,
        'total': len(sensor_history),
        'returned': len(history_data)
    })

@app.route('/stats')
def get_stats():
    return jsonify(calculate_stats())

@app.route('/export/csv')
def export_csv():
    if not sensor_history:
        return jsonify({'error': 'Aucune donnée à exporter'}), 400
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    writer.writerow(['timestamp', 'temperature', 'humidity'])
    
    for item in sensor_history:
        writer.writerow([
            item['timestamp'],
            item['temperature'],
            item['humidity']
        ])
    
    output.seek(0)
    
    filename = f"iot_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    return send_file(
        io.BytesIO(output.getvalue().encode('utf-8')),
        as_attachment=True,
        download_name=filename,
        mimetype='text/csv'
    )

@app.route('/alerts/config', methods=['GET', 'POST'])
def alerts_config_route():
    global alerts_config
    
    if request.method == 'POST':
        try:
            new_config = request.get_json()
            required_keys = ['temperature_min', 'temperature_max', 'humidity_min', 'humidity_max', 'alerts_enabled']
            
            if all(key in new_config for key in required_keys):
                alerts_config.update(new_config)
                save_alerts_config(alerts_config)
                
                socketio.emit('alerts_config_updated', alerts_config)
                
                return jsonify({
                    'status': 'success',
                    'config': alerts_config,
                    'message': 'Configuration des alertes mise à jour'
                })
            else:
                return jsonify({'error': 'Configuration invalide'}), 400
                
        except Exception as e:
            return jsonify({'error': f'Erreur: {e}'}), 500
    
    return jsonify(alerts_config)

@app.route('/upload', methods=['POST', 'OPTIONS'])
def upload_data():
    global latest_data
    
    # Gestion CORS pour les requêtes OPTIONS
    if request.method == 'OPTIONS':
        response = app.make_default_options_response()
        headers = response.headers
        headers['Access-Control-Allow-Origin'] = '*'
        headers['Access-Control-Allow-Methods'] = 'POST'
        headers['Access-Control-Allow-Headers'] = 'Content-Type'
        return response

    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400

        # Validation des données
        if 'temperature' not in data or 'humidity' not in data:
            return jsonify({"error": "Missing temperature or humidity"}), 400

        # Ajouter un timestamp si absent
        if 'timestamp' not in data:
            data["timestamp"] = datetime.now().isoformat()

        print("📩 Données reçues:", data)

        # Mettre à jour les dernières données
        latest_data.update({
            'temperature': data['temperature'],
            'humidity': data['humidity'],
            'timestamp': data['timestamp']
        })

        # Stocker dans l'historique
        sensor_history.append(data)

        # Vérifier les alertes
        alerts = check_alerts(data['temperature'], data['humidity'])
        if alerts:
            print(f"🚨 Alertes déclenchées: {alerts}")
            # Émettre les alertes via SocketIO
            socketio.emit('new_alerts', alerts)

        # Calculer les statistiques
        stats = calculate_stats()

        # CORRECTION PRINCIPALE : Émettre les nouvelles données via SocketIO
        data_with_stats = {
            **data,
            'stats': stats
        }
        
        print(f"📡 Émission SocketIO vers {len(connected_clients)} clients")
        socketio.emit('new_data', data_with_stats)

        # Sauvegarder périodiquement (tous les 10 points de données)
        if len(sensor_history) % 10 == 0:
            save_data_to_file()

        response = jsonify({"status": "success", "clients_notified": len(connected_clients)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 200

    except Exception as e:
        print(f"❌ Erreur upload_data: {e}")
        response = jsonify({"error": str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

@app.route('/led_status', methods=['GET', 'OPTIONS'])
def get_led_status():
    if request.method == 'OPTIONS':
        response = app.make_default_options_response()
        headers = response.headers
        headers['Access-Control-Allow-Origin'] = '*'
        headers['Access-Control-Allow-Methods'] = 'GET'
        headers['Access-Control-Allow-Headers'] = 'Content-Type'
        return response

    response = jsonify({'led_state': led_state})
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response

@app.route('/led_control', methods=['POST', 'OPTIONS'])
def control_led():
    global led_state
    
    if request.method == 'OPTIONS':
        response = app.make_default_options_response()
        headers = response.headers
        headers['Access-Control-Allow-Origin'] = '*'
        headers['Access-Control-Allow-Methods'] = 'POST'
        headers['Access-Control-Allow-Headers'] = 'Content-Type'
        return response

    print(f"\n💡 CONTRÔLE LED VIA HTTP")
    
    try:
        if not request.is_json:
            return jsonify({'error': 'Content-Type doit être application/json'}), 400

        data = request.get_json()
        print(f"Commande reçue: {data}")

        if not data or 'state' not in data:
            return jsonify({'error': 'Champ state requis'}), 400

        new_state = data['state']
        if not isinstance(new_state, bool):
            return jsonify({'error': 'state doit être true ou false'}), 400

        led_state = new_state
        print(f"✅ LED mise à jour: {'ON' if led_state else 'OFF'}")
        
        # Notifier tous les clients web connectés
        socketio.emit('led_update', {'led_state': led_state})

        response = jsonify({
            'status': 'success', 
            'led_state': led_state,
            'message': f"LED {'allumée' if led_state else 'éteinte'}"
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 200

    except Exception as e:
        print(f"❌ Erreur contrôle LED: {e}")
        return jsonify({'error': 'Erreur serveur'}), 500

# Gestion des connexions SocketIO
@socketio.on('connect')
def handle_connect(auth=None):
    print(f"🔌 Client connecté: {request.sid}")
    connected_clients.add(request.sid)
    
    # Envoyer les dernières données si disponibles
    if latest_data['temperature'] is not None:
        socketio.emit('new_data', {
            **latest_data,
            'stats': calculate_stats()
        }, room=request.sid)
    
    # Envoyer état LED actuel
    socketio.emit('led_update', {'led_state': led_state}, room=request.sid)
    
    # Envoyer configuration des alertes
    socketio.emit('alerts_config_updated', alerts_config, room=request.sid)
    
    # Envoyer historique récent pour les graphiques
    recent_data = list(sensor_history)[-50:] if sensor_history else []
    socketio.emit('history_data', recent_data, room=request.sid)
    
    print(f"📤 Données initiales envoyées au client {request.sid}")

@socketio.on('disconnect')
def handle_disconnect():
    print(f"🔌 Déconnecté: {request.sid}")
    connected_clients.discard(request.sid)

@socketio.on('led_control')
def handle_led_control(data):
    global led_state
    print(f"\n💡 COMMANDE LED VIA SOCKET: {data}")
    try:
        if isinstance(data, dict) and 'state' in data and isinstance(data['state'], bool):
            led_state = data['state']
            print(f"✅ LED mis à jour: {'ON' if led_state else 'OFF'}")
            
            # Notifier tous les autres clients
            socketio.emit('led_update', {'led_state': led_state})
        else:
            print("❌ Format invalide pour led_control")
    except Exception as e:
        print(f"❌ Erreur: {e}")

@socketio.on('request_history')
def handle_request_history(data):
    limit = data.get('limit', 100) if data else 100
    limit = min(limit, 1000)
    
    history_data = list(sensor_history)[-limit:] if sensor_history else []
    socketio.emit('history_data', history_data, room=request.sid)

if __name__ == '__main__':
    print("🚀 Serveur IoT Avancé démarré")
    print(f"🔗 URL locale: http://localhost:5000 (Runway ou service cloud fournira un URL public)")
    print("🔗 Endpoints disponibles:")
    print("   GET  / (dashboard)")
    print("   POST /upload (données capteur)")
    print("   GET  /led_status (état LED)")
    print("   POST /led_control (contrôle LED)")
    print("   GET  /history (historique)")
    print("   GET  /stats (statistiques)")
    print("   GET  /export/csv (export CSV)")
    print("   GET/POST /alerts/config (config alertes)")
    print("   GET  /status (statut complet)")

    # Sauvegarder les données à l'arrêt
    import atexit
    atexit.register(save_data_to_file)

    import eventlet
    import eventlet.wsgi

    port = int(os.environ.get('PORT', 5000))
    print(f"🔌 Démarrage sur le port {port} avec Eventlet...")

    # Démarrage du serveur en production
    eventlet.wsgi.server(eventlet.listen(('0.0.0.0', port)), app)


