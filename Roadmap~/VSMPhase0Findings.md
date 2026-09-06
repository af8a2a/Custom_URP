# VSM Phase 0：计时来源与质量复现

更新：2026-09-06。已完成受控重绘实验和当前基线 Game 相机的慢速斜移复现；尚未修改 allocator 或 receiver 算法。

## 计时来源

[原始实验与报告](Experiments/TimingSource/20260906_000333_82e94fab/report.md)包含固定 4K Hard、三种窗口重绘方式、三轮轮换顺序，共 9 个测量窗口。每组预热 5 秒，测量至少 10 秒和 300 条观测。实际使用 E:/VividRP_Reborn、1920×1080 Game 输出，D3D12 debug 启动标记为 false。

| 窗口自动重绘 | 三轮 GPU <1 ms 数量 | 三轮实际重绘数 | 低值间隔中位数 |
| --- | --- | --- | --- |
| 4 Hz | 41 / 40 / 41 | 41 / 41 / 41 | 0.252 / 0.254 / 0.255 s |
| 1 Hz | 84 / 11 / 37 | 32 / 11 / 11 | 两轮存在连续低值；第二轮 1.003 s |
| Manual | 0 / 0 / 0 | 0 / 0 / 0 | 无低值 |

**结论：记录窗口重绘是这一组周期性低 GPU 读数的明确影响因素。** 停止主动重绘后三轮均消失，4 Hz 的数量与周期跟随重绘。1 Hz 第一轮实际重绘超过计划值，第三轮出现成串低值，因此不宣称每条低值均已映射到特定编辑器窗口/Present，也不把观测帧 ID 当成 GPU 帧归属。

全部原始值保留，1 ms 仅用于诊断计数。schema 3 追加目标相机观测帧/序号、窗口重绘累计次数、距上次重绘时间；整帧来源继续标为 `editor_frames_unattributed`。报告分别展示采样完成、计时覆盖率、来源、末帧驻留/溢出和质量状态，覆盖率通过不再自动获得 comparable=true。

Manual 三轮全帧 GPU median 为 8.056 / 7.933 / 7.954 ms，相对极差约 1.55%。九组 Allocate median 为 3.2348–3.2374 ms，Resolve 为 1.9492–2.0219 ms。第一组包含 >100 ms 长帧，因此 coverage check 未通过；其余八组通过。这里的 coverage check 也包含相机/参数稳定性和长帧检查。

与 20260905_113329 的相机数值参数一致（名称 Camera_1 改为 Perf-Camera），光源按场景路径/名称归一后相同；SponzaLightingDay 当前为 dirty。Resolve 相比旧基线明显不同，不能将两次运行的全帧差值归因于代码优化。阶段数据支持继续优先调查 Allocate，但精确 Game 全帧收益仍需隔离 Player 或 GPU 捕获验证。

Unity 的 FrameTiming API 给出延迟的帧时间戳，而非目标 Camera 标识，见[官方数据说明](https://docs.unity3d.com/cn/6000.0/Manual/frame-timing-manager-get-timing-data.html)。新默认基线使用 Manual 重绘；原窗口已序列化的配置需点击 **Load baseline preset (manual repaint)**。采样仍持续执行，输入、暂停和保存仍有效。

## Game 相机质量起点

采用用户选择的当前基线 Game 相机：位置 (0.02020285, 7.66298294, -2.43060470)，固定朝向，世界坐标偏移 (2, 0, 2)。使用 4K PCF、First Level=1、Transition=0.2、Screen Density off、denoise off；完整场景、相机、光源与设置见各次 run.json。

- [首轮](Experiments/Quality/20260906_001414/run.json)：60 帧预热，601 个轨迹姿态，每 20 步一组，共 31 组；轨迹实际 25.758 秒。
- [复跑](Experiments/Quality/20260906_002011_43c20948/run.json)：同样 601 帧 / 31 组，实际 26.479 秒。两次所有相机姿态、VSM 活跃状态和参数检查均通过，无丢采。
- 每组包含 1920×1080 阴影 PNG、三张诊断 PNG、中心 256×256 的三份 RGBA32F 原始数据，以及同批 GPU 指令读回的四项页面计数。
- [复跑一致性](Experiments/Quality/20260906_002011_43c20948/repeatability.json)：93/93 份 ROI 原始文件逐字节一致；30/31 张阴影 PNG 一致。第 540 步只有 1 像素相差 2/255。
- [中断验证](Experiments/Quality/20260906_002157_91c28ccb/run.json)：5 秒定时停止，保留 66 帧姿态和 4 组快照，状态 interrupted，未误报完整采集。

采集使用现有 VSMReceiverDebug kernel；在当前相机 Resolve 完成后，用独立 shader 实例和可复用输出执行诊断，同一 command buffer 排队异步读回，再在 Editor update 编码/保存。无订阅时生产 Resolve 不解析诊断纹理、不分配、不发出诊断 dispatch。Player 构建不包含入口。

该运行冻结 scaled time，按 30 logical fps 推进姿态；PNG/I/O 延长了实际时长。未冻结所有 unscaled 脚本或外部状态，不能宣称普遍的确定性场景重放。开始、结束/中断、退出 Play Mode 和程序集重载时清理临时 Volume、GPU/CPU 输出，恢复相机、timeScale、captureDeltaTime、帧率、VSync、后台运行设置。正常结束与主动中断恢复已现场核验。

## 质量数据说明下一步查什么

[逐采样点统计](Experiments/Quality/20260906_001414/quality-audit.json)覆盖 31 个中心 ROI，每个 65,536 像素，原始数据完整且有限值。

1. 所有采样点都触发过渡混合，应用混合的像素数为 1,330–32,282。该轨迹能覆盖实际跨层行为。
2. 第 460 步有 **6 个像素缺页并回退**，同帧计数为 resident/requested/new/overflow = 256/158/4/0；复跑完全复现。其余 30 个采样点 ROI 无缺页/回退，所有采样点 overflow=0。这是局部瞬态，不能推导整个轨迹每一帧都无缺页。
3. 纹素屏幕足迹的 ROI median 范围 1.86–26.18 px，P95 范围 5.53–73.41 px；末段相机接近几何，足迹显著增大。足迹是接收面局部微分，轮廓、薄几何、近处掠射面需要结合画面解释，不能仅用高 P95 判定选层错误。
4. 每个 ROI 的 debug 重算阴影与实际 Resolve 阴影差值 >0.01 的像素均为 0，支持本次诊断绑定与采样对齐；不是相邻帧闪烁指标，也不是最终色彩输出的质量认证。

**后续对照已完成：**[四组密度与恢复实测](VSMDensityFindings.md)保留相同 601 个相机姿态，每组 69 份快照，覆盖 440–480 的连续 41 帧。off 在第 460/461 步分别有 6/24 个未映射回退像素，462 步恢复；采样点均无预算溢出。on 的 1/2/4 px 分别有 69/69、69/69、65/69 个采样点溢出，均未通过当前 256 页预算，不进入默认候选。

**下一步：**追踪 off 短暂缺失的 page ID 及请求→驻留帧序列；密度策略另做按层需求与预算分析。确认两层驻留且足迹合理后，才调整 bias/filter/transition 端点。性能路线保持 A1/A2/A3，小步验证；正式性能测量关闭质量采集并使用 Manual 重绘。

这条轨迹是当前 Game 相机的可重复诊断起点，不是原动图相机轨迹的重建，也没有完成原墙面六档质量矩阵或修复过渡伪影。

## 复跑与验证

在 VividRP Play Mode 打开 Game view：

- 计时：**Tools > VividRP > Diagnostics > Run Timing Source Experiment**。
- 质量：**Tools > VividRP > Diagnostics > Run Game Camera Quality Reproduction**；中断使用 **Stop Quality Reproduction**。
- 输出均在包的 Roadmap~/Experiments。两个模式互斥，不要在计时期间进行质量读回。
- 执行 `python Roadmap~/Experiments/analyze_timing_source.py <run目录>` 或 `python Roadmap~/Experiments/analyze_quality.py <run目录>` 可重新审核原始数据。

Runtime / Editor / Editor.Tests 的 Roslyn 编译通过。直接提取当前 collector/clock 实现的独立 .NET probe 通过 CSV、缺失数据、分段和重复保存检查，100,512 次预热后调用分配 0 字节。Unity Console 无错误。Unity Editor 保持打开，因此未启动 Unity Test Framework；请手动运行 VSMBaselineRecorderTests（新增重绘对照、观测元数据和轨迹/分配检查）。这不替代所有渲染线程的 Unity Profiler 分配验证。
