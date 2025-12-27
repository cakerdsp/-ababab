1. **获取设备列表页api： **

**请求路径：http://192.168.58.56:3000/devices/getList **

**请求方式：get **

**请求头：Authorization: Bearer <JWT_TOKEN> （这里JWT如果按照链接实现payload是含有user_id的，不用用户额外传递，可以解码）**

**返回结果：**	**响应格式如下，成功响应码200，JWT无效/过期401**** Unauthorized******

**{**

 **  "code": 200,**

**  "data": {**

**    "devices": [**

**      {**

**        "did": "dev_123",**

**        "name": "abc",**

**        "type": " mi_AC",**

    **“**  **brand**  **”** **: Xiaomi**

    ** “group”: 分组信息，设备存在分组时应该为gid，无则是null**

**      },**

**      {**

**        "did": "dev_456",**

**        "name": "asd",**

**        "type": "Midea_AC",**

    **“**  **brand**  **”** **: Midea**

    ** “group”: 分组信息，设备存在分组时 应该为gid，无则是null**

**      }**

**    ]**

**  }**

**}**


sensor

：{
  type: 'history',
  did: 'xiaomi_mi_air_sensor_slki1y',
  metric_type: 'temperature',
  data: [ {value: 10.9 } ],
  timestamp: '2025-06-13T08:11:00.212Z'
}
