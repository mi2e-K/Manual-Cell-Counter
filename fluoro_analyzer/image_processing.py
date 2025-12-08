"""
Image processing functions for Fluorescence Microscope Image Analyzer.
Contains brightness, contrast, and noise reduction functions.
"""

import numpy as np
from typing import Optional

try:
    from scipy import ndimage
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False


def apply_brightness(channel: np.ndarray, brightness: int) -> np.ndarray:
    """
    Apply brightness adjustment to a single channel.
    
    Args:
        channel: 2D numpy array (single channel)
        brightness: Value from -100 to 100
    
    Returns:
        Adjusted channel as uint8
    """
    if brightness == 0:
        return channel
    
    # Convert to float for calculation
    adjusted = channel.astype(np.float32)
    
    # Apply brightness (scale from -100,100 to actual pixel shift)
    adjusted = adjusted + (brightness * 2.55)  # Scale to roughly -255 to 255
    
    # Clip and convert back
    return np.clip(adjusted, 0, 255).astype(np.uint8)


def apply_contrast(channel: np.ndarray, contrast: float) -> np.ndarray:
    """
    Apply contrast adjustment to a single channel.
    
    Args:
        channel: 2D numpy array (single channel)
        contrast: Value from 0.1 to 3.0 (1.0 = no change)
    
    Returns:
        Adjusted channel as uint8
    """
    if contrast == 1.0:
        return channel
    
    # Convert to float for calculation
    adjusted = channel.astype(np.float32)
    
    # Apply contrast around midpoint (128)
    midpoint = 128.0
    adjusted = (adjusted - midpoint) * contrast + midpoint
    
    # Clip and convert back
    return np.clip(adjusted, 0, 255).astype(np.uint8)


def apply_noise_reduction_channel(channel: np.ndarray, strength: int) -> np.ndarray:
    """
    Apply noise reduction to a single channel using Gaussian blur.
    
    Args:
        channel: 2D numpy array (single channel)
        strength: Value from 0 to 10 (0 = no reduction)
    
    Returns:
        Filtered channel
    """
    if strength == 0:
        return channel
    
    if not HAS_SCIPY:
        # Fallback: return unchanged if scipy not available
        return channel
    
    # Convert strength to sigma (0-10 maps to 0-2.0 sigma)
    sigma = strength * 0.2
    
    return ndimage.gaussian_filter(channel, sigma=sigma).astype(np.uint8)


def apply_all_adjustments(image: np.ndarray, adjustments) -> np.ndarray:
    """
    Apply all image adjustments.
    
    Args:
        image: 3D numpy array (H, W, 3) RGB image
        adjustments: ImageAdjustments object
    
    Returns:
        Adjusted image
    """
    if image is None or image.ndim != 3 or image.shape[2] < 3:
        return image
    
    result = image.copy()
    
    # Apply per-channel brightness, contrast, and noise reduction
    # Red channel
    r = result[:, :, 0]
    r = apply_brightness(r, adjustments.brightness_r)
    r = apply_contrast(r, adjustments.contrast_r)
    r = apply_noise_reduction_channel(r, adjustments.noise_r)
    result[:, :, 0] = r
    
    # Green channel
    g = result[:, :, 1]
    g = apply_brightness(g, adjustments.brightness_g)
    g = apply_contrast(g, adjustments.contrast_g)
    g = apply_noise_reduction_channel(g, adjustments.noise_g)
    result[:, :, 1] = g
    
    # Blue channel
    b = result[:, :, 2]
    b = apply_brightness(b, adjustments.brightness_b)
    b = apply_contrast(b, adjustments.contrast_b)
    b = apply_noise_reduction_channel(b, adjustments.noise_b)
    result[:, :, 2] = b
    
    return result
