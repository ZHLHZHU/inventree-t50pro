# 用 InvenTree 打印硕方 T50 Pro 标签

把 InvenTree 中的物料和库存信息打印成标签，贴在元件袋、耗材盒或收纳格上。支持 **30×15 mm 小条码标签**和 **40×30 mm 二维码标签**，打印机可以通过 USB 或蓝牙连接。

如果管理员已经完成安装，直接阅读[日常打印](#日常打印)。首次部署请阅读[安装与连接](#安装与连接)。

## 它是怎么连接的？

```text
InvenTree → 本项目打印插件 → 网络 → Debian 打印服务 → USB 或蓝牙 → T50 Pro
```

打印机连接到 Debian 电脑，InvenTree 通过 IPP 网络打印协议发送标签。两台机器可以在同一局域网，也可以通过 Tailscale 互通。

本项目提供 InvenTree 插件和标签模板。控制打印机的驱动来自 [supvan-cups](https://github.com/heeen/supvan-cups)，安装时需要单独构建。

## 选择标签

| 尺寸 | 内容 | 适合用途 |
|---|---|---|
| **30×15 mm** | 上方条形码，下方简短名称，不显示编号文字 | 小元件袋、小盒子 |
| **40×30 mm** | 左侧二维码，右侧名称和编号 | 较大的耗材盒、收纳容器 |

每种尺寸都有“物料”和“库存”两个模板。物料标签标识一种物料；库存标签标识该物料的一条具体库存记录。

小标签的名称只显示一行，过长会被裁切。名称宜简短，例如 `10kΩ 0603`。

## 日常打印

1. 开启 Debian 电脑和打印机。使用蓝牙时，确保适配器插好，并断开手机 App 的连接。
2. 装入标签纸，确认尺寸与所选模板一致。
3. 在 InvenTree 中打开物料或库存，选择标签打印。
4. 选择对应尺寸的模板，以及 **硕方 T50 Pro（30×15 / 40×30 mm）** 打印插件。
5. 先打印一张，确认内容完整、定位正常，再批量打印。

### 使用 30×15 mm 黑标卡纸

这款纸已验证可正常定位。首次使用或换纸后，先在官方硕方 App 中确认以下设置：

| 设置 | 值 |
|---|---|
| 纸张类型 | 黑标卡纸 |
| 形状 | 长方形 |
| 标签尺寸 | 30×15 mm |
| 黑标高度 | 3 mm |

App 测试前，管理员需要暂停 Debian 打印服务并释放蓝牙连接。App 打印正常后，断开 App，再恢复 Debian 服务。

这些参数针对已验证的纸卷。其他纸张应使用其实际类型和尺寸；不要只改模板边距来补偿走纸错误。

## 安装与连接

以下步骤面向安装管理员。需要一台 Debian 电脑、T50 Pro，以及可配置插件的 InvenTree 实例。使用蓝牙还需要适配器；构建驱动需要 Docker 和 Git。

**已验证环境：InvenTree 1.5.6、插件 0.3.1、T50 Pro。** 其他版本或打印机型号需要自行验证兼容性。

### 1. 构建并安装打印驱动

把本仓库和驱动放到同一目录下：

```sh
git clone https://github.com/ZHLHZHU/inventree-t50pro.git
git clone https://github.com/heeen/supvan-cups.git
cd supvan-cups
git checkout 9fd7af09580c3e710202e5471e77e0b88db0e3bb
docker build -f ../inventree-t50pro/deploy/Dockerfile.debian -t supvan-t50pro:local .
```

本仓库目前为私有仓库，克隆需要访问权限。如果你已拿到项目文件，可跳过第一条命令，并按实际位置调整构建文件路径。

构建完成后，将两个程序安装到 Debian 宿主机：

```sh
docker create --name supvan-export supvan-t50pro:local
docker cp supvan-export:/usr/local/bin/supvan-printer-app ./supvan-printer-app
docker cp supvan-export:/usr/local/bin/supvan-cli ./supvan-cli
docker rm supvan-export
sudo install -d /opt/supvan/bin
sudo install -m 755 supvan-printer-app supvan-cli /opt/supvan/bin/
```

### 2. 连接打印机

**USB 连接：** 插入打印机，并安装权限规则。运行服务的用户需要属于 `plugdev` 组。

```sh
sudo install -m 644 ../inventree-t50pro/deploy/70-supvan-t50pro.rules /etc/udev/rules.d/
sudo udevadm control --reload-rules
sudo udevadm trigger --subsystem-match=hidraw
```

**蓝牙连接：** 安装并启用 BlueZ，然后配对打印机。

```sh
sudo apt-get update
sudo apt-get install -y bluez libdbus-1-3
sudo systemctl enable --now bluetooth
bluetoothctl
```

在 `bluetoothctl` 中执行下列操作。把 `PRINTER_MAC` 替换为扫描得到的打印机蓝牙地址；广播名称可能是打印机序列号。

```text
power on
agent on
default-agent
scan on
pair PRINTER_MAC
trust PRINTER_MAC
scan off
quit
```

打印服务会建立实际打印连接。不要让手机 App 同时占用打印机。

### 3. 启动 Debian 打印服务

复制服务配置并编辑：

```sh
sudo cp ../inventree-t50pro/deploy/supvan-t50pro.service /etc/systemd/system/
sudo editor /etc/systemd/system/supvan-t50pro.service
```

仓库中的文件保留了原部署值，**启用前必须替换**以下配置：

| 配置 | 如何填写 |
|---|---|
| `User` | 运行打印服务的 Debian 用户 |
| `Group` | 可访问打印机的用户组，USB 示例使用 `plugdev` |
| `SUPVAN_HOST` | Debian 的局域网或 Tailscale 地址，须能被 InvenTree 访问 |
| `SUPVAN_PORT` | 默认 `8631` |

USB 连接也需要安装运行库 `libdbus-1-3`。使用配置中的用户和组前，确认它们已经存在且具有设备访问权限。

```sh
sudo systemctl daemon-reload
sudo systemctl enable --now supvan-t50pro
systemctl status supvan-t50pro
```

从 InvenTree 所在机器访问 `http://DEBIAN_IP:8631/`，确认能看到打印机。使用 Tailscale 时，两台机器都需接入可互通的网络。

### 4. 安装 InvenTree 插件

将本仓库的 `supvan_t50pro/` 文件夹复制到 **InvenTree 数据目录的 `plugins/` 下**。

重启 InvenTree Web 服务和后台 worker，在插件管理页面启用 `supvan-t50pro`。容器部署时，两个服务都必须能读取这份插件文件。

在插件设置中填写 `PRINTER_URI`。**替换插件默认地址**，使用 Debian 打印服务公布的完整 IPP 地址，例如：

```text
ipp://DEBIAN_IP:8631/ipp/print/PRINTER_NAME
```

`PRINTER_NAME` 应从实际打印服务中取得。地址中可能带有 `t50s`，不要仅凭这个名称改写地址。

### 5. 添加标签模板

在 InvenTree 的标签模板管理中，上传对应的 HTML 文件，设置尺寸与适用对象，并启用模板：

| 模板文件 | 宽 × 高 | 适用对象 |
|---|---|---|
| `templates/part-30x15.html` | 30×15 mm | 物料 |
| `templates/stock-30x15.html` | 30×15 mm | 库存 |
| `templates/part.html` | 40×30 mm | 物料 |
| `templates/stock.html` | 40×30 mm | 库存 |

完整字段见 [`templates/config.json`](templates/config.json)。这个文件是配置参考，上传 HTML 不会自动导入其中的设置。

## 验证安装

1. 打开 Debian 打印服务页面 → 能看到打印机和正确的纸张尺寸。
2. 在 InvenTree 选择匹配的模板并打印一张 → 实际出纸，名称与条码完整，位置落在标签内。
3. 扫描小标签条码 → InvenTree 能找到对应物料或库存记录。
4. 使用无线连接时拔掉打印机 USB 线再打印 → 标签仍能正常输出。

已完成物料小标签的蓝牙实际打印和定位验证。库存小标签已验证图片解码及扫码查找，尚未单独验证实际出纸。物理小标签的扫码效果仍需用你的扫码设备检查。

## 常见问题

| 现象 | 处理方法 |
|---|---|
| 提示打印机未就绪 | 确认开机、距离合适、手机 App 已断开，等待蓝牙恢复后再试 |
| 无法连接 Debian 打印服务 | 检查服务是否运行，以及两台机器间的网络是否互通 |
| 手机 App 连不上 | 暂停 Debian 打印服务，断开其蓝牙连接，再连接 App |
| 内容跨标签或明显偏移 | 先在官方 App 核对纸张类型、尺寸及黑标高度，并打印对比 |
| 名称显示不全 | 缩短物料名称，或使用 40×30 mm 模板 |
| 扫码后找不到记录 | 确认插件已启用，标签对应的记录仍存在 |
| 页面出现 404 | 查看后台日志；InvenTree 可能删除了失败任务的进度记录 |

T50 Pro 的打印键**单击是重复打印，连续双击是退纸到起始位置**，不是单击进纸校准。详见[官方说明书](https://www.supvan.com/uploads/file/T50xi.pdf)。

管理员可在 Debian 查看服务和最近日志：

```sh
systemctl status bluetooth supvan-t50pro
journalctl -u supvan-t50pro --no-pager -n 50
```

测试官方 App 时暂停服务并断开连接；把 `PRINTER_MAC` 换成实际蓝牙地址：

```sh
sudo systemctl stop supvan-t50pro
bluetoothctl disconnect PRINTER_MAC
```

退出 App 后恢复服务：

```sh
sudo systemctl start supvan-t50pro
```

## 条码规则与使用限制

小标签使用 Code 128，条码内含记录类型和 ID，编号文字不会显示在纸上。

| 标签对象 | 编码规则 | 示例：ID 为 123 |
|---|---|---|
| 物料 | `9701` + 六位补零 ID | `9701000123` |
| 库存 | `9702` + 六位补零 ID | `9702000123` |

适用 ID 范围为 **1–999999**。请保留这两个前缀给本插件使用，避免与其他自定义条码冲突。原有 InvenTree 二维码格式不受影响。

插件目前仅支持 30×15 mm 和 40×30 mm。已知离线时会在创建打印任务前提示原因；任务提交后发生的连接故障仍需查看后台日志。插件不会自动重复提交，但 Debian 驱动可能保留任务并在重连后继续打印，重打前请检查是否已有任务等待执行。

黑标设置在打印机重启后是否保留尚未验证。重启或更换纸卷后，建议先试打一张。

## 项目文件

| 目录 | 用途 |
|---|---|
| [`supvan_t50pro/`](supvan_t50pro/) | InvenTree 打印和条码识别插件 |
| [`templates/`](templates/) | 两种尺寸的标签模板及配置参考 |
| [`deploy/`](deploy/) | 驱动构建文件、服务配置和 USB 权限规则 |
| [`docs/`](docs/) | 原部署的连接说明与实测记录 |

开发与维护细节见[连接说明](docs/T50Pro连接说明.md)。该文档包含原部署的内网地址和设备标识，部署到自己的环境时请替换。
