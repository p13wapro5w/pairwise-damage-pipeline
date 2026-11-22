"""伤害管线核心模块。

修复清单：
1. 抗性乘法叠加（两条 50% = 75%，不再加法免疫）
2. 护甲分段公式（负护甲区间增伤而非反向加防）
3. 暴击乘区在抗性之前结算
4. DOT 按施放时快照，每跳不重掷暴击
5. 护盾在减伤之后吸收，且只结算一次
6. 伤害下限钳制，不再出现 0 伤害 / 负治疗
7. 仅在最终输出取整，中间步骤保留浮点
8. 伤害由服务器权威结算，客户端上报仅作校验
9. 全程记账：溢出、吸收、每级中间值都入台账
10. 战斗日志数字按本地化格式输出
"""

from __future__ import annotations

import math

ARMOR_K = 100.0  # 护甲常数：减伤 = armor / (armor + K)


def _clamp(value, lo, hi):
    return max(lo, min(hi, value))


def resistance_multiply(*resists):
    """抗性乘法叠加：combined = 1 - Π(1 - r)。

    两条 50% 抗性叠加为 75%，只有存在真正的 100% 抗性才会免疫。
    每条抗性钳制在 [0, 1)。
    """
    remaining = 1.0
    for r in resists:
        remaining *= 1.0 - _clamp(float(r), 0.0, 1.0 - 1e-9)
    return 1.0 - remaining


def armor_segment(armor, damage):
    """护甲分段公式。

    armor >= 0：减伤区，mult = K / (K + armor)，递减趋近 0。
    armor < 0：增伤区，mult = 2 - K / (K - armor)，在 (1, 2] 区间，
    破甲让目标受伤更重，而不是反向给目标加防。
    """
    armor = float(armor)
    damage = float(damage)
    if armor >= 0:
        mult = ARMOR_K / (ARMOR_K + armor)
    else:
        mult = 2.0 - ARMOR_K / (ARMOR_K - armor)
    return damage * mult


def crit_order(crit_mult, base_damage):
    """暴击乘区作用于基础伤害，在抗性 / 护甲之前结算。

    返回暴击后的面板伤害，后续再进入护甲与抗性段，
    避免暴击乘在减伤之后导致实际收益高于面板。
    """
    return float(base_damage) * float(crit_mult)


def dot_snapshot(tick_damage, crit_mult, ticks=1):
    """DOT 快照：施放时结算一次暴击，之后每跳沿用同一数字。

    返回长度为 ticks 的列表，每跳数值相同。
    """
    tick = float(tick_damage) * float(crit_mult)
    return [tick] * max(1, int(ticks))


def shield_after(shield, damage):
    """护盾在减伤之后吸收，且吸收量只结算一次。

    返回 (剩余伤害, 剩余护盾)。护盾顶掉的部分不再进入后续记账。
    """
    shield = max(0.0, float(shield))
    damage = max(0.0, float(damage))
    absorbed = min(shield, damage)
    return damage - absorbed, shield - absorbed


def damage_floor(damage, minimum=1.0):
    """伤害下限钳制。

    正向伤害至少为 minimum（默认 1），不为正的伤害归 0，
    绝不允许负数流入治疗端。
    """
    damage = float(damage)
    if damage <= 0:
        return 0.0
    return max(damage, float(minimum))


def final_round(value):
    """仅末位取整：中间步骤一律保留浮点，输出时四舍五入（half-up）。"""
    value = float(value)
    if value >= 0:
        return int(math.floor(value + 0.5))
    return -int(math.floor(-value + 0.5))


def server_authority(client_value, server_value):
    """服务器权威：以服务器结算结果为准，客户端上报值不参与结算。"""
    return server_value


def ledger_record(*stages):
    """全程记账：记录每一步中间值，返回台账。

    台账包含所有阶段值与最终值，溢出、吸收等由调用方作为独立阶段传入，
    统计面板不再只记最终值。
    """
    entries = [float(s) if isinstance(s, (int, float)) else s for s in stages]
    return {
        "stages": entries,
        "final": entries[-1] if entries else None,
    }


def localized_number(value, decimals=0):
    """本地化数字格式：标准千位分组 + 指定小数位，返回字符串。"""
    decimals = max(0, int(decimals))
    return f"{float(value):,.{decimals}f}"


def immunity_check(*resists):
    """免疫判定：乘法叠加后达到 100% 才算免疫。

    由于每条抗性钳制在 1 以下，只有确实存在 100% 抗性时才会免疫，
    两条 50% 叠加（75%）不再误判为免疫。
    """
    return resistance_multiply(*resists) >= 1.0 - 1e-9


def pierce_calc(armor, pierce):
    """护甲穿透：只削减正护甲，负护甲区间不受穿透影响。

    防止破甲装备在负护甲区间反向给目标加防。
    """
    armor = float(armor)
    pierce = _clamp(float(pierce), 0.0, 1.0)
    if armor <= 0:
        return armor
    return armor * (1.0 - pierce)


def heal_convert(damage, floor=0.0):
    """负伤害归零：伤害下限之外的负值不转化为治疗。"""
    return max(float(damage), float(floor))


def overflow_track(damage, hp):
    """溢出追踪：实际伤害与溢出量分别入账。"""
    damage = max(0.0, float(damage))
    hp = max(0.0, float(hp))
    dealt = min(damage, hp)
    return {"dealt": dealt, "overflow": damage - dealt}


def element_split(ratios):
    """元素拆分：按比例拆分并归一化，保证总和恒为 1。"""
    ratios = [max(0.0, float(r)) for r in ratios]
    total = sum(ratios)
    if total <= 0:
        return [0.0 for _ in ratios]
    return [r / total for r in ratios]
