from app.plugins import _PluginBase
from app.core.event import eventmanager
from app.schemas.types import EventType
from app.utils.http import RequestUtils
from typing import Any, List, Dict, Tuple
from app.log import logger
import json


class CustomWebHook(_PluginBase):
    # 插件名称
    plugin_name = "自定义Webhook"
    # 插件描述
    plugin_desc = "事件发生时向第三方地址发送请求。"
    # 插件图标
    plugin_icon = "webhook.png"
    # 插件版本
    plugin_version = "1.0"
    # 插件作者
    plugin_author = "joesonshaw"
    # 作者主页
    author_url = "https://github.com/joesonshaw"
    # 插件配置项ID前缀
    plugin_config_prefix = "custom_webhook_"
    # 加载顺序
    plugin_order = 14
    # 可使用的用户级别
    auth_level = 1

    # 私有属性
    _webhook_url = None
    _method = None
    _enabled = False
    _custom_body = ""

    def init_plugin(self, config: dict = None):
        if config:
            self._enabled = config.get("enabled")
            self._webhook_url = config.get("webhook_url")
            self._method = config.get('request_method')
            self._custom_body = config.get('custom_body')

    def get_state(self) -> bool:
        return self._enabled

    @staticmethod
    def get_command() -> List[Dict[str, Any]]:
        pass

    def get_api(self) -> List[Dict[str, Any]]:
        pass

    def get_form(self) -> Tuple[List[dict], Dict[str, Any]]:
        """
        拼装插件配置页面，需要返回两块数据：1、页面配置；2、数据结构
        """
        request_options = ["POST", "GET"]
        return [
            {
                'component': 'VForm',
                'content': [
                    {
                        'component': 'VRow',
                        'content': [
                            {
                                'component': 'VCol',
                                'props': {
                                    'cols': 12,
                                    'md': 6
                                },
                                'content': [
                                    {
                                        'component': 'VSwitch',
                                        'props': {
                                            'model': 'enabled',
                                            'label': '启用插件',
                                        }
                                    }
                                ]
                            }
                        ]
                    },
                    {
                        'component': 'VRow',
                        'content': [
                            {
                                'component': 'VCol',
                                'props': {
                                    'cols': 12,
                                    'md': 4
                                },
                                'content': [
                                    {
                                        'component': 'VSelect',
                                        'props': {
                                            'model': 'request_method',
                                            'label': '请求方式',
                                            'items': request_options
                                        }
                                    }
                                ]
                            },
                            {
                                'component': 'VCol',
                                'props': {
                                    'cols': 12,
                                    'md': 8
                                },
                                'content': [
                                    {
                                        'component': 'VTextField',
                                        'props': {
                                            'model': 'webhook_url',
                                            'label': 'webhook地址'
                                        }
                                    }
                                ]
                            }
                        ]
                    },
                    {
                        'component': 'VRow',
                        'content': [
                            {
                                'component': 'VCol',
                                'props': {
                                    'cols': 12,
                                    'md': 8
                                },
                                'content': [
                                    {
                                        'component': 'VTextField',
                                        'props': {
                                            'model': 'custom_body',
                                            'label': '自定义body',
                                        }
                                    }
                                ]
                            }
                        ]
                    },
                ]
            }
        ], {
            "enabled": False,
            "request_method": "POST",
            "webhook_url": "",
            "custom_body": "",
        }

    def get_page(self) -> List[dict]:
        pass

    @eventmanager.register(EventType)
    def send(self, event):
        """
        向第三方Webhook发送请求
        """
        if not self._enabled or not self._webhook_url:
            return

        def __to_dict(_event):
            """
            递归将对象转换为字典
            """
            if isinstance(_event, dict):
                for k, v in _event.items():
                    _event[k] = __to_dict(v)
                return _event
            elif isinstance(_event, list):
                for i in range(len(_event)):
                    _event[i] = __to_dict(_event[i])
                return _event
            elif isinstance(_event, tuple):
                return tuple(__to_dict(list(_event)))
            elif isinstance(_event, set):
                return set(__to_dict(list(_event)))
            elif hasattr(_event, 'to_dict'):
                return __to_dict(_event.to_dict())
            elif hasattr(_event, '__dict__'):
                return __to_dict(_event.__dict__)
            elif isinstance(_event, (int, float, str, bool, type(None))):
                return _event
            else:
                return str(_event)
        if self._custom_body:
                event_string = self._custom_body.replace("${type}", event.event_type).replace("${data}", event.event_data)
                event_info = json.loads(event_string)
        else: 
                event_info = {
                    "type": event.event_type,
                    "data": __to_dict(event.event_data)
                }

        if self._method == 'POST':
            ret = RequestUtils(content_type="application/json").post_res(self._webhook_url, json=event_info)
        else:
            ret = RequestUtils().get_res(self._webhook_url, params=event_info)
        if ret:
            logger.info("发送成功：%s" % self._webhook_url)
        elif ret is not None:
            logger.error(f"发送失败，状态码：{ret.status_code}，返回信息：{ret.text} {ret.reason}")
        else:
            logger.error("发送失败，未获取到返回信息")

    def stop_service(self):
        """
        退出插件
        """
        pass