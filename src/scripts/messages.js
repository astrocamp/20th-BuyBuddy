import Toastify from "toastify-js";

const bgList = {
  success: "#3d7757ff",
  info: "#293343",
  warning: "#d78512ff",
  error: "#d85c34ff",
};
const infoColor = bgList["info"];

const messagesControl = () => {
  return {
    items: [],

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

          const type = (tag || "info").split(" ")[0];
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
