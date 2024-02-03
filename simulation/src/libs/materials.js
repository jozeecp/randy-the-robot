import * as THREE from "three";
import * as CANNON from "cannon-es";

export const colors = {
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

export var material_red = new THREE.MeshStandardMaterial({
    color: colors.red,
    metalness: 0.5,
    roughness: 0.5,
});

export var material_green = new THREE.MeshStandardMaterial({
    color: colors.green,
    metalness: 0.5,
    roughness: 0.5,
});

export var material_blue = new THREE.MeshStandardMaterial({
    color: colors.blue,
    metalness: 0.5,
    roughness: 0.5,
});

export var material_white = new THREE.MeshStandardMaterial({
    color: colors.white,
    metalness: 0.5,
    roughness: 0.5,
});

export const robotMaterial = new CANNON.Material();
