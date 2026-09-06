#if DLSS_PLUGIN_INTEGRATE

using System;
using System.Collections.Generic;
using Unity.Profiling;
using UnityEngine;
using UnityEngine.Rendering;

namespace VividRP.Runtime.RenderPass.Core
{
    internal sealed class DLSSNeuralRenderingPass : IDisposable
    {
        private const int CameraStateExpirationFrames = 400;

        private static readonly ProfilerMarker s_RecordMarker =
            new("VividRP.RenderPass.Record/DLSS 5 Neural Rendering");

        private readonly Dictionary<EntityId, CameraState> m_CameraStates = new();
        private readonly List<EntityId> m_ExpiredCameraIds = new();

        public bool IsSupported =>
            DLSSExtension.Initialize() && DLSSExtension.IsNeuralRenderingSupported;

        internal bool Execute(
            CommandBuffer cmd,
            VividCameraData cameraData,
            RenderTexture source,
            RenderTexture depth,
            RenderTexture motionVectors,
            RenderTexture output,
            bool resetHistory)
        {
            using var recordScope = s_RecordMarker.Auto();
            if (cmd == null || source == null || output == null)
                return false;

            if (!IsSupported || cameraData?.camera == null || depth == null || motionVectors == null)
            {
                cmd.Blit(source, output);
                return true;
            }

            VividAdditionalCameraData additionalData = cameraData.additionalData;
            bool upscaling = additionalData != null
                && additionalData.dlssNeuralRenderingUpscaling
                && output.width == source.width * 2
                && output.height == source.height * 2;
            CameraState cameraState = GetOrCreateCameraState(
                cameraData.camera,
                cameraData.frameIndex);
            CleanupExpiredCameraStates(cameraData.frameIndex);

            var parameters = new ExecutionParameters
            {
                ResetHistory = resetHistory,
                Upscaling = upscaling,
                Preset = additionalData != null
                    ? additionalData.dlssNeuralRenderingPreset
                    : DLSSNeuralRenderingPreset.Default,
                Style = additionalData != null
                    ? additionalData.dlssNeuralRenderingStyle
                    : DLSSNeuralRenderingStyle.Default,
                Intensity = additionalData?.dlssNeuralRenderingIntensity ?? 1.0f,
                LocalToneStrength = additionalData?.dlssNeuralRenderingLocalToneStrength ?? 1.0f,
                LocalStructureStrength = additionalData?.dlssNeuralRenderingLocalStructureStrength ?? 1.0f,
                SkinStructureStrength = additionalData?.dlssNeuralRenderingSkinStructureStrength ?? -1.0f,
                UseAutoMask = additionalData != null && additionalData.dlssNeuralRenderingUseAutoMask,
                UICorrection = additionalData != null && additionalData.dlssNeuralRenderingUICorrection,
            };
            cameraState.Execute(
                cmd,
                source,
                depth,
                motionVectors,
                output,
                in parameters);
            return true;
        }

        public void Dispose()
        {
            foreach (CameraState state in m_CameraStates.Values)
                state.Dispose();

            m_CameraStates.Clear();
            m_ExpiredCameraIds.Clear();
        }

        private CameraState GetOrCreateCameraState(Camera camera, int frameIndex)
        {
            EntityId cameraId = camera.GetEntityId();
            if (!m_CameraStates.TryGetValue(cameraId, out CameraState state))
            {
                state = new CameraState();
                m_CameraStates.Add(cameraId, state);
            }

            state.LastUsedFrame = frameIndex >= 0 ? frameIndex : Time.frameCount;
            return state;
        }

        private void CleanupExpiredCameraStates(int frameIndex)
        {
            int currentFrame = frameIndex >= 0 ? frameIndex : Time.frameCount;
            m_ExpiredCameraIds.Clear();

            foreach (KeyValuePair<EntityId, CameraState> pair in m_CameraStates)
            {
                if (currentFrame - pair.Value.LastUsedFrame > CameraStateExpirationFrames)
                    m_ExpiredCameraIds.Add(pair.Key);
            }

            for (int index = 0; index < m_ExpiredCameraIds.Count; index++)
            {
                EntityId cameraId = m_ExpiredCameraIds[index];
                if (!m_CameraStates.TryGetValue(cameraId, out CameraState state))
                    continue;

                state.Dispose();
                m_CameraStates.Remove(cameraId);
            }
        }

        private struct ExecutionParameters
        {
            public bool ResetHistory;
            public bool Upscaling;
            public DLSSNeuralRenderingPreset Preset;
            public DLSSNeuralRenderingStyle Style;
            public float Intensity;
            public float LocalToneStrength;
            public float LocalStructureStrength;
            public float SkinStructureStrength;
            public bool UseAutoMask;
            public bool UICorrection;
        }

        private sealed class CameraState : IDisposable
        {
            private readonly DLSSNeuralRenderingSettings m_Settings = new();
            private DLSSNeuralRendering m_NeuralRendering;

            public int LastUsedFrame { get; set; }

            public void Execute(
                CommandBuffer cmd,
                RenderTexture source,
                RenderTexture depth,
                RenderTexture motionVectors,
                RenderTexture output,
                in ExecutionParameters parameters)
            {
                m_NeuralRendering ??= new DLSSNeuralRendering();
                m_Settings.Preset = parameters.Preset;
                m_Settings.Style = parameters.Style;
                m_Settings.Intensity = parameters.Intensity;
                m_Settings.LocalToneStrength = parameters.LocalToneStrength;
                m_Settings.LocalStructureStrength = parameters.LocalStructureStrength;
                m_Settings.SkinStructureStrength = parameters.SkinStructureStrength;
                m_Settings.DepthInverted = SystemInfo.usesReversedZBuffer;
                m_Settings.UseAutoMask = parameters.UseAutoMask;
                m_Settings.UICorrection = parameters.UICorrection;
                m_Settings.Upscaling = parameters.Upscaling;
                m_Settings.MotionVectorScale = Vector2.one;

                m_NeuralRendering.Render(
                    cmd,
                    source,
                    output,
                    depth,
                    motionVectors,
                    DLSSMotionVectorEncoding.VividNormalizedUV,
                    m_Settings,
                    parameters.ResetHistory);
            }

            public void Dispose()
            {
                m_NeuralRendering?.Dispose();
                m_NeuralRendering = null;
            }
        }
    }
}

#endif
