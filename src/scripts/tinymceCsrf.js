// src/scripts/tinymceCsrf.js
function setupTinyMCECsrf() {
    setTimeout(function() {
        const textareas = document.querySelectorAll('textarea[data-mce-conf]');
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
        
        let hasUploadCapability = false;
        textareas.forEach(textarea => {
            try {
                const mceConf = JSON.parse(textarea.getAttribute('data-mce-conf') || '{}');
                if (mceConf.images_upload_url) {
                    hasUploadCapability = true;
                }
            } catch (e) {}
        });

		 if (!hasUploadCapability || !csrfToken) {
            return; 
        }

        interceptXHRForCsrf(csrfToken);
        
    }, 500);
}

function interceptXHRForCsrf(csrfToken) {    
    const originalXHR = window.XMLHttpRequest;
    const uploadUrl = document.querySelector('form[data-upload-url]')?.dataset.uploadUrl;

	if (!uploadUrl) return;

    window.XMLHttpRequest = function() {
        const xhr = new originalXHR();
        const originalOpen = xhr.open;
        const originalSend = xhr.send;
        
        xhr.open = function(method, url) {
            if (method === 'POST' && url === uploadUrl) {
                this._isUploadRequest = true;
            }
            return originalOpen.apply(this, arguments);
        };
        
        xhr.send = function(data) {
            if (this._isUploadRequest && data instanceof FormData) {
                data.append('csrfmiddlewaretoken', csrfToken);
            }
            return originalSend.apply(this, arguments);
        };
        
        return xhr;
    };
}

export { setupTinyMCECsrf };