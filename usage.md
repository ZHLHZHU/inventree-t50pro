# 使用 T50 Pro InvenTree 适配器

本指南说明 InvenTree 端需要完成的安装、配置和打印操作。

打印机通过 USB 或蓝牙连接到运行 `supvan-cups` 的机器。InvenTree 只需安装本适配器并配置 IPP 地址；两种连接方式使用相同的插件和模板。

## 安装适配器

先配置好 `supvan-cups`，确保 InvenTree 服务器能够访问其 IPP 打印地址。

1. 将本仓库的 `supvan_t50pro/` 文件夹复制到 InvenTree 数据目录的 `plugins/` 下，目录结构如下：

   ```text
   InvenTree 数据目录/
   └── plugins/
       └── supvan_t50pro/
           ├── __init__.py
           ├── ipp_client.py
           └── configuration.py
   ```

2. 重启 InvenTree Web 服务和后台 worker，确保两者都能读取插件文件。
3. 在插件管理中启用 `supvan-t50pro`。
4. 在插件设置中，将 `PRINTER_URI` 改为你的打印机地址：

```text
ipp://HOST:PORT/ipp/print/PRINTER_NAME
```

完整地址以 `supvan-cups` 公布的地址为准。插件不提供默认打印地址。

## 配置多个独立打印入口

将 [示例配置](supvan_t50pro/printers.example.json) 复制为插件目录中的 `printers.json`，填写各打印入口的名称和 IPP 地址：

```json
[
  {
    "id": "supvan-t50pro-workbench",
    "name": "硕方 T50 Pro · 工作台",
    "uri": "ipp://printer-host.local:8631/ipp/print/PRINTER_NAME"
  },
  {
    "id": "supvan-t50pro-storage",
    "name": "硕方 T50 Pro · 储物间",
    "uri": "ipp://another-printer-host.local:8631/ipp/print/PRINTER_NAME"
  }
]
```

每条配置生成一个独立打印插件入口。重启 Web 服务和 worker 后，在插件管理中分别启用它们，打印时直接选择对应名称。

- `id` 是唯一且稳定的插件标识，只能使用小写字母、数字和连字符。改名称或地址时保持 ID 不变。
- `name` 是打印窗口显示的名称，不得重复。
- `uri` 是该入口使用的完整 IPP 地址；配置文件的地址优先于插件设置中保留的地址。

没有配置文件时，只生成通用的 `supvan-t50pro` 入口，地址通过插件设置填写。配置文件存在时，只生成文件中列出的入口。移除配置后，可在插件管理中关闭对应的旧入口。

也可以用环境变量 `SUPVAN_PRINTER_CONFIG` 指定配置文件的绝对路径。Web 服务和 worker 必须读取同一份配置，修改后都要重启。配置错误会阻止插件加载，请检查服务日志。

`printers.json` 已被 Git 忽略，部署地址留在各自的配置文件中。

## 添加标签模板

在 InvenTree 标签模板管理中上传对应 HTML，设置尺寸和适用对象，然后启用模板。

| 模板 | 尺寸 | 对象 | 内容 |
|---|---|---|---|
| [`part-30x15.html`](templates/part-30x15.html) | 30×15 mm | 物料 | 条形码、简短名称 |
| [`stock-30x15.html`](templates/stock-30x15.html) | 30×15 mm | 库存 | 条形码、简短名称 |
| [`part.html`](templates/part.html) | 40×30 mm | 物料 | 二维码、名称、编号 |
| [`stock.html`](templates/stock.html) | 40×30 mm | 库存 | 二维码、名称、编号 |

模板配置参考见 [`templates/config.json`](templates/config.json)。该文件仅提供配置参考，上传 HTML 后仍需在 InvenTree 中设置尺寸、适用对象并启用模板。

## 打印标签

1. 在 InvenTree 中选择物料或库存记录，打开标签打印。
2. 选择与实际标签纸尺寸一致的模板。
3. 选择对应的硕方 T50 Pro 打印入口，提交打印。

30×15 mm 模板只显示条形码和一行名称，不显示编号文字；名称过长会被裁切。

## 扫描小标签

在 InvenTree 中扫描条码，适配器会查找对应记录。使用此功能时需要保持插件启用。

| 对象 | 条码格式 |
|---|---|
| 物料 | `9701` + 六位补零的物料 ID |
| 库存 | `9702` + 六位补零的库存 ID |

小标签适用 ID 范围为 1–999999。请避免将这两个前缀用于其他自定义条码。

## 可选：设置蓝牙空闲自动断开

这是 `supvan-cups` 打印服务端的设置，InvenTree 端无需配置。使用本仓库的驱动补丁后，可在打印服务的环境变量中配置空闲超时：

```ini
Environment=SUPVAN_BT_IDLE_TIMEOUT=60
```

单位为秒。设为 `60` 时，空闲连接约一分钟后释放，下次打印自动重连；设为 `0` 或不设置则保持原有连接行为。状态轮询不会主动唤醒已断开的蓝牙连接，正在使用的连接不会被超时关闭。

该参数属于打印服务，配置后需要重启服务。编译驱动前，在固定版本的 `supvan-cups` 源码目录应用补丁：

```sh
git checkout 9fd7af09580c3e710202e5471e77e0b88db0e3bb
git apply /path/to/inventree-t50pro/deploy/supvan-bt-idle.patch
```

蓝牙休眠期间状态不会实时刷新；提交打印任务时才尝试连接。若手机 App 正占用打印机，需先断开 App。


## 打印服务配置示例

`deploy/supvan-t50pro.service` 是服务模板。使用前需创建 `supvan` 服务用户、授予打印设备访问权限，并将 [环境变量示例](deploy/supvan-t50pro.env.example) 复制为 `/etc/supvan-t50pro.env`，填写 InvenTree 能访问的监听地址和端口。示例中的 `127.0.0.1` 仅供本机访问，跨机器使用时需修改。
