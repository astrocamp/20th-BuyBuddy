import "htmx.org";
import Alpine from "alpinejs";
import { messagesControl } from "./messages.js";
import { validators } from "./validators.js";
import { avatarPreview } from "./avatarPreview.js";
import { setupTinyMCECsrf } from "./tinymceCsrf.js";
import { productFormset } from "./productFormset.js";
import { navigationControl } from "./navigation.js";

window.Alpine = Alpine;
Alpine.data("messagesControl", messagesControl);
Alpine.data("validators", validators);
Alpine.data("avatarPreview", avatarPreview);
Alpine.data("productFormset", productFormset);
Alpine.data("navigationControl", navigationControl);

Alpine.start();

document.addEventListener("DOMContentLoaded", function () {
  setupTinyMCECsrf();
});
