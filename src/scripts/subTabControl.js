const subTabControl = () => {
  return {
    scrollSubTab() {
      if (window.innerWidth < 769 && this.$refs.activeTab) {
        let parent = this.$el;
        let tab = this.$refs.activeTab;
        let parentRect = parent.getBoundingClientRect();
        let tabRect = tab.getBoundingClientRect();
        let scrollLeft =
          tab.offsetLeft -
          parent.offsetLeft +
          tabRect.width / 2 -
          parentRect.width / 2;
        parent.scrollTo({ left: scrollLeft, behavior: "smooth" });
      }
    },
  };
};

export { subTabControl };
