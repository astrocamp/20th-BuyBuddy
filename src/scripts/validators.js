const validators = () => {
  return {
    min_goal: '',
    init(){
      if (this.$refs.min_goal.attributes.value){
        this.min_goal = this.$refs.min_goal.attributes.value.value;
      }
    },
    removeZero(){
      this.min_goal = this.min_goal.replace(/^0+/, '') || '1';
    }
  }
}

export { validators };