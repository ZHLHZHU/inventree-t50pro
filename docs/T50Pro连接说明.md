# InvenTree 连接硕方 T50 Pro：Debian 蓝牙打印

配置日期：2026 年 10 月 6 日。已在拔掉打印机 USB 线后，从 InvenTree 打印一张 40×30 mm 标签，服务报告完成，实际出纸已确认。

## 连接方式

```text
InvenTree（oracle）
  │ 自定义标签打印插件，把标签渲染为图片
  │ IPP，经 Tailscale 网络
  ▼
Debian（100.68.102.138:8631）
  │ supvan-printer-app 打印服务
  │ BlueZ + 蓝牙适配器，经典蓝牙 RFCOMM
  ▼
硕方 T50 Pro
  └─ 40×30 mm 间隙标签，无黑标
```

打印机不需要直接连接 InvenTree 服务器。Debian 负责和打印机通信，InvenTree 通过网络把标签交给 Debian。打印机 USB 线可以拔掉；蓝牙适配器仍需插在 Debian 上。

## Debian 上做了什么

安装并启用了 Linux 蓝牙服务 BlueZ，发现 T50 Pro 后完成配对并设为可信设备。打印机广播名称是序列号 `T0145B2409045195`，蓝牙地址为 `A4:93:40:81:EC:E1`。

这里使用的是经典蓝牙串口服务（RFCOMM），不是通过手机 App 转发，也不是把打印机变成 Wi-Fi 打印机。配对后，打印服务会直接通过蓝牙读标签纸信息、传输打印数据。

打印驱动采用开源项目 [supvan-cups](https://github.com/heeen/supvan-cups)，编译后部署为常驻服务：

| 项目 | 配置 |
|---|---|
| 打印服务 | `supvan-t50pro.service` |
| 程序 | `/opt/supvan/bin/supvan-printer-app` |
| 诊断工具 | `/opt/supvan/bin/supvan-cli` |
| 服务文件 | `/etc/systemd/system/supvan-t50pro.service` |
| 状态文件 | `/home/lh/.local/state/supvan-printer-app.state.json` |
| 网络监听 | `100.68.102.138:8631`，Tailscale 地址 |

蓝牙服务和打印服务均已设置开机启动。驱动支持 USB 和蓝牙：USB 可用时优先使用 USB，USB 不可用时尝试蓝牙。实际拔线测试中曾短暂离线，之后自动恢复连接，重新发送的标签成功打印。

最初使用 USB 调通打印，因此还保留了 USB 设备权限规则 `/etc/udev/rules.d/70-supvan-t50pro.rules`。它不影响无线打印。

## InvenTree 上做了什么

InvenTree 部署在 `oracle` 的 k3s 中，Web 服务和后台 worker 共用插件目录。新增了一个标签打印插件：

| 项目 | 配置 |
|---|---|
| 插件名称 | 硕方 T50 Pro（40×30 mm） |
| 插件标识 | `supvan-t50pro` |
| 版本 | `0.2.0` |
| 插件目录 | `/home/inventree/data/plugins/supvan_t50pro/` |
| 打印地址 | `ipp://100.68.102.138:8631/ipp/print/supvan_t50s_t0145b2409045195` |

地址中的 `t50s` 是驱动最初通过 USB 识别时生成的名称；这个地址对应的实际设备就是 T50 Pro，切换蓝牙后沿用同一个地址。

插件先检查打印机是否就绪，再把 InvenTree 标签渲染成 320×240 像素的图片，对应 40×30 mm、每毫米 8 个点，然后通过 IPP 提交给 Debian。当前插件限制使用 40×30 mm 标签，尺寸不符会拒绝发送。打印机已被报告为离线或暂停时，也会在发送前报错。

插件不自动重复提交打印任务，以免出现重复标签。任务提交成功和实际打印完成是两个阶段；本次测试另外检查了 Debian 服务的完成日志，并确认实际出纸。

已配置两个标签模板：

- **硕方 40×30 · 物料**：物料二维码、名称和物料编码。
- **硕方 40×30 · 库存**：库存二维码、物料名称和库存编号。

二维码位于左侧，文字位于右侧。更换纸张尺寸时，需要同时调整模板和插件的尺寸限制；仅换纸不会自动完成这两项配置。

## 日常使用

1. 保持 Debian 在线，蓝牙适配器插好，T50 Pro 开机。
2. 装入 40×30 mm 间隙标签纸，无黑标。
3. 在 InvenTree 对物料或库存发起标签打印，选择对应模板和“硕方 T50 Pro（40×30 mm）”插件。
4. 等待出纸。日常使用时让手机 App 断开打印机，避免争用蓝牙连接。

这条打印链路依赖 oracle 与 Debian 之间的 Tailscale 网络。如果 Debian 关机、Tailscale 不通或打印机离线，就无法完成打印。

## 常见排查

通过 `ssh lh@debian` 登录后，可检查服务和最近的打印日志：

```sh
systemctl status bluetooth supvan-t50pro
bluetoothctl info A4:93:40:81:EC:E1
journalctl -u supvan-t50pro --no-pager -n 50
```

`Paired: yes` 和 `Trusted: yes` 表示已配对并信任；`Connected: yes` 表示当前连接。暂时未连接不等于需要重新配对，打印服务会尝试建立连接。

日志中的 `print complete` 表示驱动收到了打印完成状态。`Host is down` 表示当时蓝牙设备不可达：先确认打印机开机、距离合适、手机 App 未占用连接，待打印机恢复就绪再重试。若上一任务是否完成不明确，应先看实际出纸和日志，再决定是否重打。

需要管理员权限重启服务时：

```sh
sudo systemctl restart bluetooth supvan-t50pro
```

这台 Debian 的部署操作使用了已授权的 Docker + chroot 管理权限；上面的 sudo 命令适用于已有 sudo 权限的管理员。

## 维护记录

- 初始 USB 测试：30×15 mm 黑标纸，出纸和定位正常。
- 后续切换：40×30 mm 无黑标间隙纸，更新插件和两套标签模板。
- 蓝牙配置：安装 BlueZ、配对并信任 T50 Pro，启用开机服务。
- 最终验证：物理拔掉打印机 USB 线，从 InvenTree 经 Tailscale → Debian → 蓝牙打印成功。

本文不包含 InvenTree API 密钥。日常打印使用已部署插件，不依赖此次配置时使用的临时 API 密钥。
