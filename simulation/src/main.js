import * as THREE from 'three';
import { GUI } from 'dat.gui';
import mqtt from 'mqtt';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
import { metersToUnits } from './libs/utils';

// Scene setup
var scene = new THREE.Scene();

// Camera setup
var aspect = window.innerWidth / window.innerHeight;
var camera = new THREE.PerspectiveCamera(60, aspect, 0.1, 1000);
camera.position.set(-15, 5, 0);
camera.lookAt(0, 0, 0);


// Renderer setup
var renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setSize(window.innerWidth, window.innerHeight);
document.body.appendChild(renderer.domElement);

const controls = new OrbitControls(camera, renderer.domElement);

const colors = {
    red: 0xff0000,
    green: 0x00ff00,
    blue: 0x0000ff,
    yellow: 0xffff00,
    cyan: 0x00ffff,
    magenta: 0xff00ff,
    white: 0xffffff,
    black: 0x000000,
    bluewhite: 0x1560bd,
    offwhite: 0xf1f1f1,
    bloodred: 0x660000,
    steelblue: 0x161a2e,
    darkforestgreen: 0x0c210e,
};

// Material
var material_red = new THREE.MeshStandardMaterial({
    color: colors.red,
    metalness: 0.5,
    roughness: 0.5
});

var material_green = new THREE.MeshStandardMaterial({
    color: colors.green,
    metalness: 0.5,
    roughness: 0.5
});

var material_blue = new THREE.MeshStandardMaterial({
    color: colors.blue,
    metalness: 0.5,
    roughness: 0.5
});

var material_white = new THREE.MeshStandardMaterial({
    color: colors.white,
    metalness: 0.5,
    roughness: 0.5
});

// Robot arm construction
var table = new THREE.Mesh(new THREE.BoxGeometry(metersToUnits(0.762), 0.5, metersToUnits(1.4986)), material_white);
var base = new THREE.Mesh(new THREE.BoxGeometry(1.4, metersToUnits(0.1016), 1.4), material_blue);
scene.add(table);
table.add(base);
base.position.y = table.geometry.parameters.height / 2 + base.geometry.parameters.height / 2;
base.position.x = -table.geometry.parameters.width / 2 + base.geometry.parameters.width / 2;
base.position.z = -table.geometry.parameters.depth / 2 + base.geometry.parameters.depth / 2;

var joints = [];
var segments = [];

function updateCameraTarget() {
    controls.target.set(
        options.camera.targetX,
        options.camera.targetY,
        options.camera.targetZ
    );
    controls.update();
}

// Helper function to create a joint and a segment
function createJointAndSegment(parent, previousSegmentLength, segmentLength, material) {
    // Create the joint as an empty Object3D
    var joint = new THREE.Object3D();

    if (parent === base) {
        // Position the joint at the top of the base
        joint.position.y = previousSegmentLength + base.geometry.parameters.height / 2;
    }else {
        joint.position.y = previousSegmentLength;
    }

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

function createGripper(parent, previousSegmentLength, material) {
    // create two boxes
    const y_offset = .750;
    var gripper = new THREE.Object3D();
    var gripper1 = new THREE.Mesh(new THREE.BoxGeometry(0.125, 0.25, 0.25), material);
    var gripper2 = new THREE.Mesh(new THREE.BoxGeometry(0.125, 0.25, 0.25), material);
    gripper1.position.y = y_offset;
    gripper2.position.y = y_offset;
    gripper.add(gripper1);
    gripper.add(gripper2);
    parent.add(gripper);

    // add vector arrows to show the gripper's orientation
    var origin = new THREE.Vector3(0, 0, 0);
    var length = 1;

    var gripperArrow1 = new THREE.ArrowHelper(new THREE.Vector3(1, 0, 0), origin, length, colors.red);
    var gripperArrow2 = new THREE.ArrowHelper(new THREE.Vector3(0, 1, 0), origin, length, colors.green);
    var gripperArrow3 = new THREE.ArrowHelper(new THREE.Vector3(0, 0, 1), origin, length, colors.blue);

    gripperArrow1.position.y = y_offset;
    gripperArrow2.position.y = y_offset;
    gripperArrow3.position.y = y_offset;
    gripper.add(gripperArrow1);
    gripper.add(gripperArrow2);
    gripper.add(gripperArrow3);

    return gripper;
}

// Connect to the MQTT broker
const client = mqtt.connect('ws://192.168.4.154:8083/mqtt', {
    clientId: 'robot_gui' + Math.random().toString(16),
    username: 'robot_gui',
    password: 'robot_gui',
    protocol: 'ws',
});
console.log(`Connecting to MQTT broker at ${client.options.hostname}:${client.options.port}`);
client.on('error', (error) => {
    console.error('MQTT error:', error);
});

// Topics that the client will subscribe to
const topics = {
    base: 'robot/base/position',
    shoulder: 'robot/shoulder/position',
    elbow: 'robot/elbow/position',
    wrist: 'robot/wrist0/position',
    wrist2: 'robot/wrist1/position',
    wrist3: 'robot/wrist2/position',
    hand: 'robot/gripper/position',
};

var options = {
    base: 0,
    shoulder: 0,
    elbow: 0,
    wrist: 0,
    wrist2: 0,
    wrist3: 0,
    hand: 0
};

// Subscribe to the topics
client.on('connect', function () {
    client.subscribe(Object.values(topics), function (err) {
        if (!err) {
            console.log('MQTT subscription successful');
        } else {
            console.log('MQTT subscription failed');
        }
    });
});

// Update joint angles when a message is received
client.on('message', function (topic, message) {
    console.log(topic, message.toString());
    // message is a buffer, convert it to a string and parse to a number
    const angle = parseFloat(message.toString());
    
    // Determine which joint the message is for and update its angle
    if (topic === topics.base) {
        options.base = angle;
    } else if (topic === topics.shoulder) {
        options.shoulder = angle;
    }
    else if (topic === topics.elbow) {
        options.elbow = angle;
    }
    else if (topic === topics.wrist) {
        options.wrist = angle;
    }
    else if (topic === topics.wrist2) {
        options.wrist2 = angle;
    }
    else if (topic === topics.wrist3) {
        options.wrist3 = angle;
    }
    else if (topic === topics.hand) {
        options.hand = angle;
    }
});

// Creating the robot arm
var lengths_m = {
    shoulder: 0.381,
    elbow: 0.254,
    wrist0: 0.0,
    wrist1: 0.0254, //0.0254 + 0.0635
    wrist2: 0.0635,
}

var shoulder = createJointAndSegment(base, 0, metersToUnits(lengths_m.shoulder), material_red);
var elbow = createJointAndSegment(shoulder, metersToUnits(lengths_m.shoulder), metersToUnits(lengths_m.elbow), material_green);
var wrist = createJointAndSegment(elbow, metersToUnits(lengths_m.elbow), metersToUnits(lengths_m.wrist0), material_blue);
var wrist2 = createJointAndSegment(wrist, metersToUnits(lengths_m.wrist0), metersToUnits(lengths_m.wrist1), material_red);
var wrist3 = createJointAndSegment(wrist2, metersToUnits(lengths_m.wrist1), metersToUnits(lengths_m.wrist2), material_blue);
var hand = createGripper(wrist3, metersToUnits(lengths_m.wrist2), material_green);

// Lighting
var light1 = new THREE.DirectionalLight(colors.cyan, 1.0);
var light2 = new THREE.DirectionalLight(colors.cyan, 1.0);
var light3 = new THREE.DirectionalLight(colors.magenta, 1.0);
light1.position.set(0, 5, 2);
light2.position.set(0, 5, 0);
light3.position.set(0, 5, -2);
light1.target = base;
light2.target = base;
light3.target = base;
scene.add(light1);
scene.add(light2);
scene.add(light3);
scene.add(new THREE.AmbientLight(colors.offwhite, 0.5));
scene.add(new THREE.AxesHelper(5));

// Control options

// GUI controls
var gui = new GUI();
gui.add(options, 'base', -180, 180).listen();
gui.add(options, 'shoulder', -180, 180).listen();
gui.add(options, 'elbow', -180, 180).listen();
gui.add(options, 'wrist', -180, 180).listen();
gui.add(options, 'wrist2', -180, 180).listen();
gui.add(options, 'wrist3', -180, 180).listen();
gui.add(options, 'hand', 0, 90).listen();

// Adding camera control options
options.camera = {
    posX: camera.position.x,
    posY: camera.position.y,
    posZ: camera.position.z,
    targetX: controls.target.x,
    targetY: controls.target.y,
    targetZ: controls.target.z,
};

// Add GUI controls for the camera
// const cameraFolder = gui.addFolder('Camera');
// cameraFolder.add(options.camera, 'posX', -100, 100).onChange(updateCameraPosition);
// cameraFolder.add(options.camera, 'posY', -100, 100).onChange(updateCameraPosition);
// cameraFolder.add(options.camera, 'posZ', -100, 100).onChange(updateCameraPosition);
// cameraFolder.add(options.camera, 'targetX', -100, 100).onChange(updateCameraTarget);
// cameraFolder.add(options.camera, 'targetY', -100, 100).onChange(updateCameraTarget);
// cameraFolder.add(options.camera, 'targetZ', -100, 100).onChange(updateCameraTarget);
// cameraFolder.open();

// Functions to update the camera position and target
function updateCameraPosition() {
    camera.position.set(options.camera.posX, options.camera.posY, options.camera.posZ);
    controls.update();
}

// How far you can dolly in and out (PerspectiveCamera only)
controls.minDistance = 1;
controls.maxDistance = 100;

// How far you can zoom in and out (OrthographicCamera only)
// controls.minZoom = 0.5;
// controls.maxZoom = 2;

// Set the position of the target the camera is looking at
controls.target.set(0, 1.5, 0);

// Optional: Enable damping (inertia), which can give a smoother user experience
controls.enableDamping = true;
controls.dampingFactor = 0.05;

// Axes for rotation
var zAxis = new THREE.Vector3(0, 0, 1);
var yAxis = new THREE.Vector3(0, 1, 0);
var xAxis = new THREE.Vector3(1, 0, 0);

var updateGripper = function (gripper, openness) {
    const half_thickness = 0.125 / 2;
    gripper.children[0].position.x = half_thickness + openness / 720;
    gripper.children[1].position.x = - half_thickness - openness / 720;
}


// Render loop
var render = function () {
    requestAnimationFrame(render);

    // Apply rotations based on GUI controls
    base.setRotationFromAxisAngle(yAxis, options.base * Math.PI / 180 + Math.PI / 2);
    shoulder.setRotationFromAxisAngle(zAxis, options.shoulder * Math.PI / 180);
    elbow.setRotationFromAxisAngle(zAxis, options.elbow * Math.PI / 180);
    wrist.setRotationFromAxisAngle(yAxis, options.wrist * Math.PI / 180);
    wrist2.setRotationFromAxisAngle(zAxis, -options.wrist2 * Math.PI / 180);
    wrist3.setRotationFromAxisAngle(yAxis, options.wrist3 * Math.PI / 180);
    updateGripper(hand, options.hand);

    controls.update();

    // Render the scene
    renderer.render(scene, camera);
};

render();
