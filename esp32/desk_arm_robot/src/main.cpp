#include <Arduino.h>
#include <AccelStepper.h>
#include <Calibration.h>
#include <EEPROM.h>

#define STEPPER_IN_1 12
#define STEPPER_IN_2 14
#define STEPPER_IN_3 27
#define STEPPER_IN_4 26

#define STEPPER_EN1 18
#define STEPPER_EN2 5

#define ACTION_BUTTON_PIN 19
#define CALIBRATION_BUTTON_PIN 17

#define EEPROM_SIZE 1

int last_position = 0;

// shoulder joint
AccelStepper stepper1(AccelStepper::FULL4WIRE, STEPPER_IN_1, STEPPER_IN_2, STEPPER_IN_3, STEPPER_IN_4);
Calibration calibration(&stepper1, CALIBRATION_BUTTON_PIN, ACTION_BUTTON_PIN, STEPPER_EN1, STEPPER_EN2);

// prototype functions
int deg_to_steps(int degrees);

void setup() {
    // init serial at 9600 baud
    Serial.begin(9600);
    Serial.println("Serial started");

    // init stepper
    stepper1.setMaxSpeed(200.0);
    stepper1.setAcceleration(100.0);

    // init pins
    pinMode(ACTION_BUTTON_PIN, INPUT_PULLUP);
    pinMode(STEPPER_EN1, OUTPUT);
    pinMode(STEPPER_EN2, OUTPUT);

    EEPROM.begin(EEPROM_SIZE);
    last_position = EEPROM.read(0);
    Serial.print("Last position: "); Serial.println(last_position);
    stepper1.moveTo(last_position);
    Serial.println("Stepper moving to last position");
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

    stepper1.run();
}

int deg_to_steps(int degrees){
    int steps = map(degrees, 85, -85, -1250, 1250);
    return steps;
}
