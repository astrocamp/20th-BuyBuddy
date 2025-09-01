const avatarPreview = (initialUrl) => {
	return {
		avatarUrl: initialUrl,
		
		handleFile(event) {
			const file = event.target.files[0]
			if (file && file.type.startsWith("image/")) {
				const reader = new FileReader()
				reader.onload = (e) => this.avatarUrl = e.target.result
				reader.readAsDataURL(file)
			}
		}
	}
}

export { avatarPreview }