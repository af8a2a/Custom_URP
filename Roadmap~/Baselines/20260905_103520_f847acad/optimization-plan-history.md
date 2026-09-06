# 历史计划存档

2026-09-06 重写最新优化方案前的文档快照。下文包含当时追加的新基线说明；最新执行顺序以 Roadmap~/VSMOptimizationPlan.md 为准。

# VSM 优化计划：当前 Play Mode 基线

2026-09-05 最新复核：**20260905_113329_d0e8beb7 已完成六档采集，作为新的单轮诊断起点**。
7,815 条观测、108 行指标与原始 CSV/JSON/Markdown 独立重算一致，必需 GPU scope 全部采齐。
在采集项目编辑器内确认启动参数无 D3D12 debug；全局 Editor.log 的另一个项目头部不能用于归因。
但整帧 GPU 极低值约每 0.25 秒出现，8K 占约 7.8%，来源待隔离验证；8K 末帧为
256 驻留 / 491 请求 / 235 溢出，不能将报告的 comparable=6 视为全部性能/质量验收通过。
详见 [最新基线复核与适用范围](Baselines/20260905_113329_d0e8beb7/README.md)。

最新优先级：先确认整帧 GPU 计时来源；**Allocate 提前为首个算法优化候选**，
4K 约 3.23 ms、8K 约 16.1–16.2 ms，已高于同档 Resolve 的约 1.0–1.1 ms。
先用 4K 无末帧溢出场景验证改动，再验证 8K 压力场景；补足交替顺序的重复轮次和质量验证后再验收收益。

以下保留 **20260905_103520_f847acad 的历史评审与原计划**；其中“本轮/当前”均指该轮。
其缺失档位和 scope 状态已被上面的新数据更新，不再作为最新采集状态。

## 当前归档与适用范围

10 个原始 CSV/JSON，共 **908,913 字节、5,320 条观测**，SHA-256 逐文件校验一致。全部 72 行指标的有效数量、median、nearest-rank P95、min/max 独立重算与导出一致；原始长帧、零值和缺失单元格均保留。

- [当前归档和复核方式](Baselines/20260905_103520_f847acad/README.md)
- [原始汇总](Baselines/20260905_103520_f847acad/raw/summary.csv)
- [运行与场景快照](Baselines/20260905_103520_f847acad/raw/run.json)
- [清单及 debug 参数证据](Baselines/20260905_103520_f847acad/manifest.json)
- [独立样本审计](Baselines/20260905_103520_f847acad/sample-audit.json)
- [跨轮对照](Baselines/20260905_103520_f847acad/comparison.json)
- [匹配本轮的启动和中断日志](Baselines/20260905_103520_f847acad/editor-log-excerpt.txt)
- [首轮历史评审](Baselines/20260905_084033_7e30074a/review.md)

运行时间为 10:35:20–10:36:31 UTC（北京时间 18:35:20–18:36:31）。最终 status=error，completedCases=3。完成状态不代表每项计量都可用。

| 档位 | 观测数 / 有效整帧 GPU 数 | 整帧 GPU median / P95（ms） | Resolve+Feedback median / P95（ms） | 当前用途 |
| --- | --- | --- | --- | --- |
| 2K Hard | 1170 / 0 | 缺失 | 1.127 / 1.410 | 长帧及全帧计时缺失，仅诊断记录 |
| 2K PCF | 2040 / 2037 | 4.764 / 5.100 | 1.131 / 1.523 | 完整单轮整帧/阶段参考 |
| 4K Hard | 1323 / 1323 | 7.504 / 7.946 | 1.761 / 2.163 | 完整单轮整帧/阶段参考 |
| 4K PCF | 787 / 786 | 7.683 / 8.140 | 1.774 / 2.131 | 6.09 秒中断样本，未满足时长 |
| 8K Hard / PCF | 未采集 | — | — | 待补采 |

整帧时间包括 Editor 工作，不是 VSM 总时间；阶段采集仍不完整，各列结果与观测帧不同步。两档“完整单轮参考”只表示已有计时窗口可供探索，不意味着达到三轮重复性或 P5 质量验收。

## 启动参数、场景与版本

- 使用的日志为用户 LocalAppData 下 Unity/Editor/Editor.log，启动于 **10:33:04 UTC**，其中明确记录了保存到本轮目录的消息；检查其完整启动参数段，未包含 -force-d3d12-debug，与用户说明一致。没有独立查询运行时 debug-layer 状态。
- 项目 Logs/Editor.log 是 **10:32:12 UTC 的前一次启动**，仍含 debug 参数；其写入早于本轮，不能用它判断重测状态。归档只保存相关日志字段，省略无关启动参数。
- Unity 6000.7.0a6 / Direct3D12 / RTX 5070 Ti；1920×1080，VSync=0，targetFrameRate=-1，单个 Game camera。实际厂商驱动版本仍未单独记录。
- 当前活动场景 Assets/ClassicSponza/Scenes/Sponza.unity，叠加 SponzaLightingDay.unity。本轮二者均不 dirty；上一轮 LightingDay 为 dirty。
- 相机 Camera_1：位置 (0.02020285, 7.66298294, -2.43060470)，欧拉角 (359.22635, 3.03022, 0.45028)，FOV=60，near/far=0.01/1000。
- 主光以名称与 sun 标志识别，不能取灯数组第一项；新一轮灯的枚举顺序已改变。Directional Light 位置 (1.10413980, 15.50647163, -8.50347042)，朝光源方向 (0.04350399, 0.86132014, -0.50619674)，bias=1/1/2.5。
- 跨轮相机快照、按场景路径/名称排序的五盏灯快照及六档参数完全一致。所有新档位开始/结束快照也一致，未报告相机运动、尺寸变化或参数不匹配；这不覆盖所有场景内容或中间运动。
- FirstLevel=1、MaxDistance=150、Transition=0.2、ScreenDensity=false、Denoise=false，9 层、256 页。末帧 2K 为 79/79/0/0，4K Hard 为 187/187/0/0；4K PCF 末帧计数不可用，原数组的四个零不能当实测。
- 原 revision 仍为空。两轮评审时相关源码哈希一致，但 review HEAD/哈希不能追认为采集时版本。此相机仍不同于 [旧墙面质量捕获](VSMQualityBaseline.md)，不将新整帧时间填入旧表的 VSM 总时间栏。

## 相比上一轮

同档 2K PCF 整帧 GPU median **5.863936 → 4.764160 ms（-18.75%）**，Resolve/Feedback **1.315072 → 1.131008 ms（-14.00%）**。这是两次独立运行的观察差异，不能把它全部归因于 debug 层开销，也不是算法优化收益。

4K Hard 本次 1324 次相机回调全部有有效 VSM snapshot、完整采集 10.0042 秒，最大帧间隔 10.513 ms；上一轮有失效和 9.84 秒停顿。因此新数据替代旧 4K Hard 作为当前参考，不从旧无效窗口计算“优化百分比”。

## 本轮剩余问题

1. **2K Hard 不满足稳定全帧参考。** 1170 条 CPU/GPU/渲染线程 FrameTiming 全为空；即使 frameTimingEnabled=true，也不代表已产生有效样本。16 条间隔超过 50 ms，6 条超过 100 ms，最大 311.283 ms。Resolve 有一条零值，仍原样保留；这些现象需要计时就绪和启动活动诊断。
2. **4K PCF 再次触发相机超时。** 匹配本轮的日志仍是 “The selected camera has not rendered for 15 seconds”。本次记录的 6.0916 秒内，FrameTiming 几乎完整（GPU 786/787），并没有上一轮末尾 517 条时间戳缺失；不能沿用旧缺失原因解释本轮。相机为何停止渲染仍待定位。
3. **本轮基线四个必执行 GPU scope 缺失。** Allocate、ClearPhysicalPages、FinalizePages、DynamicRaster 全部无样本。该轮采样时 CSMShadowPass 使用字符串 BeginSample/EndSample，已返回数据的主要阶段使用 ProfilingSampler；recorder 按 Render category 查找。绑定差异为待验证原因，不能把空列算成零。InvalidateStatic、UnityCompatibilityRaster、ResetFeedback 另需区分未执行与不可用。
4. **GC 峰值和数据范围。** 各档 Editor-frame GC median 均为 14,475 B；2K Hard 最大达 1,181,695,780 B（约 1.10 GiB），这是 recorder 的原始观测，尚未验证归因，不代表 VSM 单帧分配量。2K PCF 仍有 14 条整帧 GPU 正值低于 1 ms，不按阈值剔除。
5. **六档及重复性尚未完成。** 优先重采 2K Hard、4K PCF、8K Hard/PCF；已有 2K PCF/4K Hard 需要重复轮次。先解决数据来源、必执行 scope 和相机持续渲染问题，避免重复收集同类无效窗口。

## 第一批：补齐计量与未完成档位

首个实现批次范围为 recorder 和 profiling scope。

实现进展：recorder 已拆分暂停保存与结束释放；支持等待相机/计时、分段恢复、
重采归档、跳过、错误保留、进度与 schema 2 报告。四个缺失 scope 已统一为缓存
ProfilingSampler。Runtime/Editor/Editor.Tests 定向编译及独立采样/导出逻辑检查通过。
采样/时钟预热 100,512 次调用分配为 0 B；窗口实际方法的 6 条分支通过独立保存故障注入检查，
覆盖暂停保留、末档跳过、保存失败提示与强制清理。该检查使用会话替身，不代替 Unity 集成验证。
交互 Editor 下未启动 Unity Test Framework；新标记的实际 GPU 覆盖率、Play Mode 交互生命周期
和新的六档采集仍需验证。原始基线数据不作回填或追认。


1. 将四个必执行阶段接入可验证的统一 marker/category，补齐 Allocate 和 VSM 总工作计时。PageCull 嵌套于 CasterCull，不能重复求和；阶段 median/P95 相加也不是总量分位数。
2. 导出 marker 可用性、单位、执行/样本数量；逐观测保存相机渲染和 VSM 有效性、回退原因、FrameTiming 原始状态。异常原因写入 JSON，不能只留 error。
3. 对暂停、相机未渲染、时间戳停滞、长间隔记录明确区段。保留所有长帧；确有交互/导入/暂停证据时，标记受影响窗口并重新预热采集。真实运行尖峰继续纳入统计，不能按“太慢”剔除。
4. 本轮已完成无 debug 启动参数的复采。继续固定相机/灯光/图、1080p/256 页，优先重采 2K Hard、4K PCF 和 8K 两档，并给 2K PCF、4K Hard 增加重复轮次。记录 revision、工作区变更、实际驱动版本、图和调试状态。关闭 receiver debug replay，确保 Game view 持续渲染。
5. 每档至少 10 秒且 ≥300 个有效观测，至少 3 轮交替次序。建议门槛：无相机/VSM 失效或参数/输出变化；整帧 GPU 和必执行阶段有效覆盖率 ≥95%；同档三轮 median 相对极差 ≤5%。不达标则扩大窗口并解释波动。可选未执行阶段不强求覆盖率。超过 100 ms 的间隔需标记调查，不能仅凭累计时长完成就认证稳定窗口。

新数据另建运行，不覆盖本次。代码以 Roslyn/DXC 定向验证，稳定采集路径做预热分配检查；Editor 开启时不自动启动 Unity Test Framework。

## 第二批：Resolve/Feedback 的精确去重

当前较可靠的 ResolveAndFeedback 单轮参考为 **2K PCF 1.131 ms、4K Hard 1.761 ms**。2K Hard 的全帧计时缺失且有长帧，4K PCF 未完成，因此还没有完整同分辨率 Hard/PCF 对照。2K PCF 与 4K Hard 同时改变分辨率与过滤，不能把差值直接视为分辨率成本。反馈仍是已测候选，不支持优先降低过滤质量。

[CSMShadowResolve.compute](../Shaders/Core/Private/CSMShadowResolve.compute) 的 ResolveVSMReceiver 在主阴影已采到后仍遍历 fallback 链；MarkVSMReceiverPage 对每个像素触及的页执行 OR 和 Max 原子操作。邻近像素会重复提交同页。**原子写入争用是待实验确认的成本假设。**

先用隔离诊断变体或 GPU capture 区分反馈写入与采样成本，保持输入和驻留相同；关闭反馈的变体只用于诊断。首个生产优化实验是 wave/group 内同页请求精确去重：只合并相同语义，保留 halo、完整 coarse fallback 链、优先级、frame stamp 和分支内有效 lane 语义。不通过提前结束请求链、反馈抽样或缩小 Transition 提速。

验收：请求页集合/coarse 标志/有效时间戳等价；静态、移动、页角、跨层、缺页和超预算场景无新增漏影或恢复延迟。收益须超过重复运行噪声；工程目标为本阶段 median 改善 ≥10%、P95 不恶化，整帧无可重复回退。10% 是目标，不是现有收益。

## 分配器：补测后决定是否提前

VSMPrototypeAllocatePages 使用 **numthreads(1,1,1)**。即使末帧 new=0，仍完整扫描页表做 metadata snapshot，再遍历两阶段请求；非驻留请求另搜索空闲/驱逐槽。

9 层、128-texel 页下，2K/4K/8K 页项数为 **2,304 / 9,216 / 36,864**。这个增长值得优先测量，但 Allocate 当前无数据，不能将 4K Hard 的整帧成本归因于它。新一轮 4K Hard 已完整完成，但 2K Hard 缺少整帧 GPU 数据；拿 2K PCF 与 4K Hard 相减会同时混入过滤变化。先补全同过滤档位对照和 Allocate 计时。

**若补测表明 Allocate median 高于 Resolve，或解释了重复实验中最大的分辨率增量，分配器提前为第二批首项；否则先完成反馈去重。** 最小实验从并行 metadata snapshot/请求压缩开始，让有序分配只遍历请求列表，不直接重写全并行驱逐。保留稳定物理 slot、粗到细优先级、溢出统计、滚动孔洞、frame-zero 和缓存有效性，覆盖零新增和超预算回归。

## 第三批及质量约束

新参考中 2K PCF StaticCasterCull/PageCull median 为 0.086/0.068 ms，4K Hard 为 0.156/0.136 ms；静态光栅约 0.0074 ms。PageCull 嵌套于 CasterCull，不重复相加。补齐计时后，再决定是否按 dirty/requested page 缩减静态剔除，或在无动态 caster 时跳过无效清理/光栅；必须覆盖新页、上帧动态深度残留、失效和摄像机切换。当前末帧 overflow=0，不支持先扩大物理页池。

本轮 Screen Density 全关，且仅为静态性能记录，**没有验证最初的过渡断层，也没有验收 P5-B**。每批优化使用固定墙面 ROI、慢速斜移、跨页/跨层、FOV 变化、camera cut、动态 caster 和超预算场景；对比 preferred/sample level、fallback、transition weight、availability、请求集合及最终阴影。

质量诊断与性能运行分开，预算、光源 bias、Transition 和相机保持一致。完成 legacy 对照后，再增加 Screen Density on、target=1、LOD bias=0 的独立矩阵。新完整基线和质量对照通过前，默认质量档位保持现状。
