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
async function getGoogleClient() {
  try{
    const response = await fetch('/users/js_google_client/')

    // 如果取得失敗，則跳轉到錯誤頁面
    if(!response.ok) {
      window.location.href = '/users/error/?type=config_error';
      return null;
    }
    // 如果取得成功，則返回 Google Client ID
    const data = await response.json()
    return data
  }catch(error) {
    // 如果取得失敗，則跳轉到錯誤頁面
    window.location.href = '/users/error/?type=network_error';
    return null
  }
}


// 觸發 Google OAuth2 Popup 登入
async function triggerGoogleSignIn() {
  const googleClient = await getGoogleClient();

  if (!googleClient.GOOGLE_CLIENT_ID || !googleClient.HOSTNAME) {
    console.error('Google 設定無效或不完整:', googleClient);
    window.location.href = '/users/error/?type=config_error';
    return;
  }

  if (typeof google !== 'undefined' && google.accounts && google.accounts.oauth2) {
    const client = google.accounts.oauth2.initCodeClient({
      client_id: googleClient.GOOGLE_CLIENT_ID,
      scope: 'email profile openid',
      ux_mode: 'redirect',
      redirect_uri: `https://${googleClient.HOSTNAME}/users/social-oauth2/`
    });
    client.requestCode();
  }
}


export { googleAuth };