"""Print 40 x 30 mm InvenTree labels through the Supvan IPP service."""
import io
from rest_framework import serializers
from plugin import InvenTreePlugin
from plugin.mixins import BarcodeMixin, LabelPrintingMixin, SettingsMixin
import re
from .ipp_client import exchange


class SupvanLabelPrinter(BarcodeMixin, LabelPrintingMixin, SettingsMixin, InvenTreePlugin):
    NAME = 'Supvan T50 Pro'
    SLUG = 'supvan-t50pro'
    TITLE = '硕方 T50 Pro（30×15 / 40×30 mm）'
    DESCRIPTION = '通过内网 IPP 服务打印标签，并识别小标签数字条码'
    AUTHOR = 'Local'
    VERSION = '0.3.1'
    BLOCKING_PRINT = True
    SETTINGS = {
        'PRINTER_URI': {
            'name': '打印机 IPP 地址',
            'description': 'Debian 内网打印服务的完整 IPP 地址',
            'default': 'ipp://100.68.102.138:8631/ipp/print/supvan_t50s_t0145b2409045195',
        }
    }

    class PrintingOptionsSerializer(serializers.Serializer):
        def validate(self, attrs):
            self.context['printer_plugin'].check_ready()
            return attrs

    def get_printing_options_serializer(self, request, *args, **kwargs):
        context = dict(kwargs.pop('context', {}) or {})
        context['printer_plugin'] = self
        return self.PrintingOptionsSerializer(*args, context=context, **kwargs)

    def check_ready(self):
        uri = self.get_setting('PRINTER_URI')
        if not uri:
            raise serializers.ValidationError('尚未配置打印机 IPP 地址。')
        try:
            state = exchange(uri, 0x000b)
        except Exception as exc:
            raise serializers.ValidationError('无法连接 Debian 打印服务，请检查服务和 Tailscale 网络。') from exc
        if state.get('printer-state') == [5]:
            raise serializers.ValidationError('T50 Pro 未就绪，请确认打印机开机、手机 App 已断开，等待蓝牙重连后再试。')
        return uri

    def render_to_png(self, *args, **kwargs):
        # Render directly onto the printer grid; avoid resizing 300 dpi barcodes.
        kwargs['dpi'] = 203.2
        return super().render_to_png(*args, **kwargs)

    def print_label(self, **kwargs):
        width, height = float(kwargs['width']), float(kwargs['height'])
        size = next((size for size in ((30, 15), (40, 30))
                     if abs(width - size[0]) <= 0.1 and abs(height - size[1]) <= 0.1), None)
        if size is None:
            raise ValueError('请使用 30×15 mm 或 40×30 mm 的标签模板。')
        uri = self.check_ready()
        image = kwargs.get('png_file')
        if image is None:
            raise RuntimeError('标签图片生成失败。')
        image = image.convert('RGB')
        image = image.resize((size[0] * 8, size[1] * 8))
        payload = io.BytesIO()
        image.save(payload, format='JPEG', quality=100, subsampling=0)
        exchange(uri, 0x0002, payload.getvalue(), kwargs.get('filename', 'InvenTree label'))

    def scan(self, barcode_data, user, **kwargs):
        # Fixed-length numeric payloads keep Code 128 compact at 203 dpi.
        match = re.fullmatch(r'970([12])(\d{6})', str(barcode_data).strip())
        if not match:
            return None
        from part.models import Part
        from stock.models import StockItem
        model = Part if match[1] == '1' else StockItem
        try:
            instance = model.objects.get(pk=int(match[2]))
        except model.DoesNotExist:
            return None
        return {model.barcode_model_type(): instance.format_matched_response(user=user, **kwargs)}
