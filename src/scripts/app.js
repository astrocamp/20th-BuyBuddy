import Alpine from "alpinejs";
import { messagesControl } from "./messages.js";
import { validators } from "./validators.js";
import htmx from "htmx.org";

window.htmx = htmx;
window.Alpine = Alpine;
Alpine.data("messagesControl", messagesControl);
Alpine.data("validators", validators);


Alpine.start();
