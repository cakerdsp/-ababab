/**
 * 支持的第三方品牌枚举
 */
export enum SupportedBrand {
    Midea = "Midea",
    Xiaomi = "Xiaomi"
}

/**
 * 检查品牌是否被支持
 * @param brand 品牌名称
 * @returns 是否支持
 */
export function isSupportedBrand(brand: string): boolean {
    return Object.values(SupportedBrand).includes(brand as SupportedBrand);
}