# T50 Pro InvenTree 适配器

让 InvenTree 使用硕方 T50 Pro 打印物料和库存标签。适配器将标签转换为图片，通过 IPP 发送到 [supvan-cups](https://github.com/heeen/supvan-cups) 打印服务。

```text
InvenTree → 本适配器 → supvan-cups → T50 Pro
```

## 支持的功能

- 打印物料和库存标签。
- 支持 30×15 mm 和 40×30 mm 标签模板。
- 识别小标签中的物料和库存条码。
- 提交前检查打印机状态，离线时提示原因。

已在 InvenTree 1.5.6 和 T50 Pro 上验证。

## 使用指南

安装插件、配置打印地址、添加模板和打印标签，请阅读 **[使用指南](usage.md)**。

打印机连接与控制由 `supvan-cups` 负责；本适配器负责接入 InvenTree。
