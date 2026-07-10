/** @odoo-module **/

import { registry } from "@web/core/registry";
import { rpc } from "@web/core/network/rpc";

function validStrColour(strToTest) {
    if (strToTest === "") return false;
    if (strToTest === "inherit") return true;
    if (strToTest === "transparent") return true;
    const image = document.createElement("img");
    image.style.color = "rgb(0, 0, 0)";
    image.style.color = strToTest;
    if (image.style.color !== "rgb(0, 0, 0)") return true;
    image.style.color = "rgb(255, 255, 255)";
    image.style.color = strToTest;
    return image.style.color !== "rgb(255, 255, 255)";
}

const ribbonService = {
    start() {
        rpc("/web/environment/ribbon").then((data) => {
            const ribbon = document.createElement("div");
            ribbon.className = "test-ribbon";
            if (data.name && data.name !== "False") {
                ribbon.innerHTML = data.name;
            } else {
                ribbon.style.display = "none";
            }
            if (data.color && validStrColour(data.color)) {
                ribbon.style.color = data.color;
            }
            if (data.background_color && validStrColour(data.background_color)) {
                ribbon.style.backgroundColor = data.background_color;
            }
            document.body.appendChild(ribbon);
        });
    },
};

registry.category("services").add("web_environment_ribbon.ribbon", ribbonService);
