const navigationControl = () => {
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

    handleNavbar() {
      const currentScrollY = window.scrollY;

      if (currentScrollY > this.lastScrollY) {
        this.showNavbar = false;
      } else {
        this.showNavbar = true;
      }
      this.lastScrollY = currentScrollY;
    },
  };
};

export { navigationControl };
