# VSM baseline 20260905_084033_7e30074a

首轮探索性 Editor 采集。原始运行以 error 结束；2K Hard/PCF 完成，
4K Hard 有失效/长停顿，4K PCF 因相机 15 秒未渲染中断，8K 两档缺失。
使用 D3D12 debug；不能代表发布性能，也不能认证 P5 验收完成。

- [优化计划与完整解释](../../VSMOptimizationPlan.md)
- raw/：原始 10 个 CSV/JSON，共 788,052 字节，SHA-256 在 manifest.json。
- sample-audit.json：统计复核、连续性、缺失计时与场景快照比较。
- editor-log-excerpt.txt：关联本轮保存路径的启动参数和中断异常。
- audit_samples.py：仅用 Python 标准库重算 72 行指标，与原 summary 对照，
  输出 sample-audit.json；保留长帧和异常值。

从包目录复核：

    python Roadmap~/Baselines/20260905_084033_7e30074a/audit_samples.py

已复核：4,237 条观测，72 行指标的有效数量、median、nearest-rank P95、
min/max 一致；帧编号连续无重复，非零 FrameTiming 时间戳递增。
这不证明 GPU 数据与观测帧同步，也不将阶段分位数之和视为总时间。

原 run.json 没有 revision；review HEAD 与源码哈希仅记录评审环境，
不能追认为采集版本。采集时 LightingDay 为 dirty。后续运行另建目录，
不覆盖本目录中的原始数据。