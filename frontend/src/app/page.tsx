'use client';
import styles from './page.module.css';
import Link from 'next/link';

export default function Home() {
  return (
    <div className={styles.container}>
      <header className={styles.header}>
        <div className={styles.logo}>
          Manga<span>Lib</span> AI
        </div>
        <nav className={styles.nav}>
          <Link href="/studio" className={styles.navLink} style={{ color: '#38bdf8', fontWeight: 'bold' }}>⚡ Manga AI Studio</Link>
          <Link href="/" className={styles.navLink}>Каталог</Link>
          <a href="#updates" className={styles.navLink}>Свежие главы</a>
          <a href="#features" className={styles.navLink}>О системе</a>
        </nav>
      </header>

      <main className={styles.main}>
        <section className={styles.hero}>
          <div className={styles.heroBadge}>🔥 Интеллектуальный перевод & Клининг</div>
          <h1 className={styles.title}>Сильнейший всех времён</h1>
          <p className={styles.subtitle}>
            Автономная система парсинга, интеллектуального удаления текста (клининга) и смыслового перевода манхуа и манги.
          </p>
          <div className={styles.heroButtons}>
            <Link href="/studio" className={styles.primaryButton}>
              ⚡ Manga AI Studio →
            </Link>
            <Link href="/reader/The_Ultimate_of_All_Ages" className={styles.secondaryButton}>
              📖 Читать Главу 531
            </Link>
          </div>
        </section>

        <section id="updates" className={styles.featured}>
          <div className={styles.sectionHeader}>
            <h2 className={styles.sectionTitle}>Доступные тайтлы</h2>
            <span className={styles.sectionBadge}>1 тайтл обновлен</span>
          </div>

          <div className={styles.grid}>
            <Link href="/reader/The_Ultimate_of_All_Ages" className={styles.mangaCard}>
              <div className={styles.coverWrapper}>
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                  src="/manga/The_Ultimate_of_All_Ages/chapter_531/v1_original/page_001.webp"
                  alt="The Ultimate of All Ages"
                  className={styles.coverImage}
                  onError={(e) => {
                    // Fallback to placeholder styling if backend isn't reachable yet
                    e.currentTarget.style.display = 'none';
                  }}
                />
                <div className={styles.cardBadge}>NEW</div>
              </div>
              <div className={styles.cardInfo}>
                <h3 className={styles.mangaTitle}>The Ultimate of All Ages (Сильнейший всех времён)</h3>
                <div className={styles.mangaChapterRow}>
                  <span className={styles.chapterTag}>Глава 531</span>
                  <span className={styles.pagesTag}>12 страниц (Strip)</span>
                </div>
                <div className={styles.versionsPills}>
                  <span className={styles.pillOriginal}>RAW</span>
                  <span className={styles.pillCleaned}>Клининг</span>
                  <span className={styles.pillTranslated}>Перевод</span>
                </div>
                <div className={styles.tags}>
                  <span className={styles.tag}>Экшен</span>
                  <span className={styles.tag}>Культивация</span>
                  <span className={styles.tag}>Реинкарнация</span>
                </div>
              </div>
            </Link>
          </div>
        </section>

        <section id="features" className={styles.featuresSection}>
          <h2 className={styles.featuresTitle}>3 Режима переключения</h2>
          <div className={styles.featuresGrid}>
            <div className={styles.featureCard}>
              <div className={styles.featureIcon}>1️⃣</div>
              <h3>Оригинальный скан (RAW)</h3>
              <p>Оригинальные страницы высокого разрешения без изменений.</p>
            </div>
            <div className={styles.featureCard}>
              <div className={styles.featureIcon}>2️⃣</div>
              <h3>Клининг (Чистые баблы)</h3>
              <p>Компьютерное зрение OpenCV сегментирует и очищает баблы от английского текста, сохраняя контуры и арт.</p>
            </div>
            <div className={styles.featureCard}>
              <div className={styles.featureIcon}>3️⃣</div>
              <h3>Смысловой перевод</h3>
              <p>Контекстный перевод диалогов на русский язык с автоподгонкой шрифта под размер бабла.</p>
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}
