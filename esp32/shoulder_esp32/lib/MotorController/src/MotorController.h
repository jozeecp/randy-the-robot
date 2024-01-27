// #include <Arduino.h>
// #include <AccelStepper.h>
// #include <Adafruit_PWMServoDriver.h>


// struct Motors{
//     AccelStepper *base; // stepper with gear
//     AccelStepper *shoulder; // stepper with worm gear

//     // the rest are servos
//     Adafruit_PWMServoDriver *pwm;
//     int elbow;
//     int wrist1;
//     int wrist2;
//     int wrist3;
//     int gripper;
// };

// struct RobotPosition{
//     float base;
//     float shoulder;
//     float elbow;

//     float wrist1;
//     float wrist2;
//     float wrist3;

//     float gripper;
// };

// class MotorController{
//     public:
//         MotorController(Motors *motors);

//         RobotPosition getCurrentPosition();
//         void moveRobotToPosition(RobotPosition position);

//         void moveBaseToPosition(float position);
//         void moveShouldeToPosition(float position);
//         void moveElbowToPosition(float position);

//         void moveWrist1ToPosition(float position);
//         void moveWrist2ToPosition(float position);
//         void moveWrist3ToPosition(float position);

//         void moveGripperToPosition(float position);

//     private:
//         Motors *motors;
//         RobotPosition currentPosition;
//         void updateCurrentPosition(RobotPosition position);
// };
