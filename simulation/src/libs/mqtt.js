import mqtt from "mqtt";
import { topics } from "./constants";

// Connect to the MQTT broker
export const client = mqtt.connect("ws://192.168.4.154:8083/mqtt", {
    clientId: "robot_gui" + Math.random().toString(16),
    username: "robot_gui",
    password: "robot_gui",
    protocol: "ws",
});
console.log(
    `Connecting to MQTT broker at ${client.options.hostname}:${client.options.port}`,
);
client.on("error", (error) => {
    console.error("MQTT error:", error);
});

// Subscribe to the topics
client.on("connect", function () {
    client.subscribe(Object.values(topics), function (err) {
        if (!err) {
            console.log("MQTT subscription successful");
        } else {
            console.log("MQTT subscription failed");
        }
    });
});
