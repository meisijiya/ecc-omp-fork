---
name: ecc-omp-release-management
description: 打 tag、写 changelog、分级发布与回滚，核对制品可追溯。发版、写发布说明时用。
---

# 发布与上线管理（release management / ship）

本 skill 管「把一个通过验证的版本安全送到生产并能被追溯、能回滚」这一整段事。
它不覆盖 Dockerfile 写法、容器编排、K8s manifest 写法，也不展开滚动 / 蓝绿 / 金丝雀三种策略的对比——
那部分属于 `skill://ecc-omp-deployment-patterns`；数据库迁移细节看 `skill://ecc-omp-database-migrations`；
发布前的整体验证闭环看 `skill://ecc-omp-verification-loop`。

---

## 何时用

- 要打 release tag、写或更新 changelog / release notes。
- 要决定本次改动是 patch / minor / major，以及是否需要分级发布。
- 要评估「能不能回滚」「回滚会不会带崩数据库」。
- 要审核一次依赖升级、宣布弃用（deprecation）、核对制品来源。

## 何时不用

- 只是本地改一个函数、跑通单测：用 `skill://ecc-omp-error-handling` 这类按语言的 skill。
- 只涉及 CI 流水线本身的定义（YAML 怎么写）：看 `skill://ecc-omp-deployment-patterns`。
- 只做代码评审或提交信息格式：分别看 `skill://ecc-omp-springboot-verification`（按语言）与
  `skill://ecc-omp-conventional-commit-review`。
- 改库表结构本身怎么做迁移：看 `skill://ecc-omp-database-migrations`，本 skill 只说「迁移与回滚的关系」。

---

## 步骤

### 1. 版本号与变更记录

采用 SemVer（`MAJOR.MINOR.PATCH`）：

- **MAJOR**：有不兼容的 API 变更（breaking）。旧客户端调不动。
- **MINOR**：向后兼容的新功能。旧客户端照常工作。
- **PATCH**：向后兼容的缺陷修复。

**什么算 breaking**（即必须进 MAJOR）：
- 删除或重命名公开接口 / 字段 / 配置项。
- 改变接口语义（同名但行为不同，例如分页从 1-based 变 0-based、错误码含义变化）。
- 改变默认行为且用户可能依赖旧默认（例如默认超时从 30s 改成 5s）。
- 升级到不兼容的依赖大版本。

**不算 breaking**（进 MINOR 即可）：新增可选字段、新增接口、给错误补充信息、性能优化、日志调整。

**changelog 条目格式样例**（按类型分组的 Keep-a-Changelog 风格）：

```markdown
## [1.3.0] - 2026-10-31

### Added
- 导出报表支持 PDF (#142)

### Changed
- 分页接口默认页大小由 20 调整为 50 (#138)

### Fixed
- 修复时区导致定时任务重复触发 (#145)

### Deprecated
- `/v1/legacy/users` 将于 2.0.0 删除，改用 `/v2/users` (#130)

### Breaking
- 删除 `/v1/legacy/users`，迁移指引见迁移文档 (#130)
```

**版本号与制品 tag 的对应**：git tag 一律用 `v<semver>`（如 `v1.3.0`）。
制品（镜像、npm 包、jar）的版本号与 tag 一字不差地对应；**不要用 `latest` 作为发布版本**，
`latest` 只给内部尝鲜通道。CI 构建出的镜像 tag = `v1.3.0`，不可改写为日期或 build number。

### 2. 发布前门禁清单

三个时点，证据逐级变硬：

| 时点 | 必备证据 |
| --- | --- |
| **合并前** | CI 绿（构建 + 单测通过）；变更记录条目已写（含关联 issue / PR 号）；新配置项有默认值且文档齐；`skill://ecc-omp-change-impact` 影响面已确认 |
| **打 tag 前** | 上一项全过；集成 / E2E 通过；迁移脚本已就绪且可回滚（见第 3 节）；dependency 锁文件已签入；changelog 条目齐；`skill://ecc-omp-verification-loop` 闭环跑完 |
| **发布前** | 上述全过；分级发布计划已定（内测 → 小流量 → 全量）；回滚预案与责任人明确；监控 / 告警已就位；`skill://ecc-omp-security-review` 对涉及鉴权 / 数据的改动已确认 |

少任何一项都不许进下一时点。tag 是单向承诺：一旦打了 `v1.3.0`，这个号码就代表那一份制品，不能再改内容。

### 3. 分级发布与回滚决策

顺序：**内测（内部 / canary）→ 小流量（1%–10%）→ 全量**。每一级先观察核心指标
（错误率、延迟 P99、关键业务转化）再放量；放量节奏由指标驱动，不由日历驱动。

**触发回滚的条件**（任一即回滚，不犹豫）：
- 错误率超过基线 2 倍且持续 5 分钟。
- 关键业务路径失败率上升或出现数据写入异常。
- 出现安全相关问题（越权、泄露）。
- 回滚比继续排查更快且风险更低。

**回滚与数据库迁移的关系（expand-contract）**：
- 迁移遵守「先加后删、向后兼容」：先在旧版本上**加**新列 / 新表 / 新字段（expand），
  让新旧代码都能跑；确认新代码稳定后再**删**旧结构（contract）。
- 因此**回滚代码是安全的**：回滚到的旧版本仍然认识当时的数据库结构。
- 反过来，破坏性迁移（删列、改类型）必须与代码发布解耦，且确认没有任何在跑的旧版本依赖它。
- **绝不只回滚代码不回滚配置**：配置往往先于代码生效，单独回滚代码会让新配置指向不存在的行为。配置与代码作为同一发布单元一起回滚。

### 4. 制品与依赖的可追溯性

- **可重现构建**：锁文件（`package-lock.json` / `poetry.lock` / `gradle.lockfile`）必须签入；
  记录构建环境（基础镜像 digest、编译器版本、构建参数）。同一 `v1.3.0` 在任何机器上重建应得到同一产物。
- **依赖升级与弃用公告**：升级依赖先在本仓小范围验证，再写 changelog 的 `Deprecated` / `Breaking` 段；
  对外依赖用发布渠道（release notes + 代码内 deprecation 注解）给出迁移指引和淘汰时间线。
- **用 changelog 标注 breaking**：所有 MAJOR 级、删除类、语义变更类改动必须在 changelog 的 `Breaking` 段显式列出，
  并附迁移文档链接，禁止埋在 `Fixed` / `Changed` 里悄悄发。

---

## 命令样例

下面命令与具体 CI 产品无关；GitHub Actions / npm / docker 仅作示例，按你实际工具替换。

1. **打标注 tag 并推送**（tag 名 = 版本号）：
   ```sh
   git tag -a v1.3.0 -m "release: 1.3.0" && git push origin v1.3.0
   ```

2. **语义化版本比较 / 过滤**（用 semver 工具，可替换为自家版本库）：
   ```sh
   npx semver 1.3.0 -r ">=1.0.0 <2.0.0"   # 命中则打印 1.3.0，未命中无输出
   git tag -l 'v*' | sort -V               # 列出所有版本并按语义排序
   ```

3. **查某个 commit 影响了哪些文件 / 模块**（判断它该不该进这个 release）：
   ```sh
   git diff-tree --no-commit-id --name-only -r <commit>
   git show --stat <commit> | head -40
   ```

4. **查看某次发布（tag）相对上一次包含了哪些文件**：
   ```sh
   git diff --stat v1.2.0 v1.3.0
   git ls-tree -r --name-only v1.3.0       # 该 tag 当时的完整文件清单
   ```

5. **校验 changelog 与 tag 是否一致**（发版前门禁脚本片段）：
   ```sh
   grep -q "^## \[1.3.0\]" CHANGELOG.md && git rev-parse -q --verify v1.3.0 >/dev/null \
     && echo "OK: changelog 与 tag 一致" || echo "FAIL: 缺 changelog 条目或 tag"
   ```

6. **列出两次发布之间的提交**（写 release notes 的输入）：
   ```sh
   git log v1.2.0..v1.3.0 --oneline
   ```

7. **宣布依赖弃用**（示例用 npm，其它生态替换命令）：
   ```sh
   npm deprecate some-pkg@"<2.0.0" "use v2 API, removed in 2027; see migration guide"
   ```

---

## 判定表

| 发布级别 | 典型内容 | 门禁强度 | 回滚要求 |
| --- | --- | --- | --- |
| **patch** | 缺陷修复、无行为变更 | 合并前 + 打 tag 前清单；CI + 单测 + 锁文件 | 可快速回滚；迁移通常无；配置与代码同滚 |
| **minor** | 向后兼容新功能 / 弃用预告 | 上者全过 + 集成 / E2E + changelog 条目齐 | 分级发布到小流量即可；expand 类迁移先上 |
| **major** | breaking 变更 | 全部门禁 + 分级发布计划 + 回滚预案 + 监控就位 + 安全评审 | 强制分级（内测 → 小流量 → 全量）；迁移按 expand-contract 分两发；Breaking 段必写 |

级别越高，门禁越硬、回滚预案越正式、发布越分级。major 不允许「一次性全量直推」。

---

## 反模式

1. **直接改已发布版本号**：发了 `v1.3.0` 又往里塞内容重打同号 tag。版本号是承诺，不可改写；要改就发 `v1.3.1`。
2. **把 breaking change 混在 patch 里**：minor 甚至 patch 偷偷删接口 / 改语义，旧客户端无预警崩。breaking 必须进 MAJOR。
3. **只回滚代码不回滚配置**：配置常先于代码生效，单独回滚代码让新配置指向不存在的行为，反而扩大事故。
4. **没有 changelog 条目就发 tag**：tag 代表一份制品，但没人能从 release 看出改了什么、要不要迁移。
5. **依赖升级不锁版本**：用 `^` 浮动或 `latest`，导致同一 tag 在不同时间重建出不同产物，丧失可重现性。
6. **破坏性迁移与代码同发且不可回滚**：删列 / 改类型后旧版本立刻崩，回滚代码也救不回。必须遵守 expand-contract 先加后删。
7. **用 `latest` 作为发布版本**：无法追溯某台机器跑的是哪份代码，回滚和事故定位都失准。
