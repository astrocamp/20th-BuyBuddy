const productFormset = () => {
  return {
	totalFormsInput: null,
	formsContainer: null,
	emptyFormTemplate: null,

	init() {
		this.totalFormsInput = document.getElementById("id_product-TOTAL_FORMS")
		this.formsContainer = this.$refs.formsContainer
		this.emptyFormTemplate = this.$refs.emptyFormTemplate
	},

	addForm() {
		let formIdx = parseInt(this.totalFormsInput.value)
		const newFormHtml = this.emptyFormTemplate.innerHTML.replace(/__prefix__/g, formIdx)
		this.formsContainer.insertAdjacentHTML("beforeend", newFormHtml)
		this.totalFormsInput.value = formIdx +1
	}
}}

export { productFormset}

