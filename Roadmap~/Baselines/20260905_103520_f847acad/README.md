# 当前 VSM 基线：20260905_103520_f847acad

当前无 D3D12 debug 启动参数的探索性 Editor 参考，取代上一轮作为后续工作的起点。
匹配本轮保存路径的日志启动于 10:33:04 UTC，已检查无 -force-d3d12-debug 参数。
项目 Logs/Editor.log 属于更早的一次启动；本轮实际日志路径记录在 manifest.json。

- [当前优化计划与统计解释](../../VSMOptimizationPlan.md)
- raw/：10 个原始 CSV/JSON，908,913 字节；SHA-256 见 manifest.json。
- sample-audit.json：5,320 条观测，72 行指标的独立复算与完整性审计。
- comparison.json：跨轮相机/光源/参数比较和同档 2K PCF 变化。
- editor-log-excerpt.txt：经筛选的启动字段与本轮相机超时消息。

2K PCF（2040 条）、4K Hard（1323 条）可作完整单轮整帧/阶段计时参考。
2K Hard 全帧计时全缺失且有长帧；4K PCF 在 6.09 秒后中断；8K 未采集。
Allocate 等必执行阶段依旧无数据，原 revision 为空。不能认证全套性能或质量完成。

复核（在包目录）：

    python Roadmap~/Baselines/20260905_103520_f847acad/audit_samples.py

已复核 72 行有效数量、median、nearest-rank P95、min/max 与原始 summary 一致。
帧编号连续无重复，非零时间戳递增；缺失值和异常值均未替换/删除。
旧数据保留在相邻的 20260905_084033_7e30074a 目录。新轮另建目录，不覆盖原始样本。
