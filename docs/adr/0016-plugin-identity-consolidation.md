# ADR-0016: 插件身份收口——远端改名、运维 skill 进仓、TypeScript 入口去重

**Date**: 2026-11-03
**Status**: accepted
**Deciders**: 本 fork 维护者

## Context

ADR-0013 把插件 id、安装根与运行名前缀改成 `omp-skill-forge` / `forge-`，但还有三处没收口：

1. **远端仓库名**仍是 `meisijiya/ecc-omp-fork`，文档里的克隆地址与 issue 入口都指着它，
   插件叫 forge、仓库叫 omp-fork，对使用者仍是两套名字。
2. **本插件自己的运维 skill**（更新流水线、CI 失败定位、收纳第三方 skill）写成了宿主里的
   managed skill，名字带旧前缀，且不受仓库版本管：改了仓库里的门禁流程，这些 playbook
   不会跟着更新。同一件事有两个入口。
3. **TypeScript 入口重复**：ECC 上游新加了 `typescript-patterns`，收纳池里的 pstack
   `typescript-best-practices` 讲的是同一件事（判别联合、窄化、类型守卫）。两条都会被
   「写 TS」的请求触发，模型只能随机挑一条。

## Decision

1. **远端改名一次做完**：`gh repo rename omp-skill-forge` 之后，`origin` 与文档里的 URL
   一并指向新名，仓库、插件 id、安装根、运行名前缀四者同名。
2. **运维 skill 进 `own/skills/`**：以 `forge-pipeline`、`forge-ci-triage`、
   `forge-absorb-third-party-skill` 三条随插件分发，宿主里的 managed skill 副本删除。
   内容按当前状态重写（七个门禁、当前 profile 规模、`forge-` 前缀、仓库相对路径），
   旧的机器绝对路径不再进正文。`own/skills/` 无条件进所有 profile，所以这三条对每个
   profile 都可见。
3. **TypeScript 只留一个入口**：上游的 `forge-typescript-patterns` 承担 TS 写法，
   pstack 的 `forge-typescript-best-practices` 留在收纳池里但不再物化；选路表指向新入口。
   理由：上游那条自包含且随上游更新；pstack 那条原本依赖同包的
   `principle-type-system-discipline`（我们不发这个 principle），属于悬空依赖。
4. **上游新资产必须分类**：pin 前进后 `manifest/groups.json` 必须与 `pool/` 成员完全一致
   （`apply_selection.py` 的硬校验），新到的 skill 要么进某个 group（并补中文触发描述），
   要么就只能待在 `pool/` 里不进任何 profile。

## Alternatives

- **运维 skill 继续放 managed skill**：不占提示开销，但与仓库脱节、改门禁不会同步，
  名字还带旧前缀。否决。
- **两条 TypeScript skill 都留**：full profile 本来就是「全都要」，代价是两个入口同时
  抢同一类请求。否决。
- **把 `typescript-patterns` 加进 java-python profile**：TS 不是本 profile 的目标栈，
  加进来只是每轮多付提示开销。否决。

## Consequences

- 宿主里那三条 managed skill 消失，运维知识跟着插件版本走；换机器或重装插件即可拿到。
- full profile 的 TypeScript 入口从 pstack 换到 ECC，skill 正文不再引用不发 principle。
- 上游继续前进时，每批新 skill 都要走「进 group + 补中文描述」或「只留 pool」两条路之一，
  否则 `apply_selection.py` 直接失败——分类缺失不会被静默放过。
