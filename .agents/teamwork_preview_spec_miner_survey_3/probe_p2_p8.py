import os, cv2, json, numpy as np

p2_v1 = r'backend/data/manga/The_Ultimate_of_All_Ages/chapter_531/v1_original/page_002.webp'
p2_v2 = r'backend/data/manga/The_Ultimate_of_All_Ages/chapter_531/v2_cleaned/page_002.webp'
p2_v3 = r'backend/data/manga/The_Ultimate_of_All_Ages/chapter_531/v3_translated/page_002.webp'
p2_ocr = p2_v1 + '.ocr.json'

p8_v1 = r'backend/data/manga/The_Ultimate_of_All_Ages/chapter_531/v1_original/page_008.webp'
p8_v2 = r'backend/data/manga/The_Ultimate_of_All_Ages/chapter_531/v2_cleaned/page_008.webp'
p8_v3 = r'backend/data/manga/The_Ultimate_of_All_Ages/chapter_531/v3_translated/page_008.webp'
p8_ocr = p8_v1 + '.ocr.json'

def ssim_metric(img1, img2, mask=None):
    C1 = (0.01 * 255) ** 2
    C2 = (0.03 * 255) ** 2
    
    img1 = img1.astype(np.float64)
    img2 = img2.astype(np.float64)
    
    kernel = cv2.getGaussianKernel(11, 1.5)
    window = np.outer(kernel, kernel.transpose())
    
    mu1 = cv2.filter2D(img1, -1, window)[5:-5, 5:-5]
    mu2 = cv2.filter2D(img2, -1, window)[5:-5, 5:-5]
    
    mu1_sq = mu1 ** 2
    mu2_sq = mu2 ** 2
    mu1_mu2 = mu1 * mu2
    
    sigma1_sq = cv2.filter2D(img1 ** 2, -1, window)[5:-5, 5:-5] - mu1_sq
    sigma2_sq = cv2.filter2D(img2 ** 2, -1, window)[5:-5, 5:-5] - mu2_sq
    sigma12 = cv2.filter2D(img1 * img2, -1, window)[5:-5, 5:-5] - mu1_mu2
    
    ssim_map = ((2 * mu1_mu2 + C1) * (2 * sigma12 + C2)) / ((mu1_sq + mu2_sq + C1) * (sigma1_sq + sigma2_sq + C2))
    
    if mask is not None:
        mask_crop = mask[5:-5, 5:-5]
        if np.sum(mask_crop) > 0:
            return np.mean(ssim_map[mask_crop > 0])
    return np.mean(ssim_map)

def analyze_page(name, v1_p, v2_p, v3_p, ocr_p):
    img1 = cv2.imread(v1_p)
    img2 = cv2.imread(v2_p)
    img3 = cv2.imread(v3_p)
    
    with open(ocr_p, 'r', encoding='utf-8') as f:
        clusters = json.load(f)
        
    print(f'=== {name} Analysis ===')
    print(f'Dimensions: Width={img1.shape[1]}px, Height={img1.shape[0]}px, Channels={img1.shape[2]}')
    print(f'Total Clusters Detected: {len(clusters)}')
    
    mask_bubbles = np.zeros(img1.shape[:2], dtype=np.uint8)
    for c in clusters:
        x, y, w, h = c['box']
        cv2.rectangle(mask_bubbles, (max(0, x-10), max(0, y-10)), (min(img1.shape[1], x+w+10), min(img1.shape[0], y+h+10)), 255, -1)
        print(f'  ID {c.get("id")}: Box={c["box"]}, SFX={c.get("is_sfx")}, Dark={c.get("is_dark")}')
        print(f'    Text: "{c["text"]}"')
        
    bg_mask = (mask_bubbles == 0).astype(np.uint8)
    
    # Check SSIM on grayscale
    gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
    gray3 = cv2.cvtColor(img3, cv2.COLOR_BGR2GRAY)
    
    bg_ssim = ssim_metric(gray1, gray3, mask=bg_mask)
    degradation = (1.0 - bg_ssim) * 100
    
    diff_bg = np.abs(img1.astype(float) - img3.astype(float))
    diff_bg_outside = diff_bg[bg_mask > 0]
    max_diff = np.max(diff_bg_outside)
    mean_diff = np.mean(diff_bg_outside)
    pct_nonzero_diff = np.mean(diff_bg_outside > 0) * 100
    
    print(f'Background SSIM: {bg_ssim:.6f}')
    print(f'Background Degradation: {degradation:.4f}% (Threshold: <= 0.5%)')
    print(f'Pixel difference stats: Max={max_diff:.1f}, Mean={mean_diff:.4f}, Non-zero pixels={pct_nonzero_diff:.4f}%')
    print(f'SSIM Pass Status: {"PASS" if degradation <= 0.5 else "FAIL"}\n')

analyze_page('Chapter 531 Page 002', p2_v1, p2_v2, p2_v3, p2_ocr)
analyze_page('Chapter 531 Page 008', p8_v1, p8_v2, p8_v3, p8_ocr)