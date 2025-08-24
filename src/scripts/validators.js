const validators = () => {
  return {
    min_goal: '',
    init(){
      if (this.$refs.min_goal.hasAttribute('value')){
        this.min_goal = this.$refs.min_goal.getAttribute('value');
      }
    },
    removeZero(){
      this.min_goal = this.min_goal.replace(/^0+/, '') || '0';
    },
  }
}

export { validators };