# 静止接收面的 TSR 光照响应

2026-09-06，VividRP_Reborn / Sponza。最终保留 C7，完整捕获编号 `120315`；基线代码为 `f4210389`。

静止接收面现在可以确认持续的光照变化，并暂时缩短历史累计。三帧同方向差异确认后，将样本数限制为 4、最终历史权重限制为 0.75，同时过期旧的 resurrection 缓存。它改善了屋檐的响应，仍有少量静止边缘波动，不能视为即时响应或彻底消除拖尾。

## 实测结果

相机、接收面保持静止，灯光在 step 16 绕局部 X 转动 2°，step 96 恢复。下表为从光照改变到旧状态残留指标连续三个 Active 帧低于 10% 的起始延迟。

| 区域 / 滤波 | 基线 | 最终版本 |
|---|---:|---:|
| 屋檐 / tent | 17 帧 | 14 帧 |
| 屋檐 / 随机 9 次比较 | 17 帧 | 11 帧 |
| 横檐 / tent | 8 帧 | 8 帧 |
| 横檐 / 随机 9 次比较 | 8 帧 | 7 帧 |

反向恢复的四组结果均为 1 帧，与基线相同。灯光改变的 step 16 / 96 各有一帧既有 VSM 回退；下一帧恢复 Active。原始颜色通常已恢复，TSR 颜色还在追赶。因此，上表包含这一回退对历史的影响，并非无回退的纯光照阶跃。

[正向响应对照](E:/VividRP_Reborn/Packages/VividRP/Roadmap~/Experiments/TSRLightingResponse_20260906_102401/tent_forward_before_after_6x.gif) · [完整静止 48 帧对照](E:/VividRP_Reborn/Packages/VividRP/Roadmap~/Experiments/TSRLightingResponse_20260906_102401/tent_static_before_after_6x.gif)

静止画面的代价如下。单位是相同固定曝光下、预曝光线性 HDR 亮度的总时间 RMS；固定掩码和输入颜色尺度一致。

| 区域 / 滤波 | 基线 RMS | 最终 RMS | 变化 |
|---|---:|---:|---:|
| 屋檐 / tent | 0.029319 | 0.030007 | +2.35% |
| 屋檐 / 随机 9 次比较 | 0.030865 | 0.032011 | +3.71% |
| 横檐 / tent | 0.094692 | 0.094816 | +0.13% |
| 横檐 / 随机 9 次比较 | 0.094972 | 0.095134 | +0.17% |

总方差同时包含抖动相位之间的变化和同相位残余。屋檐的同相位 RMS 为 tent `0.000765 → 0.002571`、随机 `0.009428 → 0.011171`，所以不能只看总量百分比而称其零退化。静止阶段没有新增硬拒绝，但软响应仍会在少量静止边缘触发。最严新增点的统一显示映射 RMS 为屋檐 `(849,239)` 的 `0.475 → 3.24` 显示码、横檐 `(829,503)` 的 `0.212 → 4.26` 显示码。

[屋檐最严新增点，同一相位](E:/VividRP_Reborn/Packages/VividRP/Roadmap~/Experiments/TSRLightingResponse_20260906_102401/tent_static_roof_same_phase_detail.png) · [横檐最严新增点，同一相位](E:/VividRP_Reborn/Packages/VividRP/Roadmap~/Experiments/TSRLightingResponse_20260906_102401/tent_static_ledge_same_phase_detail.png)

相机执行 64 步水平往返、最大偏移 0.18 世界单位，再静止 32 帧。回停末 16 帧的总 RMS，屋檐增加 2.46% / 3.32%，横檐增加 0.11% / 0.03%（tent / 随机）。它包含回停恢复，不能把移动帧图像差异直接叫作拖影或噪声。

## 实现

- `TSRRejectShading` 保留移动表面的原有颜色拒绝。静止且有有效主历史时，使用裁剪后历史的亮度 / 色度差，累计三个连续、同方向的候选；延续门槛为启动门槛的一半。确认只输出软响应标记，保持主历史 RGB 和接受掩码。
- 几何保护使用现有 `DepthError`：中心以及偏移 `{-3,-1,1,3}²` 的 16 个候选采样，保护附近的重建区域。深度误差本身覆盖源图 3×3。门槛为当前设备深度尺度的 2%；它是保守启发式，不是严格的世界空间距离或完整时域影响界。
- resurrection 颜色纹理原本未使用的 alpha 储存 `direction*4+count`。颜色仍按 jitter 重投影；离散计数在 `uv-motion` 的稳定输出网格上 point 采样，避免逐帧量化 jitter 位移造成累计漂移。无主历史 / 越界会清状态；resurrection 颜色缓存失效时，pending 状态仍可独立存在。
- 接受颜色 alpha 的 `-1` 表示移动颜色硬拒绝，`-2` 表示静止软响应，非负数表示 pending 状态。Update 对 `-2` 明确限制最终权重到 0.75，并把累计数降到至多 4。两种负值都禁止当帧 resurrection，并过期其颜色和年龄；无效主历史仍可恢复兼容的旧历史。
- 复用现有纹理和 Pass；C# 增加一个 Reject 输入绑定和仅 Editor 可订阅的历史采集事件。没有加入新的画质开关。

## 为什么保留这一版

直接取消静止面的运动门槛，或者在三帧确认后丢弃全部历史，虽然更快，但真实静止画面出现了明显的 16 / 24 帧周期闪烁。空间保护修复了几个几何边缘反例，却不能区分平坦墙面上的静止阴影锯齿。稳定网格计数修复了状态漂移，也没有单独消除误确认。最终使用保留部分历史的响应，控制误确认的影响。

本轮没有采用持续软响应或额外空间均值判据。固定捕获历史上的反事实估计显示：持续响应会让静止候选活跃率增加约 3.6 / 2.6 倍，并存在长时间同向差异；简单均值也仍然跟随某些阴影锯齿。这些只做了离线诊断，未加入生产代码，也不代表其闭环效果已测定。详见 [未采用方案的诊断](E:/VividRP_Reborn/Packages/VividRP/Roadmap~/Experiments/TSRLightingResponse_20260906_102401/deferred-detector-diagnostics-summary.json)。

## 测量方法与范围

- 1920×1080，NativeAA TSR，8 个 jitter 相位，history samples=16，sharpness=0.483。临时固定 VSM 2048、屏幕密度 target=1、LOD bias=0、PCF 开启，分别测试 tent 和随机 9 次比较。
- 每种滤波采集静止 48、相机 96、光照 176 帧，共 640 帧。每阶段至少预热 128 个独立相机帧；调用相机的后处理历史重置不能单独证明 TSR 硬重置，比较依赖预热和固定相位起点。
- 手动固定曝光 EV100=12.252064、补偿 0；640 帧 GPU 预曝光标量恒为 `0.00020500351`。静止基线使用 `103211` 的固定曝光捕获；动态基线使用 `100901`。动态随机组源颜色尺度比旧基线低约 0.15% / 0.17%，报告保留该限制。
- 原生 crop 为 `(700,170,420,410)`。屋檐和横檐使用仅由基线建立的共同掩码；光照掩码来自两种基线 raw 阴影变化大于 0.2 的交集。结果不是更高分辨率可见性真值。
- 残留指标是当前颜色相对同相位稳定后颜色的误差，在变化前后颜色差上的投影比例。判据使用绝对值连续三个 Active 帧低于 10%；不保证每个像素或此后所有帧都稳定。
- 两路采集逐帧配对，相位、GPU VP、相机 / 光源姿态和 bias 均匹配。ROI 缺页为 0；最大诊断重放误差为 `0.00053406`。随机静止组 seed 与其固定基线不同，动态 seed 匹配。
- 可视化使用统一 `c/(1+c)` 后转 sRGB，共享 256 色、不抖色；每步 100ms，相对名义 60Hz 为 6 倍慢放，不是实测帧率。细节图只做 nearest 3 倍放大，无额外对比度增益。
- 仅验证本次 Sponza 镜头、轨迹和灯光阶跃。非 Native 比例只做了 GPU 状态合同检查，尚无场景画质验证。采集包含 readback / 压缩开销，本轮不提供 GPU 性能或 Profiler GC 结论。

完整指标与审计见 [统计摘要](E:/VividRP_Reborn/Packages/VividRP/Roadmap~/Experiments/TSRLightingResponse_20260906_102401/lighting-response-summary.json) 和 [视觉审计](E:/VividRP_Reborn/Packages/VividRP/Roadmap~/Experiments/TSRLightingResponse_20260906_102401/visual-review-summary.json)。

## 验证与复现

- 最终生产 Reject / Update 的独立 GPU 诊断 **244 / 244** 通过：亮度 / 色度、递归历史、几何邻域、软响应数值、样本数恢复、移动拒绝和 resurrection 过期。原生 8×8 的实际 GPU 输出回填下一步输入；场景的完整图像递归另由 640 帧捕获验证。
- Reproject 的独立 GPU 诊断 **38 / 38** 通过：非零 jitter 下计数稳定、RGB 重建、八相位状态反馈、运动 / 越界，以及 render=8 / output=13 的状态合同。
- 三个修改的 compute shader 在 wave / scalar、16-bit 开关下共 **12 个 DXC 变体**通过。最终 Runtime、Editor、Editor.Tests 三个程序集通过独立 Roslyn 编译，Unity 导入编译成功。
- Editor 保持交互会话，**未运行 Unity Test Framework**。需手动运行 `TSRLightingResponseTests`、`TSRUpscalerPassTests`；GPU 诊断结果不冒充 NUnit 执行结果。
- 临时诊断脚本与其 Unity 生成的 meta 已清理；相机、光源、AA 参数、timeScale=1、captureDelta=0、runInBackground=false、非 Play 状态已核对恢复，临时诊断对象为 0。原有 Volume 配置恢复，随机滤波默认设置保持原值。

本目录的 `.cs.txt` 是诊断源码副本，不会被 Unity 导入。`compile-shaders.ps1` 和 `validate-csharp.ps1` 可重复执行独立编译检查；结果及最终源文件 SHA256 已保存。重测基线时，仅还原基线 TSR shader，保留采集绑定 / Editor 事件；两侧均使用相同临时固定设置、预热和相位起点。

最终逐帧 gzip、完整 JSON、反向动图与 shader 冻结副本位于 `E:/VividRP_Reborn/Packages/VividRP/Temp~/tsr-lighting-response/120315`，该目录被忽略。原始动态基线在 `C:/Users/11252/AppData/Local/Temp/tsr-lighting-response/100901`，固定曝光静止基线在 `C:/Users/11252/AppData/Local/Temp/tsr-lighting-static/103211`。中途被脚本重载打断的 `120153` 已排除；未完成的 C6 只用于其完整静止阶段的反例分析。
