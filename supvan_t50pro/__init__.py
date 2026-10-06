"""Print 40 x 30 mm InvenTree labels through the Supvan IPP service."""
import io
from rest_framework import serializers
from plugin import InvenTreePlugin
from plugin.mixins import LabelPrintingMixin, SettingsMixin
from .ipp_client import exchange


class SupvanLabelPrinter(LabelPrintingMixin, SettingsMixin, InvenTreePlugin):
    NAME = 'Supvan T50 Pro'
    SLUG = 'supvan-t50pro'
    TITLE = '硕方 T50 Pro（40×30 mm）'
    DESCRIPTION = '通过内网 IPP 服务打印 40×30 mm 标签'
    AUTHOR = 'Local'
    VERSION = '0.2.0'
    BLOCKING_PRINT = True
    SETTINGS = {
        'PRINTER_URI': {
            'name': '打印机 IPP 地址',
            'description': 'Debian 内网打印服务的完整 IPP 地址',
            'default': 'ipp://100.68.102.138:8631/ipp/print/supvan_t50s_t0145b2409045195',
        }
    }

    class PrintingOptionsSerializer(serializers.Serializer):
        pass

    def print_label(self, **kwargs):
        if abs(float(kwargs['width']) - 40) > 0.1 or abs(float(kwargs['height']) - 30) > 0.1:
            raise ValueError('请使用宽 40 mm、高 30 mm 的标签模板。')
        uri = self.get_setting('PRINTER_URI')
        if not uri:
            raise ValueError('尚未配置打印机 IPP 地址。')
        state = exchange(uri, 0x000b)
        if state.get('printer-state') == [5]:
            raise RuntimeError('打印机暂停或离线：' + str(state.get('printer-state-reasons', [])))
        image = kwargs.get('png_file')
        if image is None:
            raise RuntimeError('标签图片生成失败。')
        image = image.convert('RGB')
        image = image.resize((320, 240))
        payload = io.BytesIO()
        image.save(payload, format='JPEG', quality=100, subsampling=0)
        exchange(uri, 0x0002, payload.getvalue(), kwargs.get('filename', 'InvenTree label'))
