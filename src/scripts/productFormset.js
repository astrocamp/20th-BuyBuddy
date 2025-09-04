const productFormset = () => {
  return {
	totalFormsInput: null,
	formsContainer: null,
	emptyFormTemplate: null,
	limitedConfig: null,

	init() {
		this.totalFormsInput = document.getElementById("id_product-TOTAL_FORMS")
		this.formsContainer = this.$refs.formsContainer
		this.emptyFormTemplate = this.$refs.emptyFormTemplate
		const configStr = this.$el.dataset.limitedConfig;
		if (configStr) {
            this.limitedConfig = JSON.parse(configStr);
        } else {
            console.error("找不到 'data-limited-config' 設定！");
            this.limitedConfig = {};
        }
	},

	addForm() {
		let formIdx = parseInt(this.totalFormsInput.value)
		const newFormHtml = this.emptyFormTemplate.innerHTML.replace(/__prefix__/g, formIdx)
		this.$refs.addButton.insertAdjacentHTML("beforebegin", newFormHtml)

		const newTextareaId = `id_product-${formIdx}-description`;
		const finalSettings = {
            ...this.limitedConfig, 
            selector: `#${newTextareaId}`, 
        };
		tinymce.init(finalSettings);
		this.totalFormsInput.value = formIdx +1


	}
}}

export { productFormset}

