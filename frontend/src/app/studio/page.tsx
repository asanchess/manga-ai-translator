'use client';

import React, { useState, useEffect, useRef } from 'react';
import Link from 'next/link';
import styles from './page.module.css';

export default function MangaStudioPage() {
  // Option controls
  const [sourceLang, setSourceLang] = useState('auto');
  const [targetLang, setTargetLang] = useState('ru');
  const [detectorMode, setDetectorMode] = useState('CTD');
  const [fontStyle, setFontStyle] = useState('auto');

  // Input tab
  const [activeTab, setActiveTab] = useState<'url' | 'upload'>('url');
  
  // URL Input
  const [mangaName, setMangaName] = useState('The_Ultimate_of_All_Ages');
  const [chapterNum, setChapterNum] = useState('531');
  const [sourceUrl, setSourceUrl] = useState('https://theultimateofallages.com/manga/the-ultimate-of-all-ages-chapter-531/');

  // Task processing state
  const [taskId, setTaskId] = useState<string | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [taskData, setTaskData] = useState<any>(null);

  // Split-Slider comparison state
  const [sliderPos, setSliderPos] = useState(50);
  const [compareMode, setCompareMode] = useState<'translated' | 'cleaned'>('translated');
  const [isDragging, setIsDragging] = useState(false);
  const splitRef = useRef<HTMLDivElement>(null);

  // File Upload
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);

  // Task status polling
  useEffect(() => {
    if (!taskId) return;
    const interval = setInterval(async () => {
      try {
        const res = await fetch(`http://localhost:8000/api/studio/tasks/${taskId}`);
        const data = await res.json();
        setTaskData(data);
        if (data.status === 'completed' || data.status === 'failed') {
          setIsProcessing(false);
          clearInterval(interval);
        }
      } catch (err) {
        console.error('Error fetching task status:', err);
      }
    }, 1500);

    return () => clearInterval(interval);
  }, [taskId]);

  const handleStartTranslate = async () => {
    setIsProcessing(true);
    setTaskData(null);
    try {
      const res = await fetch('http://localhost:8000/api/studio/translate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          manga_name: mangaName,
          chapter_num: chapterNum,
          source_url: activeTab === 'url' ? sourceUrl : undefined,
          source_lang: sourceLang,
          target_lang: targetLang,
          detector_mode: detectorMode,
          font_style: fontStyle
        })
      });
      const data = await res.json();
      if (data.task_id) {
        setTaskId(data.task_id);
      }
    } catch (err) {
      console.error('Failed to start translation:', err);
      setIsProcessing(false);
    }
  };

  const handleFileUpload = async (files: FileList | null) => {
    if (!files || files.length === 0) return;
    const fileList = Array.from(files);
    setSelectedFiles(fileList);

    const formData = new FormData();
    formData.append('manga_name', mangaName);
    formData.append('chapter_num', chapterNum);
    formData.append('auto_start', 'true');
    fileList.forEach(f => formData.append('files', f));

    setIsProcessing(true);
    try {
      const res = await fetch('http://localhost:8000/api/studio/upload', {
        method: 'POST',
        body: formData
      });
      const data = await res.json();
      if (data.task_id) {
        setTaskId(data.task_id);
      }
    } catch (err) {
      console.error('Upload failed:', err);
      setIsProcessing(false);
    }
  };

  // Slider drag handler
  const handleMouseMove = (e: React.MouseEvent | React.TouchEvent) => {
    if (!isDragging || !splitRef.current) return;
    const rect = splitRef.current.getBoundingClientRect();
    const clientX = 'touches' in e ? e.touches[0].clientX : (e as React.MouseEvent).clientX;
    const offset = clientX - rect.left;
    const percentage = Math.max(0, Math.min(100, (offset / rect.width) * 100));
    setSliderPos(percentage);
  };

  return (
    <div className={styles.container}>
      {/* Header */}
      <header className={styles.header}>
        <Link href="/studio" className={styles.logoArea}>
          <div className={styles.logoIcon}>⚡</div>
          <div className={styles.logoTitle}>Manga AI Studio</div>
        </Link>
        <div className={styles.navActions}>
          <Link href={`/reader/${mangaName}?chapter=chapter_${chapterNum}`} className={styles.navBtn}>
            📖 Открыть Ридер
          </Link>
          <a href="http://localhost:8000/docs" target="_blank" rel="noreferrer" className={styles.navBtn}>
            ⚙️ API Docs
          </a>
        </div>
      </header>

      {/* Hero */}
      <section className={styles.hero}>
        <div className={styles.badgeRow}>
          <span className={`${styles.badge} ${styles.badgeGreen}`}>● Автономный Пайплайн</span>
          <span className={`${styles.badge} ${styles.badgePurple}`}>⚡ 5-Pass EagleEye Cleaner</span>
          <span className={styles.badge}>🤖 OpenRouter LLM Cascade</span>
        </div>
        <h1 className={styles.heroTitle}>
          Профессиональный <span className={styles.gradientText}>ИИ-переводчик Манги</span>
        </h1>
        <p className={styles.heroSub}>
          Автоматическое распознавание баблов, чистый 5-проходный клининг и мгновенный литературный перевод маньхуа в один клик.
        </p>
      </section>

      {/* Main Workspace */}
      <div className={styles.workspace}>
        {/* Options Card (Like MangaTranslate.com) */}
        <div className={styles.optionsCard}>
          <div className={styles.optionItem}>
            <label className={styles.optionLabel}>Исходный язык</label>
            <select className={styles.selectInput} value={sourceLang} onChange={e => setSourceLang(e.target.value)}>
              <option value="auto">🌐 Автоопределение</option>
              <option value="en">Английский (English)</option>
              <option value="zh">Китайский (中文)</option>
              <option value="ja">Японский (日本語)</option>
              <option value="ko">Корейский (한국어)</option>
            </select>
          </div>

          <div className={styles.optionItem}>
            <label className={styles.optionLabel}>Целевой язык</label>
            <select className={styles.selectInput} value={targetLang} onChange={e => setTargetLang(e.target.value)}>
              <option value="ru">🇷🇺 Русский (Russian)</option>
              <option value="en">🇬🇧 Английский (English)</option>
            </select>
          </div>

          <div className={styles.optionItem}>
            <label className={styles.optionLabel}>Модель распознавания</label>
            <select className={styles.selectInput} value={detectorMode} onChange={e => setDetectorMode(e.target.value)}>
              <option value="CTD">Comic Text Detector (Рекомендуется)</option>
              <option value="EagleEye">EagleEye 5-Pass Inpainter</option>
              <option value="Hybrid">Hybrid Deep Detector</option>
            </select>
          </div>

          <div className={styles.optionItem}>
            <label className={styles.optionLabel}>Стиль шрифта</label>
            <select className={styles.selectInput} value={fontStyle} onChange={e => setFontStyle(e.target.value)}>
              <option value="auto">Auto (CC Wild Words & Impact)</option>
              <option value="anime_ace">Anime Ace 3.0</option>
              <option value="cultivation">Cultivation Power</option>
            </select>
          </div>
        </div>

        {/* Ingestion Tabs */}
        <div className={styles.tabsContainer}>
          <button 
            className={`${styles.tabBtn} ${activeTab === 'url' ? styles.tabBtnActive : ''}`}
            onClick={() => setActiveTab('url')}
          >
            🔗 Импорт по ссылке (URL)
          </button>
          <button 
            className={`${styles.tabBtn} ${activeTab === 'upload' ? styles.tabBtnActive : ''}`}
            onClick={() => setActiveTab('upload')}
          >
            📁 Загрузка файлов / ZIP архива
          </button>
        </div>

        {/* Ingestion Panel */}
        <div className={styles.panelCard}>
          {activeTab === 'url' ? (
            <div className={styles.urlForm}>
              <div className={styles.inputGrid}>
                <div>
                  <label className={styles.optionLabel}>Ссылка на главу манхвы / сканы</label>
                  <input 
                    type="text" 
                    className={styles.textInput}
                    placeholder="https://theultimateofallages.com/manga/...-chapter-531/"
                    value={sourceUrl}
                    onChange={e => setSourceUrl(e.target.value)}
                  />
                </div>
                <div>
                  <label className={styles.optionLabel}>Номер главы</label>
                  <input 
                    type="text" 
                    className={styles.textInput}
                    placeholder="531"
                    value={chapterNum}
                    onChange={e => setChapterNum(e.target.value)}
                  />
                </div>
              </div>
              <div className={styles.actionBtnRow}>
                <button 
                  className={styles.btnPrimaryLarge}
                  onClick={handleStartTranslate}
                  disabled={isProcessing}
                >
                  {isProcessing ? '⏳ Обработка главы...' : '🚀 Сканировать и Перевести в 1 Клик'}
                </button>
              </div>
            </div>
          ) : (
            <div>
              <div 
                className={styles.uploadDropzone}
                onClick={() => fileInputRef.current?.click()}
                onDragOver={e => e.preventDefault()}
                onDrop={e => {
                  e.preventDefault();
                  handleFileUpload(e.dataTransfer.files);
                }}
              >
                <input 
                  type="file" 
                  ref={fileInputRef} 
                  multiple 
                  accept="image/*,.zip" 
                  style={{ display: 'none' }}
                  onChange={e => handleFileUpload(e.target.files)}
                />
                <div className={styles.uploadIcon}>📥</div>
                <div className={styles.uploadTitle}>
                  Перетащите сюда страницы главы (WebP, PNG, JPG) или .ZIP архив
                </div>
                <div className={styles.uploadSub}>
                  Автоматический клининг, распознавание и перевод запустятся сразу после загрузки
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Live Progress Card */}
        {(isProcessing || taskData) && (
          <div className={styles.progressCard}>
            <div className={styles.progressHeader}>
              <div className={styles.progressTitle}>
                <span>⚡ Статус: {taskData?.current_step || 'Выполняется обработка...'}</span>
              </div>
              <div className={styles.progressPercent}>
                {taskData?.progress || (isProcessing ? 30 : 100)}%
              </div>
            </div>
            <div className={styles.progressBarTrack}>
              <div 
                className={styles.progressBarFill} 
                style={{ width: `${taskData?.progress || (isProcessing ? 30 : 100)}%` }}
              />
            </div>
            <div className={styles.logBox}>
              {taskData?.logs && taskData.logs.map((log: string, i: number) => (
                <div key={i} className={styles.logLine}>{log}</div>
              ))}
            </div>
          </div>
        )}

        {/* Interactive Split-Slider Comparison */}
        <section className={styles.comparisonSection}>
          <div className={styles.sectionTitle}>
            <span>✨ Интерактивное сравнение результатов</span>
          </div>
          <p className={styles.sectionSub}>
            Потяните ползунок влево и вправо, чтобы сравнить качество клининга и перевода диалогов с оригиналом:
          </p>

          <div className={styles.sliderControls}>
            <button 
              className={`${styles.sliderBtn} ${compareMode === 'translated' ? styles.sliderBtnActive : ''}`}
              onClick={() => setCompareMode('translated')}
            >
              Оригинал ↔ Русский Перевод
            </button>
            <button 
              className={`${styles.sliderBtn} ${compareMode === 'cleaned' ? styles.sliderBtnActive : ''}`}
              onClick={() => setCompareMode('cleaned')}
            >
              Оригинал ↔ 5-Pass Клининг
            </button>
          </div>

          <div 
            className={styles.splitWrapper}
            ref={splitRef}
            onMouseDown={() => setIsDragging(true)}
            onMouseUp={() => setIsDragging(false)}
            onMouseLeave={() => setIsDragging(false)}
            onMouseMove={handleMouseMove}
            onTouchStart={() => setIsDragging(true)}
            onTouchEnd={() => setIsDragging(false)}
            onTouchMove={handleMouseMove}
          >
            {/* Underlay Image (Cleaned or Translated) */}
            <img 
              src={`/manga/${mangaName}/chapter_${chapterNum}/${compareMode === 'translated' ? 'v3_translated' : 'v2_cleaned'}/page_003.webp`}
              alt="Processed Page"
              className={styles.splitImageUnderlay}
            />

            {/* Overlay Image (Original) clipped to slider position */}
            <div 
              className={styles.splitImageOverlay}
              style={{ width: `${sliderPos}%` }}
            >
              <img 
                src={`/manga/${mangaName}/chapter_${chapterNum}/v1_original/page_003.webp`}
                alt="Original Page"
                className={styles.splitOverlayImg}
                style={{ width: splitRef.current ? `${splitRef.current.clientWidth}px` : '720px' }}
              />
            </div>

            {/* Draggable Divider */}
            <div 
              className={styles.splitDivider}
              style={{ left: `${sliderPos}%` }}
            >
              <div className={styles.splitHandle}>
                ◀ ▶
              </div>
            </div>

            <div className={styles.splitLabelLeft}>Оригинал (ENG/RAW)</div>
            <div className={styles.splitLabelRight}>
              {compareMode === 'translated' ? 'Русский Перевод' : '5-Pass Клининг'}
            </div>
          </div>
        </section>

        {/* Results & Actions Bar */}
        <div className={styles.resultsBar}>
          <div className={styles.resultsMeta}>
            <div className={styles.resultsTitle}>Глава {chapterNum}: «{mangaName.replace(/_/g, ' ')}»</div>
            <div className={styles.resultsSub}>Готово к чтению и скачиванию</div>
          </div>
          <div className={styles.resultsBtns}>
            <a 
              href={`http://localhost:8000/api/studio/download/${mangaName}/chapter_${chapterNum}/v3_translated`}
              className={styles.navBtn}
            >
              📥 Скачать архив главы (.ZIP)
            </a>
            <Link 
              href={`/reader/${mangaName}?chapter=chapter_${chapterNum}`}
              className={`${styles.navBtn} ${styles.navBtnPrimary}`}
            >
              📖 Открыть главу в читалке
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
