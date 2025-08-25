document.addEventListener("alpine:init", () => {
  Alpine.data("countdown", (deadlineISOString) => ({
    deadline: new Date(deadlineISOString).getTime(),
    days: "00",
    hours: "00",
    minutes: "00",
    seconds: "00",
    init() {
      const updateCountdown = () => {
        const now = new Date().getTime();
        const distance = this.deadline - now;

        if (distance < 0) {
          clearInterval(this.timer);
          this.days = "00";
          this.hours = "00";
          this.minutes = "00";
          this.seconds = "00";
          return;
        }
        this.days = String(
          Math.floor(distance / (1000 * 60 * 60 * 24))
        ).padStart(2, "0");
        this.hours = String(
          Math.floor((distance % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60))
        ).padStart(2, "0");
        this.minutes = String(
          Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60))
        ).padStart(2, "0");
        this.seconds = String(
          Math.floor((distance % (1000 * 60)) / 1000)
        ).padStart(2, "0");
      };

      updateCountdown(); // Initial call to display immediately
      this.timer = setInterval(updateCountdown, 1000);

      // Alpine.js will call this cleanup function when the component is destroyed.
      this.$el.addEventListener('alpine:destroy', () => {
        clearInterval(this.timer);
      });
    },
  }));
});
