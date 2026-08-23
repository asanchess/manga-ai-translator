'use client';

import React, { useState, useEffect, useRef, useCallback } from 'react';
import Link from 'next/link';
import styles from './page.module.css';

interface ChapterMeta {
  chapter: string;
  folder?: string;
  pages_count?: number;
  meta_url?: string;
}

interface MangaOption {
  name: string;
  title: string;
  chapters: string[];
  chapters_meta?: ChapterMeta[];
  total_chapters?: number;
}

interface StudioTaskData {
  task_id?: string;
  status: 'idle' | 'connecting' | 'processing' | 'completed' | 'failed' | 'offline';
  current_step?: string;
  stage?: string;
  chapter?: string;
  page?: number;
  total_pages?: number;
  progress?: number;
  logs?: string[];
  zip_url?: string;
  read_url?: string;
  error?: string;
}

type LauncherMode = 'single' | 'batch';

export default function MangaStudioPage() {
  // Option controls
  const [sourceLang, setSourceLang] = useState('auto');
  const [targetLang, setTargetLang] = useState('ru');
  const [detectorMode, setDetectorMode] = useState('CTD');
  const [fontStyle, setFontStyle] = useState('auto');

  // Ingestion & Launcher Modes
  const [launcherMode, setLauncherMode] = useState<LauncherMode>('batch');
  const [activeTab, setActiveTab] = useState<'url' | 'upload'>('upload');

  // Manga Selection & Chapters
  const [availableMangas, setAvailableMangas] = useState<MangaOption[]>([
    {
      name: 'The_Ultimate_of_All_Ages',
      title: 'The Ultimate of All Ages',
      chapters: ['531', '532', '533', '534', '535', '536', '537', '538', '539', '540', '541', '542'],
      total_chapters: 12
    }
  ]);
  const [mangaName, setMangaName] = useState('The_Ultimate_of_All_Ages');
  const [chapterNum, setChapterNum] = useState('531');
  const [startChapter, setStartChapter] = useState('531');
  const [endChapter, setEndChapter] = useState('542');
  const [sourceUrl, setSourceUrl] = useState(
    'https://theultimateofallages.com/manga/the-ultimate-of-all-ages-chapter-531/'
  );

  // Task processing state
  const [taskId, setTaskId] = useState<string | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [taskData, setTaskData] = useState<StudioTaskData | null>(null);

  // Split-Slider comparison state
  const [sliderPos, setSliderPos] = useState(50);
  const [compareMode, setCompareMode] = useState<'translated' | 'cleaned'>('translated');
  const [isDragging, setIsDragging] = useState(false);
  const splitRef = useRef<HTMLDivElement>(null);

  // File & Folder Upload
  const fileInputRef = useRef<HTMLInputElement>(null);
  const folderInputRef = useRef<HTMLInputElement>(null);
  const [uploadedFilesSummary, setUploadedFilesSummary] = useState<string | null>(null);
  const selectedFilesRef = useRef<File[]>([]);

  // Search in Chapter Library
  const [librarySearch, setLibrarySearch] = useState('');

  // Fetch available mangas and chapters
  const loadMangas = useCallback(async () => {
    try {
      const res = await fetch('/api/studio/mangas');
      if (res.ok) {
        const data = await res.json();
        if (data.mangas && Array.isArray(data.mangas) && data.mangas.length > 0) {
          setAvailableMangas(data.mangas);
          // Default range from first manga
          const firstManga = data.mangas.find((m: MangaOption) => m.name === 'The_Ultimate_of_All_Ages') || data.mangas[0];
          if (firstManga && firstManga.chapters.length > 0) {
            setStartChapter(firstManga.chapters[0]);
            setEndChapter(firstManga.chapters[firstManga.chapters.length - 1]);
            setChapterNum(firstManga.chapters[0]);
          }
        }
      }
    } catch (err) {
      console.warn('Could not load manga list:', err);
    }
  }, []);

  useEffect(() => {
    loadMangas();
  }, [loadMangas]);

  // Real-Time SSE Telemetry Stream Connection
  useEffect(() => {
    if (!taskId) return;

    let eventSource: EventSource | null = null;
    let isCancelled = false;

    setTaskData((prev) => ({
      task_id: taskId,
      status: 'connecting',
      current_step: 'Подключение к SSE потоку телеметрии...',
      progress: 5,
      logs: [`[${new Date().toLocaleTimeString()}] Инициализация SSE потока для задачи ${taskId}...`]
    }));

    const streamUrl = `http://localhost:8000/api/pipeline/stream/${taskId}`;

    try {
      eventSource = new EventSource(streamUrl);

      eventSource.onopen = () => {
        if (isCancelled) return;
        setTaskData((prev) => ({
          ...prev,
          task_id: taskId,
          status: 'processing',
          current_step: 'Связь с конвейером установлена (SSE online)'
        }));
      };

      eventSource.onmessage = (event) => {
        if (isCancelled) return;
        try {
          const payload = JSON.parse(event.data);
          setTaskData((prev) => {
            const newLogs = prev?.logs ? [...prev.logs] : [];
            if (payload.log && !newLogs.includes(payload.log)) {
              newLogs.push(`[${new Date().toLocaleTimeString()}] ${payload.log}`);
            }

            const currentStatus =
              payload.status === 'completed'
                ? 'completed'
                : payload.status === 'error' || payload.status === 'failed'
                ? 'failed'
                : 'processing';

            return {
              task_id: taskId,
              status: currentStatus,
              stage: payload.stage || prev?.stage,
              chapter: payload.chapter ? String(payload.chapter) : prev?.chapter,
              page: payload.page || prev?.page,
              total_pages: payload.total_pages || prev?.total_pages,
              progress: typeof payload.progress === 'number' ? payload.progress : prev?.progress || 10,
              current_step:
                payload.log ||
                (payload.chapter && payload.page
                  ? `[Глава ${payload.chapter}] [Стр. ${payload.page}/${payload.total_pages || 12}] -> ${payload.stage || 'Обработка'}`
                  : payload.status === 'completed'
                  ? 'Все этапы успешно завершены'
                  : 'Выполняется конвейер...'),
              logs: newLogs,
              zip_url: payload.zip_url || prev?.zip_url,
              read_url: payload.read_url || prev?.read_url,
              error: payload.error
            };
          });

          if (payload.status === 'completed' || payload.status === 'error' || payload.status === 'failed') {
            setIsProcessing(false);
            eventSource?.close();
          }
        } catch (e) {
          console.warn('SSE parse warning:', e);
        }
      };

      eventSource.onerror = () => {
        if (isCancelled) return;
        // Check if already completed or if connection failed honestly
        eventSource?.close();
        setTaskData((prev) => {
          if (prev?.status === 'completed') return prev;
          return {
            task_id: taskId,
            status: 'offline',
            current_step: 'Сервер обработки недоступен или поток завершен',
            progress: prev?.progress || 0,
            logs: [
              ...(prev?.logs || []),
              `[${new Date().toLocaleTimeString()}] ⚠️ Не удалось подключиться к SSE серверу http://localhost:8000/api/pipeline/stream/${taskId}`
            ],
            error: 'Backend offline: убедитесь, что запущен FastAPI сервер (python backend/server.py или start_service.bat)'
          };
        });
        setIsProcessing(false);
      };
    } catch (e) {
      console.warn('EventSource initialization error:', e);
      setIsProcessing(false);
      setTaskData({
        task_id: taskId,
        status: 'offline',
        current_step: 'Ошибка подключения к серверу',
        logs: [`[${new Date().toLocaleTimeString()}] Исключение при создании EventSource: ${String(e)}`],
        error: String(e)
      });
    }

    return () => {
      isCancelled = true;
      if (eventSource) {
        eventSource.close();
      }
    };
  }, [taskId]);

  // Launch Single Chapter Translation
  const handleStartSingleTranslate = async () => {
    setIsProcessing(true);
    const newTaskId = `task_single_${mangaName}_${chapterNum}_${Date.now()}`;
    setTaskId(newTaskId);
    setTaskData({
      task_id: newTaskId,
      status: 'processing',
      current_step: `Запуск перевода главы ${chapterNum}...`,
      progress: 5,
      logs: [`[${new Date().toLocaleTimeString()}] Запрос на обработку главы ${chapterNum}...`]
    });

    try {
      const res = await fetch('http://localhost:8000/api/studio/translate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          task_id: newTaskId,
          manga_name: mangaName,
          chapter_num: chapterNum,
          source_url: activeTab === 'url' ? sourceUrl : undefined,
          source_lang: sourceLang,
          target_lang: targetLang,
          detector_mode: detectorMode,
          font_style: fontStyle
        })
      });

      if (res.ok) {
        const json = await res.json();
        if (json.task_id && json.task_id !== newTaskId) {
          setTaskId(json.task_id);
        }
      }
    } catch (err) {
      console.warn('Backend single launch warning:', err);
      // Let SSE effect detect offline status honestly
    }
  };

  // Launch Batch Range Translation
  const handleStartBatchTranslate = async () => {
    setIsProcessing(true);
    const newTaskId = `task_batch_${mangaName}_${startChapter}_${endChapter}_${Date.now()}`;
    setTaskId(newTaskId);
    setTaskData({
      task_id: newTaskId,
      status: 'processing',
      current_step: `Запуск пакетного перевода глав [${startChapter}–${endChapter}]...`,
      progress: 5,
      logs: [
        `[${new Date().toLocaleTimeString()}] Инициализация пакетной обработки глав с ${startChapter} по ${endChapter}...`,
        `[${new Date().toLocaleTimeString()}] Конфигурация: ${detectorMode} OCR | Failover LLM -> ${targetLang.toUpperCase()} | Font: ${fontStyle}`
      ]
    });

    try {
      const res = await fetch('http://localhost:8000/api/studio/batch', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          task_id: newTaskId,
          manga_name: mangaName,
          start_chapter: startChapter,
          end_chapter: endChapter,
          source_lang: sourceLang,
          target_lang: targetLang,
          detector_mode: detectorMode,
          font_style: fontStyle
        })
      });

      if (res.ok) {
        const json = await res.json();
        if (json.task_id && json.task_id !== newTaskId) {
          setTaskId(json.task_id);
        }
      }
    } catch (err) {
      console.warn('Backend batch launch warning:', err);
      // Let SSE effect detect offline status honestly
    }
  };

  // File & Folder Drop / Ingestion Handlers
  const handleProcessUploadedFiles = async (files: FileList | File[]) => {
    const fileList = Array.from(files);
    if (fileList.length === 0) return;

    selectedFilesRef.current = fileList;
    const totalSizeMb = (fileList.reduce((acc, f) => acc + f.size, 0) / (1024 * 1024)).toFixed(1);
    setUploadedFilesSummary(`${fileList.length} файлов (${totalSizeMb} MB): ${fileList[0].name}${fileList.length > 1 ? ' и др.' : ''}`);

    const newTaskId = `task_upload_${mangaName}_${chapterNum}_${Date.now()}`;
    setTaskId(newTaskId);
    setIsProcessing(true);
    setTaskData({
      task_id: newTaskId,
      status: 'processing',
      current_step: `Загрузка ${fileList.length} файлов на сервер...`,
      progress: 10,
      logs: [`[${new Date().toLocaleTimeString()}] Загрузка ${fileList.length} файлов (${totalSizeMb} MB)...`]
    });

    const formData = new FormData();
    formData.append('task_id', newTaskId);
    formData.append('manga_name', mangaName);
    formData.append('chapter_num', chapterNum);
    formData.append('auto_start', 'true');
    formData.append('detector_mode', detectorMode);
    formData.append('target_lang', targetLang);
    fileList.forEach((f) => formData.append('files', f));

    try {
      const res = await fetch('http://localhost:8000/api/studio/upload', {
        method: 'POST',
        body: formData
      });
      if (res.ok) {
        const json = await res.json();
        if (json.task_id && json.task_id !== newTaskId) {
          setTaskId(json.task_id);
        }
      }
    } catch (err) {
      console.warn('Upload network warning:', err);
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

  const currentMangaObj = availableMangas.find((m) => m.name === mangaName) || availableMangas[0];
  const chaptersList = currentMangaObj?.chapters || ['531', '532', '533', '534', '535', '536', '537', '538', '539', '540', '541', '542'];

  const filteredChapters = chaptersList.filter((ch) =>
    librarySearch ? ch.includes(librarySearch) || `глава ${ch}`.toLowerCase().includes(librarySearch.toLowerCase()) : true
  );

  return (
    <div className={styles.container}>
      {/* Header */}
      <header className={styles.header}>
        <Link href="/" className={styles.logoArea}>
          <div className={styles.logoIcon}>⚡</div>
          <div>
            <div className={styles.logoTitle}>Manga AI Translator Studio</div>
            <div className={styles.logoSub}>SOTA Turnkey Autonomous Pipeline v4.0</div>
          </div>
        </Link>
        <div className={styles.navActions}>
          <Link href={`/reader/${mangaName}?chapter=chapter_${chapterNum}`} className={styles.navBtn}>
            📖 Открыть Ридер
          </Link>
          <a href="http://localhost:8000/docs" target="_blank" rel="noreferrer" className={styles.navBtn}>
            ⚙️ FastAPI Docs
          </a>
        </div>
      </header>

      {/* Hero Section */}
      <section className={styles.hero}>
        <div className={styles.badgeRow}>
          <span className={`${styles.badge} ${styles.badgeGreen}`}>● Автономный Пайплайн</span>
          <span className={`${styles.badge} ${styles.badgePurple}`}>⚡ Anti-Patch Telea Inpaint</span>
          <span className={`${styles.badge} ${styles.badgeBlue}`}>🤖 Zero-Leak LLM Cascade</span>
          <span className={styles.badge}>📦 SOTA Russian ZIP Release</span>
        </div>
        <h1 className={styles.heroTitle}>
          Студия <span className={styles.gradientText}>Пакетного ИИ-Перевода</span> Манги
        </h1>
        <p className={styles.heroSub}>
          Автоматическое 2-проходное распознавание баблов (светлые + инвертированные темные), чистый Telea Inpainting без прямоугольных заплат и математический тайпсеттинг.
        </p>
      </section>

      {/* Main Workspace */}
      <div className={styles.workspace}>
        {/* Top Options Card */}
        <div className={styles.optionsCard}>
          <div className={styles.optionItem}>
            <label className={styles.optionLabel}>Тайтл манги</label>
            <select
              className={styles.selectInput}
              value={mangaName}
              onChange={(e) => {
                const selected = e.target.value;
                setMangaName(selected);
                const obj = availableMangas.find((m) => m.name === selected);
                if (obj && obj.chapters.length > 0) {
                  setStartChapter(obj.chapters[0]);
                  setEndChapter(obj.chapters[obj.chapters.length - 1]);
                  setChapterNum(obj.chapters[0]);
                }
              }}
            >
              {availableMangas.map((m) => (
                <option key={m.name} value={m.name}>
                  {m.title || m.name.replace(/_/g, ' ')}
                </option>
              ))}
            </select>
          </div>

          <div className={styles.optionItem}>
            <label className={styles.optionLabel}>Исходный язык</label>
            <select className={styles.selectInput} value={sourceLang} onChange={(e) => setSourceLang(e.target.value)}>
              <option value="auto">🌐 Автоопределение (Auto)</option>
              <option value="en">Английский (English)</option>
              <option value="zh">Китайский (中文)</option>
              <option value="ja">Японский (日本語)</option>
              <option value="ko">Корейский (한국어)</option>
            </select>
          </div>

          <div className={styles.optionItem}>
            <label className={styles.optionLabel}>Целевой язык</label>
            <select className={styles.selectInput} value={targetLang} onChange={(e) => setTargetLang(e.target.value)}>
              <option value="ru">🇷🇺 Русский (Russian)</option>
              <option value="en">🇬🇧 Английский (English)</option>
            </select>
          </div>

          <div className={styles.optionItem}>
            <label className={styles.optionLabel}>Модель OCR & Клининга</label>
            <select className={styles.selectInput} value={detectorMode} onChange={(e) => setDetectorMode(e.target.value)}>
              <option value="CTD">Comic Text Detector + Telea Inpaint (SOTA)</option>
              <option value="EagleEye">EagleEye 2-Pass (Inverted Bubble Guard)</option>
              <option value="Hybrid">Hybrid Deep Inpainter</option>
            </select>
          </div>

          <div className={styles.optionItem}>
            <label className={styles.optionLabel}>Кириллический шрифт</label>
            <select className={styles.selectInput} value={fontStyle} onChange={(e) => setFontStyle(e.target.value)}>
              <option value="auto">Auto (Comicbd / SegoeUI / Arial)</option>
              <option value="comicbd">Comicbd Bold (Классика манги)</option>
              <option value="segoeuib">Segoe UI Bold (Культивация / Вебтун)</option>
              <option value="arialbd">Arial Bold (Нейтральный)</option>
            </select>
          </div>
        </div>

        {/* Launcher Mode Selector: Single vs Batch Range */}
        <div className={styles.launcherModeCard}>
          <div className={styles.launcherModeHeader}>
            <span className={styles.launcherModeTitle}>Режим запуска перевода</span>
            <div className={styles.modeToggleGroup}>
              <button
                className={`${styles.modeToggleBtn} ${launcherMode === 'batch' ? styles.modeToggleActive : ''}`}
                onClick={() => setLauncherMode('batch')}
              >
                🚀 Пакетный диапазон ({startChapter}–{endChapter})
              </button>
              <button
                className={`${styles.modeToggleBtn} ${launcherMode === 'single' ? styles.modeToggleActive : ''}`}
                onClick={() => setLauncherMode('single')}
              >
                📄 Одиночная глава
              </button>
            </div>
          </div>

          {launcherMode === 'batch' ? (
            <div className={styles.batchControlsGrid}>
              <div className={styles.batchInputCol}>
                <label className={styles.optionLabel}>Начальная глава</label>
                <input
                  type="text"
                  className={styles.textInput}
                  value={startChapter}
                  onChange={(e) => setStartChapter(e.target.value)}
                  placeholder="531"
                />
              </div>

              <div className={styles.batchInputCol}>
                <label className={styles.optionLabel}>Конечная глава</label>
                <input
                  type="text"
                  className={styles.textInput}
                  value={endChapter}
                  onChange={(e) => setEndChapter(e.target.value)}
                  placeholder="542"
                />
              </div>

              <div className={styles.batchActionCol}>
                <button
                  className={styles.btnPrimaryLarge}
                  onClick={handleStartBatchTranslate}
                  disabled={isProcessing}
                >
                  {isProcessing ? '⏳ Выполняется пакетный перевод...' : `🚀 Запустить пакетный перевод [${startChapter}–${endChapter}]`}
                </button>
              </div>
            </div>
          ) : (
            <div className={styles.singleControlsGrid}>
              <div className={styles.singleInputCol}>
                <label className={styles.optionLabel}>Выберите или введите номер главы</label>
                <div className={styles.singleInputRow}>
                  <select
                    className={styles.selectInput}
                    value={chapterNum}
                    onChange={(e) => setChapterNum(e.target.value)}
                  >
                    {chaptersList.map((ch) => (
                      <option key={ch} value={ch}>
                        Глава {ch}
                      </option>
                    ))}
                  </select>
                  <input
                    type="text"
                    className={styles.textInput}
                    value={chapterNum}
                    onChange={(e) => setChapterNum(e.target.value)}
                    placeholder="531"
                    style={{ maxWidth: '120px' }}
                  />
                </div>
              </div>

              <div className={styles.singleActionCol}>
                <button
                  className={styles.btnPrimaryLarge}
                  onClick={handleStartSingleTranslate}
                  disabled={isProcessing}
                >
                  {isProcessing ? '⏳ Обработка главы...' : `🚀 Сканировать и Перевести главу ${chapterNum}`}
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Ingestion Tabs */}
        <div className={styles.tabsContainer}>
          <button
            className={`${styles.tabBtn} ${activeTab === 'upload' ? styles.tabBtnActive : ''}`}
            onClick={() => setActiveTab('upload')}
          >
            📁 Загрузка файлов / Папок со сканами / .ZIP
          </button>
          <button
            className={`${styles.tabBtn} ${activeTab === 'url' ? styles.tabBtnActive : ''}`}
            onClick={() => setActiveTab('url')}
          >
            🔗 Импорт по прямой ссылке (URL)
          </button>
        </div>

        {/* Ingestion Panel */}
        <div className={styles.panelCard}>
          {activeTab === 'upload' ? (
            <div className={styles.uploadArea}>
              <div
                className={styles.uploadDropzone}
                onClick={() => fileInputRef.current?.click()}
                onDragOver={(e) => e.preventDefault()}
                onDrop={(e) => {
                  e.preventDefault();
                  if (e.dataTransfer.files) {
                    handleProcessUploadedFiles(e.dataTransfer.files);
                  }
                }}
              >
                {/* File picker */}
                <input
                  type="file"
                  ref={fileInputRef}
                  multiple
                  accept="image/*,.zip,.cbz"
                  style={{ display: 'none' }}
                  onChange={(e) => {
                    if (e.target.files) handleProcessUploadedFiles(e.target.files);
                  }}
                />

                {/* Folder picker (webkitdirectory) */}
                <input
                  type="file"
                  ref={folderInputRef}
                  // @ts-expect-error webkitdirectory is standard in Chromium browsers
                  webkitdirectory="true"
                  directory="true"
                  multiple
                  style={{ display: 'none' }}
                  onChange={(e) => {
                    if (e.target.files) handleProcessUploadedFiles(e.target.files);
                  }}
                />

                <div className={styles.uploadIcon}>📥</div>
                <div className={styles.uploadTitle}>
                  Перетащите сюда страницы главы (.WebP, .PNG, .JPG), архив .ZIP/.CBZ или папку со сканами
                </div>
                <div className={styles.uploadSub}>
                  Автоматический Anti-Patch клининг, распознавание баблов и перевод запустятся сразу
                </div>

                <div className={styles.uploadButtonsRow} onClick={(e) => e.stopPropagation()}>
                  <button
                    className={styles.uploadActionBtn}
                    onClick={() => fileInputRef.current?.click()}
                  >
                    📄 Выбрать файлы / .ZIP
                  </button>
                  <button
                    className={styles.uploadActionBtn}
                    onClick={() => folderInputRef.current?.click()}
                  >
                    📁 Выбрать целую папку главы
                  </button>
                </div>

                {uploadedFilesSummary && (
                  <div className={styles.uploadSummaryBadge}>
                    ✅ Выбрано: {uploadedFilesSummary}
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div className={styles.urlForm}>
              <div className={styles.inputGrid}>
                <div>
                  <label className={styles.optionLabel}>Ссылка на главу манги / вебтуна</label>
                  <input
                    type="text"
                    className={styles.textInput}
                    placeholder="https://theultimateofallages.com/manga/...-chapter-531/"
                    value={sourceUrl}
                    onChange={(e) => setSourceUrl(e.target.value)}
                  />
                </div>
                <div>
                  <label className={styles.optionLabel}>Номер целевой главы</label>
                  <input
                    type="text"
                    className={styles.textInput}
                    placeholder="531"
                    value={chapterNum}
                    onChange={(e) => setChapterNum(e.target.value)}
                  />
                </div>
              </div>
              <div className={styles.actionBtnRow}>
                <button
                  className={styles.btnPrimaryLarge}
                  onClick={handleStartSingleTranslate}
                  disabled={isProcessing}
                >
                  {isProcessing ? '⏳ Обработка главы...' : '🚀 Сканировать и Перевести в 1 Клик'}
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Real-Time SSE Telemetry Progress Visualizer */}
        {(isProcessing || taskData) && (
          <div className={`${styles.progressCard} ${taskData?.status === 'offline' ? styles.progressCardOffline : ''}`}>
            <div className={styles.progressHeader}>
              <div className={styles.progressTitle}>
                <span className={styles.pulseDot} />
                <span>Телеметрия конвейера: {taskData?.current_step || 'Инициализация...'}</span>
              </div>
              <div className={styles.progressPercent}>{taskData?.progress || 0}%</div>
            </div>

            {/* 5-Stage Visualizer Pipeline */}
            <div className={styles.stagesPipeline}>
              <div
                className={`${styles.stageStep} ${
                  (taskData?.progress || 0) >= 15 ? styles.stageStepActive : ''
                }`}
              >
                <div className={styles.stageNum}>1</div>
                <div className={styles.stageName}>2-Pass OCR</div>
              </div>
              <div className={styles.stageArrow}>→</div>
              <div
                className={`${styles.stageStep} ${
                  (taskData?.progress || 0) >= 40 ? styles.stageStepActive : ''
                }`}
              >
                <div className={styles.stageNum}>2</div>
                <div className={styles.stageName}>Telea Inpaint</div>
              </div>
              <div className={styles.stageArrow}>→</div>
              <div
                className={`${styles.stageStep} ${
                  (taskData?.progress || 0) >= 65 ? styles.stageStepActive : ''
                }`}
              >
                <div className={styles.stageNum}>3</div>
                <div className={styles.stageName}>LLM Cascade</div>
              </div>
              <div className={styles.stageArrow}>→</div>
              <div
                className={`${styles.stageStep} ${
                  (taskData?.progress || 0) >= 85 ? styles.stageStepActive : ''
                }`}
              >
                <div className={styles.stageNum}>4</div>
                <div className={styles.stageName}>Typeset Engine</div>
              </div>
              <div className={styles.stageArrow}>→</div>
              <div
                className={`${styles.stageStep} ${
                  (taskData?.progress || 0) >= 100 ? styles.stageStepActive : ''
                }`}
              >
                <div className={styles.stageNum}>5</div>
                <div className={styles.stageName}>ZIP Packaging</div>
              </div>
            </div>

            {/* Progress Bar */}
            <div className={styles.progressBarTrack}>
              <div className={styles.progressBarFill} style={{ width: `${taskData?.progress || 0}%` }} />
            </div>

            {/* Diagnostics Banner on offline / error */}
            {taskData?.status === 'offline' && (
              <div className={styles.offlineBanner}>
                <div className={styles.offlineIcon}>⚠️</div>
                <div className={styles.offlineText}>
                  <strong>Сервер обработки FastAPI оффлайн</strong> (http://localhost:8000). Запустите{' '}
                  <code>start_service.bat</code> или <code>python backend/server.py</code>, чтобы активировать локальный
                  ML конвейер.
                </div>
                <button
                  className={styles.retryBtn}
                  onClick={() => {
                    if (launcherMode === 'batch') handleStartBatchTranslate();
                    else handleStartSingleTranslate();
                  }}
                >
                  🔄 Повторить попытку
                </button>
              </div>
            )}

            {/* Live SSE Log Output */}
            <div className={styles.logBox}>
              {taskData?.logs && taskData.logs.length > 0 ? (
                taskData.logs.map((log: string, i: number) => (
                  <div key={i} className={styles.logLine}>
                    {log}
                  </div>
                ))
              ) : (
                <div className={styles.logLine}>[Ожидание первого события SSE...]</div>
              )}
            </div>

            {/* Quick Completion Action Links */}
            {taskData?.status === 'completed' && (
              <div className={styles.completedActions}>
                <span className={styles.completedBadge}>🎉 Все главы успешно обработаны!</span>
                <div className={styles.completedBtns}>
                  <Link
                    href={`/reader/${mangaName}?chapter=chapter_${taskData.chapter || chapterNum}`}
                    className={styles.btnPrimarySmall}
                  >
                    📖 Открыть в читалке
                  </Link>
                  <a
                    href={`/manga/${mangaName}/chapter_${taskData.chapter || chapterNum}/${mangaName}_Chapter_${
                      taskData.chapter || chapterNum
                    }_Russian.zip`}
                    download
                    className={styles.btnSecondarySmall}
                  >
                    📥 Скачать Russian ZIP
                  </a>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Interactive Chapter Library Grid */}
        <section className={styles.librarySection}>
          <div className={styles.libraryHeader}>
            <div>
              <h2 className={styles.libraryTitle}>📚 Библиотека Глав Тайтла</h2>
              <p className={styles.librarySub}>
                Всего доступно <strong>{chaptersList.length}</strong> глав. Скачивайте русские релизы .ZIP или открывайте в читалке.
              </p>
            </div>
            <div className={styles.librarySearchBox}>
              <input
                type="text"
                placeholder="🔍 Поиск по номеру главы..."
                className={styles.searchInput}
                value={librarySearch}
                onChange={(e) => setLibrarySearch(e.target.value)}
              />
            </div>
          </div>

          <div className={styles.chapterGrid}>
            {filteredChapters.map((ch) => {
              const zipFilename = `${mangaName}_Chapter_${ch}_Russian.zip`;
              const zipPath = `/manga/${mangaName}/chapter_${ch}/${zipFilename}`;
              const backendZipPath = `http://localhost:8000/api/studio/download/${mangaName}/chapter_${ch}/v3`;

              return (
                <div key={ch} className={styles.chapterCard}>
                  <div className={styles.chapterCardTop}>
                    <div className={styles.chapterCardBadge}>Глава {ch}</div>
                    <div className={styles.layerIndicators}>
                      <span className={styles.layerBadgeRaw} title="Оригинальный скан (RAW)">v1 RAW</span>
                      <span className={styles.layerBadgeClean} title="Клининг баблов (Telea)">v2 Clean</span>
                      <span className={styles.layerBadgeRus} title="Русский перевод и тайпсеттинг">v3 РУС</span>
                    </div>
                  </div>

                  <div className={styles.chapterCardMeta}>
                    <span className={styles.pagesCountText}>📄 8–14 страниц</span>
                    <span className={styles.formatText}>WebP HD • ZIP готов</span>
                  </div>

                  <div className={styles.chapterCardActions}>
                    <Link
                      href={`/reader/${mangaName}?chapter=chapter_${ch}`}
                      className={styles.cardReadBtn}
                    >
                      📖 Читать
                    </Link>
                    <a
                      href={zipPath}
                      download={zipFilename}
                      className={styles.cardZipBtn}
                      title={`Скачать архив главы ${ch} (.ZIP)`}
                      onClick={() => {
                        fetch(zipPath, { method: 'HEAD' }).then((res) => {
                          if (!res.ok) window.open(backendZipPath, '_blank');
                        });
                      }}
                    >
                      📥 .ZIP
                    </a>
                  </div>
                </div>
              );
            })}
          </div>
        </section>

        {/* Interactive Split-Slider Comparison */}
        <section className={styles.comparisonSection}>
          <div className={styles.sectionTitle}>
            <span>✨ Интерактивное сравнение слоев (RAW vs Клининг vs Перевод)</span>
          </div>
          <p className={styles.sectionSub}>
            Потяните ползунок влево и вправо, чтобы сравнить качество Anti-Patch клининга и литературного перевода диалогов с оригиналом:
          </p>

          <div className={styles.sliderControls}>
            <button
              className={`${styles.sliderBtn} ${compareMode === 'translated' ? styles.sliderBtnActive : ''}`}
              onClick={() => setCompareMode('translated')}
            >
              Оригинал (v1) ↔ Русский Перевод (v3)
            </button>
            <button
              className={`${styles.sliderBtn} ${compareMode === 'cleaned' ? styles.sliderBtnActive : ''}`}
              onClick={() => setCompareMode('cleaned')}
            >
              Оригинал (v1) ↔ Чистый Клининг (v2)
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
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src={`/manga/${mangaName}/chapter_${chapterNum}/${compareMode === 'translated' ? 'v3_translated' : 'v2_cleaned'}/page_003.webp`}
              alt="Processed Page"
              className={styles.splitImageUnderlay}
              onError={(e) => {
                const target = e.currentTarget;
                if (!target.src.includes('page_001')) {
                  target.src = `/manga/${mangaName}/chapter_${chapterNum}/${compareMode === 'translated' ? 'v3' : 'v2'}/page_001.webp`;
                }
              }}
            />

            {/* Overlay Image (Original) clipped to slider position */}
            <div className={styles.splitImageOverlay} style={{ width: `${sliderPos}%` }}>
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src={`/manga/${mangaName}/chapter_${chapterNum}/v1_original/page_003.webp`}
                alt="Original Page"
                className={styles.splitOverlayImg}
                style={{ width: splitRef.current ? `${splitRef.current.clientWidth}px` : '720px' }}
                onError={(e) => {
                  const target = e.currentTarget;
                  if (!target.src.includes('page_001')) {
                    target.src = `/manga/${mangaName}/chapter_${chapterNum}/v1/page_001.webp`;
                  }
                }}
              />
            </div>

            {/* Draggable Divider */}
            <div className={styles.splitDivider} style={{ left: `${sliderPos}%` }}>
              <div className={styles.splitHandle}>◀ ▶</div>
            </div>

            <div className={styles.splitLabelLeft}>Оригинал (RAW)</div>
            <div className={styles.splitLabelRight}>
              {compareMode === 'translated' ? 'Русский Перевод (v3)' : 'Telea Клининг (v2)'}
            </div>
          </div>
        </section>

        {/* Results & Actions Bar */}
        <div className={styles.resultsBar}>
          <div className={styles.resultsMeta}>
            <div className={styles.resultsTitle}>
              Глава {chapterNum}: «{mangaName.replace(/_/g, ' ')}»
            </div>
            <div className={styles.resultsSub}>Релиз готов к чтению и мгновенному скачиванию</div>
          </div>
          <div className={styles.resultsBtns}>
            <a
              href={`/manga/${mangaName}/chapter_${chapterNum}/${mangaName}_Chapter_${chapterNum}_Russian.zip`}
              download={`${mangaName}_Chapter_${chapterNum}_Russian.zip`}
              className={styles.navBtn}
              onClick={() => {
                fetch(`/manga/${mangaName}/chapter_${chapterNum}/${mangaName}_Chapter_${chapterNum}_Russian.zip`, { method: 'HEAD' }).then((res) => {
                  if (!res.ok) window.open(`http://localhost:8000/api/studio/download/${mangaName}/chapter_${chapterNum}/v3`, '_blank');
                });
              }}
            >
              📥 Скачать релиз .ZIP
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
