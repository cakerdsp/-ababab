class SupportedBrand {
  constructor(brandName, isBound = false) {
    this.brandName = brandName;
    this.isBound = isBound;
  }

  // Get brand name
  getBrandName() {
    return this.brandName;
  }

  // Check if it is bound
  isBrandBound() {
    return this.isBound;
  }

  // Set binding status
  setBoundStatus(status) {
    this.isBound = status;
  }
}

module.exports = SupportedBrand;
