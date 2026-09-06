# VSM 优化计划：首轮 Play Mode 样本

2026-09-05。决策：**先补齐计量并重采可靠基线，再优化 Resolve/Feedback；串行分配器是必须先测清的另一候选。** 当前数据不足以选择默认 4K/8K，也不能关闭 P5 性能或过渡质量验收。

## 原始数据与有效范围

已逐字节归档运行 **20260905_084033_7e30074a** 的 10 个 CSV/JSON，共 788,052 字节。保留全部原始长帧和缺失数据，不补零、不覆盖。

- [归档及复核说明](README.md)
- [原始汇总](raw/summary.csv)
- [运行与初始场景](raw/run.json)
- [SHA-256 清单](manifest.json)
- [独立样本审计](sample-audit.json)
- [启动参数和中断日志](editor-log-excerpt.txt)

4,237 条观测，全部 72 行指标的有效数量、median、P95、min、max 独立重算后与导出一致。帧编号连续无重复，非零 FrameTiming 时间戳递增。这些检查不证明 GPU 数据与观测帧同步。

运行于 08:40:33–08:41:47 UTC，最终 status=error。completedCases=3 只表示前三档已处理，其中一档未满足有效基线条件。只有前两档可作探索性静态参考。

| 档位 | 观测数 / 有效整帧 GPU 数 | 整帧 GPU median / P95（ms） | Resolve+Feedback median / P95（ms） | 判定 |
| --- | --- | --- | --- | --- |
| 2K Hard | 1708 / 1702 | 5.602 / 6.202 | 1.319 / 1.843 | 完成，探索性参考 |
| 2K PCF | 1579 / 1577 | 5.864 / 6.479 | 1.315 / 1.852 | 完成，探索性参考 |
| 4K Hard | 346 / 345 | 8.739 / 9.466 | 1.318 / 1.863 | 回退标记及长停顿，不用于收益对照 |
| 4K PCF | 604 / 87 | 9.129 / 9.817 | 1.319 / 1.832 | 中断，时长不足 |
| 8K Hard / PCF | 未采集 | — | — | 待补采 |

整帧 GPU 包含 Editor 和其它渲染工作，不是 VSM 总耗时。表中未剔除异常值。

## 场景起点

- Unity 6000.7.0a6，Direct3D12，RTX 5070 Ti，1920×1080；VSync=0、targetFrameRate=-1。
- 与本轮保存路径对应的 Editor 日志显示启动参数包含 **-force-d3d12-debug**，本轮不能代表普通启动或 Player 发布性能。
- 当前场景 Sponza：Assets/ClassicSponza/Scenes/Sponza.unity；叠加 SponzaLightingDay.unity，后者为 dirty。
- Camera_1 位于 LightingDay；位置 (0.02020285, 7.66298294, -2.43060470)，欧拉角 (359.22635, 3.03022, 0.45028)，FOV=60，near/far=0.01/1000。
- 主方向光位置 (1.10413980, 15.50647163, -8.50347042)，欧拉角 (59.46513, 355.08792, 0.46698)，朝光源方向 (0.04350399, 0.86132014, -0.50619674)；depth/normal/slope bias=1/1/2.5。
- 所有已采档位：FirstLevel=1、MaxDistance=150、Transition=0.2、ScreenDensity=false、Denoise=false；9 个 clipmap，物理页预算 256。
- 各档开始/结束的相机、五盏灯和场景信息一致；未触发相机运动、尺寸变化、参数不匹配。端点一致不能排除未记录的中间物体或光源运动。
- 2K 两档末帧 allocated/requested/new/overflow 均为 79/79/0/0；4K Hard 为 187/187/0/0。这不能证明整段或更高分辨率没有预算压力。
- 原 run.json 的 revision 为空。清单中的 review HEAD 和源码哈希只标识评审时工作区，不能追认为采集版本。LightingDay 有未保存修改，仅加载场景文件不能重建本轮状态。

本轮相机不同于 [原固定墙面捕获](../../VSMQualityBaseline.md)，故保持独立基线，不把这些整帧时间写进旧表的 VSM 总耗时列，也不移植旧 ROI 质量结论。

## 计量问题

**必执行阶段缺失。** Allocate、ClearPhysicalPages、FinalizePages、DynamicRaster 全部没有样本，而 [CSMShadowPass](../../../Runtime/RenderPass/Core/CSMShadowPass.cs) 的有效 VSM 路径会执行这些 scope。它们使用字符串 BeginSample/EndSample，有数据的多数阶段使用 [VSMProfiling](../../../Runtime/RenderPass/Core/VSMProfiling.cs) 的 ProfilingSampler；recorder 则按 Render category 查名称。类别/句柄绑定不一致是待验证原因，空列不能解释为工作为零。InvalidateStatic、UnityCompatibilityRaster、ResetFeedback 可能在静态窗口未执行，需要区分未执行与采集不可用。

**4K Hard 不代表 13 秒稳定运行。** 观测跨度 12.9815 秒，其中一次帧间隔 9.8368 秒；其余帧间隔合计约 3.154 秒。350 次相机回调中 3 次缺少有效 VSM receiver snapshot。当前累计时间和总观测数的完成条件会被停顿推进；导出字段也无法将这三次失效定位到具体样本，不能挑行拼成有效基线。失效和停顿的根因及关系尚未确认。

**4K PCF 是相机渲染超时。** 日志明确为 “The selected camera has not rendered for 15 seconds”，不是已证实的 GPU 超时或分配器崩溃。观测跨度仅 5.5523 秒，最后连续 517 条没有新 FrameTiming 结果。阶段计时仍有变化，因此不能强行按行关联。相机为何停止渲染、FrameTiming 为何提前停止更新，仍需后续上下文。

**整帧 GPU 与 GC 归因有限。** 2K Hard/PCF 分别有 41/45 条正 GPU 时间低于 1 ms，最小约 0.032 ms；4K Hard 有 63 条低于 1 ms。需核对 Editor/计时来源，不能按阈值删除或与不同延迟的 Resolve 逐行比较。两档完整样本的 Editor-frame GC median 均为 14,475 B，P95=35,738/67,077 B；最大帧间隔为 55.89/447.22 ms。应跟踪首个分配调用栈和对应 Editor 活动，不能直接归因于 VSM。

## 第一批：补齐计量并复采

这是**下一步的首个实现批次**，范围为 recorder 和 profiling scope。

1. 将四个必执行阶段接入可验证的统一 marker/category，补齐 Allocate 和 VSM 总工作计时。PageCull 嵌套于 CasterCull，不能重复求和；阶段 median/P95 相加也不是总量分位数。
2. 导出 marker 可用性、单位、执行/样本数量；逐观测保存相机渲染和 VSM 有效性、回退原因、FrameTiming 原始状态。异常原因写入 JSON，不能只留 error。
3. 对暂停、相机未渲染、时间戳停滞、长间隔记录明确区段。保留所有长帧；确有交互/导入/暂停证据时，标记受影响窗口并重新预热采集。真实运行尖峰继续纳入统计，不能按“太慢”剔除。
4. 普通 D3D12 启动下，固定本相机/灯光/图、1080p/256 页重跑六档。记录 revision、工作区变更、实际驱动版本、图和调试状态。关闭 receiver debug replay，确保 Game view 持续渲染。
5. 每档至少 10 秒且 ≥300 个有效观测，至少 3 轮交替次序。建议门槛：无相机/VSM 失效或参数/输出变化；整帧 GPU 和必执行阶段有效覆盖率 ≥95%；同档三轮 median 相对极差 ≤5%。不达标则扩大窗口并解释波动。可选未执行阶段不强求覆盖率。超过 100 ms 的间隔需标记调查，不能仅凭累计时长完成就认证稳定窗口。

新数据另建运行，不覆盖本次。代码以 Roslyn/DXC 定向验证，稳定采集路径做预热分配检查；Editor 开启时不自动启动 Unity Test Framework。

## 第二批：Resolve/Feedback 的精确去重

目前最可靠的已测候选是约 **1.32 ms** 的 ResolveAndFeedback。2K PCF 相对 Hard 的 Resolve median 仅差约 -0.004 ms，远小于尾部波动；这不证明 PCF 免费，也不支持优先降低过滤质量。

[CSMShadowResolve.compute](../../../Shaders/Core/Private/CSMShadowResolve.compute) 的 ResolveVSMReceiver 在主阴影已采到后仍遍历 fallback 链；MarkVSMReceiverPage 对每个像素触及的页执行 OR 和 Max 原子操作。邻近像素会重复提交同页。**原子写入争用是待实验确认的成本假设。**

先用隔离诊断变体或 GPU capture 区分反馈写入与采样成本，保持输入和驻留相同；关闭反馈的变体只用于诊断。首个生产优化实验是 wave/group 内同页请求精确去重：只合并相同语义，保留 halo、完整 coarse fallback 链、优先级、frame stamp 和分支内有效 lane 语义。不通过提前结束请求链、反馈抽样或缩小 Transition 提速。

验收：请求页集合/coarse 标志/有效时间戳等价；静态、移动、页角、跨层、缺页和超预算场景无新增漏影或恢复延迟。收益须超过重复运行噪声；工程目标为本阶段 median 改善 ≥10%、P95 不恶化，整帧无可重复回退。10% 是目标，不是现有收益。

## 分配器：补测后决定是否提前

VSMPrototypeAllocatePages 使用 **numthreads(1,1,1)**。即使末帧 new=0，仍完整扫描页表做 metadata snapshot，再遍历两阶段请求；非驻留请求另搜索空闲/驱逐槽。

9 层、128-texel 页下，2K/4K/8K 页项数为 **2,304 / 9,216 / 36,864**。这个增长值得优先测量，但 Allocate 当前无数据，不能将约 3.14 ms 的 2K→4K 整帧 median 增量归因于它；4K 样本本身也无效。

**若补测表明 Allocate median 高于 Resolve，或解释了重复实验中最大的分辨率增量，分配器提前为第二批首项；否则先完成反馈去重。** 最小实验从并行 metadata snapshot/请求压缩开始，让有序分配只遍历请求列表，不直接重写全并行驱逐。保留稳定物理 slot、粗到细优先级、溢出统计、滚动孔洞、frame-zero 和缓存有效性，覆盖零新增和超预算回归。

## 第三批及质量约束

2K StaticCasterCull median 约 0.105 ms，嵌套 PageCull 约 0.081 ms；4K 的探索值约 0.192/0.167 ms。静态光栅约 0.0087 ms。补齐计时后，再决定是否按 dirty/requested page 缩减静态剔除，或在无动态 caster 时跳过无效清理/光栅；必须覆盖新页、上帧动态深度残留、失效和摄像机切换。当前末帧 overflow=0，不支持先扩大物理页池。

本轮 Screen Density 全关，且仅为静态性能记录，**没有验证最初的过渡断层，也没有验收 P5-B**。每批优化使用固定墙面 ROI、慢速斜移、跨页/跨层、FOV 变化、camera cut、动态 caster 和超预算场景；对比 preferred/sample level、fallback、transition weight、availability、请求集合及最终阴影。

质量诊断与性能运行分开，预算、光源 bias、Transition 和相机保持一致。完成 legacy 对照后，再增加 Screen Density on、target=1、LOD bias=0 的独立矩阵。新完整基线和质量对照通过前，默认质量档位保持现状。