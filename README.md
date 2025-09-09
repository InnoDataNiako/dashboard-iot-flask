#  Dashboard Web IoT - Monitoring Température & Humidité

> **Projet IoT M1 IA** - Système de monitoring environnemental en temps réel avec ESP32 simulé et interface web moderne

##  Description
Dashboard web temps réel pour visualiser les données de **température** et **humidité** provenant d'un capteur **DHT22** connecté à un **ESP32 simulé** sur Wokwi. Solution complètement **auto-hébergée localement** sans dépendance à des plateformes tierces.

###  **Fonctionnalités Principales**
- 📊 **Visualisation temps réel** des données capteur
- 🔄 **Mise à jour automatique** via WebSocket
- 📱 **Interface responsive** 
- 💡 **Contrôle LED** à distance
- 📤 **Export CSV** des données

##  Architecture Système

```
┌─────────────────┐    HTTP POST    ┌─────────────────┐    WebSocket    ┌─────────────────┐
│   ESP32 + DHT22 │ ────────────────> │  Backend Flask  │ ────────────────> │  Dashboard Web  │
│   (Wokwi Sim)   │                 │  + SocketIO     │                 │   (Browser)     │
└─────────────────┘                 └─────────────────┘                 └─────────────────┘
       │                                     │                                     │
       │                                     ▼                                     │
       │                            ┌─────────────────┐                          │
       └─── Contrôle LED ───────────│  Données JSON   │◄─── Contrôles ──────────┘
                                    │   Persistance   │
                                    └─────────────────┘
```

##  Installation & Configuration

### **Prérequis**
- Python 3.7+ installé
- Navigateur web moderne
- Accès à [Wokwi.com](https://wokwi.com) pour simulation
- (Optionnel) ngrok pour exposition publique

### **1. Installation Backend**

```bash
# Cloner le projet
git clone https://github.com/InnoDataNiako/dashboard-iot-flask
cd dashboard-iot-flask

# Installer les dépendances Python
pip install flask flask-socketio

# Vérifier l'installation
python --version
pip list | grep flask
```

### **2. Structure Projet**

```
projet-iot-dashboard/
├── server.py                  #  Serveur Flask principal
├── templates/
│   └── index.html            #  Interface web dashboard
├── esp32_client.ino          #  Code Arduino ESP32
├── iot_data.json            #   Données persistantes 
└── README.md                #  Cette documentation
```

### **3. Démarrage Serveur**

```bash
# Lancer le serveur Flask
python server.py

# Le serveur démarre sur : http://localhost:5000
# Endpoints disponibles :
#   GET  /              (Dashboard web)
#   POST /upload        (Réception données capteur)
#   GET  /history       (Historique données)
#   POST /led_control   (Contrôle LED)
```

### **4. Configuration **

**Option B : Exposition Publique (ngrok)**
```bash
# Installer ngrok
# Exposer le serveur local
ngrok http --scheme=http 5000

# Utiliser l'URL fournie : https://abcd1234.ngrok.io/upload
```

##  Configuration ESP32 (Wokwi)

### **1. Création Projet Wokwi**

1. Aller sur [https://wokwi.com](https://wokwi.com)
2. Créer nouveau projet ESP32
3. Ajouter composant **DHT22**

### **2. Câblage Virtual**

```
DHT22 Sensor    ESP32
├── VCC    →    3.3V
├── GND    →    GND  
└── DATA   →    GPIO15 (D15)
```


### **4. Configuration dans Wokwi**

1. **Copier le code** dans l'éditeur Arduino
2. **Modifier l'URL** 
3. **Démarrer la simulation**
4. **Vérifier les logs** dans le moniteur série

##  Accès Dashboard Web

### **Interface Utilisateur**

1. **Ouvrir navigateur** → `http://localhost:5000`
2. **Dashboard temps réel** avec :
   - 🌡️ **Température actuelle** + historique
   - 💧 **Humidité actuelle** + historique  
   - 📊 **Graphiques interactifs** Chart.js
   - 📈 **Statistiques** (min/max/moyenne)
   - 🚨 **Alertes visuelles** configurables
   - 💡 **Contrôle LED** interactif
   - 📥 **Export CSV** données

## API Endpoints

| **Endpoint** | **Méthode** | **Description** | **Paramètres** |
|------------- |------------  |----------------|----------------|
| `/`          | GET | Dashboard principal | - |
| `/upload`    | POST | Réception données capteur | `{temperature, humidity}` |
| `/led_control`| POST | Contrôle LED | `{state: boolean}` |
| `/history`   | GET | Historique données | `?limit=100` |
| `/stats`     | GET | Statistiques calculées | - |
| `/export/csv`| GET | Export CSV | - |
| `/alerts/config`| GET/POST | Configuration alertes | Config JSON |

### **Exemple Utilisation API**

```bash
# Test envoi données
curl -X POST http://localhost:5000/upload \
  -H "Content-Type: application/json" \
  -d '{"temperature": 23.5, "humidity": 65.0}'

# Contrôle LED
curl -X POST http://localhost:5000/led_control \
  -H "Content-Type: application/json" \
  -d '{"state": true}'

# Récupérer historique
curl http://localhost:5000/history?limit=50
```

##  Choix Techniques Justifiés

### **Backend : Flask + SocketIO**
- ✅ **Flask** : Framework Python léger, parfait pour API REST
- ✅ **SocketIO** : Communication temps réel bidirectionnelle
- ✅ **Threading** : Gestion multiple clients simultanés
- ✅ **JSON** : Format standard IoT, persistence simple

### **Frontend : HTML5 + Bootstrap + Chart.js**
- ✅ **Bootstrap** : Interface responsive rapide
- ✅ **Chart.js** : Visualisations interactives
- ✅ **Socket.IO Client** : Temps réel navigateur
- ✅ **Vanilla JS** : Performance optimale

### **Simulation : Wokwi ESP32**
- ✅ **Wokwi** : Pas de matériel physique requis
- ✅ **DHT22** : Capteur standard industrie IoT
- ✅ **Arduino IDE** : Environnement familier
- ✅ **HTTP POST** : Protocole standard IoT


### **Problèmes Fréquents**

**ESP32 ne se connecte pas :**
```cpp
// Vérifier l'URL dans le code
const char* serverURL = "http://IP_CORRECTE:5000/upload";

// Debug WiFi
Serial.println(WiFi.localIP()); // Afficher IP ESP32
```

**Dashboard ne se met pas à jour :**
```javascript
// Ouvrir console navigateur (F12)
// Vérifier connexion WebSocket
console.log('Socket connecté:', socket.connected);
```

**Serveur n'accepte pas les données :**
```bash
# Vérifier CORS et Content-Type
curl -v -X POST http://localhost:5000/upload \
  -H "Content-Type: application/json" \
  -d '{"temperature": 25, "humidity": 60}'
```

### **Logs Utiles**

```python
# Backend Flask (server.py)
print("📩 Données reçues:", data)        # Réception
print("📡 Diffusion vers clients")        # WebSocket
print("🚨 Alerte déclenchée:", alert)    # Système alertes
```

```cpp
// ESP32 (esp32_client.ino)  
Serial.println("✅ Données envoyées");    // HTTP Success
Serial.println("❌ Erreur HTTP");        // HTTP Error
```

```javascript
// Frontend (script.js)
console.log('Nouvelles données:', data);  // WebSocket reçu
console.log('LED état:', ledState);       // Contrôle LED
```

##  Ressources & Documentation

### **Documentation Technique**
- [Flask Documentation](https://flask.palletsprojects.com)
- [Flask-SocketIO Guide](https://flask-socketio.readthedocs.io)
- [Wokwi ESP32 Guide](https://docs.wokwi.com/guides/esp32)
- [DHT22 Datasheet](https://www.sparkfun.com/datasheets/Sensors/Temperature/DHT22.pdf)

### **Outils Développement**
- [Wokwi Simulator](https://wokwi.com) - Simulation ESP32
- [ngrok](https://ngrok.com) - Exposition serveur local
- [Postman](https://postman.com) - Test API REST
- [Chrome DevTools](https://developer.chrome.com/docs/devtools) - Debug frontend


##  Projet Académique

**Auteur :** NIAKO KEBE  
**Formation :** M1 Intelligence Artificielle  
**Cours :** IoT et Systèmes Embarqués  
**Type :** Projet individuel  

### **Compétences Démontrées**
-  **Développement Backend** Python/Flask
-  **Architecture Web** moderne REST + WebSocket  
-  **Programmation Embarquée** ESP32/Arduino
-  **Visualisation Données** temps réel
-  **Intégration Systèmes** IoT complets
-  **Debug & Monitoring** multi-composants

### **Livrables**
- ✅ Code source complet et documenté
- ✅ Interface web fonctionnelle
- ✅ Simulation ESP32 opérationnelle  
- ✅ Documentation technique complète


## 🔗 Liens Utiles

- **📁 Repository :** [GitHub Project](https://github.com/InnoDataNiako/dashboard-iot-flask)
- **🎥 Démonstration :** [Vidéo Demo]
- **📊 Wokwi Simulation :** [Projet Wokwi](https://wokwi.com/projects/441437655550837761)
- **📧 Contact :** keben663@gmail.com

---

**🚀 Projet réalisé avec passion pour l'IoT et les technologies modernes !**