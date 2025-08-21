import Alpine from "alpinejs";
import { messagesControl } from "./messages.js";
import { createGroup } from "./create_group.js";

window.Alpine = Alpine;
Alpine.data("messagesControl", messagesControl);
Alpine.data("createGroup", createGroup);

Alpine.start();
