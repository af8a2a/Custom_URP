# 固定 2048：9 次随机比较与动态 TSR 对照

2026-09-06，VividRP_Reborn / Sponza，捕获编号 091947。

本轮结果不支持用随机核替换默认 tent。已加入默认关闭的 `virtualShadowMapStochasticFiltering` 开关，需同时开启 VSM PCF。保留当前 2048、屏幕密度选层及 bias 修复；TSR 算法未修改，仅增加 Editor 可选采集事件。

随机分支每个有效投影执行 9 次直接深度比较：单位圆盘分成 3 个等面积径向带 × 3 个角向扇区，用像素和帧号产生分层 hash 随机样本。这不是 STBN。每次比较仍按实际整数纹素中心修正接收平面深度，并在采样前保守检查完整 ±1 纹素支持页。跨层混合可采两个投影，不能把 9 次比较理解成每个屏幕像素的总成本；额外页检查和随机数运算也有成本，本轮不提供性能结论。

**静止结果**

| 指标 | 屋檐 tent → 随机 | 横檐 tent → 随机 |
|---|---:|---:|
| 48 帧 raw 平均相对同圆盘 1024 比较参考的 MAE | 0.001934 → 0.001482 | 0.001978 → 0.001457 |
| 同 jitter 相位的 TSR 输出残余噪声 RMS | 0.000702 → 0.008822 | 0.001092 → 0.006827 |

MAE 使用全部有效 ROI；噪声使用两组相同的阴影边缘掩码，单位为线性 HDR 亮度。每个 jitter 相位有 6 帧；分别去除 8 个相位的均值后统计，因此不把确定性的相机抖动周期当成随机噪声。剩余量也包含历史演化，不是单一画质评分。

随机组 TSR 输出噪声 RMS 降为输入颜色噪声的约 25% / 28%，但仍明显高于 tent。1024 比较参考只验证同一个圆盘核的估计误差，不是更高分辨率的可见性真值；tent 本来就是不同的核，不能用该 MAE 宣称随机方案恢复了缺失的遮挡细节。

[屋檐静态对照](static_roof.png) · [横檐静态对照](static_ledge.png)

**动态结果**

光源在 step 16 绕局部 X 转动 2°，相机和接收面保持静止。两组都在这一帧出现 `ReceiverFeedbackUnavailable` 回退，step 17 恢复 Active。参考页面均未溢出。

| TSR 旧阴影残留指标 | 屋檐 tent / 随机 | 横檐 tent / 随机 |
|---|---:|---:|
| 首个恢复 Active 的帧（step 17） | 52.5% / 56.5% | 38.3% / 40.6% |
| 连续 3 帧低于 10% 的起始 step | 33 / 33 | 24 / 24 |
| 从光照改变算起的帧数 | 17 / 17 | 8 / 8 |

step 17 原始阴影已经切到新位置，但测量区域 motion=0、历史接受率=100%。残留指标是当前颜色相对已稳定结果的误差，在变化前后颜色差上的投影比例，并非直接读取的 shader 混合权重。恢复阈值取该指标绝对值连续 3 个 Active 帧低于 10%，不表示之后永久无残留或全部像素已稳定。变化前、稳定后的参考均按相同 jitter 相位建立；两组使用共同的 raw 阴影变化区域。

这说明新阴影就位之后，最终颜色仍有时域延迟。首帧回退会影响历史，本轮没有单独量化“完全无回退的光照阶跃”；不能把整个响应都归因于随机滤波，也不能据此直接取消所有历史保护。

相机对照执行 64 步水平往返（最大 0.18 世界单位），再保持 32 帧；两种滤波的轨迹、相位逐帧一致，整个移动段 VSM Active、无采样缺页。移动画面的 A/B 差异不是拖影真值。停止后末 16 帧的同相位输出残差 RMS，屋檐为 tent 0.000995 / 随机 0.006843，横檐为 0.003104 / 0.006118，仍包含恢复和噪声；原始阴影恢复与颜色恢复不能混为一谈。更完整的移动段与停止恢复统计见 `camera-evidence.json`。

[光源变化对照动图](light_step_compact_6x.gif) · [相机移动对照动图](camera_compact_6x.gif)

动图按离散步号慢放，相对于名义 60 Hz 为 6 倍，不代表实测帧率。raw 阴影固定 0–1 灰度；TSR 前后 HDR 预览使用相同固定映射。静态图最后一行来自真实最终截图，保留实际显示颜色。

**下一步**

优先单独验证静止接收面上的光照变化响应。目前 `TSRRejectShading.compute` 的颜色与深度拒绝都要求 motion > 1 pixel。应区分持续的光照变化与逐帧随机采样噪声，再调整历史拒绝或权重；通过移动阴影测试后再评估 STBN 等序列。继续扩大核或提高 TSR 历史权重，都无法恢复 2048 深度栅格中未保存的几何信息。

**验证与复现**

- 六组共 480 个独立、连续的 camera frame。每组至少预热 128 帧，模式开始时重置一次历史，光源变化时不重置。
- 1920×1080，NativeAA TSR，history samples=16，sharpness=0.483；固定 virtual resolution=2048、density target=1、LOD bias=0、PCF 开启，其余既有阴影参数保持一致。
- A/B 每步的 GPU VP、jitter、相机、光源和 bias 完全相同，CSM/TSR 均同 camera frame 配对。每帧 seed 等于 cameraFrame，随机组不会因重放诊断使用不同 seed。
- 478 个有效 VSM 帧的诊断重放最大误差 0.00048822，与 R16 输出量化相符；ROI 采样缺页为零。两次光源变化各有一个明确记录的回退帧。全程页溢出为零。
- 35 个生产/采样测试入口及 1 个临时参考入口通过 DXC。隔离 D3D12 GPU 诊断通过分层、浮点边界、缺页回退和斜面/近遮挡物检查；64 帧均值 MSE 从单帧的 0.018277 降至 0.0004356。
- C# 测试程序集通过独立 Roslyn 编译。Editor 保持交互会话，未运行 Unity Test Framework；需手动运行 `VirtualShadowMapSamplingTests`、`CascadedShadowSettingsVolumeTests`、`VSMBaselineRecorderTests`。
- 相机姿态、原 AA 参数、光源局部旋转、timeScale=1、captureDelta=0、runInBackground=false、非 Play 状态已恢复；临时 Volume、诊断脚本、参考 Shader 与对应自动生成的 meta 已清理。

原始逐帧 gzip 和截图仍在 `C:/Users/11252/AppData/Local/Temp/vsm-stochastic-probe/091947`。本目录保存精简证据、统计、可视化与诊断源码副本；`.cs.txt` / `.compute.txt` 不会被 Unity 导入。完整方法在 `stochastic-evidence.json`、`independent-pairing.json` 及可视化 method 文件中，编译和 GPU 结果另有独立 JSON。
