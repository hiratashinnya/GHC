# dataclass ルーティングメソッドパターン

## 問題

複数フィールドを「キー文字列」で選択するロジックが、dataclass の外部モジュールに自由関数として置かれると、
dataclass の内部構造（フィールド名）が外部に漏れ、新フィールド追加時に 2 ファイルの修正が必要になる。

```python
# NG — エンジン側が AccessControlConfig のフィールド名を直接知っている
def _get_candidate_rules(config: AccessControlConfig, operation_type: str) -> List[Rule]:
    if operation_type == "write":
        group = config.write_rules    # フィールド名が外部に漏れている
    elif operation_type == "read":
        group = config.read_rules
    elif operation_type == "command":
        group = config.command_rules
    else:
        return []
    return group.rules if group.enabled else []
```

**問題点:**
- `operation_type` → フィールド名のマッピングは `AccessControlConfig` の内部知識
- 新フィールド（例: `network_rules`）追加時に、`AccessControlConfig` と外部関数の両方を修正しなければならない

## 解決策

キー → フィールドのマッピングを dataclass 自身のメソッドとして持つ。

```python
# OK — config 自身がフィールドマッピングを知っている
@dataclass
class AccessControlConfig:
    write_rules: RuleGroup = field(default_factory=RuleGroup)
    read_rules: RuleGroup = field(default_factory=RuleGroup)
    command_rules: RuleGroup = field(default_factory=RuleGroup)

    def get_group(self, operation_type: str) -> RuleGroup:
        mapping = {
            "write": self.write_rules,
            "read": self.read_rules,
            "command": self.command_rules,
        }
        return mapping.get(operation_type, RuleGroup())


# 外部関数は thin adapter に留まる（フィールド名を知らない）
def _get_candidate_rules(config: AccessControlConfig, operation_type: str) -> List[Rule]:
    group = config.get_group(operation_type)
    return group.rules if group.enabled else []
```

**新フィールド追加時は `AccessControlConfig` と `get_group()` の mapping だけ更新すれば済む。**

## 判断基準

「その関数の引数が 1 つの dataclass インスタンスだけで、
戻り値もそのインスタンスのフィールドから作られる」場合はメソッドに移動する。
