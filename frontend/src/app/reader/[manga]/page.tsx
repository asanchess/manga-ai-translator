'use client';
import React, { useState, useEffect, useCallback } from 'react';
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

interface PipelineState {
  status: 'idle' | 'running' | 'completed' | 'error';
  current_agent: string;
  progress: number;
  current_page: number;
  total_pages: number;
  logs: string[];
}

export default function ReaderPage({ params }: { params: Promise<{ manga: string }> }) {
  const unwrappedParams = React.use(params);
  const [data, setData] = useState<MangaApiResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [currentVersion, setCurrentVersion] = useState<'v1_original' | 'v2_cleaned' | 'v3_translated'>('v3_translated');
  const [selectedChapterIdx, setSelectedChapterIdx] = useState(0);
  const [maxWidth, setMaxWidth] = useState<'narrow' | 'medium' | 'wide'>('medium');
  
  // Pipeline State
  const [pipeline, setPipeline] = useState<PipelineState>({
    status: 'idle',
    current_agent: '',
    progress: 0,
    current_page: 0,
    total_pages: 0,
    logs: []
  });
  const [showLogs, setShowLogs] = useState(false);

  const fetchChapterData = useCallback(() => {
    fetch(`/api/chapters/${unwrappedParams.manga}`)
      .then((res) => res.json())
      .then((resData: MangaApiResponse) => {
        setData(resData);
        setLoading(false);
        if (typeof window !== 'undefined') {
          const urlParams = new URLSearchParams(window.location.search);
          const chParam = urlParams.get('chapter');
          if (chParam && resData.chapters) {
            const cleanNum = chParam.replace('chapter_', '');
            const foundIdx = resData.chapters.findIndex(c => c.number === cleanNum);
            if (foundIdx !== -1) {
              setSelectedChapterIdx(foundIdx);
            }
          }
        }
      })
      .catch((err) => {
        console.error('Fetch error:', err);
        setLoading(false);
      });
  }, [unwrappedParams.manga]);

  useEffect(() => {
    fetchChapterData();
  }, [fetchChapterData]);

  // Polling pipeline status
  useEffect(() => {
    let interval: NodeJS.Timeout | null = null;
    if (pipeline.status === 'running') {
      interval = setInterval(() => {
        fetch('/api/pipeline/status')
          .then((res) => res.json())
          .then((pState: PipelineState) => {
            setPipeline(pState);
            if (pState.status === 'completed') {
              fetchChapterData();
            }
          })
          .catch((err) => console.error('Status poll error:', err));
      }, 1200);
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [pipeline.status, fetchChapterData]);

  const handleRunPipeline = async () => {
    const currentChapter = data?.chapters[selectedChapterIdx];
    const chapterNum = currentChapter ? currentChapter.number : '531';
    
    setPipeline((prev) => ({
      ...prev,
      status: 'running',
      progress: 5,
      current_agent: 'Initializing',
      logs: ['[00:00:00] Запрос на запуск 5-агентного конвейера отправлен...']
    }));

    try {
      await fetch('/api/pipeline/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          manga: unwrappedParams.manga,
          chapter: chapterNum
        })
      });
    } catch (e) {
      console.error('Failed to trigger pipeline:', e);
    }
  };

  const handlePrevChapter = useCallback(() => {
    if (selectedChapterIdx > 0) {
      setSelectedChapterIdx(selectedChapterIdx - 1);
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }
  }, [selectedChapterIdx]);

  const handleNextChapter = useCallback(() => {
    if (data && selectedChapterIdx < data.chapters.length - 1) {
      setSelectedChapterIdx(selectedChapterIdx + 1);
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }
  }, [data, selectedChapterIdx]);

  // Keyboard shortcut support (1 = Original, 2 = Cleaned, 3 = Translated, ArrowLeft/Right = Chapters)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement || e.target instanceof HTMLSelectElement) {
        return;
      }
      if (e.key === '1') setCurrentVersion('v1_original');
      if (e.key === '2') setCurrentVersion('v2_cleaned');
      if (e.key === '3') setCurrentVersion('v3_translated');
      if (e.key === 'ArrowLeft' || e.key === 'a' || e.key === 'A') handlePrevChapter();
      if (e.key === 'ArrowRight' || e.key === 'd' || e.key === 'D') handleNextChapter();
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [handlePrevChapter, handleNextChapter]);

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

  const currentChapter = data.chapters[selectedChapterIdx] || data.chapters[0];
  const requestedImages = currentChapter.versions[currentVersion] || [];
  const images = requestedImages.length > 0 ? requestedImages : (currentChapter.versions.v1_original || []);

  return (
    <div className={styles.readerContainer}>
      {/* Sticky Top Header */}
      <header className={styles.readerHeader}>
        <div className={styles.headerLeft}>
          <Link href="/" className={styles.backLink} title="В каталог">
            <span className={styles.backIcon}>←</span> Каталог
          </Link>
          <Link href="/studio" className={styles.backLink} style={{ color: '#38bdf8' }} title="Manga AI Studio">
            ⚡ Studio
          </Link>
          <div className={styles.titleInfo}>
            <h1>{data.manga.replace(/_/g, ' ')}</h1>
            <div className={styles.chapterSelectWrapper}>
              <select
                className={styles.chapterSelect}
                value={selectedChapterIdx}
                onChange={(e) => setSelectedChapterIdx(Number(e.target.value))}
              >
                {data.chapters.map((ch, idx) => (
                  <option key={idx} value={idx}>
                    Глава {ch.number}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </div>

        {/* Version Switcher */}
        <div className={styles.versionSelector}>
          <button
            className={currentVersion === 'v1_original' ? styles.activeBtn : styles.btn}
            onClick={() => setCurrentVersion('v1_original')}
            title="Горячая клавиша: 1"
          >
            <span className={styles.btnTag}>1</span> Оригинал
          </button>
          <button
            className={currentVersion === 'v2_cleaned' ? styles.activeBtn : styles.btn}
            onClick={() => setCurrentVersion('v2_cleaned')}
            title="Горячая клавиша: 2"
          >
            <span className={styles.btnTag}>2</span> Клининг
          </button>
          <button
            className={currentVersion === 'v3_translated' ? styles.activeBtn : styles.btn}
            onClick={() => setCurrentVersion('v3_translated')}
            title="Горячая клавиша: 3"
          >
            <span className={styles.btnTag}>3</span> Перевод (РУС)
          </button>
        </div>

        {/* Width Controls */}
        <div className={styles.headerRight}>
          <div className={styles.widthControls}>
            <button
              className={maxWidth === 'narrow' ? styles.activeWidthBtn : styles.widthBtn}
              onClick={() => setMaxWidth('narrow')}
              title="700px"
            >
              S
            </button>
            <button
              className={maxWidth === 'medium' ? styles.activeWidthBtn : styles.widthBtn}
              onClick={() => setMaxWidth('medium')}
              title="850px"
            >
              M
            </button>
            <button
              className={maxWidth === 'wide' ? styles.activeWidthBtn : styles.widthBtn}
              onClick={() => setMaxWidth('wide')}
              title="100% Full"
            >
              L
            </button>
          </div>
        </div>
      </header>

      {/* Agent Mission Control Banner */}
      <section className={styles.missionControl}>
        <div className={styles.controlTop}>
          <div className={styles.agentCards}>
            <div className={`${styles.agentBadge} ${pipeline.status === 'completed' ? styles.done : (pipeline.current_agent.includes('Asset') ? styles.active : '')}`}>
              📥 Scraper
            </div>
            <div className={`${styles.agentBadge} ${pipeline.status === 'completed' ? styles.done : (pipeline.current_agent.includes('Cleaner') ? styles.active : '')}`}>
              🧹 5-Pass Cleaner
            </div>
            <div className={`${styles.agentBadge} ${pipeline.status === 'completed' ? styles.done : (pipeline.current_agent.includes('LLM') ? styles.active : '')}`}>
              🤖 OpenRouter LLM
            </div>
            <div className={`${styles.agentBadge} ${pipeline.status === 'completed' ? styles.done : (pipeline.current_agent.includes('Typesetter') ? styles.active : '')}`}>
              ✍️ Pro Typesetter
            </div>
            <div className={`${styles.agentBadge} ${pipeline.status === 'completed' ? styles.done : (pipeline.current_agent.includes('QA') ? styles.active : '')}`}>
              🛡️ QA Inspector
            </div>
          </div>

          <div className={styles.controlActions}>
            <button
              className={styles.triggerBtn}
              onClick={handleRunPipeline}
              disabled={pipeline.status === 'running'}
            >
              {pipeline.status === 'running' ? (
                <>⏳ Обработка ({pipeline.progress}%)</>
              ) : (
                <>⚡ Запустить автоперевод главы {currentChapter.number}</>
              )}
            </button>
            <button
              className={styles.toggleLogBtn}
              onClick={() => setShowLogs(!showLogs)}
            >
              {showLogs ? 'Скрыть логи ▲' : 'Логи агентов ▼'}
            </button>
          </div>
        </div>

        {pipeline.status === 'running' && (
          <div className={styles.progressContainer}>
            <div
              className={styles.progressBar}
              style={{ width: `${Math.max(5, pipeline.progress)}%` }}
            />
          </div>
        )}

        {showLogs && (
          <div className={styles.logDrawer}>
            {pipeline.logs.length === 0 ? (
              <div className={styles.logLine}>Логи агентов появятся здесь после запуска конвейера...</div>
            ) : (
              pipeline.logs.map((log, lIdx) => (
                <div key={lIdx} className={styles.logLine}>
                  {log}
                </div>
              ))
            )}
          </div>
        )}
      </section>

      {/* Pages Container */}
      <main className={styles.mainContent}>
        <div className={`${styles.mangaPages} ${styles[maxWidth]}`}>
          {images.length === 0 ? (
            <div className={styles.noPagesMessage}>
              <p>В этой версии страницы отсутствуют.</p>
            </div>
          ) : (
            images.map((imgUrl, i) => (
              <div key={i} className={styles.pageWrapper}>
                <div className={styles.pageNumberBadge}>Стр. {i + 1}</div>
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                  src={imgUrl}
                  alt={`Глава ${currentChapter.number} - Страница ${i + 1}`}
                  className={styles.pageImage}
                  loading={i > 2 ? 'lazy' : 'eager'}
                />
              </div>
            ))
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
            title="Предыдущая глава (Клавиша: ←)"
          >
            ← Пред. глава
          </button>
          <button
            className={styles.navChapterBtn}
            onClick={handleNextChapter}
            disabled={!data || selectedChapterIdx >= data.chapters.length - 1}
            title="Следующая глава (Клавиша: →)"
          >
            След. глава →
          </button>
        </div>

        <div className={styles.bottomInfo}>
          <span>
            Глава <strong>{currentChapter.number}</strong> • {images.length} страниц •{' '}
            <span className={styles.activeVersionText}>
              {currentVersion === 'v1_original' && 'Оригинал (ENG)'}
              {currentVersion === 'v2_cleaned' && 'Клининг (Очищенные баблы)'}
              {currentVersion === 'v3_translated' && 'Смысловой перевод (РУС)'}
            </span>
          </span>
        </div>

        <button
          className={styles.scrollTopBtn}
          onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}
          title="Наверх"
        >
          ▲ Наверх
        </button>
      </footer>
    </div>
  );
}
