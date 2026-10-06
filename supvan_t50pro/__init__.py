"""Print 40 x 30 mm InvenTree labels through the Supvan IPP service."""
import io
import json
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
    VERSION = '0.4.0'
    BLOCKING_PRINT = True
    SETTINGS = {
        'PRINTER_URI': {
            'name': '打印机 IPP 地址',
            'description': '默认打印服务的完整 IPP 地址',
            'default': 'ipp://100.68.102.138:8631/ipp/print/supvan_t50s_t0145b2409045195',
        },
        'PRINTERS': {
            'name': '可选打印机',
            'description': 'JSON 对象，名称对应 IPP 地址；留空时使用默认地址',
            'default': '{}',
        },
    }

    class PrintingOptionsSerializer(serializers.Serializer):
        def validate(self, attrs):
            self.context['printer_plugin'].check_ready(attrs.get('printer'))
            return attrs

    def get_printing_options_serializer(self, request, *args, **kwargs):
        context = dict(kwargs.pop('context', {}) or {})
        context['printer_plugin'] = self
        serializer = self.PrintingOptionsSerializer(*args, context=context, **kwargs)
        printers = self.get_printers()
        if printers:
            serializer.fields['printer'] = serializers.ChoiceField(
                choices=list(printers), default=next(iter(printers)), label='打印机'
            )
        return serializer

    def get_printers(self):
        printers = json.loads(self.get_setting('PRINTERS') or '{}')
        if not isinstance(printers, dict) or any(
            not isinstance(name, str) or not isinstance(uri, str) or not uri.startswith('ipp://')
            for name, uri in printers.items()
        ):
            raise serializers.ValidationError('可选打印机必须是名称对应 IPP 地址的 JSON 对象。')
        return printers

    def check_ready(self, printer=None):
        printers = self.get_printers()
        if printer is not None and printer not in printers:
            raise serializers.ValidationError('所选打印机已不存在，请重新选择。')
        uri = printers[printer] if printer is not None else self.get_setting('PRINTER_URI')
        if not uri:
            raise serializers.ValidationError('尚未配置打印机 IPP 地址。')
        try:
            state = exchange(uri, 0x000b)
        except Exception as exc:
            raise serializers.ValidationError('无法连接所选打印服务，请检查服务和 Tailscale 网络。') from exc
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
        uri = self.check_ready((kwargs.get('printing_options') or {}).get('printer'))
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
