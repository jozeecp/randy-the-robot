#include <AccelStepper.h>

class Calibration {
public:
    Calibration(
        AccelStepper *stepper,
        int calibration_button_pin,
        int action_button_pin,
        int en1_pin,
        int en2_pin
    );

    void calibrate_motor(bool return_to_last_position);
    void zero_motor();

private:
    AccelStepper *stepper;
    int calibration_button_pin;
    int action_button_pin;
    int switch_pin;
    int en1_pin;
    int en2_pin;
};
