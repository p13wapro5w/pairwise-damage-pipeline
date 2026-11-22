# pairwise-damage-pipeline

## 领域

游戏、图形与多媒体

## 主题

伤害结算管线

## 说明

抗性乘法叠加、护甲分段、DOT 快照与服务器权威。

初始状态下 `gameplay/damage_pipeline.py` 中所有函数抛出 `NotImplementedError`，测试全部失败。
修复实现后运行：

```bash
python -m pytest -q
```

期望全部通过。
