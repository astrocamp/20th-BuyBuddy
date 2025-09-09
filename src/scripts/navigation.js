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

      // 當滾動到頂部時（scrollY為0或接近0）強制顯示導航欄
      if (currentScrollY <= 10) {
        this.showNavbar = true;
      } else if (currentScrollY > this.lastScrollY) {
        this.showNavbar = false;
      } else {
        this.showNavbar = true;
      }
      this.lastScrollY = currentScrollY;
    },
  };
};

export { navigationControl };
