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
5. 导入 `templates/` 下的 HTML；配置见 `templates/config.json`。模板尺寸必须为 40×30 mm。

当前文件用于记录实际运行配置，包含内网地址和设备标识，不包含 API 密钥。更换打印机或部署机器后需更新配置。

## 验证

插件已通过真实 IPP 服务完成物理打印。标签图片为 320×240 像素，纸张为 40×30 mm 无黑标间隙纸。尺寸不符或服务报告暂停/离线时拒绝发送；提交不自动重试，避免重复打印。
