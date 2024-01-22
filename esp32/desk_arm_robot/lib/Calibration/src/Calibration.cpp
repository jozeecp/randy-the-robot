#include "Calibration.h"
#include <Arduino.h>

int MAX_OFFSET = 1250;

Calibration::Calibration(AccelStepper *stepper, int calibration_button_pin, int action_button_pin, int en1_pin, int en2_pin)
    {
        this->stepper = stepper;
        this->calibration_button_pin = calibration_button_pin;
        this->action_button_pin = action_button_pin;
        this->en1_pin = en1_pin;
        this->en2_pin = en2_pin;
    }

void Calibration::calibrate_motor(bool return_to_last_position) {

    // do nothing until the switch is pressed
    Serial.println("Press action button to start calibration");
    int last_position = stepper->currentPosition();
    while (digitalRead(action_button_pin) == HIGH) {}
    Serial.println("Calibrating...");

    delay(1000);

    // enable stepper
    digitalWrite(en1_pin, HIGH);
    digitalWrite(en2_pin, HIGH);

    // Move the motor until the switch is pressed
    while (digitalRead(calibration_button_pin) == HIGH) {
        stepper->move(1);
        stepper->setSpeed(100);
        stepper->run();
    }
    Serial.println("calibration button pressed");
    stepper->stop();
    stepper->setCurrentPosition(MAX_OFFSET);

    if(return_to_last_position){
        Serial.println("Returning to last position ...");
        stepper->moveTo(last_position);
        while (stepper->distanceToGo() != 0) {
            stepper->run();
        }
    }else{
        // move back a little bit
        stepper->moveTo(MAX_OFFSET - 100);
        while (stepper->distanceToGo() != 0) {
            stepper->run();
        }
    }

    // disable stepper
    digitalWrite(en1_pin, LOW);
    digitalWrite(en2_pin, LOW);

    Serial.println("Motor zeroed");
}

void Calibration::zero_motor() {
    this->calibrate_motor(false);
    this->stepper->moveTo(0);
    while (stepper->distanceToGo() != 0) {
        stepper->run();
    }
}
