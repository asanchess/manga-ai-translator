---
name: Manga Processing Guidelines
description: Strict constraints for manga image cleaning, typesetting, and typography.
---

# Manga Processing Guidelines

When working on manga image processing, cleaning, or typesetting scripts, you MUST adhere to the following rules to prevent visual artifacts and regressions:

## 1. Cleaning & Inpainting
- **NEVER** use crude bounding box fills (e.g., `cv2.rectangle`) to wipe speech bubbles. This destroys bubble borders and overlapping artwork.
- **ALWAYS** use precision pixel-level masking (e.g., `cv2.threshold`) combined with `cv2.inpaint(img, mask, radius, cv2.INPAINT_TELEA)` or similar advanced inpainting models (like LaMa) to seamlessly remove text while preserving the background texture.

## 2. Typography & Rendering
- **Contrast Matching:** Text color must dynamically match the background contrast. Use Luma calculation to render black text on white backgrounds, and white text on dark backgrounds.
- **No Programmer Artifacts:** Do not render programmer/markup tags like `*[ ]*` or HTML tags into the final image. Text should be rendered cleanly as standard manga dialogue.
- **Fonts:** Only use high-quality, Cyrillic-verified TrueType fonts for Russian text (e.g., Comic Sans, Arial Bold, Segoe UI). Never use fonts that do not support Cyrillic characters.
- **SFX (Sound Effects):** Render SFX naturally blending into the background or ignore them. Do not create ugly box badges for them unless explicitly requested.
