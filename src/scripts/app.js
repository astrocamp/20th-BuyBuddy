import "htmx.org";
import Alpine from "alpinejs";
import { messagesControl } from "./messages.js";
import { validators } from "./validators.js";
import { imagePreview } from "./imagePreview.js";
import { setupTinyMCECsrf } from "./tinymceCsrf.js";
import { productFormset } from "./productFormset.js";
import { backToTopBtnControl } from "./backToTopBtn.js";
import { addressFormControl } from "./address.js";
import { googleAuth } from "./googleAuth.js";
import { subTabControl } from "./subTabControl.js";

window.Alpine = Alpine;
Alpine.data("messagesControl", messagesControl);
Alpine.data("validators", validators);
Alpine.data("imagePreview", imagePreview);
Alpine.data("productFormset", productFormset);
Alpine.data("backToTopBtnControl", backToTopBtnControl);
Alpine.data("addressFormControl", addressFormControl);
Alpine.data("subTabControl", subTabControl);
Alpine.start();

document.addEventListener("DOMContentLoaded", function () {
  setupTinyMCECsrf();
  googleAuth();
});
