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
           └── ipp_client.py
   ```

2. 重启 InvenTree Web 服务和后台 worker，确保两者都能读取插件文件。
3. 在插件管理中启用 `supvan-t50pro`。
4. 在插件设置中，将 `PRINTER_URI` 改为你的打印机地址：

```text
ipp://HOST:PORT/ipp/print/PRINTER_NAME
```

完整地址以 `supvan-cups` 公布的地址为准。请替换插件自带的默认地址，不要直接沿用其他部署的地址。

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
3. 选择“硕方 T50 Pro（30×15 / 40×30 mm）”插件，提交打印。

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
