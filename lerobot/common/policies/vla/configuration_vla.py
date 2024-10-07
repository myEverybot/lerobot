#!/usr/bin/env python

# Copyright 2024 Tony Z. Zhao and The HuggingFace Inc. team. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from dataclasses import dataclass, field


@dataclass
class VLAConfig:
    """Configuration class for the Action Chunking Transformers policy.

    Defaults are configured for training on bimanual Aloha tasks like "insertion" or "transfer".

    The parameters you will most likely need to change are the ones which depend on the environment / sensors.
    Those are: `input_shapes` and 'output_shapes`.

    Notes on the inputs and outputs:
        - Either:
            - At least one key starting with "observation.image is required as an input.
              AND/OR
            - The key "observation.environment_state" is required as input.
        - If there are multiple keys beginning with "observation.images." they are treated as multiple camera
          views. Right now we only support all images having the same shape.
        - May optionally work without an "observation.state" key for the proprioceptive robot state.
        - "action" is required as an output key.

    Args:
        n_obs_steps: Number of environment steps worth of observations to pass to the policy (takes the
            current step and additional steps going back).
        chunk_size: The size of the action prediction "chunks" in units of environment steps.
        n_action_steps: The number of action steps to run in the environment for one invocation of the policy.
            This should be no greater than the chunk size. For example, if the chunk size size 100, you may
            set this to 50. This would mean that the model predicts 100 steps worth of actions, runs 50 in the
            environment, and throws the other 50 out.
        input_shapes: A dictionary defining the shapes of the input data for the policy. The key represents
            the input data name, and the value is a list indicating the dimensions of the corresponding data.
            For example, "observation.image" refers to an input from a camera with dimensions [3, 96, 96],
            indicating it has three color channels and 96x96 resolution. Importantly, `input_shapes` doesn't
            include batch dimension or temporal dimension.
        output_shapes: A dictionary defining the shapes of the output data for the policy. The key represents
            the output data name, and the value is a list indicating the dimensions of the corresponding data.
            For example, "action" refers to an output shape of [14], indicating 14-dimensional actions.
            Importantly, `output_shapes` doesn't include batch dimension or temporal dimension.
        input_normalization_modes: A dictionary with key representing the modality (e.g. "observation.state"),
            and the value specifies the normalization mode to apply. The two available modes are "mean_std"
            which subtracts the mean and divides by the standard deviation and "min_max" which rescale in a
            [-1, 1] range.
        output_normalization_modes: Similar dictionary as `normalize_input_modes`, but to unnormalize to the
            original scale. Note that this is also used for normalizing the training targets.
        vision_backbone: Name of the torchvision resnet backbone to use for encoding images.
        pretrained_backbone_weights: Pretrained weights from torchvision to initalize the backbone.
            `None` means no pretrained weights.
        replace_final_stride_with_dilation: Whether to replace the ResNet's final 2x2 stride with a dilated
            convolution.
        pre_norm: Whether to use "pre-norm" in the transformer blocks.
        dim_model: The transformer blocks' main hidden dimension.
        n_heads: The number of heads to use in the transformer blocks' multi-head attention.
        dim_feedforward: The dimension to expand the transformer's hidden dimension to in the feed-forward
            layers.
        feedforward_activation: The activation to use in the transformer block's feed-forward layers.
        n_encoder_layers: The number of transformer layers to use for the transformer encoder.
        n_decoder_layers: The number of transformer layers to use for the transformer decoder.
        use_vae: Whether to use a variational objective during training. This introduces another transformer
            which is used as the VAE's encoder (not to be confused with the transformer encoder - see
            documentation in the policy class).
        latent_dim: The VAE's latent dimension.
        n_vae_encoder_layers: The number of transformer layers to use for the VAE's encoder.
        temporal_ensemble_coeff: Coefficient for the exponential weighting scheme to apply for temporal
            ensembling. Defaults to None which means temporal ensembling is not used. `n_action_steps` must be
            1 when using this feature, as inference needs to happen at every step to form an ensemble. For
            more information on how ensembling works, please see `ACTTemporalEnsembler`.
        dropout: Dropout to use in the transformer layers (see code for details).
        kl_weight: The weight to use for the KL-divergence component of the loss if the variational objective
            is enabled. Loss is then calculated as: `reconstruction_loss + kl_weight * kld_loss`.
    """

    # Input / output structure.
    n_obs_steps: int = 1
    chunk_size: int = 100
    n_action_steps: int = 100

    input_shapes: dict[str, list[int]] = field(
        default_factory=lambda: {
            "observation.images.top": [3, 480, 640],
            "observation.state": [14],
        }
    )
    output_shapes: dict[str, list[int]] = field(
        default_factory=lambda: {
            "action": [14],
        }
    )

    # Normalization / Unnormalization
    input_normalization_modes: dict[str, str] = field(
        default_factory=lambda: {
            "observation.images.top": "mean_std",
            "observation.state": "mean_std",
        }
    )
    output_normalization_modes: dict[str, str] = field(
        default_factory=lambda: {
            "action": "mean_std",
        }
    )

    # Architecture.

    # Language + Main transformer
    vocab_size: int = 152064
    hidden_size: int = 8192
    intermediate_size: int = 29568
    num_hidden_layers: int = 80
    num_decoder_layers: int = 1
    attn_implementation: str = "eager"
    num_attention_heads: int = 64
    num_key_value_heads: int = 8
    dim_feedforward: int = 3200
    hidden_act: str = "silu"
    pad_token_id: int = 0
    max_position_embeddings: int = 32768
    initializer_range: float = 0.02
    rms_norm_eps: float = 1e-05
    use_cache: bool = True
    tie_word_embeddings: bool = False
    rope_theta: float = 1000000.0
    use_sliding_window: bool = False
    sliding_window = 4096
    max_window_layers = 80
    attention_dropout = 0.0
    rope_scaling: dict = field(
        default_factory=lambda: {
            "type": "mrope",
            "mrope_section": [2, 2, 2],
        }
    )
    pruned_heads = None

    # Vision encoder
    # depth: int = 32
    # embed_dim: int = 1280
    # hidden_size: int = 3584
    # hidden_act: str = "quick_gelu"
    # mlp_ratio: int = 4
    # num_heads: int = 16
    # in_channels: int = 3
    # patch_size: int = 14
    # spatial_merge_size: int = 2
    # temporal_patch_size: int = 2
    # attn_implementation: str = "eager"
    vision_config: dict = field(
        default_factory=lambda: {
            "depth": 32,
            "embed_dim": 1280,
            "hidden_size": 3584,
            "hidden_act": "quick_gelu",
            "mlp_ratio": 4,
            "num_heads": 16,
            "in_channels": 3,
            "patch_size": 14,
            "spatial_merge_size": 2,
            "temporal_patch_size": 2,
            "attn_implementation": "eager",
        }
    )

    def __post_init__(self):
        """Input validation (not exhaustive)."""
        # if not self.vision_backbone.startswith("resnet"):
        #     raise ValueError(
        #         f"`vision_backbone` must be one of the ResNet variants. Got {self.vision_backbone}."
        #     )
        # if self.temporal_ensemble_coeff is not None and self.n_action_steps > 1:
        #     raise NotImplementedError(
        #         "`n_action_steps` must be 1 when using temporal ensembling. This is "
        #         "because the policy needs to be queried every step to compute the ensembled action."
        #     )
        if self.n_action_steps > self.chunk_size:
            raise ValueError(
                f"The chunk size is the upper bound for the number of action steps per model invocation. Got "
                f"{self.n_action_steps} for `n_action_steps` and {self.chunk_size} for `chunk_size`."
            )
        if self.n_obs_steps != 1:
            raise ValueError(
                f"Multiple observation steps not handled yet. Got `nobs_steps={self.n_obs_steps}`"
            )
        if (
            not any(k.startswith("observation.image") for k in self.input_shapes)
            and "observation.environment_state" not in self.input_shapes
        ):
            raise ValueError("You must provide at least one image or the environment state among the inputs.")