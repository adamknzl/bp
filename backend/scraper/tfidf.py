"""
@file    tfidf.py
@brief   TF-IDF keyword extraction over the textual content of organization websites.
@author  Adam Kinzel (xkinzea00)
"""

import time

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sqlalchemy import select

from database import Organization, Session
from utils import get_web_content


# Common Czech function words that carry little semantic value on their own.
_BASE_STOPWORDS = (
    "nebo", "jako", "jsou", "který", "která", "které", "byla", "bylo", "bude",
    "mají", "není", "jsme", "naše", "naši", "jejich", "jeho", "její", "mezi",
    "tento", "tato", "tyto", "tomto", "proti", "další", "také", "když", "aby",
    "roce", "roku", "všechny", "všech", "vše", "podle", "proto",
)

# Boilerplate vocabulary typical of website navigation, footers, and cookie banners.
_WEB_STOPWORDS = (
    "číst", "dále", "stránky", "stránka", "domů", "více", "informací", "informace",
    "email", "kontakt", "kontakty", "články", "článek", "novinky", "aktuality",
    "galerie", "úvod", "vyhledávání", "menu", "odkazy", "ke stažení", "zobrazit",
    "zpracování", "údajů", "cookies", "podmínky",
)

# Generic institutional vocabulary that would otherwise dominate the TF-IDF results.
_INSTITUTIONAL_STOPWORDS = (
    "český", "česká", "české", "českého", "českou", "republika", "republiky", "čr",
    "svaz", "svazu", "společnost", "společnosti", "organizace", "organizací",
    "sdružení", "spolek", "spolku", "asociace", "nadace", "shromáždění", "člen",
    "členové", "členů", "výbor", "zapsaný", "statut", "stanovy", "předseda",
    "činnost", "činnosti", "rámci", "praha", "praze", "brno",
)


def get_czech_web_stopwords() -> list[str]:
    """Return a combined list of Czech stopwords tailored for nonprofit websites."""
    return list(_BASE_STOPWORDS + _WEB_STOPWORDS + _INSTITUTIONAL_STOPWORDS)


def _is_meaningful_term(term: str) -> bool:
    """A term is considered meaningful if it is non-numeric and longer than 3 characters."""
    return not term.isnumeric() and len(term) > 3


def _print_top_keywords_per_org(names: list[str], urls: list[str], tfidf_matrix, feature_names, top_n: int = 15) -> None:
    """Print the top TF-IDF keywords for each organization."""
    print("\n" + "=" * 60)
    print(" TOP keywords")
    print("=" * 60)

    for i, name in enumerate(names):
        row_data = tfidf_matrix[i].T.todense()
        df = pd.DataFrame(row_data, index=feature_names, columns=['tfidf'])
        ranked = df.sort_values(by='tfidf', ascending=False).head(30)

        keywords = [
            word for word, val in ranked.itertuples()
            if val > 0 and _is_meaningful_term(word)
        ][:top_n]

        print(f" {name}")
        print(f" URL: {urls[i]}")
        print(f" Keywords: {', '.join(keywords)}")
        print("-" * 60)


def _print_global_top_keywords(tfidf_matrix, feature_names, top_n: int = 50) -> None:
    """Print the globally most frequent TF-IDF keywords across all organizations."""
    print("\n" + "#" * 60)
    print(" SUMMARY:")
    print("#" * 60)

    sum_tfidf = np.squeeze(np.asarray(tfidf_matrix.sum(axis=0)))
    df_global = pd.DataFrame({'slovo': feature_names, 'skore': sum_tfidf})
    df_global = df_global[
        (~df_global['slovo'].str.isnumeric()) & (df_global['slovo'].str.len() > 3)
    ]
    top = df_global.sort_values(by='skore', ascending=False).head(top_n)

    for rank, row in enumerate(top.itertuples(), 1):
        print(f" {rank:2d}. {row.slovo:<20} (skóre: {row.skore:.2f})")
    print("#" * 60 + "\n")


def _fetch_corpus() -> tuple[list[str], list[str], list[str]]:
    """
    Download web content for all organizations with a known URL.

    Returns:
        tuple: ``(names, urls, texts)`` of organizations whose pages yielded
        sufficient text for TF-IDF analysis.
    """
    session = Session()
    try:
        stmt = select(Organization.name, Organization.web_url).where(Organization.web_url != None)
        orgs = session.execute(stmt).all()
    finally:
        session.close()

    names: list[str] = []
    urls: list[str] = []
    texts: list[str] = []

    print(f"Downloading web content for {len(orgs)} organizations...")
    for org in orgs:
        print(f" - Trying: {org.web_url}")
        text = get_web_content(org.web_url)

        if text and len(text.strip()) > 50:
            names.append(org.name)
            urls.append(org.web_url)
            texts.append(text)

        time.sleep(1)

    return names, urls, texts


def run_raw_web_tfidf() -> None:
    """
    Compute and print TF-IDF keywords from the raw web content of all organizations.

    Outputs both per-organization top keywords and a global summary across the
    full corpus. Intended for exploratory analysis of the dataset.
    """
    try:
        names, urls, texts = _fetch_corpus()
        if not texts:
            print("Unable to download any valid texts.")
            return

        print("\nCalculating TF-IDF matrix from raw web content...")
        vectorizer = TfidfVectorizer(
            stop_words=get_czech_web_stopwords(),
            max_df=0.50,
            min_df=2,
            lowercase=True,
            ngram_range=(1, 1),
        )
        tfidf_matrix = vectorizer.fit_transform(texts)
        feature_names = vectorizer.get_feature_names_out()

        _print_top_keywords_per_org(names, urls, tfidf_matrix, feature_names)
        _print_global_top_keywords(tfidf_matrix, feature_names)

    except Exception as e:
        print(f"Unexpected error: {e}")


if __name__ == "__main__":
    run_raw_web_tfidf()