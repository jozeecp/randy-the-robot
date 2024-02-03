import * as CANNON from "cannon-es";
import * as THREE from "three";

import {
    colors,
    robotMaterial,
} from "./materials";

var joints = [];
var segments = [];

// Helper function to create a joint and a segment
export function createJointAndSegment(
    base,
    parent,
    previousSegmentLength,
    segmentLength,
    material,
) {
    // Create the joint as an empty Object3D
    var joint = new THREE.Object3D();

    if (parent === base) {
        // Position the joint at the top of the base
        joint.position.y =
            base.geometry.parameters.height / 2 + segmentLength / 2;
    } else {
        joint.position.y = previousSegmentLength;
    }
    // joint.position.y = previousSegmentLength;

    // Add the joint to the parent
    parent.add(joint);
    joints.push(joint);

    // Create the geometry and mesh for the new segment
    if (parent === base) {
        var segmentGeometry = new THREE.BoxGeometry(0.25, segmentLength, 0.5);
    } else {
        var segmentGeometry = new THREE.BoxGeometry(0.25, segmentLength, 0.25);
    }
    var segment = new THREE.Mesh(segmentGeometry, material);

    // Position the segment so that its base is at the joint's origin
    segment.position.y = segmentLength / 2;

    // Add the segment to the joint
    joint.add(segment);
    segments.push(segment);

    return joint;
}

export function createGripper(parent, previousSegmentLength, material) {
    // create two boxes
    const y_offset = 0.75;
    var gripper = new THREE.Object3D();
    var gripper1 = new THREE.Mesh(
        new THREE.BoxGeometry(0.125, 0.25, 0.25),
        material,
    );
    var gripper2 = new THREE.Mesh(
        new THREE.BoxGeometry(0.125, 0.25, 0.25),
        material,
    );
    gripper1.position.y = y_offset;
    gripper2.position.y = y_offset;
    gripper.add(gripper1);
    gripper.add(gripper2);
    parent.add(gripper);

    // add vector arrows to show the gripper's orientation
    var origin = new THREE.Vector3(0, 0, 0);
    var length = 1;

    var gripperArrow1 = new THREE.ArrowHelper(
        new THREE.Vector3(1, 0, 0),
        origin,
        length,
        colors.red,
    );
    var gripperArrow2 = new THREE.ArrowHelper(
        new THREE.Vector3(0, 1, 0),
        origin,
        length,
        colors.green,
    );
    var gripperArrow3 = new THREE.ArrowHelper(
        new THREE.Vector3(0, 0, 1),
        origin,
        length,
        colors.blue,
    );

    gripperArrow1.position.y = y_offset;
    gripperArrow2.position.y = y_offset;
    gripperArrow3.position.y = y_offset;
    gripper.add(gripperArrow1);
    gripper.add(gripperArrow2);
    gripper.add(gripperArrow3);

    return gripper;
}

// Helper function to create a Cannon body from a Three.js geometry
export function createCannonBodyFromThreeMesh(
    mesh,
    material,
    bodyType = CANNON.Body.DYNAMIC,
) {
    const shape = new CANNON.Box(
        new CANNON.Vec3().copy(mesh.geometry.parameters).scale(0.5),
    );
    const body = new CANNON.Body({
        mass: bodyType === CANNON.Body.DYNAMIC ? 1 : 0, // Set mass to 0 for static bodies
        material: material,
    });
    body.addShape(shape);
    body.position.copy(mesh.position);
    body.quaternion.copy(mesh.quaternion);
    world.addBody(body);
    return body;
}

// Helper function to create a Cannon Kinematic body from a Three.js geometry
export function createCannonKinematicBodyFromThreeMesh(
    world,
    mesh,
    material,
    previousSegmentLength = 0,
) {
    const shape = new CANNON.Box(
        new CANNON.Vec3().copy(mesh.geometry.parameters).scale(1),
    );
    const body = new CANNON.Body({
        mass: 0, // Set mass to 0 for kinematic bodies
        material: material,
        type: CANNON.Body.Kinematic,
    });
    body.addShape(shape);
    body.position.copy(mesh.position);
    body.quaternion.copy(mesh.quaternion);
    body.position.y = previousSegmentLength;
    world.addBody(body);
    return body;
}

export function createPhysicsBodiesFromGripper(
    gripper,
    parentBody,
    previousSegmentLength,
) {
    // create two boxes
    const half_thickness = 0.125 / 2;
    const y_offset = 0.75;
    var gripper1 = new CANNON.Box(
        new CANNON.Vec3(
            gripper.children[0].geometry.parameters.width / 2,
            gripper.children[0].geometry.parameters.height / 2,
            gripper.children[0].geometry.parameters.depth / 2,
        ),
    );
    var gripper2 = new CANNON.Box(
        new CANNON.Vec3(
            gripper.children[1].geometry.parameters.width / 2,
            gripper.children[1].geometry.parameters.height / 2,
            gripper.children[1].geometry.parameters.depth / 2,
        ),
    );
    var gripper1Body = new CANNON.Body({
        mass: 1, // Set mass to 0 for kinematic bodies
        material: robotMaterial,
        type: CANNON.Body.KINEMATIC,
    });
    var gripper2Body = new CANNON.Body({
        mass: 1, // Set mass to 0 for kinematic bodies
        material: robotMaterial,
        type: CANNON.Body.KINEMATIC,
    });
    gripper1Body.addShape(gripper1);
    gripper2Body.addShape(gripper2);
    gripper1Body.position.copy(gripper.children[0].position);
    gripper2Body.position.copy(gripper.children[1].position);
    gripper1Body.position.y = 0;
    gripper2Body.position.y = 0;
    gripper1Body.quaternion.copy(gripper.children[0].quaternion);
    gripper2Body.quaternion.copy(gripper.children[1].quaternion);
    parentBody.addShape(gripper1, new CANNON.Vec3(0, 0, 0));
    parentBody.addShape(gripper2, new CANNON.Vec3(0, 0, 0));

    return [gripper1Body, gripper2Body];
}
