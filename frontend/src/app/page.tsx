'use client';
import React, { useState, useEffect } from 'react';
import styles from './page.module.css';
import Link from 'next/link';

interface ChapterMeta {
  chapter: string;
  folder: string;
  pages_count: number;
}

export default function Home() {
  const [chapters, setChapters] = useState<ChapterMeta[]>([
    { chapter: '531', folder: 'chapter_531', pages_count: 12 },
    { chapter: '532', folder: 'chapter_532', pages_count: 13 },
    { chapter: '533', folder: 'chapter_533', pages_count: 14 },
    { chapter: '534', folder: 'chapter_534', pages_count: 11 },
    { chapter: '535', folder: 'chapter_535', pages_count: 13 },
    { chapter: '536', folder: 'chapter_536', pages_count: 14 },
    { chapter: '537', folder: 'chapter_537', pages_count: 8 },
    { chapter: '538', folder: 'chapter_538', pages_count: 8 },
    { chapter: '539', folder: 'chapter_539', pages_count: 9 },
    { chapter: '540', folder: 'chapter_540', pages_count: 8 },
    { chapter: '541', folder: 'chapter_541', pages_count: 12 },
    { chapter: '542', folder: 'chapter_542', pages_count: 8 }
  ]);

  useEffect(() => {
    fetch('/manga/chapters_index.json')
      .then((res) => res.json())
      .then((data) => {
        const list = data?.mangas?.['The_Ultimate_of_All_Ages']?.chapters;
        if (list && list.length > 0) {
          setChapters(list);
        }
      })
      .catch(() => {});
  }, []);

  return (
    <div className={styles.container}>
      <header className={styles.header}>
        <div className={styles.logo}>
          Manga<span>Lib</span> AI
        </div>
        <nav className={styles.nav}>
          <Link href="/studio" className={styles.navLink} style={{ color: '#38bdf8', fontWeight: 'bold' }}>⚡ Manga AI Studio</Link>
          <Link href="/" className={styles.navLink}>Каталог</Link>
          <a href="#chapters-list" className={styles.navLink}>Все главы (531–542)</a>
          <a href="#features" className={styles.navLink}>О системе</a>
        </nav>
      </header>

      <main className={styles.main}>
        <section className={styles.hero}>
          <div className={styles.heroBadge}>🔥 Интеллектуальный перевод & Клининг v3.0 SOTA</div>
          <h1 className={styles.title}>Сильнейший всех времён</h1>
          <p className={styles.subtitle}>
            Автономная система парсинга, интеллектуального удаления текста (клининга) и смыслового перевода манхуа и манги. Доступно 12 полностью переведенных глав!
          </p>
          <div className={styles.heroButtons}>
            <Link href="/reader/The_Ultimate_of_All_Ages?chapter=chapter_531" className={styles.primaryButton}>
              📖 Читать с Главы 531 →
            </Link>
            <Link href="/reader/The_Ultimate_of_All_Ages?chapter=chapter_542" className={styles.secondaryButton}>
              🔥 Свежая Глава 542
            </Link>
          </div>
        </section>

        <section id="updates" className={styles.featured}>
          <div className={styles.sectionHeader}>
            <h2 className={styles.sectionTitle}>Главный тайтл</h2>
            <span className={styles.sectionBadge}>12 глав переведено</span>
          </div>

          <div className={styles.grid}>
            <div className={styles.mangaCard} style={{ cursor: 'default' }}>
              <div className={styles.coverWrapper}>
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                  src="/manga/The_Ultimate_of_All_Ages/chapter_531/v3/page_001.webp"
                  alt="The Ultimate of All Ages"
                  className={styles.coverImage}
                  onError={(e) => {
                    e.currentTarget.src = '/manga/The_Ultimate_of_All_Ages/chapter_531/v1/page_001.webp';
                  }}
                />
                <div className={styles.cardBadge}>12 ГЛАВ</div>
              </div>
              <div className={styles.cardInfo}>
                <h3 className={styles.mangaTitle}>The Ultimate of All Ages (Сильнейший всех времён)</h3>
                <div className={styles.mangaChapterRow}>
                  <span className={styles.chapterTag}>Главы 531 – 542</span>
                  <span className={styles.pagesTag}>130 страниц</span>
                </div>
                <div className={styles.versionsPills}>
                  <span className={styles.pillOriginal}>RAW (v1)</span>
                  <span className={styles.pillCleaned}>Клининг (v2)</span>
                  <span className={styles.pillTranslated}>Перевод (v3)</span>
                </div>
                <div className={styles.tags}>
                  <span className={styles.tag}>Экшен</span>
                  <span className={styles.tag}>Культивация</span>
                  <span className={styles.tag}>Реинкарнация</span>
                  <span className={styles.tag}>SOTA v3.0</span>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section id="chapters-list" style={{ marginTop: '2.5rem', marginBottom: '3rem' }}>
          <div className={styles.sectionHeader}>
            <h2 className={styles.sectionTitle}>Список доступных глав</h2>
            <span className={styles.sectionBadge}>100% переведено на русский</span>
          </div>

          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))',
            gap: '1rem',
            marginTop: '1rem'
          }}>
            {chapters.map((ch) => (
              <Link
                key={ch.chapter}
                href={`/reader/The_Ultimate_of_All_Ages?chapter=chapter_${ch.chapter}`}
                style={{
                  background: 'rgba(30, 41, 59, 0.7)',
                  border: '1px solid rgba(56, 189, 248, 0.2)',
                  borderRadius: '12px',
                  padding: '1.2rem',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '0.5rem',
                  textDecoration: 'none',
                  color: '#fff',
                  transition: 'all 0.2s ease',
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.borderColor = '#38bdf8';
                  e.currentTarget.style.transform = 'translateY(-3px)';
                  e.currentTarget.style.boxShadow = '0 8px 20px rgba(56, 189, 248, 0.25)';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.borderColor = 'rgba(56, 189, 248, 0.2)';
                  e.currentTarget.style.transform = 'translateY(0)';
                  e.currentTarget.style.boxShadow = 'none';
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontWeight: 'bold', fontSize: '1.1rem', color: '#38bdf8' }}>Глава {ch.chapter}</span>
                  <span style={{ fontSize: '0.8rem', background: '#0284c7', padding: '2px 8px', borderRadius: '6px' }}>v3 РУС</span>
                </div>
                <span style={{ fontSize: '0.85rem', color: '#94a3b8' }}>{ch.pages_count} страниц (Strip)</span>
                <div style={{ marginTop: '0.4rem', fontSize: '0.85rem', color: '#38bdf8', fontWeight: '500' }}>
                  Читать онлайн →
                </div>
              </Link>
            ))}
          </div>
        </section>

        <section id="features" className={styles.featuresSection}>
          <h2 className={styles.featuresTitle}>3 Режима переключения</h2>
          <div className={styles.featuresGrid}>
            <div className={styles.featureCard}>
              <div className={styles.featureIcon}>1️⃣</div>
              <h3>Оригинальный скан (RAW)</h3>
              <p>Оригинальные страницы высокого разрешения без изменений (клавиша 1).</p>
            </div>
            <div className={styles.featureCard}>
              <div className={styles.featureIcon}>2️⃣</div>
              <h3>Клининг (Чистые баблы)</h3>
              <p>Компьютерное зрение OpenCV и Inpainting очищают баблы, сохраняя арт (клавиша 2).</p>
            </div>
            <div className={styles.featureCard}>
              <div className={styles.featureIcon}>3️⃣</div>
              <h3>Смысловой перевод</h3>
              <p>Контекстный перевод диалогов на русский с эллиптической автоподгонкой шрифта (клавиша 3).</p>
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}
