import "htmx.org";
import Alpine from "alpinejs";
import { messagesControl } from "./messages.js";
import { validators } from "./validators.js";
import { avatarPreview } from "./avatarPreview.js";

window.Alpine = Alpine;
Alpine.data("messagesControl", messagesControl);
Alpine.data("validators", validators);
Alpine.data("avatarPreview", avatarPreview);
Alpine.start();
