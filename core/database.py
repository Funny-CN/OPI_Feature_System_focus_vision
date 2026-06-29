"""
螺丝型号数据库模块

管理已知螺丝型号的增删改查，
以及测量值到型号的匹配逻辑。
"""

import os
import json
from typing import List, Optional, Dict
from dataclasses import dataclass, asdict


@dataclass
class ScrewSpec:
    """单个螺丝型号的规格定义"""
    id: str               # 唯一标识，如 "M6x12"
    name: str             # 显示名称，如 "M6×12 盘头螺丝"
    diameter: float       # 标准直径 (mm)
    length: float         # 标准长度 (mm)
    tolerance: float      # 匹配公差 (mm)


@dataclass
class MatchResult:
    """匹配结果"""
    matched: bool                     # 是否匹配成功
    screw: Optional[ScrewSpec] = None # 匹配到的型号
    deviation: float = 999.0          # 测量值与标准的偏差
    measured_diameter: float = 0.0    # 实际测量值


class ScrewDatabase:
    """螺丝型号数据库，负责型号管理和匹配逻辑"""

    def __init__(self, config_path: Optional[str] = None):
        if config_path is None:
            config_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)), "config.json")
        self._config_path = config_path
        self._screws: List[ScrewSpec] = []
        self._load()

    # ── 内部数据读写 ──────────────────────────────────

    def _load(self):
        """从 config.json 加载螺丝型号列表"""
        try:
            with open(self._config_path, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            raw_list = cfg.get("screws", [])
            self._screws = [ScrewSpec(**item) for item in raw_list]
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"[DB] 加载 config.json 失败: {e}")
            self._screws = []

    def _save(self):
        """将当前螺丝型号列表写回 config.json"""
        try:
            with open(self._config_path, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            cfg["screws"] = [asdict(s) for s in self._screws]
            with open(self._config_path, "w", encoding="utf-8") as f:
                json.dump(cfg, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[DB] 保存 config.json 失败: {e}")

    # ── 型号管理 CRUD ───────────────────────────────

    def list_all(self) -> List[ScrewSpec]:
        """返回所有已注册的螺丝型号"""
        return self._screws.copy()

    def get_by_id(self, screw_id: str) -> Optional[ScrewSpec]:
        """按 ID 查找螺丝型号"""
        for s in self._screws:
            if s.id == screw_id:
                return s
        return None

    def add(self, screw: ScrewSpec) -> bool:
        """添加新螺丝型号，ID 重复时返回 False"""
        if self.get_by_id(screw.id) is not None:
            return False
        self._screws.append(screw)
        self._save()
        return True

    def remove(self, screw_id: str) -> bool:
        """删除指定螺丝型号"""
        before = len(self._screws)
        self._screws = [s for s in self._screws if s.id != screw_id]
        if len(self._screws) < before:
            self._save()
            return True
        return False

    def update(self, screw: ScrewSpec) -> bool:
        """更新螺丝型号参数"""
        for i, s in enumerate(self._screws):
            if s.id == screw.id:
                self._screws[i] = screw
                self._save()
                return True
        return False

    # ── 匹配逻辑 ────────────────────────────────────

    def match(self, measured_diameter: float) -> MatchResult:
        """
        将测量值与数据库中的所有型号比对，返回最佳匹配。

        匹配规则：
          1. 只考虑偏差在 tolerance 以内的型号
          2. 取偏差最小的作为匹配结果
          3. 如果没有型号在公差内，返回 matched=False
        """
        candidates = []
        for screw in self._screws:
            deviation = abs(measured_diameter - screw.diameter)
            if deviation <= screw.tolerance:
                candidates.append((deviation, screw))

        if not candidates:
            return MatchResult(
                matched=False,
                measured_diameter=measured_diameter
            )

        candidates.sort(key=lambda x: x[0])
        best_dev, best_screw = candidates[0]
        return MatchResult(
            matched=True,
            screw=best_screw,
            deviation=round(best_dev, 3),
            measured_diameter=measured_diameter
        )

    def match_multi(self, measurements: List[float]) -> List[MatchResult]:
        """批量匹配多颗螺丝的测量结果"""
        return [self.match(d) for d in measurements]
