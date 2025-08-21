const createGroup = () => {
  return {
    goal_choice: '',
    amount: '',
    quantity: '',
    choiceFocus(e){
      switch(e){
        case 'amount_input':
          this.$refs.amount_input.focus();
          this.goal_choice = 'amount';
          break;
        case 'amount_radio':
          this.$refs.amount_radio.checked = true;
          this.goal_choice = 'amount';
          break;
        case 'quantity_input':
          this.$refs.quantity_input.focus();
          this.goal_choice = 'quantity';
          break;
        case 'quantity_radio':
          this.$refs.quantity_radio.checked = true;
          this.goal_choice = 'quantity';
          break;
      }
    },
    removeZero(){
      this.amount = this.amount.replace(/^0+/, '') || '';
      this.quantity = this.quantity.replace(/^0+/, '') || '';
    },
    clearInput(){
      switch(this.goal_choice){
        case 'amount':
          this.quantity = '';
          break;
        case 'quantity':
          this.amount = '';
          break;
      }
    }
  }
}


export { createGroup };