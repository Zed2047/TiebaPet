# 黄豆扩展插件

用户安装的插件请放到：

```text
桌宠目录\extensions
```

项目中的这个目录仅用于保存开发说明，并会随打包版本一起提供。

最小插件示例：

```python
from PySide6.QtWidgets import QMenu
from tiebapet.plugins.base import BasePlugin


class HelloPlugin(BasePlugin):
    api_version = 1
    plugin_id = "hello"
    display_name = "打招呼"

    def populate_menu(self, menu: QMenu) -> None:
        action = menu.addAction("让黄豆打招呼")
        action.triggered.connect(
            lambda: self.context.notify("老哥好！", "开心")
        )
```

约定：

- 插件必须继承 `BasePlugin`
- 当前支持的 `api_version` 为 `1`
- `plugin_id` 不能与其他插件重复
- 插件异常会写入 `桌宠目录\logs\tieba-pet.log`

插件可以执行本机代码，只安装你信任的插件。
