"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.isSupportedBrand = exports.SupportedBrand = void 0;
/**
 * 支持的第三方品牌枚举
 */
var SupportedBrand;
(function (SupportedBrand) {
    SupportedBrand["Midea"] = "Midea";
    SupportedBrand["Xiaomi"] = "Xiaomi";
})(SupportedBrand = exports.SupportedBrand || (exports.SupportedBrand = {}));
/**
 * 检查品牌是否被支持
 * @param brand 品牌名称
 * @returns 是否支持
 */
function isSupportedBrand(brand) {
    return Object.values(SupportedBrand).includes(brand);
}
exports.isSupportedBrand = isSupportedBrand;
//# sourceMappingURL=SupportedBrand.js.map