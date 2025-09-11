const backToTopBtnControl = () => {
  return {
    showBackToTop: false,
    showNavbar: true,
    lastScrollY: 0,

    handleBackToTop() {
      if (window.scrollY > 200) {
        this.showBackToTop = true;
      } else {
        this.showBackToTop = false;
      }
    },
  };
};

export { backToTopBtnControl };
