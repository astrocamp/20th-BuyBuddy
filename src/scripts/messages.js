import Toastify from "toastify-js";

const bgList = {
  success: "#06890aff",
  warning: "#e57d0dff",
  error: "#df2e1aff",
  info: "#1e1f24",
};
const infoColor = bgList["info"];

const messagesControl = () => {
  return {
    items: [],
    modal: { show: false, title: "", text: "", type: "" },
    hasShownVerify: false,

    showAllFrom(jsonRef) {
      if (!jsonRef) {
        // DEVLOG: DOM 元素沒抓到
        // console.log("DOM 元素沒抓到");
        return;
      }

      try {
        const content = jsonRef.textContent.trim();
        // DEVLOG: 訊息內容
        // console.log("訊息內容:", content);

        if (!content) {
          // DEVLOG: 訊息內容為空
          // console.log("訊息內容為空");
          return;
        }

        const messages = JSON.parse(content);
        // DEVLOG: JSON 解析結果
        // console.log("訊息內容JSON:", messages);

        if (!Array.isArray(messages)) {
          // DEVLOG: 格式錯誤
          // console.log("訊息格式錯誤");
          return;
        }

        messages.forEach(({ text, tag }) => {
          if (!text) return;

          const tagsStr = String(tag || "");
          const isVerify = tagsStr.includes("verify");
          const fromRegister = tagsStr.includes("register");
          const fromProfile = tagsStr.includes("profile");
          const isSuccess = tagsStr.includes("success");

          if (!this.hasShownVerify && isVerify) {
            let title = "通知";
            if (fromRegister) {
              title = "註冊＆登入成功";
            } else if (fromProfile) {
              title = isSuccess ? "已寄出驗證信" : "驗證信寄送失敗";
            }

            this.modal.title = title;
            this.modal.text = text;
            this.modal.type = isSuccess ? "success" : "warning";
            this.modal.show = true;
            this.hasShownVerify = true;
            return;
          }

          const type = tagsStr.split(" ")[0] || "info";
          const bg = bgList[type] || infoColor;

          // DEVLOG: Toastify 內容
          // console.log("Showing toast:", text, tag);

          Toastify({
            text,
            gravity: "top",
            position: "center",
            close: true,
            duration: 3500,
            offset: {
              y: 10,
            },
            style: {
              background: bg,
              borderRadius: "50px",
              padding: "12px 20px",
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              gap: "5px",
            },
            stopOnFocus: true,
          }).showToast();
        });
      } catch (error) {
        // DEVLOG: 解析錯誤
        // console.log("解析訊息時發生錯誤:", error);
        return;
      }
    },
  };
};

export { messagesControl };
