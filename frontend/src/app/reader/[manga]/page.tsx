'use client';

import React, { useState, useEffect, useCallback, useRef } from 'react';
import Link from 'next/link';
import styles from './page.module.css';

interface ChapterData {
  number: string;
  versions: {
    v1_original?: string[];
    v2_cleaned?: string[];
    v3_translated?: string[];
  };
}

interface MangaApiResponse {
  manga: string;
  chapters: ChapterData[];
}

type LayerVersion = 'v1_original' | 'v2_cleaned' | 'v3_translated';
type WidthPreset = '700px' | '900px' | '1200px' | '100%';
type ReadingMode = 'webtoon' | 'single';

export default function ReaderPage({ params }: { params: Promise<{ manga: string }> }) {
  const unwrappedParams = React.use(params);
  const [data, setData] = useState<MangaApiResponse | null>(null);
  const [loading, setLoading] = useState(true);
  
  // User Preferences
  const [currentVersion, setCurrentVersion] = useState<LayerVersion>('v3_translated');
  const [selectedChapterIdx, setSelectedChapterIdx] = useState(0);
  const [maxWidthPreset, setMaxWidthPreset] = useState<WidthPreset>('900px');
  const [readingMode, setReadingMode] = useState<ReadingMode>('webtoon');
  
  // Single page & Progress state
  const [currentSinglePageIdx, setCurrentSinglePageIdx] = useState(0);
  const [visibleWebtoonPage, setVisibleWebtoonPage] = useState(1);
  const [scrollProgress, setScrollProgress] = useState(0);
  
  const pageRefs = useRef<(HTMLDivElement | null)[]>([]);

  // Load user preferences from localStorage on mount
  useEffect(() => {
    try {
      const savedLayer = localStorage.getItem('manga_reader_layer') as LayerVersion | null;
      if (savedLayer && ['v1_original', 'v2_cleaned', 'v3_translated'].includes(savedLayer)) {
        setCurrentVersion(savedLayer);
      }
      const savedWidth = localStorage.getItem('manga_reader_width') as WidthPreset | null;
      if (savedWidth && ['700px', '900px', '1200px', '100%'].includes(savedWidth)) {
        setMaxWidthPreset(savedWidth);
      }
      const savedMode = localStorage.getItem('manga_reader_mode') as ReadingMode | null;
      if (savedMode && ['webtoon', 'single'].includes(savedMode)) {
        setReadingMode(savedMode);
      }
    } catch (e) {
      console.warn('localStorage not accessible:', e);
    }
  }, []);

  const handleSetVersion = (ver: LayerVersion) => {
    setCurrentVersion(ver);
    try {
      localStorage.setItem('manga_reader_layer', ver);
    } catch {}
  };

  const handleSetWidth = (w: WidthPreset) => {
    setMaxWidthPreset(w);
    try {
      localStorage.setItem('manga_reader_width', w);
    } catch {}
  };

  const handleSetReadingMode = (m: ReadingMode) => {
    setReadingMode(m);
    try {
      localStorage.setItem('manga_reader_mode', m);
    } catch {}
  };

  // Fetch chapter data
  const fetchChapterData = useCallback(async () => {
    try {
      let resData: MangaApiResponse | null = null;
      try {
        const res = await fetch(`/api/chapters/${unwrappedParams.manga}`);
        if (res.ok) {
          const parsed = await res.json();
          if (parsed && parsed.chapters && parsed.chapters.length > 0) {
            resData = parsed;
          }
        }
      } catch (e) {
        console.warn('API route fetch failed, falling back to static index:', e);
      }

      // Fallback to static /manga/chapters_index.json
      if (!resData || !resData.chapters || resData.chapters.length === 0) {
        const indexRes = await fetch('/manga/chapters_index.json');
        if (indexRes.ok) {
          const indexJson = await indexRes.json();
          const cleanManga = unwrappedParams.manga.replace(/ /g, '_');
          const mangaEntry = indexJson.mangas?.[cleanManga] || indexJson.mangas?.['The_Ultimate_of_All_Ages'];
          if (mangaEntry && mangaEntry.chapters) {
            const staticChapters: ChapterData[] = mangaEntry.chapters.map((ch: any) => {
              const chNum = String(ch.chapter);
              const chFolder = ch.folder || `chapter_${chNum}`;
              const count = ch.pages_count || 12;
              const v1: string[] = [];
              const v2: string[] = [];
              const v3: string[] = [];
              for (let i = 1; i <= count; i++) {
                const p = `page_${String(i).padStart(3, '0')}.webp`;
                v1.push(`/manga/${cleanManga}/${chFolder}/v1/${p}`);
                v2.push(`/manga/${cleanManga}/${chFolder}/v2/${p}`);
                v3.push(`/manga/${cleanManga}/${chFolder}/v3/${p}`);
              }
              return {
                number: chNum,
                versions: {
                  v1_original: v1,
                  v2_cleaned: v2,
                  v3_translated: v3,
                }
              };
            });
            resData = {
              manga: cleanManga,
              chapters: staticChapters
            };
          }
        }
      }

      if (resData && resData.chapters) {
        setData(resData);
        setLoading(false);
        if (typeof window !== 'undefined' && resData.chapters.length > 0) {
          const urlParams = new URLSearchParams(window.location.search);
          const chParam = urlParams.get('chapter');
          let foundIdx = -1;
          
          if (chParam) {
            const cleanNum = chParam.replace('chapter_', '');
            foundIdx = resData.chapters.findIndex((c) => c.number === cleanNum);
          }
          
          // Fallback to localStorage
          if (foundIdx === -1) {
            const savedChapter =
              localStorage.getItem(`manga_${unwrappedParams.manga}_last_chapter`) ||
              localStorage.getItem('last_read_chapter');
            if (savedChapter) {
              const cleanSaved = savedChapter.replace('chapter_', '');
              foundIdx = resData.chapters.findIndex((c) => c.number === cleanSaved);
            }
          }
          
          if (foundIdx !== -1) {
            setSelectedChapterIdx(foundIdx);
          } else {
            setSelectedChapterIdx(0);
          }
        }
      } else {
        setLoading(false);
      }
    } catch (err) {
      console.error('Fetch error:', err);
      setLoading(false);
    }
  }, [unwrappedParams.manga]);

  useEffect(() => {
    fetchChapterData();
  }, [fetchChapterData]);

  // Sync selected chapter to URL and localStorage
  useEffect(() => {
    if (typeof window !== 'undefined' && data && data.chapters && data.chapters.length > selectedChapterIdx) {
      const currentChapter = data.chapters[selectedChapterIdx];
      if (currentChapter) {
        const chapterNumber = currentChapter.number;
        const newUrl = `${window.location.pathname}?chapter=chapter_${chapterNumber}`;
        window.history.replaceState({ path: newUrl }, '', newUrl);
        try {
          localStorage.setItem(`manga_${unwrappedParams.manga}_last_chapter`, chapterNumber);
          localStorage.setItem('last_read_chapter', chapterNumber);
        } catch {}
      }
    }
  }, [selectedChapterIdx, data, unwrappedParams.manga]);

  // Chapter Navigation Handlers
  const handlePrevChapter = useCallback(() => {
    if (selectedChapterIdx > 0) {
      setSelectedChapterIdx((prev) => prev - 1);
      setCurrentSinglePageIdx(0);
      setVisibleWebtoonPage(1);
      window.scrollTo({ top: 0, behavior: 'instant' });
    }
  }, [selectedChapterIdx]);

  const handleNextChapter = useCallback(() => {
    if (data && selectedChapterIdx < data.chapters.length - 1) {
      setSelectedChapterIdx((prev) => prev + 1);
      setCurrentSinglePageIdx(0);
      setVisibleWebtoonPage(1);
      window.scrollTo({ top: 0, behavior: 'instant' });
    }
  }, [data, selectedChapterIdx]);

  const handleChapterSelect = (idx: number) => {
    setSelectedChapterIdx(idx);
    setCurrentSinglePageIdx(0);
    setVisibleWebtoonPage(1);
    window.scrollTo({ top: 0, behavior: 'instant' });
  };

  // Current images resolution
  const currentChapter = data?.chapters?.[selectedChapterIdx] || data?.chapters?.[0];
  const requestedImages = currentChapter?.versions?.[currentVersion] || [];
  const images = requestedImages.length > 0 ? requestedImages : (currentChapter?.versions?.v1_original || []);

  // Single Page Navigation Handlers
  const handlePrevSinglePage = useCallback(() => {
    if (currentSinglePageIdx > 0) {
      setCurrentSinglePageIdx((prev) => prev - 1);
      window.scrollTo({ top: 0, behavior: 'instant' });
    } else if (selectedChapterIdx > 0) {
      handlePrevChapter();
    }
  }, [currentSinglePageIdx, selectedChapterIdx, handlePrevChapter]);

  const handleNextSinglePage = useCallback(() => {
    if (currentSinglePageIdx < images.length - 1) {
      setCurrentSinglePageIdx((prev) => prev + 1);
      window.scrollTo({ top: 0, behavior: 'instant' });
    } else if (data && selectedChapterIdx < data.chapters.length - 1) {
      handleNextChapter();
    }
  }, [currentSinglePageIdx, images.length, data, selectedChapterIdx, handleNextChapter]);

  // Scroll Progress Calculation (Webtoon Mode)
  useEffect(() => {
    if (readingMode !== 'webtoon') return;
    
    const handleScroll = () => {
      const scrollHeight = document.documentElement.scrollHeight - window.innerHeight;
      if (scrollHeight <= 0) {
        setScrollProgress(100);
      } else {
        const pct = (window.scrollY / scrollHeight) * 100;
        setScrollProgress(Math.min(100, Math.max(0, pct)));
      }
    };

    window.addEventListener('scroll', handleScroll, { passive: true });
    handleScroll();
    return () => window.removeEventListener('scroll', handleScroll);
  }, [readingMode, data, selectedChapterIdx, currentVersion, images.length]);

  // Progress Calculation (Single Page Mode)
  useEffect(() => {
    if (readingMode === 'single') {
      const total = Math.max(1, images.length);
      const pct = ((currentSinglePageIdx + 1) / total) * 100;
      setScrollProgress(pct);
    }
  }, [readingMode, currentSinglePageIdx, images.length]);

  // Dynamic IntersectionObserver for Webtoon Page Indicator
  useEffect(() => {
    if (readingMode !== 'webtoon' || images.length === 0) return;

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            const pageIndexAttr = entry.target.getAttribute('data-page-index');
            if (pageIndexAttr !== null) {
              const pageIdx = parseInt(pageIndexAttr, 10);
              if (!isNaN(pageIdx)) {
                setVisibleWebtoonPage(pageIdx + 1);
              }
            }
          }
        });
      },
      {
        root: null,
        rootMargin: '-20% 0px -50% 0px',
        threshold: 0.05
      }
    );

    pageRefs.current.forEach((ref) => {
      if (ref) observer.observe(ref);
    });

    return () => observer.disconnect();
  }, [readingMode, images, currentVersion]);

  // Global Keyboard Shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (
        e.target instanceof HTMLInputElement ||
        e.target instanceof HTMLTextAreaElement ||
        e.target instanceof HTMLSelectElement
      ) {
        return;
      }

      // Layer shortcuts: 1, 2, 3
      if (e.key === '1') handleSetVersion('v1_original');
      if (e.key === '2') handleSetVersion('v2_cleaned');
      if (e.key === '3') handleSetVersion('v3_translated');

      // Chapter hotkeys: A, D
      if (e.key === 'a' || e.key === 'A') handlePrevChapter();
      if (e.key === 'd' || e.key === 'D') handleNextChapter();

      // Arrow keys
      if (e.key === 'ArrowLeft') {
        if (readingMode === 'single') {
          handlePrevSinglePage();
        } else {
          handlePrevChapter();
        }
      }
      if (e.key === 'ArrowRight') {
        if (readingMode === 'single') {
          handleNextSinglePage();
        } else {
          handleNextChapter();
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [readingMode, handlePrevChapter, handleNextChapter, handlePrevSinglePage, handleNextSinglePage]);

  if (loading) {
    return (
      <div className={styles.centerContainer}>
        <div className={styles.spinner}></div>
        <p className={styles.loadingText}>Загрузка глав манги...</p>
      </div>
    );
  }

  if (!data || !data.chapters || data.chapters.length === 0) {
    return (
      <div className={styles.centerContainer}>
        <div className={styles.errorCard}>
          <h2>Главы не найдены</h2>
          <p>Манга &quot;{unwrappedParams.manga.replace(/_/g, ' ')}&quot; пока не имеет обработанных глав.</p>
          <Link href="/" className={styles.backBtn}>
            ← Вернуться в каталог
          </Link>
        </div>
      </div>
    );
  }

  const activePageNumber = readingMode === 'single' ? currentSinglePageIdx + 1 : visibleWebtoonPage;
  const totalPages = Math.max(1, images.length);

  return (
    <div className={styles.readerContainer}>
      {/* 3px Top Scroll Progress Bar */}
      <div
        className={styles.topProgressBar}
        style={{ width: `${scrollProgress}%` }}
        aria-hidden="true"
      />

      {/* Sticky Top Header */}
      <header className={styles.readerHeader}>
        <div className={styles.headerLeft}>
          <Link href="/" className={styles.backLink} title="Вернуться в каталог">
            <span className={styles.backIcon}>←</span> В каталог
          </Link>
          <Link href="/studio" className={styles.studioLink} title="Manga AI Studio">
            ⚡ Studio
          </Link>
          <div className={styles.titleInfo}>
            <h1 title={data.manga.replace(/_/g, ' ')}>{data.manga.replace(/_/g, ' ')}</h1>
            <div className={styles.chapterSelectWrapper}>
              <select
                className={styles.chapterSelect}
                value={selectedChapterIdx}
                onChange={(e) => handleChapterSelect(Number(e.target.value))}
                aria-label="Выбор главы"
              >
                {data.chapters.map((ch, idx) => (
                  <option key={idx} value={idx}>
                    Глава {ch.number}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Quick Header Prev / Next Chapter Buttons */}
          <div className={styles.headerNavButtons}>
            <button
              className={styles.navChapterBtn}
              onClick={handlePrevChapter}
              disabled={selectedChapterIdx === 0}
              title="Предыдущая глава (A / ←)"
              aria-label="Предыдущая глава"
            >
              ← Пред
            </button>
            <button
              className={styles.navChapterBtn}
              onClick={handleNextChapter}
              disabled={selectedChapterIdx >= data.chapters.length - 1}
              title="Следующая глава (D / →)"
              aria-label="Следующая глава"
            >
              След →
            </button>
          </div>
        </div>

        {/* Center: Standardized Layer Switcher */}
        <div className={styles.versionSelector} role="radiogroup" aria-label="Переключение слоев">
          <button
            className={currentVersion === 'v1_original' ? styles.activeBtn : styles.btn}
            onClick={() => handleSetVersion('v1_original')}
            title="Горячая клавиша: 1 (Оригинальный скан)"
            role="radio"
            aria-checked={currentVersion === 'v1_original'}
          >
            <span className={styles.btnTag}>1</span> RAW
          </button>
          <button
            className={currentVersion === 'v2_cleaned' ? styles.activeBtn : styles.btn}
            onClick={() => handleSetVersion('v2_cleaned')}
            title="Горячая клавиша: 2 (Клининг баблов)"
            role="radio"
            aria-checked={currentVersion === 'v2_cleaned'}
          >
            <span className={styles.btnTag}>2</span> Clean
          </button>
          <button
            className={currentVersion === 'v3_translated' ? styles.activeBtn : styles.btn}
            onClick={() => handleSetVersion('v3_translated')}
            title="Горячая клавиша: 3 (Смысловой перевод)"
            role="radio"
            aria-checked={currentVersion === 'v3_translated'}
          >
            <span className={styles.btnTag}>3</span> РУС
          </button>
        </div>

        {/* Right: Reading Mode & Width Controls */}
        <div className={styles.headerRight}>
          {/* Dual Reading Mode Switcher */}
          <div className={styles.modeControls} role="group" aria-label="Режим чтения">
            <button
              className={readingMode === 'webtoon' ? styles.activeModeBtn : styles.modeBtn}
              onClick={() => handleSetReadingMode('webtoon')}
              title="Режим вебтуна: непрерывный вертикальный скролл"
            >
              📜 Лента
            </button>
            <button
              className={readingMode === 'single' ? styles.activeModeBtn : styles.modeBtn}
              onClick={() => handleSetReadingMode('single')}
              title="Постраничный режим: перелистывание страниц"
            >
              📄 Постранично
            </button>
          </div>

          {/* 4 Width Presets */}
          <div className={styles.widthControls} role="group" aria-label="Ширина страницы">
            <button
              className={maxWidthPreset === '700px' ? styles.activeWidthBtn : styles.widthBtn}
              onClick={() => handleSetWidth('700px')}
              title="Узкий (700px)"
            >
              700px
            </button>
            <button
              className={maxWidthPreset === '900px' ? styles.activeWidthBtn : styles.widthBtn}
              onClick={() => handleSetWidth('900px')}
              title="Стандарт (900px)"
            >
              900px
            </button>
            <button
              className={maxWidthPreset === '1200px' ? styles.activeWidthBtn : styles.widthBtn}
              onClick={() => handleSetWidth('1200px')}
              title="Широкий (1200px)"
            >
              1200px
            </button>
            <button
              className={maxWidthPreset === '100%' ? styles.activeWidthBtn : styles.widthBtn}
              onClick={() => handleSetWidth('100%')}
              title="На весь экран (100%)"
            >
              100%
            </button>
          </div>
        </div>
      </header>

      {/* Floating Sub-Header / Page Indicator */}
      <div className={styles.subBar}>
        <div className={styles.pageIndicator}>
          <span>
            Страница <strong className={styles.highlightNumber}>{activePageNumber}</strong> из{' '}
            <strong>{totalPages}</strong>
          </span>
        </div>

        {readingMode === 'single' && (
          <div className={styles.singlePageControls}>
            <button
              className={styles.singleNavBtn}
              onClick={handlePrevSinglePage}
              disabled={currentSinglePageIdx === 0 && selectedChapterIdx === 0}
              title="Предыдущая страница (← / Click Left)"
            >
              ◀ Назад
            </button>

            <select
              className={styles.pageJumpSelect}
              value={currentSinglePageIdx}
              onChange={(e) => {
                setCurrentSinglePageIdx(Number(e.target.value));
                window.scrollTo({ top: 0, behavior: 'instant' });
              }}
              aria-label="Перейти на страницу"
            >
              {images.map((_, i) => (
                <option key={i} value={i}>
                  Стр. {i + 1}
                </option>
              ))}
            </select>

            <button
              className={styles.singleNavBtn}
              onClick={handleNextSinglePage}
              disabled={currentSinglePageIdx >= images.length - 1 && selectedChapterIdx >= data.chapters.length - 1}
              title="Следующая страница (→ / Click Right)"
            >
              Вперед ▶
            </button>
          </div>
        )}
      </div>

      {/* Pages Container */}
      <main className={styles.mainContent}>
        <div
          className={styles.mangaPages}
          style={{ maxWidth: maxWidthPreset === '100%' ? '100%' : maxWidthPreset }}
        >
          {images.length === 0 ? (
            <div className={styles.noPagesMessage}>
              <p>В этой версии страницы отсутствуют.</p>
            </div>
          ) : readingMode === 'webtoon' ? (
            /* Webtoon Continuous Scroll Mode */
            images.map((imgUrl, i) => (
              <div
                key={`${currentVersion}-${selectedChapterIdx}-${i}`}
                ref={(el) => {
                  pageRefs.current[i] = el;
                }}
                data-page-index={i}
                className={styles.pageWrapper}
              >
                <div className={styles.pageNumberBadge}>Стр. {i + 1}</div>
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                  src={imgUrl}
                  alt={`Глава ${currentChapter?.number} - Страница ${i + 1}`}
                  className={styles.pageImage}
                  loading={i > 2 ? 'lazy' : 'eager'}
                />
              </div>
            ))
          ) : (
            /* Single Page Flip Mode with Click Zones */
            <div className={styles.singlePageWrapper}>
              {/* Floating Side Arrows */}
              <button
                className={`${styles.sideFloatingBtn} ${styles.sideLeft}`}
                onClick={handlePrevSinglePage}
                disabled={currentSinglePageIdx === 0 && selectedChapterIdx === 0}
                title="Предыдущая страница (←)"
                aria-label="Предыдущая страница"
              >
                ‹
              </button>

              <button
                className={`${styles.sideFloatingBtn} ${styles.sideRight}`}
                onClick={handleNextSinglePage}
                disabled={currentSinglePageIdx >= images.length - 1 && selectedChapterIdx >= data.chapters.length - 1}
                title="Следующая страница (→)"
                aria-label="Следующая страница"
              >
                ›
              </button>

              {/* Click Zones */}
              <div
                className={styles.clickZoneLeft}
                onClick={handlePrevSinglePage}
                title="Нажмите для перехода на предыдущую страницу"
              />
              <div
                className={styles.clickZoneRight}
                onClick={handleNextSinglePage}
                title="Нажмите для перехода на следующую страницу"
              />

              <div className={styles.pageNumberBadge}>
                Стр. {currentSinglePageIdx + 1} / {images.length}
              </div>

              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src={images[currentSinglePageIdx]}
                alt={`Глава ${currentChapter?.number} - Страница ${currentSinglePageIdx + 1}`}
                className={styles.pageImage}
              />
            </div>
          )}
        </div>
      </main>

      {/* Bottom Sticky Bar */}
      <footer className={styles.bottomBar}>
        <div className={styles.chapterNavButtons}>
          <button
            className={styles.navChapterBtn}
            onClick={handlePrevChapter}
            disabled={selectedChapterIdx === 0}
            title="Предыдущая глава (Клавиши: A / ←)"
          >
            ← Пред. глава
          </button>
          <button
            className={styles.navChapterBtn}
            onClick={handleNextChapter}
            disabled={!data || selectedChapterIdx >= data.chapters.length - 1}
            title="Следующая глава (Клавиши: D / →)"
          >
            След. глава →
          </button>
        </div>

        <div className={styles.bottomInfo}>
          <span>
            Глава <strong>{currentChapter?.number}</strong> • {images.length} страниц •{' '}
            <span className={styles.activeVersionText}>
              {currentVersion === 'v1_original' && 'Оригинал (RAW)'}
              {currentVersion === 'v2_cleaned' && 'Клининг (Чистые баблы)'}
              {currentVersion === 'v3_translated' && 'Смысловой перевод (РУС)'}
            </span>{' '}
            • Стр. <strong className={styles.highlightNumber}>{activePageNumber}</strong>/{totalPages}
          </span>
        </div>

        <button
          className={styles.scrollTopBtn}
          onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}
          title="Прокрутить наверх"
        >
          ▲ Наверх
        </button>
      </footer>
    </div>
  );
}
