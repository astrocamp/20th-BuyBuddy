import "htmx.org";
import Alpine from "alpinejs";
import { messagesControl } from "./messages.js";
import { validators } from "./validators.js";
import { imagePreview } from "./imagePreview.js";
import { setupTinyMCECsrf } from "./tinymceCsrf.js";
import { productFormset } from "./productFormset.js";
import { navigationControl } from "./navigation.js";
import { addressFormControl } from "./address.js";

window.Alpine = Alpine;
Alpine.data("messagesControl", messagesControl);
Alpine.data("validators", validators);
Alpine.data("imagePreview", imagePreview);
Alpine.data("productFormset", productFormset);
Alpine.data("navigationControl", navigationControl);
Alpine.data("addressFormControl", addressFormControl);
Alpine.start();

document.addEventListener("DOMContentLoaded", function () {
  setupTinyMCECsrf();
});
