let taiwanDistrictsCache = null;

const loadTaiwanDistrictsCache = async () => {
  if (taiwanDistrictsCache) {
    return taiwanDistrictsCache;
  }

  const valid = {};

  try {
    const response = await fetch("/assets/assets/taiwan-districts.json");
    const rawData = await response.json();

    rawData.forEach((item) => {
      const county = item.name;
      valid[county] = {};

      item.districts.forEach((d) => {
        valid[county][d.name] = d.zip;
      });
    });
    taiwanDistrictsCache = valid;
    return valid;
  } catch (error) {
    console.log("載入縣市資料失敗", error);
    return valid;
  }
};

const addressFormControl = () => {
  return {
    valid: {},

    async init() {
      try {
        this.valid = await loadTaiwanDistrictsCache();

        if (
          this.$refs.county &&
          this.$refs.county.options &&
          this.$refs.county.options.length > 0
        ) {
          this.$refs.county.options[0].disabled = true;
        }

        if (
          this.$refs.district &&
          this.$refs.district.options &&
          this.$refs.district.options.length > 0
        ) {
          this.$refs.district.options[0].disabled = true;
        }
      } catch (error) {
        console.error("初始化地址欄位失敗", error);
      }
    },

    getCurrentSelections() {
      return {
        county: this.$refs.county?.value,
        district: this.$refs.district?.value,
      };
    },

    applyDistrict() {
      const { county } = this.getCurrentSelections();

      if (county) {
        this.$refs.district.innerHTML =
          '<option value="" disabled>請選擇區域</option>';

        // 加入新選項
        if (this.valid[county]) {
          Object.keys(this.valid[county]).forEach((name) => {
            this.$refs.district.innerHTML += `<option value="${name}">${name}</option>`;
          });
        }

        const { district } = this.getCurrentSelections();
        if (this.valid[county] && this.valid[county][district]) {
          this.$refs.zip.value = this.valid[county][district];
        } else {
          this.$refs.zip.value = "";
        }
      }
    },

    updateZip() {
      const { county, district } = this.getCurrentSelections();

      if (
        county &&
        district &&
        this.valid[county] &&
        this.valid[county][district]
      ) {
        this.$refs.zip.value = this.valid[county][district];
      } else {
        // 無效回空值
        this.$refs.zip.value = "";
      }
    },
  };
};

export { addressFormControl };
