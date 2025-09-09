#include <Arduino.h>
#include <ArduinoJson.h>
#include <HTTPClient.h>
#include <WiFi.h>

// --- Configuration WiFi ---
const char* ssid = "Wokwi-GUEST";
const char* password = "";

// --- Configuration du Serveur ---
//  Mets ici ton URL ngrok 
const char* serverUrl ="http://6d7bf3db032b.ngrok-free.app/upload"; // Pour les données
const char* ledStatusUrl ="http://6d7bf3db032b.ngrok-free.app/led_status"; // Pour l'état LED

// --- Configuration de la LED ---
const int LED_PIN = 12;
bool ledState = false;

// Timer pour envoi des données
unsigned long lastSendTime = 0;
const long sendInterval = 10000;

// Timer pour vérifier l'état de la LED
unsigned long lastLedCheckTime = 0;
const long ledCheckInterval = 5000;

void setup() {
  Serial.begin(115200);
  delay(2000);

  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, LOW);

  Serial.println("\n=== ESP32 IoT Client - Version Corrigée ===");
  Serial.print("Connexion au WiFi...");
  WiFi.begin(ssid, password);

  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 20) {
    delay(500);
    Serial.print(".");
    attempts++;
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\n✅ WiFi connecté!");
    Serial.print("IP: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println("\n Échec WiFi (Wokwi continue quand même)");
  }

  Serial.println("---");
  Serial.print("Envoi vers: ");
  Serial.println(serverUrl);
  Serial.print("État LED depuis: ");
  Serial.println(ledStatusUrl);
  Serial.println("Démarrage simulation DHT22...");
  Serial.println("---");
}

void loop() {
  unsigned long currentMillis = millis();

  // Envoi des données
  if (currentMillis - lastSendTime >= sendInterval) {
    lastSendTime = currentMillis;
    float temp = random(180, 320) / 10.0;
    float humidity = random(350, 850) / 10.0;

    Serial.println("\n=== NOUVELLE MESURE ===");
    Serial.print("🌡️ Température: ");
    Serial.print(temp, 1);
    Serial.println("°C");
    Serial.print("💧 Humidité: ");
    Serial.print(humidity, 1);
    Serial.println("%");

    sendDataToServer(temp, humidity);
  }

  // Vérification état LED
  if (currentMillis - lastLedCheckTime >= ledCheckInterval) {
    lastLedCheckTime = currentMillis;
    checkLedCommand();
  }

  delay(100);
}

void sendDataToServer(float temperature, float humidity) {
  Serial.println("\n📡 Envoi des données...");
  HTTPClient http;
  http.begin(serverUrl);
  http.addHeader("Content-Type", "application/json");
  http.addHeader("ngrok-skip-browser-warning", "true");
  http.addHeader("User-Agent", "ESP32-IoT-Client");
  http.setTimeout(15000);

  DynamicJsonDocument doc(200);
  doc["temperature"] = round(temperature * 10) / 10.0;
  doc["humidity"] = round(humidity * 10) / 10.0;

  String jsonPayload;
  serializeJson(doc, jsonPayload);

  Serial.print("📦 JSON: ");
  Serial.println(jsonPayload);

  int httpCode = http.POST(jsonPayload);

  if (httpCode > 0) {
    if (httpCode == 200) {
      Serial.println("✅ Succès ! Réponse:");
      Serial.println(http.getString());
    } else {
      Serial.print(" Échec HTTP: ");
      Serial.println(httpCode);
      Serial.println(http.getString());
    }
  } else {
    Serial.print(" Échec connexion: ");
    Serial.println(http.errorToString(httpCode));
  }

  http.end();
  Serial.println("=== FIN ENVOI ===\n");
}

// --- Vérification de l'état de la LED ---
void checkLedCommand() {
  Serial.println("\n🔍 Vérification état LED...");
  Serial.print("📡 URL: ");
  Serial.println(ledStatusUrl);

  HTTPClient http;
  http.begin(ledStatusUrl);
  http.addHeader("User-Agent", "ESP32-IoT-Client");
  http.setTimeout(10000);

  int httpCode = http.GET();

  if (httpCode > 0) {
    if (httpCode == 200) {
      String payload = http.getString();
      Serial.print("✅ Réponse: ");
      Serial.println(payload);

      DynamicJsonDocument doc(200);
      DeserializationError error = deserializeJson(doc, payload);

      if (!error) {
        if (doc.containsKey("led_state")) {
          bool newLedState = doc["led_state"];

          Serial.print("🔧 État souhaité: ");
          Serial.println(newLedState ? "ON" : "OFF");

          if (newLedState != ledState) {
            ledState = newLedState;
            digitalWrite(LED_PIN, ledState ? HIGH : LOW);
            Serial.println(ledState ? "💡 LED allumée" : " LED éteinte");
          } else {
            Serial.println("🔄 État inchangé.");
          }
        } else {
          Serial.println(" Clé 'led_state' manquante");
        }
      } else {
        Serial.print(" Erreur JSON: ");
        Serial.println(error.c_str());
      }
    } else {
      Serial.print(" Code HTTP: ");
      Serial.println(httpCode);
      Serial.println(http.getString());
    }
  } else {
    Serial.print(" Connexion échouée: ");
    Serial.println(http.errorToString(httpCode));
  }

  http.end();
  Serial.println("🔍 Fin vérification LED.\n");
}