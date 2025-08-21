const createGroup = () => {
  return {
    min_goal: '',
    removeZero(){
      this.min_goal = this.min_goal.replace(/^0+/, '') || '0';
    }
  }
}

export { createGroup };