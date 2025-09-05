const imagePreview = (initialUrl) => {
  return {
    imageUrl: initialUrl,
    fileName: null,

    handleFile(event) {
      const file = event.target.files[0];
      if (file && file.type.startsWith("image/")) {
        // 取檔案名前十個字
        this.fileName =
          file.name.length > 10
            ? file.name.substring(0, 10) + "..."
            : file.name;

        const reader = new FileReader();
        reader.onload = (e) => (this.avatarUrl = e.target.result);
        reader.readAsDataURL(file);
      }
    },
  };
};

export { imagePreview };
