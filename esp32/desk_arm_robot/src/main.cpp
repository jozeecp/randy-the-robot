#include <Arduino.h>
#include <AccelStepper.h>
#include <EEPROM.h>

#include <Calibration.h>
#include <Secrets.h>

#include <WiFi.h>
#include <PubSubClient.h>

#define STEPPER_IN_1 12
#define STEPPER_IN_2 14
#define STEPPER_IN_3 27
#define STEPPER_IN_4 26

#define STEPPER_EN1 18
#define STEPPER_EN2 5

#define ACTION_BUTTON_PIN 19
#define CALIBRATION_BUTTON_PIN 17

#define EEPROM_SIZE 1

// WiFi
const char *ssid = WIFI_SSID; // Enter your WiFi name
const char *password = WIFI_PASS;  // Enter WiFi password
WiFiClient wifi_client;

// MQTT Broker
PubSubClient client(wifi_client);
const char *mqtt_broker = MQTT_BROKER;
const char *topic = MQTT_TOPIC;
const char *command_topic = "robot/shoulder/cmd";
const char *mqtt_username = MQTT_USERNAME;
const char *mqtt_password = MQTT_PASSWORD;
const int mqtt_port = 1883;


int last_position = 0;
long last_timestamp = 0;
long last_position_timestamp = 0;
long performance_timestamp = 0;

// shoulder joint
AccelStepper stepper1(AccelStepper::FULL4WIRE, STEPPER_IN_1, STEPPER_IN_2, STEPPER_IN_3, STEPPER_IN_4);
Calibration calibration(&stepper1, CALIBRATION_BUTTON_PIN, ACTION_BUTTON_PIN, STEPPER_EN1, STEPPER_EN2);

// prototype functions
int deg_to_steps(int degrees);
int steps_to_deg(int steps);
void mqtt_callback(char* topic, byte *payload, unsigned int length);
void reconnect();

void setup() {
    // init serial at 9600 baud
    Serial.begin(9600);
    Serial.println("Serial started");

    // init WiFi
    WiFi.begin(ssid, password);
    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        Serial.println("Connecting to WiFi..");
    }

    // init MQTT
    client.setServer(mqtt_broker, mqtt_port);
    client.setCallback(mqtt_callback);
    while (!client.connected()) {
        String client_id = "robot-shoulder-esp32";
        client_id += String(WiFi.macAddress());
        Serial.printf("The client %s connects to the public MQTT broker\n", client_id.c_str());
        if (client.connect(client_id.c_str(), mqtt_username, mqtt_password)) {
            Serial.println("Lab cluster broker connected");
        } else {
            Serial.print("failed with state ");
            Serial.print(client.state());
            delay(2000);
        }
    }
    client.subscribe(topic);
    client.subscribe(command_topic);

    // init stepper
    stepper1.setMaxSpeed(200.0);
    stepper1.setAcceleration(100.0);

    // init pins
    pinMode(ACTION_BUTTON_PIN, INPUT_PULLUP);
    pinMode(STEPPER_EN1, OUTPUT);
    pinMode(STEPPER_EN2, OUTPUT);

    // init EEPROM
    EEPROM.begin(EEPROM_SIZE);
    last_position = EEPROM.read(0);
    Serial.print("Last position: "); Serial.println(last_position);
    stepper1.moveTo(last_position);
    Serial.println("Stepper moving to last position");

    // print instructions
    Serial.println("Press both buttons to calibrate");
    Serial.println("Hold both buttons to reset to zero");
    Serial.println("Send degrees to move stepper");
}

void loop() {
    // disable stepper if it reached the target position
    // and record the position in EEPROM
    if(stepper1.distanceToGo() == 0){
        digitalWrite(STEPPER_EN1, LOW);
        digitalWrite(STEPPER_EN2, LOW);
        int current_position = stepper1.currentPosition();
        if(current_position != last_position){
            EEPROM.write(0, current_position);
            EEPROM.commit();
            last_position = current_position;
        }
    }else{
        digitalWrite(STEPPER_EN1, HIGH);
        digitalWrite(STEPPER_EN2, HIGH);
    }

    // press both buttons to calibrate
    if(digitalRead(ACTION_BUTTON_PIN) != HIGH && digitalRead(CALIBRATION_BUTTON_PIN) != HIGH){
        delay(1000);
        // handle long press
        if (digitalRead(ACTION_BUTTON_PIN) != HIGH && digitalRead(CALIBRATION_BUTTON_PIN) != HIGH){
            Serial.println("Long press detected");
            calibration.zero_motor();
            return;
        }

        calibration.calibrate_motor(true);
    }

    // Check if data is available to read from serial
    if (Serial.available() > 0) {
        int requested_degrees = Serial.parseInt();
        if(requested_degrees > 85 || requested_degrees < -85){
            Serial.println("Invalid position");
            return;
        }
        Serial.print("Received degrees: "); Serial.println(requested_degrees);
        int position = deg_to_steps(requested_degrees);
        Serial.print("Received position: "); Serial.println(position);
        stepper1.moveTo(position); // Move stepper to the received position
    }

    long now_position = millis();
    if( now_position - last_position_timestamp > 100){
        last_position_timestamp = now_position;
        client.publish("robot/shoulder/realtime_position", String(steps_to_deg(stepper1.currentPosition()) - 1).c_str());
    }

    // client.publish("robot/shoulder/realtime_position", String(steps_to_deg(stepper1.currentPosition()) - 1).c_str());
    stepper1.run();

    if (!client.connected()) {
        reconnect();
    }
    client.loop();

    long now = millis();
    if (now - last_timestamp > 10000) {
        last_timestamp = now;
        client.publish("robot/shoulder/uptime", String(millis() / 1000).c_str());
    }
}

int deg_to_steps(int degrees){
    int steps = map(degrees, 85, -85, -1250, 1250);
    return steps;
}

int steps_to_deg(int steps){
    int degrees = map(steps, -1250, 1250, 85, -85);
    return degrees;
}

void mqtt_callback(char* topic, byte *payload, unsigned int length){
    Serial.print("Message arrived in topic: ");Serial.println(topic);
    if(String(topic) == "robot/shoulder/cmd"){
        Serial.println("Command topic");
        String msg;
        for (int i = 0; i < length; i++) {
            msg += (char)payload[i];
        }
        Serial.print("Message: ");Serial.println(msg);
        if(msg == "calibrate"){
            calibration.calibrate_motor(true);
        }
        return;
    }
    String msg;
    for (int i = 0; i < length; i++) {
        msg += (char)payload[i];
    }
    Serial.print("Message: ");Serial.println(msg);
    int requested_degrees = msg.toInt();
    if(requested_degrees > 85 || requested_degrees < -85){
        Serial.println("Invalid position");
        return;
    }
    Serial.print("Received degrees: "); Serial.println(requested_degrees);
    int position = deg_to_steps(requested_degrees);
    Serial.print("Received position: "); Serial.println(position);
    stepper1.moveTo(position); // Move stepper to the received position
}

void reconnect() {
    String client_id = "robot-shoulder-esp32";
    // Loop until we're reconnected
    while (!client.connected()) {
        Serial.print("Attempting MQTT connection...");
        // Attempt to connect
        if (client.connect(client_id.c_str(), mqtt_username, mqtt_password)) {
            Serial.println("connected");
            // Subscribe
            client.subscribe(topic);
        } else {
            Serial.print("failed, rc=");
            Serial.print(client.state());
            Serial.println(" try again in 5 seconds");
            // Wait 5 seconds before retrying
            delay(5000);
        }
    }
}
