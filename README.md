# InvenTree × 硕方 T50 Pro

InvenTree 标签打印插件、40×30 mm 标签模板及 Debian 部署配置。

连接路径：InvenTree → 本仓库插件 → IPP（Tailscale）→ supvan-cups → 蓝牙 / USB → T50 Pro。

已在 InvenTree 1.5.6 上验证，拔掉打印机 USB 线后通过蓝牙打印成功。详细配置见 [连接说明](docs/T50Pro连接说明.md)。

## 文件

- `supvan_t50pro/`：InvenTree 标签插件，检查打印机状态，生成 320×240 JPEG 并提交 IPP 任务。
- `templates/`：物料、库存标签 HTML 和配置。
- `deploy/`：驱动构建文件、当前 systemd 服务和 USB 权限规则。

## 驱动版本

驱动使用 [heeen/supvan-cups](https://github.com/heeen/supvan-cups)，提交 `9fd7af09580c3e710202e5471e77e0b88db0e3bb`。本仓库不复制驱动源代码。

在驱动源码目录中构建：

```sh
docker build -f /path/to/inventree-t50pro/deploy/Dockerfile.debian -t supvan-t50pro:local .
```

镜像内程序为 `/usr/local/bin/supvan-printer-app` 和 `/usr/local/bin/supvan-cli`。当前部署将它们复制到宿主机 `/opt/supvan/bin/`，由 systemd 运行；蓝牙使用宿主机 BlueZ。

## 部署

1. Debian 安装 BlueZ，配对并信任打印机；准备 `plugdev` 用户组及运行用户。
2. 安装驱动程序到 `/opt/supvan/bin/`。
3. 按实际机器修改服务文件的用户、组和 `SUPVAN_HOST`；当前文件保留已验证的部署值。安装 systemd 服务及 udev 规则，启用蓝牙和打印服务。
4. 将 `supvan_t50pro/` 复制到 InvenTree 数据目录的 `plugins/` 下，重启 Web 和 worker，启用插件。按实际环境设置插件的 `PRINTER_URI`。
5. 导入 `templates/` 下的 HTML；配置见 `templates/config.json`。模板尺寸按配置设置为 30×15 mm 或 40×30 mm。

当前文件用于记录实际运行配置，包含内网地址和设备标识，不包含 API 密钥。更换打印机或部署机器后需更新配置。

## 验证

插件已通过真实 IPP 服务完成物理打印。标签图片为 320×240 像素，纸张为 40×30 mm 无黑标间隙纸。不支持的尺寸或服务报告暂停/离线时拒绝发送；提交不自动重试，避免重复打印。

## 30×15 mm 小标签（插件 0.3.0）

新增 `part-30x15.html`、`stock-30x15.html`：上方 Code 128，下方 `part.name`，不打印编号文字。名称显示一行，超长部分裁切，应使用简短名称。

条码是 `9701`（物料）或 `9702`（库存）加六位补零对象 ID，例如 `9701000123`。由本插件的 BarcodeMixin 识别，支持 ID 1–999999；不要将这两个前缀用于其他自定义条码。这个格式不会改动 InvenTree 原有二维码或全局条码格式。

30×15 mm 图片为 240×120 像素。Code 128 最窄条宽 0.25 mm（2 点），两侧静区各 2.5 mm。原有 40×30 mm 模板继续可用；请按实际装入的纸张选择尺寸。小标签需要启用本插件才能在 InvenTree 中识别。

小标签验证：两套模板均渲染为 240×120，最终提交用 JPEG 已由 ZXing 解码为预期数字条码；扫码处理的物料/库存查找已验证。条码源图采用 4 倍分辨率，避免小图栅格化导致条宽失真。物料小标签已通过 InvenTree → Debian → 蓝牙实际打印，用户确认定位正常；库存小标签已验证图片解码和扫码查找，尚未单独验证实际出纸。

## 0.3.1：打印前检查

InvenTree 1.5.6 会删除失败任务的 DataOutput，页面继续轮询时可能显示 404。插件在打印选项校验阶段检查 IPP 状态：已知离线或网络不可达时直接返回明确错误，不创建后台任务。后台发送前仍会再次检查；提交后发生的故障仍可能触发 InvenTree 的任务失败行为。

所有标签直接按 203.2 dpi 渲染，避免从默认 300 dpi 缩放导致小条码条宽失真。已通过打印 API 的离线和网络故障模拟验证：均返回 400 及明确原因，未创建 DataOutput。

## 已验证的黑标卡纸设置

2026 年 10 月 6 日，30×15 mm 物料条码标签实际打印定位验证通过。官方硕方 App 的纸张设置为：**黑标卡纸、长方形、30×15 mm、黑标高度 3 mm**。

定位异常时设备返回 type=1；经官方 App 设置后返回 type=2、gap=3 mm，恢复 Debian 蓝牙连接后 InvenTree 出纸正常。模板没有添加偏移补偿，驱动没有修改。此结果针对当前纸卷；设置是否在打印机重启后保留尚未验证。

官方 App 与 Debian 不应同时占用蓝牙连接。详细操作见 [连接说明](docs/T50Pro连接说明.md#黑标卡纸的定位设置)。
