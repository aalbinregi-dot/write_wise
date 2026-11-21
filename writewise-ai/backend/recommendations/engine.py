"""
Knowledge Graph Recommendation Engine
Queries Neo4j for lesson recommendations based on detected writing weaknesses.
Falls back to CSV-based recommendations if Neo4j is unavailable.
"""
import logging
from pathlib import Path
from functools import lru_cache

import pandas as pd

logger = logging.getLogger(__name__)

NANDANA_ROOT = Path(__file__).resolve().parent.parent.parent.parent
ARCHIVE_DIR  = NANDANA_ROOT / 'archive (2)'

# Map problem category → competency category
PROBLEM_TO_COMPETENCY = {
    'Grammar':              'Grammar',
    'Spelling':             'Grammar',
    'Vocabulary':           'Vocabulary',
    'Readability':          'Writing',
    'Structure':            'Writing',
    'Argument Development': 'Writing',
    'Coherence':            'Writing',
    'Pronunciation':        'Pronunciation',
}

# Map grammar error type → lesson keywords
ERROR_TO_LESSON_KEYWORDS = {
    'Subject-Verb Agreement': ['subject', 'verb', 'agreement'],
    'Verb Tense Errors':      ['tense', 'verb'],
    'Article Error':          ['article', 'determiner'],
    'Punctuation Error':      ['punctuation'],
    'Spelling Error':         ['spelling'],
    'Word Choice':            ['vocabulary', 'word'],
}


@lru_cache(maxsize=1)
def _load_lessons() -> pd.DataFrame:
    """Load all lesson CSVs from the archive directory."""
    dfs = []
    lesson_files = {
        'Grammar':       'Grammar.csv',
        'Writing':       'Writing_Skill.csv',
        'Reading':       'Reading_Skill.csv',
        'Listening':     'Listening_Skill.csv',
        'Speaking':      'Speaking_Skill.csv',
        'Vocabulary':    'Vocabulary.csv',
        'Pronunciation': 'Pronunciation.csv',
    }
    for category, filename in lesson_files.items():
        path = ARCHIVE_DIR / filename
        if path.exists():
            try:
                df = pd.read_csv(path, encoding='utf-8-sig')
                df.columns = [c.strip() for c in df.columns]
                df['Category'] = category
                dfs.append(df)
            except Exception as e:
                logger.warning(f'Could not load {filename}: {e}')

    if not dfs:
        return pd.DataFrame()

    combined = pd.concat(dfs, ignore_index=True)
    combined.columns = [c.strip() for c in combined.columns]
    return combined


@lru_cache(maxsize=1)
def _load_neo4j_driver():
    """Try to connect to Neo4j. Returns driver or None."""
    try:
        from django.conf import settings
        from neo4j import GraphDatabase
        driver = GraphDatabase.driver(
            settings.NEO4J_URI,
            auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
        )
        driver.verify_connectivity()
        logger.info('✅ Neo4j connected')
        return driver
    except Exception as e:
        logger.warning(f'Neo4j not available: {e}. Using CSV fallback.')
        return None


def get_recommendations(student_id: int, problems: list) -> list:
    """
    Given a list of detected problems, return recommended lessons.
    Tries Neo4j first, falls back to CSV lookup.
    """
    if not problems:
        return []

    driver = _load_neo4j_driver()
    if driver:
        return _neo4j_recommendations(driver, problems)
    else:
        return _csv_recommendations(problems)


def _neo4j_recommendations(driver, problems: list) -> list:
    """Query Neo4j for lessons matching weak competencies."""
    recommendations = []
    categories = list({PROBLEM_TO_COMPETENCY.get(p['category'], 'Writing') for p in problems})

    cypher = """
    MATCH (l:Lesson)
    WHERE l.Category IN $categories
    RETURN l.Lesson_ID as lesson_id, l.Lesson as lesson,
           l.Category as category, l.Difficulty as difficulty,
           l.Time_to_learn as time_to_learn
    ORDER BY l.Difficulty ASC
    LIMIT 10
    """
    try:
        with driver.session() as session:
            result = session.run(cypher, categories=categories)
            for record in result:
                recommendations.append(dict(record))
    except Exception as e:
        logger.warning(f'Neo4j query failed: {e}')
        return _csv_recommendations(problems)

    return recommendations


def _csv_recommendations(problems: list) -> list:
    """Fall back to CSV-based lesson lookup."""
    lessons_df = _load_lessons()
    if lessons_df.empty:
        return []

    recommendations = []
    seen = set()
    priorities = {'HIGH': 0, 'MEDIUM': 1, 'LOW': 2}

    sorted_problems = sorted(problems, key=lambda p: priorities.get(p.get('priority', 'LOW'), 2))

    for problem in sorted_problems[:4]:
        category = PROBLEM_TO_COMPETENCY.get(problem['category'], 'Writing')
        cat_lessons = lessons_df[lessons_df['Category'] == category]

        # Try to match error keywords
        error_types = problem.get('error_types', [])
        keywords = []
        for et in error_types:
            keywords.extend(ERROR_TO_LESSON_KEYWORDS.get(et, []))

        if keywords and 'Lesson' in cat_lessons.columns:
            mask = cat_lessons['Lesson'].str.lower().apply(
                lambda x: any(k in x for k in keywords)
            )
            matched = cat_lessons[mask]
            if not matched.empty:
                cat_lessons = matched

        # Sort by difficulty
        if 'Difficulty' in cat_lessons.columns:
            cat_lessons = cat_lessons.sort_values('Difficulty')

        for _, row in cat_lessons.head(2).iterrows():
            lid = str(row.get('Lesson_ID', ''))
            if lid not in seen:
                seen.add(lid)
                recommendations.append({
                    'lesson_id':    lid,
                    'lesson':       str(row.get('Lesson', '')),
                    'category':     str(row.get('Category', category)),
                    'difficulty':   float(row.get('Difficulty', 1.0)) if pd.notna(row.get('Difficulty')) else 1.0,
                    'time_to_learn': int(row.get('Time_to_learn', 1)) if pd.notna(row.get('Time_to_learn')) else 1,
                    'priority':     problem.get('priority', 'MEDIUM'),
                    'reason':       f'Recommended based on: {problem["title"]}',
                })

    return recommendations[:8]


def get_all_lessons(category: str = None) -> list:
    """Get all lessons, optionally filtered by category."""
    df = _load_lessons()
    if df.empty:
        return []
    if category:
        df = df[df['Category'] == category]
    cols = [c for c in ['Lesson_ID', 'Lesson', 'Category', 'Difficulty', 'Time_to_learn'] if c in df.columns]
    return df[cols].fillna('').to_dict(orient='records')
