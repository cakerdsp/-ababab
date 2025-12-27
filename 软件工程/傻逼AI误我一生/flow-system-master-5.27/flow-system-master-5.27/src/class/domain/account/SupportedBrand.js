class SupportedBrand {
  constructor(brandName, isBound = false) {
    this.brandName = brandName;
    this.isBound = isBound;
  }

  // 获取品牌名称
  getBrandName() {
    return this.brandName;
  }

  // 检查是否已绑定
  isBrandBound() {
    return this.isBound;
  }

  // 设置绑定状态
  setBoundStatus(status) {
    this.isBound = status;
  }
}

module.exports = SupportedBrand;