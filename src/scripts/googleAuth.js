function googleAuth() {
  // 綁定 Google 登入按鈕點擊事件
  const googleBtn = document.getElementById('google-signin-btn');
  if (googleBtn) {
    googleBtn.addEventListener('click', function(e) {
      e.preventDefault();
      triggerGoogleSignIn();
    });
  }
}

// 取得 Google Client ID
async function getClientId() {
  try{
    const response = await fetch('/users/js_google_client/')
    // 如果取得失敗，則跳轉到錯誤頁面
    if(!response.ok) {
      window.location.href = '/users/error/?type=config_error';
      return null;
    }
    // 如果取得成功，則返回 Google Client ID
    const data = await response.json()
    return data.client_id
  }catch(error) {
    // 如果取得失敗，則跳轉到錯誤頁面
    window.location.href = '/users/error/?type=network_error';
    return null
  }
}


// 觸發 Google OAuth2 Popup 登入
async function triggerGoogleSignIn() {
  const clientId = await getClientId();
  if (typeof google !== 'undefined' && google.accounts && google.accounts.oauth2) {
    const client = google.accounts.oauth2.initCodeClient({
      client_id: clientId,
      scope: 'email profile openid',
      ux_mode: 'popup',
      callback: handleGoogleOAuthResponse
    });
    client.requestCode();
  }
}

// Google OAuth2 Popup 登入處理
function handleGoogleOAuthResponse(response) {
  if (response.code) {
    document.getElementById('google_code').value = response.code;
    document.getElementById('social_provider').value = 'google';
    document.getElementById('google-oauth2-form').submit();
  }else if (response.error) {
    window.location.href = '/users/error/?type=auth_failed';
    return;
  }
}        


export { googleAuth };