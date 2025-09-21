function lineAuth() {
  const lineBtn = document.getElementById('line-oauth2-btn');
  if (lineBtn) {
    lineBtn.addEventListener('click', function(e) {
      e.preventDefault();
      triggerLineSignIn();
    });
  }
}

async function getLineClient() {
  const response = await fetch('/users/js_line_client/');
  const data = await response.json();
  return data;
}

async function triggerLineSignIn() {
  const lineClient = await getLineClient();
  window.location.href = lineClient.auth_url;
}

export { lineAuth }