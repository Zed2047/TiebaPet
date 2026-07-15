# TiebaPet 2.1

使用 Python + PySide6 制作的 Windows 桌宠，内置 31 个贴吧黄豆表情、可编辑台词、行为状态和插件系统。

项目主页：<https://github.com/Zed2047/TiebaPet>

## 当前功能

- 31 个独立表情，首次运行自动去白底并缓存透明图片
- 透明窗口、置顶、拖动、随机动作和自动移动
- 可调整黄豆大小、回复字体、气泡高度、移动速度和行为频率
- 自动保存窗口位置和全部设置
- 待机、行走、睡眠、工作、拖动、提醒六种状态
- 多定时提醒、可恢复的番茄钟、系统时间与 CPU/内存信息
- 支持从用户扩展目录自动加载第三方插件，并隔离插件异常
- 台词保存在 JSON 中，可修改后热重载
- Windows 开机启动和系统托盘控制
- 轮转日志、全局异常记录和表情磁盘缓存

## 运行方法

环境要求：Windows 10/11、Python 3.10 或更高版本。

直接双击 `run.bat`，或者在项目目录打开 PowerShell：

```powershell
pip install -r requirements.txt
python main.py
```

## 使用方法

- 单击黄豆：随机切换表情并说话
- 按住左键拖动：移动桌宠并保存位置
- 右键黄豆：打开表情、插件和设置菜单
- 单击托盘图标：重新显示黄豆
- 托盘右键：打开设置、插件或退出

### 修改黄豆大小和回复字体

右键黄豆，点击“设置...”：

- “黄豆大小”控制表情尺寸
- “回复字体大小”控制气泡中的文字大小
- “气泡高度”控制回复框高度

修改后点击“保存”立即生效。

### 修改表情对应文案

右键黄豆，点击“打开用户数据目录”，编辑其中的 `phrases.json`。每个表情名对应一组台词，例如：

```json
{
  "phrases": {
    "开心": ["乐", "这下舒服了", "好好好"]
  },
  "passive": ["还搁这摸鱼呢？"],
  "drag": ["不是哥们，你要给我拖哪去？"]
}
```

新增台词时不要在末尾添加句号，需要语气时只保留 `？`、`！` 等字符。保存后右键黄豆，点击“重新加载文案”，无需重启。

## 用户数据位置

运行后会在以下目录保存个人数据，不再改写程序安装目录：

```text
%APPDATA%\TiebaPet\
├─ config.json                 # 大小、字体、位置和插件状态
├─ phrases.json                # 表情与台词
├─ extensions\                # 第三方插件
├─ cache\expressions\         # 透明表情缓存
└─ logs\tieba-pet.log          # 运行与错误日志
```

项目中的 `data\config.json` 和 `data\phrases.json` 是初始模板。用户文件不存在时才会复制，已有文件不会被覆盖。

从旧版升级时，程序会在首次运行时把 `%APPDATA%\HuangdouPet` 复制到 `%APPDATA%\TiebaPet`，旧目录仍会保留。

## 插件系统

内置插件：

- 定时提醒：可同时建立多个提醒，重启后仍会保留
- 番茄钟：专注和休息倒计时，重启后可继续
- 系统状态：显示时间、CPU 和内存占用

第三方插件放入 `%APPDATA%\TiebaPet\extensions`，下次启动自动加载。插件菜单会显示加载数量和错误数量。插件是可执行代码，只安装来源可信的插件。

## 打包 EXE

双击 `build_exe.bat`，生成：

```text
dist\TiebaPet\TiebaPet.exe
```

分发时复制整个 `dist\TiebaPet` 文件夹，不要只复制单个 EXE。

## 测试

```powershell
python tests\smoke_test.py
python tests\core_test.py
```

## 项目结构

```text
桌宠\
├─ assets\expressions\        # 原始表情
├─ data\                      # 用户数据初始模板
├─ extensions\                # 插件开发示例
├─ huangdou\
│  ├─ assets.py               # 图片透明化、磁盘与内存缓存
│  ├─ config.py               # 设置持久化
│  ├─ paths.py                # 安装目录和用户目录
│  ├─ logging_setup.py        # 日志与异常记录
│  ├─ state.py                # 行为状态机
│  ├─ settings_dialog.py      # 设置窗口
│  ├─ pet.py                  # 桌宠主窗口
│  └─ plugins\                # 插件框架和内置插件
├─ tests\
├─ main.py
├─ run.bat
└─ build_exe.bat
```

原始表情不会被修改；透明化结果只写入用户缓存目录。
