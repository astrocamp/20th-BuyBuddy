import Toastify from "toastify-js";

const messagesControl = () => {
  return {
    items: [],
    showAllFrom(jsonRef) {
      if (!jsonRef) {
        // DEVLOG: 沒有訊息
        // console.log("沒有訊息");
        return;
      }

      try {
        const content = jsonRef.textContent.trim();
        // DEVLOG: 訊息內容
        // console.log("訊息內容:", content);

        if (!content) {
          // DEVLOG: 沒有訊息內容
          // console.log("沒有訊息內容");
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

        messages.forEach(({ text, level }) => {
          if (!text) return;

          const kind = (level || "info").split(" ")[0];
          const bg =
            {
              success: "#259a50ff",
              info: "#2b65e2ff",
              warning: "#d78512ff",
              error: "#c23232ff",
            }[kind] || "#2b65e2ff";

          // DEVLOG: Toastify 內容
          // console.log("Showing toast:", text, level);

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
