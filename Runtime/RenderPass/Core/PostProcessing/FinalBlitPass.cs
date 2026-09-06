using System;
using Unity.Profiling;
using UnityEngine;
using UnityEngine.Experimental.Rendering;
using UnityEngine.Rendering;
using UnityEngine.Rendering.RenderGraphModule;

namespace VividRP.Runtime.RenderPass.Core
{
    public class FinalBlitPass : UnsafePass, IRenderGizmoPrePostProcessBoundaryPass, IPostProcessSourceOverridePass, IStablePassResourceLayout
    {
        private static readonly int ColorGradingLutId = Shader.PropertyToID("_VividColorGradingLut");
        private static readonly int ColorGradingParamsId = Shader.PropertyToID("_VividColorGradingParams");
        private static readonly int AutoExposureBufferId = Shader.PropertyToID("_VividAutoExposureBuffer");
        private static readonly int AutoExposureMaterialParamsId = Shader.PropertyToID("_VividAutoExposureParams");
        private static readonly int HDROutputParamsId = Shader.PropertyToID("_HDROutputParams");
        private static readonly int HDROutputParams2Id = Shader.PropertyToID("_HDROutputParams2");
        private static readonly int FilmGrainTextureId = Shader.PropertyToID("_VividFilmGrainTexture");
        private static readonly int FilmGrainParamsId = Shader.PropertyToID("_VividFilmGrainParams");
        private static readonly int FilmGrainTexParamsId = Shader.PropertyToID("_VividFilmGrainTexParams");
        private static readonly int VignetteParams1Id = Shader.PropertyToID("_VividVignetteParams1");
        private static readonly int VignetteParams2Id = Shader.PropertyToID("_VividVignetteParams2");
        private static readonly int VignetteColorId = Shader.PropertyToID("_VividVignetteColor");
        private static readonly int VignetteMaskId = Shader.PropertyToID("_VividVignetteMask");
        private static readonly int VignetteScreenParamsId = Shader.PropertyToID("_VividVignetteScreenParams");
        private static readonly ProfilerMarker s_PrepareCameraMarker = new("VividRP.RenderPass.FinalBlit.Prepare.Camera");
        private static readonly ProfilerMarker s_PrepareSettingsMarker = new("VividRP.RenderPass.FinalBlit.Prepare.Settings");
        private static readonly ProfilerMarker s_PrepareColorGradingSettingsMarker = new("VividRP.RenderPass.FinalBlit.Prepare.Settings.ColorGrading");
        private static readonly ProfilerMarker s_PrepareFilmGrainSettingsMarker = new("VividRP.RenderPass.FinalBlit.Prepare.Settings.FilmGrain");
        private static readonly ProfilerMarker s_PrepareBloomSettingsMarker = new("VividRP.RenderPass.FinalBlit.Prepare.Settings.Bloom");
        private static readonly ProfilerMarker s_PrepareLensFlareSettingsMarker = new("VividRP.RenderPass.FinalBlit.Prepare.Settings.LensFlare");
        private static readonly ProfilerMarker s_PrepareVignetteSettingsMarker = new("VividRP.RenderPass.FinalBlit.Prepare.Settings.Vignette");
        private static readonly ProfilerMarker s_PrepareExposureMarker = new("VividRP.RenderPass.FinalBlit.Prepare.Exposure");

        [RenderGraphResource(Access = AccessFlags.Read)]
        private RenderGraphTexture source = new();

        [RenderGraphResource(Name = "ColorGradingTexture", Access = AccessFlags.Read)]
        private RenderGraphTexture colorGradingLut = new();

        [RenderGraphResource(Name = "BloomTexture", Access = AccessFlags.Read)]
        private RenderGraphTexture bloomTexture = new();

#if DLSS_PLUGIN_INTEGRATE
        [RenderGraphResource(
            Name = "DLSSNRDepth",
            Access = AccessFlags.Read,
            BindingMode = RenderGraphResourceBindingMode.PassOwnedOverrideable)]
        private RenderGraphTexture m_DlssNeuralRenderingDepth =
            RenderGraphTexture.CreateInput("DLSSNRDepth", GraphicsFormat.None, DepthBits.Depth32);

        [RenderGraphResource(
            Name = "DLSSNRMotionVectors",
            Access = AccessFlags.Read,
            BindingMode = RenderGraphResourceBindingMode.PassOwnedOverrideable)]
        private RenderGraphTexture m_DlssNeuralRenderingMotionVectors =
            RenderGraphTexture.CreateInput("DLSSNRMotionVectors", GraphicsFormat.R16G16_SFloat);

        [RenderGraphResource(Name = "FinalBlitOutput", Access = AccessFlags.ReadWrite)]
        [TransientResource]
        private RenderGraphTexture m_FinalBlitOutput =
            RenderGraphTexture.CreateColorTarget("FinalBlitOutput", GraphicsFormat.R16G16B16A16_SFloat);

        [RenderGraphResource(Name = "DLSSNROutput", Access = AccessFlags.ReadWrite)]
        [TransientResource]
        private RenderGraphTexture m_DlssNeuralRenderingOutput =
            RenderGraphTexture.CreateColorTarget("DLSSNROutput", GraphicsFormat.R16G16B16A16_SFloat);
#endif

        private Material m_Material;
        private ColorGradingSettingsData m_ColorGradingSettings;
        private FilmGrainSettingsData m_FilmGrainSettings;
        private BloomSettingsData m_BloomSettings;
        private ScreenSpaceLensFlareSettingsData m_ScreenSpaceLensFlareSettings;
        private VignetteSettingsData m_VignetteSettings;
        private VividExposureData m_ExposureData;
        private RenderTargetIdentifier m_CameraBackBufferTarget;
        private TextureUVOrigin m_CameraBackBufferTextureUVOrigin;
        private bool m_ShouldSetViewport;
        private bool m_PostProcessingAllowed;
        private bool m_HDROutputActive;
        private bool m_EnableExposure;
        private Rect m_Viewport;
        private int m_FrameCount;
        private bool m_IsPassResourceLayoutDirty;
        private RenderGraphTexture m_OriginalSource;
        private bool m_HasSourceTextureOverride;
#if DLSS_PLUGIN_INTEGRATE
        private readonly RenderGraphTexture m_DefaultDlssNeuralRenderingDepth;
        private readonly RenderGraphTexture m_DefaultDlssNeuralRenderingMotionVectors;
        private DLSSNeuralRenderingPass m_DlssNeuralRenderingPass;
        private VividCameraData m_CameraData;
        private Rect m_DlssNeuralRenderingInputViewport;
        private bool m_DlssNeuralRenderingActive;
        private bool m_DlssNeuralRenderingResetHistory;
#endif

        public FinalBlitPass()
        {
#if DLSS_PLUGIN_INTEGRATE
            m_DefaultDlssNeuralRenderingDepth = m_DlssNeuralRenderingDepth;
            m_DefaultDlssNeuralRenderingMotionVectors = m_DlssNeuralRenderingMotionVectors;
            ConfigureDlssNeuralRenderingTexture(
                m_FinalBlitOutput,
                "FinalBlitOutput",
                1,
                1,
                enableRandomWrite: false);
            ConfigureDlssNeuralRenderingTexture(
                m_DlssNeuralRenderingOutput,
                "DLSSNROutput",
                1,
                1,
                enableRandomWrite: true);
#endif
        }

        public bool IsPassResourceLayoutDirty => m_IsPassResourceLayoutDirty;

        public void ClearPassResourceLayoutDirty()
        {
            m_IsPassResourceLayoutDirty = false;
        }

        internal RenderGraphTexture GetSourceTexture()
        {
            return source;
        }

        internal void SetSourceTexture(RenderGraphTexture sourceTexture)
        {
            if (sourceTexture == null)
                throw new ArgumentNullException(nameof(sourceTexture));

            if (ReferenceEquals(source, sourceTexture))
                return;

            if (!m_HasSourceTextureOverride)
            {
                m_OriginalSource = source;
            }

            source = sourceTexture;
            m_HasSourceTextureOverride = true;
            m_IsPassResourceLayoutDirty = true;
        }

        internal void RestoreSourceTexture()
        {
            if (!m_HasSourceTextureOverride)
                return;

            if (!ReferenceEquals(source, m_OriginalSource) && m_OriginalSource != null)
            {
                source = m_OriginalSource;
                m_IsPassResourceLayoutDirty = true;
            }

            m_OriginalSource = null;
            m_HasSourceTextureOverride = false;
        }

        RenderGraphTexture IPostProcessSourceOverridePass.GetSourceTexture() => GetSourceTexture();

        void IPostProcessSourceOverridePass.SetSourceTexture(RenderGraphTexture sourceTexture) => SetSourceTexture(sourceTexture);

        void IPostProcessSourceOverridePass.RestoreSourceTexture() => RestoreSourceTexture();

        public override void Prepare(ContextContainer frameData)
        {
            Camera camera;

            using (s_PrepareCameraMarker.Auto())
            {
                var cameraData = frameData.Get<VividCameraData>();
#if DLSS_PLUGIN_INTEGRATE
                m_CameraData = cameraData;
#endif
                camera = cameraData?.camera;
                m_HDROutputActive = cameraData != null && cameraData.hdrOutputActive;
                var hasTargetTexture = camera != null && camera.targetTexture != null;
                var cameraType = camera != null ? camera.cameraType : CameraType.Game;

                m_CameraBackBufferTarget = hasTargetTexture
                    ? new RenderTargetIdentifier(camera.targetTexture)
                    : BuiltinRenderTextureType.CameraTarget;
                m_CameraBackBufferTextureUVOrigin = GetCameraBackBufferTextureUVOrigin(cameraType, hasTargetTexture);
                m_ShouldSetViewport = ShouldSetViewport(cameraType);

                m_Viewport = cameraData != null
                    ? GetViewport(cameraData)
                    : new Rect(0f, 0f, Screen.width, Screen.height);
                m_PostProcessingAllowed = camera != null && CoreUtils.ArePostProcessesEnabled(camera);
            }

            using (s_PrepareSettingsMarker.Auto())
            {
                using (s_PrepareColorGradingSettingsMarker.Auto())
                {
                    if (!m_PostProcessingAllowed && !m_HDROutputActive)
                    {
                        m_ColorGradingSettings = ColorGradingSettingsData.CreateDefault();
                    }
                    else if (!m_PostProcessingAllowed)
                    {
                        m_ColorGradingSettings = ColorGradingSettingsResolver.ResolveHDROutput(frameData);
                    }
                    else if (ColorGradingSettingsResolver.TryGetResolved(
                                 frameData,
                                 out var colorGradingSettings,
                                 out _))
                    {
                        m_ColorGradingSettings = colorGradingSettings;
                    }
                    else
                    {
                        m_ColorGradingSettings = ColorGradingSettingsResolver.Resolve(frameData, out _);
                    }
                }

                using (s_PrepareFilmGrainSettingsMarker.Auto())
                {
                    m_FilmGrainSettings = m_PostProcessingAllowed
                        ? FilmGrainSettingsResolver.Resolve()
                        : FilmGrainSettingsData.CreateDefault();
                }

                using (s_PrepareBloomSettingsMarker.Auto())
                {
                    m_BloomSettings = m_PostProcessingAllowed
                        ? BloomSettingsResolver.Resolve()
                        : BloomSettingsData.CreateDefault();
                }

                using (s_PrepareLensFlareSettingsMarker.Auto())
                {
                    m_ScreenSpaceLensFlareSettings = m_PostProcessingAllowed
                        ? ScreenSpaceLensFlareSettingsResolver.Resolve()
                        : ScreenSpaceLensFlareSettingsData.CreateDefault();
                }

                using (s_PrepareVignetteSettingsMarker.Auto())
                {
                    m_VignetteSettings = m_PostProcessingAllowed
                        ? VignetteSettingsResolver.Resolve()
                        : VignetteSettingsData.CreateDefault();
                }
            }

            using (s_PrepareExposureMarker.Auto())
            {
                m_ExposureData = frameData.Get<VividExposureData>();

                m_FrameCount = Time.frameCount;
                m_EnableExposure = m_PostProcessingAllowed
                    && m_ExposureData != null
                    && m_ExposureData.exposureEnabled;

                var exposureBuffer = m_EnableExposure
                    ? m_ExposureData?.frameExposureBuffer
                    : m_ExposureData?.defaultExposureBuffer;
                if (exposureBuffer != null)
                {
                    PassRecorder.ImportBufferForPass(
                        this,
                        exposureBuffer,
                        AccessFlags.Read);
                }
            }

#if DLSS_PLUGIN_INTEGRATE
            PrepareDlssNeuralRendering(frameData.Get<VividAntialiasingData>());
#endif
        }

        public override void Create()
        {
            var resources = PipelineResourceManager.Get<VividRPCoreResources>();

            m_Material = CoreUtils.CreateEngineMaterial(resources.FinalBlitShader);
#if DLSS_PLUGIN_INTEGRATE
            m_DlssNeuralRenderingPass = new DLSSNeuralRenderingPass();
#endif
        }

        public override void Record(UnsafePassContext context)
        {
            if (m_Material == null)
                return;

            var cmd = context.cmd;
            var unsafeCmd = CommandBufferHelpers.GetNativeCommandBuffer(cmd);
            RTHandle sourceHandle = source.innerHandle;
            if (sourceHandle == null)
                return;

            var defaultExposureBuffer = m_ExposureData?.defaultExposureBuffer;
            var autoExposureBuffer = m_EnableExposure
                ? m_ExposureData?.frameExposureBuffer ?? defaultExposureBuffer
                : defaultExposureBuffer;

            if (autoExposureBuffer != null)
                m_Material.SetBuffer(AutoExposureBufferId, autoExposureBuffer);

            m_Material.SetVector(
                AutoExposureMaterialParamsId,
                new Vector4(m_EnableExposure ? 1f : 0f, 0f, 0f, 0f));

            ConfigureMaterialHDROutput(
                m_Material,
                m_ColorGradingSettings.hdrOutputActive,
                m_ColorGradingSettings.hdrDisplayColorGamut);
            if (m_ColorGradingSettings.hdrOutputActive)
            {
                m_Material.SetVector(HDROutputParamsId, m_ColorGradingSettings.hdrOutputParameters);
                m_Material.SetVector(HDROutputParams2Id, m_ColorGradingSettings.hdrOutputParameters2);
            }

            var useColorGradingLut = m_PostProcessingAllowed
                || m_ColorGradingSettings.hdrOutputActive;
            useColorGradingLut = useColorGradingLut
                && m_ColorGradingSettings.RequiresLut
                && colorGradingLut != null
                && colorGradingLut.innerHandle.IsValid();

            m_Material.SetVector(
                ColorGradingParamsId,
                new Vector4(
                    1f / ColorGradingLutBuilder.LutSize,
                    ColorGradingLutBuilder.LutSize - 1f,
                    useColorGradingLut ? 1f : 0f,
                    m_ColorGradingSettings.postExposureLinear));

            if (useColorGradingLut)
                cmd.SetGlobalTexture(ColorGradingLutId, colorGradingLut.innerHandle);

            if (m_FilmGrainSettings.enabled && m_FilmGrainSettings.texture != null)
            {
                m_Material.SetTexture(FilmGrainTextureId, m_FilmGrainSettings.texture);
                m_Material.SetVector(
                    FilmGrainParamsId,
                    FilmGrainRuntimeUtility.CreateMaterialParams(m_FilmGrainSettings));

                var texWidth = (float)m_FilmGrainSettings.texture.width;
                var texHeight = (float)m_FilmGrainSettings.texture.height;
                var screenWidth = m_Viewport.width > 0f ? m_Viewport.width : Screen.width;
                var screenHeight = m_Viewport.height > 0f ? m_Viewport.height : Screen.height;

                var offsetX = Random01FromFrame(m_FrameCount, 0);
                var offsetY = Random01FromFrame(m_FrameCount, 1);

                m_Material.SetVector(
                    FilmGrainTexParamsId,
                    new Vector4(
                        screenWidth / texWidth,
                        screenHeight / texHeight,
                        offsetX,
                        offsetY));

                CoreUtils.SetKeyword(m_Material, "_FILM_GRAIN", true);
            }
            else
            {
                CoreUtils.SetKeyword(m_Material, "_FILM_GRAIN", false);
            }

            if (m_VignetteSettings.enabled)
            {
                m_Material.SetVector(VignetteParams1Id, VignetteRuntimeUtility.CreateParams1(m_VignetteSettings));
                m_Material.SetVector(VignetteParams2Id, VignetteRuntimeUtility.CreateParams2(m_VignetteSettings));
                m_Material.SetVector(VignetteColorId, VignetteRuntimeUtility.CreateColor(m_VignetteSettings));
                m_Material.SetVector(VignetteScreenParamsId, VignetteRuntimeUtility.CreateScreenParams(m_Viewport));

                if (!m_VignetteSettings.IsProcedural)
                    m_Material.SetTexture(VignetteMaskId, m_VignetteSettings.mask != null ? m_VignetteSettings.mask : Texture2D.blackTexture);

                CoreUtils.SetKeyword(m_Material, "_VIGNETTE", true);
            }
            else
            {
                CoreUtils.SetKeyword(m_Material, "_VIGNETTE", false);
            }

            // Bloom and screen-space lens flare share the BloomTexture contribution.
            var bloomContributionEnabled = m_BloomSettings.enabled || m_ScreenSpaceLensFlareSettings.enabled;
            if (bloomContributionEnabled)
            {
                CoreUtils.SetKeyword(m_Material, "_BLOOM", true);
                CoreUtils.SetKeyword(m_Material, "_BLOOM_HQ", m_BloomSettings.enabled && m_BloomSettings.highQualityFiltering);
                if (m_BloomSettings.enabled && m_BloomSettings.dirtTexture != null && m_BloomSettings.dirtIntensity > 0f)
                    CoreUtils.SetKeyword(m_Material, "_BLOOM_DIRT", true);
                else
                    CoreUtils.SetKeyword(m_Material, "_BLOOM_DIRT", false);
            }
            else
            {
                CoreUtils.SetKeyword(m_Material, "_BLOOM", false);
                CoreUtils.SetKeyword(m_Material, "_BLOOM_HQ", false);
                CoreUtils.SetKeyword(m_Material, "_BLOOM_DIRT", false);
            }

            var sourceTextureUVOrigin = context.GetTextureUVOrigin(source.innerHandle);
#if DLSS_PLUGIN_INTEGRATE
            var executeDlssNeuralRendering = CanExecuteDlssNeuralRendering();
            if (executeDlssNeuralRendering)
            {
                var finalBlitScaleBias = sourceHandle.GetScaleBias(
                    sourceTextureUVOrigin,
                    context.GetTextureUVOrigin(m_FinalBlitOutput.innerHandle));
                cmd.SetRenderTarget(m_FinalBlitOutput.innerHandle);
                cmd.SetViewport(m_DlssNeuralRenderingInputViewport);
                Blitter.BlitTexture(unsafeCmd, sourceHandle, finalBlitScaleBias, m_Material, 0);

                m_DlssNeuralRenderingPass.Execute(
                    unsafeCmd,
                    m_CameraData,
                    m_FinalBlitOutput,
                    m_DlssNeuralRenderingDepth,
                    m_DlssNeuralRenderingMotionVectors,
                    m_DlssNeuralRenderingOutput,
                    m_DlssNeuralRenderingResetHistory);

                RTHandle neuralRenderingOutputHandle = m_DlssNeuralRenderingOutput.innerHandle;
                var presentScaleBias = neuralRenderingOutputHandle.GetScaleBias(
                    context.GetTextureUVOrigin(m_DlssNeuralRenderingOutput.innerHandle),
                    m_CameraBackBufferTextureUVOrigin);
                cmd.SetRenderTarget(m_CameraBackBufferTarget);
                if (m_ShouldSetViewport)
                    cmd.SetViewport(m_Viewport);
                Blitter.BlitTexture(
                    unsafeCmd,
                    neuralRenderingOutputHandle,
                    presentScaleBias,
                    0f,
                    bilinear: true);
            }
            else
#endif
            {
                var scaleBias = sourceHandle.GetScaleBias(
                    sourceTextureUVOrigin,
                    m_CameraBackBufferTextureUVOrigin);
                cmd.SetRenderTarget(m_CameraBackBufferTarget);
                if (m_ShouldSetViewport)
                    cmd.SetViewport(m_Viewport);
                Blitter.BlitTexture(unsafeCmd, sourceHandle, scaleBias, m_Material, 0);
            }

#if UNITY_EDITOR
            var camera = context.Get<VividCameraData>()?.camera;
            if (VividAdditionalCameraData.TryGetFinalFrameScreenshotCaptureTarget(camera, out var screenshotTarget))
            {
#if DLSS_PLUGIN_INTEGRATE
                if (executeDlssNeuralRendering)
                {
                    RTHandle neuralRenderingOutputHandle = m_DlssNeuralRenderingOutput.innerHandle;
                    var screenshotScaleBias = neuralRenderingOutputHandle.GetScaleBias(
                        context.GetTextureUVOrigin(m_DlssNeuralRenderingOutput.innerHandle),
                        TextureUVOrigin.BottomLeft);

                    cmd.SetRenderTarget(screenshotTarget);
                    cmd.SetViewport(new Rect(0f, 0f, screenshotTarget.width, screenshotTarget.height));
                    Blitter.BlitTexture(
                        unsafeCmd,
                        neuralRenderingOutputHandle,
                        screenshotScaleBias,
                        0f,
                        bilinear: true);
                }
                else
#endif
                {
                    var screenshotScaleBias = sourceHandle.GetScaleBias(
                        sourceTextureUVOrigin,
                        TextureUVOrigin.BottomLeft);

                    cmd.SetRenderTarget(screenshotTarget);
                    cmd.SetViewport(new Rect(0f, 0f, screenshotTarget.width, screenshotTarget.height));
                    Blitter.BlitTexture(unsafeCmd, sourceHandle, screenshotScaleBias, m_Material, 0);
                }
                VividAdditionalCameraData.MarkFinalFrameScreenshotCaptureTargetWritten(camera);

                cmd.SetRenderTarget(m_CameraBackBufferTarget);
                if (m_ShouldSetViewport)
                    cmd.SetViewport(m_Viewport);
            }
#endif
        }

        public override void Dispose()
        {
            if (m_Material != null)
            {
                CoreUtils.Destroy(m_Material);
                m_Material = null;
            }
#if DLSS_PLUGIN_INTEGRATE
            m_DlssNeuralRenderingPass?.Dispose();
            m_DlssNeuralRenderingPass = null;
            m_CameraData = null;
#endif
        }

#if DLSS_PLUGIN_INTEGRATE
        internal void PrepareDlssNeuralRendering(VividAntialiasingData antialiasingData)
        {
            var depthTexture = antialiasingData?.neuralRenderingDepthTexture;
            var motionVectorsTexture = antialiasingData?.neuralRenderingMotionVectorsTexture;
            m_DlssNeuralRenderingActive = antialiasingData?.effectiveMode
                == VividAntialiasingMode.DLSSNeuralRendering
                && depthTexture != null
                && motionVectorsTexture != null;
            m_DlssNeuralRenderingResetHistory = m_DlssNeuralRenderingActive
                && antialiasingData.resetHistory;

            SetDlssNeuralRenderingInputs(
                m_DlssNeuralRenderingActive ? depthTexture : m_DefaultDlssNeuralRenderingDepth,
                m_DlssNeuralRenderingActive ? motionVectorsTexture : m_DefaultDlssNeuralRenderingMotionVectors);

            var inputSize = m_DlssNeuralRenderingActive
                ? antialiasingData.renderSize
                : Vector2Int.one;
            var outputSize = m_DlssNeuralRenderingActive
                ? antialiasingData.outputSize
                : Vector2Int.one;
            ConfigureDlssNeuralRenderingTexture(
                m_FinalBlitOutput,
                "FinalBlitOutput",
                inputSize.x,
                inputSize.y,
                enableRandomWrite: false);
            ConfigureDlssNeuralRenderingTexture(
                m_DlssNeuralRenderingOutput,
                "DLSSNROutput",
                outputSize.x,
                outputSize.y,
                enableRandomWrite: true);
            m_DlssNeuralRenderingInputViewport = new Rect(
                0f,
                0f,
                Mathf.Max(1, inputSize.x),
                Mathf.Max(1, inputSize.y));
        }

        private void SetDlssNeuralRenderingInputs(
            RenderGraphTexture depthTexture,
            RenderGraphTexture motionVectorsTexture)
        {
            if (ReferenceEquals(m_DlssNeuralRenderingDepth, depthTexture)
                && ReferenceEquals(m_DlssNeuralRenderingMotionVectors, motionVectorsTexture))
            {
                return;
            }

            m_DlssNeuralRenderingDepth = depthTexture;
            m_DlssNeuralRenderingMotionVectors = motionVectorsTexture;
            m_IsPassResourceLayoutDirty = true;
        }

        private bool CanExecuteDlssNeuralRendering()
        {
            return m_DlssNeuralRenderingActive
                && m_DlssNeuralRenderingPass != null
                && m_CameraData?.camera != null
                && m_FinalBlitOutput?.innerHandle.IsValid() == true
                && m_DlssNeuralRenderingDepth?.innerHandle.IsValid() == true
                && m_DlssNeuralRenderingMotionVectors?.innerHandle.IsValid() == true
                && m_DlssNeuralRenderingOutput?.innerHandle.IsValid() == true;
        }

        private static void ConfigureDlssNeuralRenderingTexture(
            RenderGraphTexture texture,
            string name,
            int width,
            int height,
            bool enableRandomWrite)
        {
            if (texture?.desc == null)
                return;

            var descriptor = texture.desc;
            descriptor.Name = name;
            descriptor.Width = Mathf.Max(1, width);
            descriptor.Height = Mathf.Max(1, height);
            descriptor.Slices = 1;
            descriptor.Dimension = TextureDimension.Tex2D;
            descriptor.ColorFormat = GraphicsFormat.R16G16B16A16_SFloat;
            descriptor.DepthBufferBits = DepthBits.None;
            descriptor.MsaaSamples = MSAASamples.None;
            descriptor.FilterMode = FilterMode.Bilinear;
            descriptor.WrapMode = TextureWrapMode.Clamp;
            descriptor.AnisoLevel = 1;
            descriptor.MipMapBias = 0f;
            descriptor.ClearBuffer = false;
            descriptor.ClearColor = Color.clear;
            descriptor.IsShadowMap = false;
            descriptor.EnableRandomWrite = enableRandomWrite;
            descriptor.BindTextureMS = false;
            descriptor.UseDynamicScale = false;
            descriptor.UseDynamicScaleExplicit = false;
            descriptor.ScaleFactor = Vector2.one;
            descriptor.UseMipMap = false;
            descriptor.AutoGenerateMips = false;
            descriptor.MipCount = 1;
        }
#endif

        private static long HashFrame(int frame, int state)
        {
            long hash = frame * 747796405 + 2891336453 + state * 197;
            hash = ((hash >> 16) ^ hash) * 45679;
            hash = ((hash >> 16) ^ hash) * 45679;
            hash = (hash >> 16) ^ hash;
            return hash & 0x7FFFFFFF;
        }

        private static float Random01FromFrame(int frame, int state)
        {
            return (HashFrame(frame, state) & 0xFFFFFF) / 16777216f;
        }

        private static TextureUVOrigin GetCameraBackBufferTextureUVOrigin(CameraType cameraType, bool hasTargetTexture)
        {
            var useActualBackbufferOrientation = cameraType != CameraType.SceneView
                && cameraType != CameraType.Preview
                && !hasTargetTexture;

            if (!useActualBackbufferOrientation)
                return TextureUVOrigin.BottomLeft;

            return SystemInfo.graphicsUVStartsAtTop ? TextureUVOrigin.TopLeft : TextureUVOrigin.BottomLeft;
        }

        private static bool ShouldSetViewport(CameraType cameraType)
        {
            return cameraType != CameraType.SceneView;
        }

        private static void ConfigureMaterialHDROutput(Material material, bool hdrOutputActive, ColorGamut gamut)
        {
            if (material == null)
                return;

            if (hdrOutputActive)
            {
                HDROutputUtils.ConfigureHDROutput(
                    material,
                    gamut,
                    HDROutputUtils.Operation.ColorConversion | HDROutputUtils.Operation.ColorEncoding);
                return;
            }

            CoreUtils.SetKeyword(material, HDROutputUtils.ShaderKeywords.HDR_ENCODING, false);
            CoreUtils.SetKeyword(material, HDROutputUtils.ShaderKeywords.HDR_COLORSPACE_CONVERSION, false);
            CoreUtils.SetKeyword(material, HDROutputUtils.ShaderKeywords.HDR_COLORSPACE_CONVERSION_AND_ENCODING, false);
            CoreUtils.SetKeyword(material, HDROutputUtils.ShaderKeywords.HDR_INPUT, false);
        }

        private static Rect GetViewport(VividCameraData cameraData)
        {
            if (cameraData.pixelRect.width > 0f && cameraData.pixelRect.height > 0f)
                return cameraData.pixelRect;

            var width = cameraData.actualWidth > 0 ? cameraData.actualWidth : cameraData.pixelWidth;
            var height = cameraData.actualHeight > 0 ? cameraData.actualHeight : cameraData.pixelHeight;

            if (width <= 0 || height <= 0)
                return new Rect(0f, 0f, Screen.width, Screen.height);

            return new Rect(0f, 0f, width, height);
        }

    }
}
