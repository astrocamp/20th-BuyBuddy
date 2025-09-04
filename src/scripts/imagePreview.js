const imagePreview = (initialUrl) => {
	return {
		imageUrl: initialUrl,
		
		handleFile(event) {
			const file = event.target.files[0]
			if (file && file.type.startsWith("image/")) {
				const reader = new FileReader()
				reader.onload = (e) => {
					this.imageUrl = e.target.result
				}
				reader.readAsDataURL(file)
			}
		},
	}
}

export { imagePreview }