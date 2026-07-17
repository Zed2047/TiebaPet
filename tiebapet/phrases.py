"""黄豆的人设、表情和台词。"""

from __future__ import annotations

import json
import random
from pathlib import Path

from .paths import ensure_user_directories, migrate_resource_file, user_data_root


EXPRESSION_NAMES = (
    "what", "乖", "兴奋", "吐了", "吐舌", "呵呵",
    "啊", "喷水", "噗", "小乖", "开心", "微微一笑",
    "捂嘴笑", "欢呼", "汗", "流汗", "爱", "生气",
    "疑问", "真棒", "笑", "紧张", "阴险", "黑头高兴",
    "吃瓜", "喝酒", "嘿嘿嘿", "狂汗", "泪", "嘻嘻", "呀咩爹",
)


PHRASES = {
    "what": (
        "不是哥们？", "啊？还能这么整的？",
        "逆天", "我寻思也没人跟我说啊。",
    ),
    "乖": (
        "义父在上，请受孩儿一拜。", "孝！太孝了！", "真的假的",
        "我一直都是你最忠实的黄豆啊", "这波必须给老哥磕一个。",
    ),
    "兴奋": (
        "大的要来了！", "芜湖，起飞！", "好好好，这下有节目效果了。",
        "速速端上来罢，我已经等不及了", "这波指定有狠活。",
    ),
    "吐了": (
        "麻了，午饭算是白吃了。", "鉴定为纯纯的逆天。", "别发了，真顶不住。",
        "看一眼难受一天。", "寄，我先去缓缓。",
    ),
    "吐舌": (
        "略略略，急了急了。", "不会真破防了吧？", "就这？就这？",
        "你先别急，让我乐一会儿。", "气不气？气就对了。",
        "我命令你骂他","LZSB","薄纱","错误的，除了我","在吗起手",
        "正确的",
    ),
    "呵呵": (
        "典", "你说得对", "差不多得了",
        "我就笑笑，不说话。", "绷","打个∠先","合乎周礼",
    ),
    "啊": (
        "啊？", "不是，这也能寄？", "我超，发生甚么事了？",
        "坏了，没绷住。", "这下真给我整不会了。",
    ),
    "喷水": (
        "蚌埠住了，一口水喷屏幕上。", "绷，这谁顶得住。", "你是懂节目效果的。",
        "刚喝的水，算你头上。", "别整了，真要笑喷了。","被河坝玩法吓晕"
    ),
    "噗": (
        "噗，没忍住。", "绷。", "本来不想笑的，除非忍不住。",
        "这下属实有点难绷。", "一开口就是老乐子人了。",
    ),
    "小乖": (
        "我暂且蒙在鼓里。", "孝。", "老实巴交黄豆一枚。",
        "老哥说啥就是啥。", "弱小、可怜，但能吃瓜。",
    ),
    "开心": (
        "好好好，舒服了。", "今天状态属实不错。", "乐。",
        "+3", "有一说一，确实爽。","我破防了"
    ),
    "微微一笑": (
        "懂的都懂。", "笑而不语。", "典中典",
        "有些话说出来就没意思了。", "一切尽在掌握。",
    ),
    "捂嘴笑": (
        "想笑，先憋一下。", "绷不住了，但要保持礼貌。", "差点笑出声。",
        "乐子来了，先别声张。", "我一般不笑，除非真的好笑。",
    ),
    "欢呼": (
        "赢！", "开香槟喽！", "拿下，直接拿下！",
        "芜湖，这波赢麻了。", "兄弟们，把好耶打在公屏上。",
        "建议去竞选弱智吧吧主",
    ),
    "汗": (
        "汗流浃背了吧，老弟。", "这下有点尴尬了。", "情况不对，准备润。",
        "我不好说，我擦个汗先。", "压力一下就上来了。",
    ),
    "流汗": (
        "麻。", "小丑竟是我自己。", "问题不大——问题很大。",
        "这下真汗流浃背了。", "先叠个甲，我不是针对谁。",
    ),
    "爱": (
        "好兄弟，贴贴。", "老哥你是这个。", "这波属于双向奔赴。",
        "可以，关注了。", "你小子还怪招人稀罕的。","拱坝老哥狂喜",
    ),
    "生气": (
        "急。", "你说谁急了？我一点都不急！", "差不多得了，真当我没脾气啊。",
        "再整烂活我可要开喷了。", "血压上来了。",
    ),
    "疑问": (
        "不是，哥们？", "细说。", "啊？这合理吗？",
        "有没有懂哥解释一下。", "所以这跟我有什么关系呢？",
    ),
    "真棒": (
        "赢。", "可以的，老哥。", "这波操作我给满分。",
        "有一手，确实有一手。", "好活，当赏。",
    ),
    "笑": (
        "乐。", "哈哈哈哈，绷不住了。", "笑嘻了家人们。",
        "今日首绷。", "这贴的意义就是让我笑出声。",
        "嚯嚯嚯，夸脏喔","入典，合影","一针见血的","6的，这样下去会越来越好的",
        "玩原神玩的"
    ),
    "紧张": (
        "坏了，要寄。", "稳住，先别急。", "情况不妙，随时准备润。",
        "这下压力来到黄豆这边。", "完了，手心全是汗。",
    ),
    "阴险": (
        "真的假的", "阿珍你來真的啊",
        "先别声张，我有一个大胆的想法。", "优势在我。","TD","转人工"
    ),
    "黑头高兴": (
        "好似，开香槟喽。", "乐，今天就爱看这个。", "这下心里平衡了。",
        "好好好，大家都有光明的未来。", "地狱笑话虽迟但到。",
    ),
    "吃瓜": (
        "前排吃瓜", "细说，我爱听", "这瓜保熟吗？",
        "别急，让子弹飞一会儿", "有乐子？那我可不困了",
    ),
    "喝酒": (
        "来，走一个！", "都在酒里了", "老哥我先干了",
        "借酒消愁是吧？", "今天不聊别的，开喝",
    ),
    "嘿嘿嘿": (
        "嘿嘿嘿", "被我逮到了吧", "你小子最好有事",
        "这下让我抓到把柄了", "懂了，这就去拱火",
    ),
    "狂汗": (
        "汗流浃背了吧老弟", "这下真顶不住了", "坏了，压力拉满",
        "别催了，已经在做了！", "润不掉了，硬着头皮上吧",
    ),
    "泪": (
        "寄！", "真破防了", "别骂了别骂了",
        "这下眼泪不争气地流了下来", "我这一生如履薄冰",
    ),
    "嘻嘻": (
        "嘻嘻", "乐", "有好戏看了",
        "别管，我自有妙计", "今天心情不错",
    ),
    "呀咩爹": (
        "不要啊！", "达咩！", "你不要过来啊！",
        "停停停，真顶不住了", "救一下啊老哥！",
    ),
}


PASSIVE_PHRASES = (
    "还搁这摸鱼呢？作业写完了吗？",
    "别刷了，代码不会自己跑。",
    "保存了吗？别等寄了才开始急。",
    "有一说一，该干点正事了。",
    "摆。就摆五分钟，不能再多了。",
    "黄豆正在视奸你的桌面。",
    "再摸下去，ddl 都要骑脸了。",
    "情况不对先保存，然后再润。",
    "麻了就歇会儿，回来继续整。",
    "今天你负责学习，我负责在旁边指点江山。",
    "代码跑了吗？没跑你搁这分析啥呢。",
    "老哥，起来喝口水，别真给自己熬寄了。",
    "Du bist gut genug",
)


DRAG_PHRASES = (
    "急急急，给我放下来！",

    "不是哥们，你要给我拖哪去？",
    "扎不多得嘞，黄豆也是有尊严的。",
    "要润是吧？行，带我一个。",
    "6，把我当窗口拖是吧。",
    "咕咕嘎嘎！",
)


def phrase_for(expression: str) -> str:
    """按表情随机选择一句台词。"""
    return random.choice(PHRASES.get(expression, PASSIVE_PHRASES))


DATA_PATH = user_data_root() / "phrases.json"


class PhraseRepository:
    """从 JSON 加载台词，并在文件不存在时迁移当前内置文案。"""

    def __init__(self, path: Path = DATA_PATH) -> None:
        self.path = Path(path)
        if self.path == DATA_PATH:
            ensure_user_directories()
            migrate_resource_file("data/phrases.json", self.path)
        self.phrases: dict[str, tuple[str, ...]] = {}
        self.passive: tuple[str, ...] = ()
        self.drag: tuple[str, ...] = ()
        self.reload()

    @staticmethod
    def _default_data() -> dict:
        return {
            "phrases": {name: list(values) for name, values in PHRASES.items()},
            "passive": list(PASSIVE_PHRASES),
            "drag": list(DRAG_PHRASES),
        }

    def _write_defaults(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(self._default_data(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def reset_to_defaults(self) -> None:
        """用当前版本内置默认文案覆盖外部文案文件。"""
        self._write_defaults()
        self.reload()

    def reload(self) -> None:
        if not self.path.exists():
            self._write_defaults()
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
            phrase_data = raw.get("phrases", {})
            self.phrases = {
                name: tuple(str(text) for text in phrase_data.get(name, PHRASES[name]))
                for name in EXPRESSION_NAMES
            }
            self.passive = tuple(str(text) for text in raw.get("passive", PASSIVE_PHRASES))
            self.drag = tuple(str(text) for text in raw.get("drag", DRAG_PHRASES))
            if not self.passive or not self.drag:
                raise ValueError("待机或拖动台词不能为空")
        except (OSError, ValueError, TypeError, json.JSONDecodeError, KeyError):
            self._write_defaults()
            raw = self._default_data()
            self.phrases = {name: tuple(values) for name, values in raw["phrases"].items()}
            self.passive = tuple(raw["passive"])
            self.drag = tuple(raw["drag"])

    def for_expression(self, expression: str) -> str:
        return random.choice(self.phrases.get(expression, self.passive))
