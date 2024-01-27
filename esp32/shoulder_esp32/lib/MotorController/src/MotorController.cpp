// #include "MotorController.h"

// MotorController::MotorController(Motors *motors) {
//     this->motors = motors;
//     // Initialize currentPosition with zeros or a safe default position
//     this->currentPosition = {0, 0, 0, 0, 0, 0, 0};
// }

// RobotPosition MotorController::getCurrentPosition() {
//     return this->currentPosition;
// }

// void MotorController::moveRobotToPosition(RobotPosition position) {
//     moveBaseToPosition(position.base);
//     moveShouldeToPosition(position.shoulder);
//     moveElbowToPosition(position.elbow);
//     moveWrist1ToPosition(position.wrist1);
//     moveWrist2ToPosition(position.wrist2);
//     moveWrist3ToPosition(position.wrist3);
//     moveGripperToPosition(position.gripper);
// }

// void MotorController::moveBaseToPosition(float position) {
//     // Implement logic to move base motor
//     motors->base->moveTo(position);
//     updateCurrentPosition({position, currentPosition.shoulder, currentPosition.elbow, currentPosition.wrist1, currentPosition.wrist2, currentPosition.wrist3, currentPosition.gripper});
// }

// void MotorController::moveShouldeToPosition(float position) {
//     // Implement logic to move shoulder motor
//     motors->shoulder->moveTo(position);
//     updateCurrentPosition({currentPosition.base, position, currentPosition.elbow, currentPosition.wrist1, currentPosition.wrist2, currentPosition.wrist3, currentPosition.gripper});
// }

// void MotorController::moveElbowToPosition(float position) {
//     // Implement logic to move elbow servo
//     motors->pwm->setPWM(motors->elbow, 0, position);  // Assumes position is in PWM units
//     updateCurrentPosition({currentPosition.base, currentPosition.shoulder, position, currentPosition.wrist1, currentPosition.wrist2, currentPosition.wrist3, currentPosition.gripper});
// }

// void MotorController::moveWrist1ToPosition(float position) {
//     motors->pwm->setPWM(motors->wrist1, 0, position);
//     updateCurrentPosition({currentPosition.base, currentPosition.shoulder, currentPosition.elbow, position, currentPosition.wrist2, currentPosition.wrist3, currentPosition.gripper});
// }

// void MotorController::moveWrist2ToPosition(float position) {
//     motors->pwm->setPWM(motors->wrist2, 0, position);
//     updateCurrentPosition({currentPosition.base, currentPosition.shoulder, currentPosition.elbow, currentPosition.wrist1, position, currentPosition.wrist3, currentPosition.gripper});
// }

// void MotorController::moveWrist3ToPosition(float position) {
//     motors->pwm->setPWM(motors->wrist3, 0, position);
//     updateCurrentPosition({currentPosition.base, currentPosition.shoulder, currentPosition.elbow, currentPosition.wrist1, currentPosition.wrist2, position, currentPosition.gripper});
// }

// void MotorController::moveGripperToPosition(float position) {
//     motors->pwm->setPWM(motors->gripper, 0, position);
//     updateCurrentPosition({currentPosition.base, currentPosition.shoulder, currentPosition.elbow, currentPosition.wrist1, currentPosition.wrist2, currentPosition.wrist3, position});
// }

// void MotorController::updateCurrentPosition(RobotPosition position) {
//     this->currentPosition = position;
// }
