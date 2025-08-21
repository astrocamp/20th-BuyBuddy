import Toastify from "toastify-js";

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
          const bgList = {
            success: "#259a50ff",
            info: "#2b65e2ff",
            warning: "#d78512ff",
            error: "#c23232ff",
          };
          const bg = bgList[type] || "#2b65e2ff";

          // DEVLOG: Toastify 內容
          // console.log("Showing toast:", text, tag);

          Toastify({
            text,
            gravity: "top",
            position: "center",
            close: true,
            duration: 3500,
            style: {
              background: bg,
              borderRadius: "8px",
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
