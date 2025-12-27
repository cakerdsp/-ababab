#### 1. 获取授权码 API

**端点**: `POST /mockapi/auth/getAuthorizationCode`
**功能**: 为指定用户生成第三方品牌服务的授权码
**认证**: 无

**请求参数 (JSON Body)**:

```json
{
  "userId": "string, // 必填，用户唯一标识",
  "brand": "string   // 必填，品牌名称（如：xiaomi, midea）"
}
```

**成功响应 (200 OK)**:

```json
{
  "status": "success",
  "code": 200,
  "message": "授权码生成成功",
  "data": {
    "authorizationCode": "string // 8位授权码",
    "createdAt": "string // ISO 8601格式时间"
  }
}
```

**错误响应**:

| 状态码 | 错误信息       | 响应示例                                                                    |
| ------ | -------------- | --------------------------------------------------------------------------- |
| 400    | 缺少必要参数   | `{"status":"error","code":400,"message":"缺少必要参数: userId 或 brand"}` |
| 401    | 品牌未配置     | `{"status":"error","code":401,"message":"品牌 'huawei' 未配置"}`          |
| 404    | 用户不存在     | `{"status":"error","code":404,"message":"用户ID 'user123' 不存在"}`       |
| 500    | 服务器内部错误 | `{"status":"error","code":500,"message":"服务器内部错误"}`                |

---

#### 2. 绑定第三方账号 API

**端点**: `POST  http://172.19.15.2:3000/auth/code`
**功能**: 使用授权码绑定第三方品牌账号
**认证**: JWT Bearer Token

大

**请求头**:

```
Authorization: Bearer <your_jwt_token>
```

**请求参数 (JSON Body)**:

```json
{
  "code": "string",           // 必填，授权码
  "brand": "string"           // 必填，品牌名称（仅支持: xiaomi, midea）
}
```

**成功响应 (200 OK)**:

```json
{
  "status": "success",
  "message": "Code exchanged successfully",
  "data": { void }
}
```

**错误响应**:

| 状态码 | 错误信息       | 响应示例                                                     |
| ------ | -------------- | ------------------------------------------------------------ |
| 400    | 参数验证失败   | `{"status":"error","errors":[{"msg":"code is required"}]}` |
| 401    | JWT认证失败    | `{"status":"error","message":"无效的访问令牌"}`            |
| 500    | 服务器内部错误 | `{"status":"error","message":"授权码交换失败"}`            |
