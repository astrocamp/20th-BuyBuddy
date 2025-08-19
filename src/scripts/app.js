import Alpine from "alpinejs";
import { messagesControl } from "./messages.js";

window.Alpine = Alpine;
Alpine.data("messagesControl", messagesControl);

Alpine.start();
