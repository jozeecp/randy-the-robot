import * as THREE from "three";
import { GUI } from "dat.gui";
import mqtt from "mqtt";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";
import { metersToUnits } from "./libs/utils";
import * as CANNON from "cannon-es";
import {
    createCannonKinematicBodyFromThreeMesh,
    createJointAndSegment,
    createPhysicsBodiesFromGripper,
    createGripper,
} from "./libs/cannon_helpers";
import {
    colors,
    material_blue,
    material_green,
    material_red,
    material_white,
    robotMaterial,
} from "./libs/materials";
import { topics } from "./libs/constants";
import { client } from "./libs/mqtt";

// Initialize the physics world
const world = new CANNON.World();
world.gravity.set(0, -9.82, 0); // Set gravity in the negative z direction

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

// Example: Add ground plane to the physics world
const groundMaterial = new CANNON.Material();
const groundBody = new CANNON.Body({
    mass: 0, // mass = 0 makes the ground static
    shape: new CANNON.Plane(),
    material: groundMaterial,
});
groundBody.quaternion.setFromEuler(-Math.PI / 2, 0, 0); // Rotate to match the ground plane
groundBody.position.y = 0.25; // Lower the ground by 0.5 units to match the base of the robot
world.addBody(groundBody);

// Robot arm construction
var table = new THREE.Mesh(
    new THREE.BoxGeometry(metersToUnits(0.762), 0.5, metersToUnits(1.4986)),
    material_white,
);
var base = new THREE.Mesh(
    new THREE.BoxGeometry(1.4, metersToUnits(0.1016), 1.4),
    material_blue,
);
scene.add(table);
table.add(base);
base.position.y =
    table.geometry.parameters.height / 2 + base.geometry.parameters.height / 2;
base.position.x =
    -table.geometry.parameters.width / 2 + base.geometry.parameters.width / 2;
base.position.z =
    -table.geometry.parameters.depth / 2 + base.geometry.parameters.depth / 2;

// Example: Add physics to the robot base
const baseBody = createCannonKinematicBodyFromThreeMesh(
    world,
    base,
    robotMaterial,
    table.geometry.parameters.height / 2 + base.geometry.parameters.height / 2,
);

function updateCameraTarget() {
    controls.target.set(
        options.camera.targetX,
        options.camera.targetY,
        options.camera.targetZ,
    );
    controls.update();
}

var cubeMaterial = new CANNON.Material();
var cubeRobotContactMaterial = new CANNON.ContactMaterial(
    cubeMaterial,
    robotMaterial,
    {
        friction: 0.3,
        restitution: 0.1,
    },
);
world.addContactMaterial(cubeRobotContactMaterial);
world.addContactMaterial(new CANNON.ContactMaterial(cubeMaterial, groundMaterial, {
    friction: 0.3,
    restitution: 0.1,
}));
// Function to add a cube
function addCube(x, y, z, size) {
    const geometry = new THREE.BoxGeometry(size, size, size);
    const mesh = new THREE.Mesh(geometry, material_red);
    mesh.position.set(x, y, z);
    scene.add(mesh);

    const shape = new CANNON.Box(new CANNON.Vec3(size / 2, size / 2, size / 2));
    const body = new CANNON.Body({
        mass: 1,
        material: cubeMaterial,
    });
    body.addShape(shape);
    body.position.set(x, y, z);
    world.addBody(body);

    return { mesh, body };
}

var options = {
    base: 0,
    shoulder: 0,
    elbow: 0,
    wrist: 0,
    wrist2: 0,
    wrist3: 0,
    hand: 0,
};

// Update joint angles when a message is received
client.on("message", function (topic, message) {
    // console.log(topic, message.toString());
    // message is a buffer, convert it to a string and parse to a number
    const angle = parseFloat(message.toString());

    // Determine which joint the message is for and update its angle
    if (topic === topics.base) {
        options.base = angle;
    } else if (topic === topics.shoulder) {
        options.shoulder = angle;
    } else if (topic === topics.elbow) {
        options.elbow = angle;
    } else if (topic === topics.wrist) {
        options.wrist = angle;
    } else if (topic === topics.wrist2) {
        options.wrist2 = angle;
    } else if (topic === topics.wrist3) {
        options.wrist3 = angle;
    } else if (topic === topics.hand) {
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
};

var shoulder = createJointAndSegment(
    base,
    base,
    0,
    metersToUnits(lengths_m.shoulder),
    material_red,
);
var elbow = createJointAndSegment(
    base,
    shoulder,
    metersToUnits(lengths_m.shoulder),
    metersToUnits(lengths_m.elbow),
    material_green,
);
var wrist = createJointAndSegment(
    base,
    elbow,
    metersToUnits(lengths_m.elbow),
    metersToUnits(lengths_m.wrist0),
    material_blue,
);
var wrist2 = createJointAndSegment(
    base,
    wrist,
    metersToUnits(lengths_m.wrist0),
    metersToUnits(lengths_m.wrist1),
    material_red,
);
var wrist3 = createJointAndSegment(
    base,
    wrist2,
    metersToUnits(lengths_m.wrist1),
    metersToUnits(lengths_m.wrist2),
    material_blue,
);
var hand = createGripper(
    wrist3,
    metersToUnits(lengths_m.wrist2),
    material_green,
);

// Add the robot arm to the physics world
var shoulderBody = createCannonKinematicBodyFromThreeMesh(
    world,
    shoulder.children[0],
    robotMaterial,
    base.geometry.parameters.height / 2,
);
world.addBody(shoulderBody);
var elbowBody = createCannonKinematicBodyFromThreeMesh(
    world,
    elbow.children[0],
    robotMaterial,
    metersToUnits(lengths_m.shoulder),
);
world.addBody(elbowBody);
var wristBody = createCannonKinematicBodyFromThreeMesh(
    world,
    wrist.children[0],
    robotMaterial,
    metersToUnits(lengths_m.elbow),
);
world.addBody(wristBody);
var wrist2Body = createCannonKinematicBodyFromThreeMesh(
    world,
    wrist2.children[0],
    robotMaterial,
    metersToUnits(lengths_m.wrist0),
);
world.addBody(wrist2Body);
var wrist3Body = createCannonKinematicBodyFromThreeMesh(
    world,
    wrist3.children[0],
    robotMaterial,
    metersToUnits(lengths_m.wrist1),
);
world.addBody(wrist3Body);
var [gb1, gb2] = createPhysicsBodiesFromGripper(
    hand,
    wrist3Body,
    metersToUnits(lengths_m.wrist2),
);
console.log(gb1, gb2);
world.addBody(gb1);
world.addBody(gb2);

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

// Add a cube
let cube = addCube(
    metersToUnits(-0.1),
    metersToUnits(0.5),
    metersToUnits(-0.4),
    metersToUnits(0.1),
);
cube.body.addEventListener("collide", function(e) {
    console.log("Collision detected with", e.body);
});

// Control options

// GUI controls
var gui = new GUI();
gui.add(options, "base", -180, 180).listen();
gui.add(options, "shoulder", -180, 180).listen();
gui.add(options, "elbow", -180, 180).listen();
gui.add(options, "wrist", -180, 180).listen();
gui.add(options, "wrist2", -180, 180).listen();
gui.add(options, "wrist3", -180, 180).listen();
gui.add(options, "hand", 0, 90).listen();

// Adding camera control options
options.camera = {
    posX: camera.position.x,
    posY: camera.position.y,
    posZ: camera.position.z,
    targetX: controls.target.x,
    targetY: controls.target.y,
    targetZ: controls.target.z,
};

// Functions to update the camera position and target
function updateCameraPosition() {
    camera.position.set(
        options.camera.posX,
        options.camera.posY,
        options.camera.posZ,
    );
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
    gripper.children[1].position.x = -half_thickness - openness / 720;
};

var updatePhysics = function () {
    // Update the physics world
    world.step(1 / 60); // Assuming 60 FPS, adjust as needed

    // Sync Three.js object with Cannon body
    base.position.copy(baseBody.position);
    base.quaternion.copy(baseBody.quaternion);
    shoulder.position.copy(shoulderBody.position);
    shoulder.quaternion.copy(shoulderBody.quaternion);
    elbow.position.copy(elbowBody.position);
    elbow.quaternion.copy(elbowBody.quaternion);
    wrist.position.copy(wristBody.position);
    wrist.quaternion.copy(wristBody.quaternion);
    wrist2.position.copy(wrist2Body.position);
    wrist2.quaternion.copy(wrist2Body.quaternion);
    wrist3.position.copy(wrist3Body.position);
    wrist3.quaternion.copy(wrist3Body.quaternion);
    hand.position.copy(gb1.position);
    hand.quaternion.copy(gb1.quaternion);
    hand.position.copy(gb2.position);
    hand.quaternion.copy(gb2.quaternion);

    cube.mesh.position.copy(cube.body.position);
    cube.mesh.quaternion.copy(cube.body.quaternion);
};

// Render loop
var render = function () {
    requestAnimationFrame(render);

    // Update the physics world
    updatePhysics();

    // Apply rotations based on GUI controls
    base.setRotationFromAxisAngle(
        yAxis,
        (options.base * Math.PI) / 180 + Math.PI / 2,
    );
    shoulder.setRotationFromAxisAngle(
        zAxis,
        (options.shoulder * Math.PI) / 180,
    );
    elbow.setRotationFromAxisAngle(zAxis, (options.elbow * Math.PI) / 180);
    wrist.setRotationFromAxisAngle(yAxis, (options.wrist * Math.PI) / 180);
    wrist2.setRotationFromAxisAngle(zAxis, (-options.wrist2 * Math.PI) / 180);
    wrist3.setRotationFromAxisAngle(yAxis, (options.wrist3 * Math.PI) / 180);
    updateGripper(hand, options.hand);

    controls.update();

    // Render the scene
    renderer.render(scene, camera);
};

render();
