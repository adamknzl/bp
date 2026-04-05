import pandas as pd
import numpy as np
import time
from sklearn.feature_extraction.text import TfidfVectorizer
from sqlalchemy import select
from database import Session, Organization
from utils import get_web_content

def get_czech_web_stopwords():
    base_stopwords = [
        "nebo", "jako", "jsou", "který", "která", "které", "byla", "bylo", "bude", 
        "mají", "není", "jsme", "naše", "naši", "jejich", "jeho", "její", "mezi",
        "tento", "tato", "tyto", "tomto", "proti", "další", "také", "když", "aby",
        "roce", "roku", "všechny", "všech", "vše", "podle", "proto", "jsou"
    ]
    
    web_stopwords = [
        "číst", "dále", "stránky", "stránka", "domů", "více", "informací", "informace",
        "email", "kontakt", "kontakty", "články", "článek", "novinky", "aktuality", 
        "galerie", "úvod", "vyhledávání", "menu", "odkazy", "ke stažení", "zobrazit",
        "zpracování", "údajů", "cookies", "podmínky"
    ]
    
    institutional_stopwords = [
        "český", "česká", "české", "českého", "českou", "republika", "republiky", "čr",
        "svaz", "svazu", "společnost", "společnosti", "organizace", "organizací", 
        "sdružení", "spolek", "spolku", "asociace", "nadace", "shromáždění", "člen",
        "členové", "členů", "výbor", "zapsaný", "statut", "stanovy", "předseda",
        "činnost", "činnosti", "rámci", "praha", "praze", "brno"
    ]
    
    return base_stopwords + web_stopwords + institutional_stopwords

def run_raw_web_tfidf(limit=20):
    session = Session()
    try:
        stmt = select(Organization.name, Organization.web_url).where(Organization.web_url != None)#.limit(limit)
        orgs = session.execute(stmt).all()
        
        if not orgs:
            print("No organizations with URL in DB.")
            return

        names = []
        raw_texts = []
        urls_used = []

        print(f"Downloading web content for {len(orgs)} organizations...")
        for org in orgs:
            print(f" - Trying: {org.web_url}")
            text = get_web_content(org.web_url)
            
            if text and len(text.strip()) > 50: 
                names.append(org.name)
                urls_used.append(org.web_url)
                raw_texts.append(text)
            
            time.sleep(1) 

        if not raw_texts:
            print("Unable to download any valid texts.")
            return

        print("\nCalculating TF-IDF matrix from raw web content...")
        vectorizer = TfidfVectorizer(
            stop_words=get_czech_web_stopwords(),
            max_df=0.50,
            min_df=2,
            lowercase=True,
            ngram_range=(1, 1)
        )

        tfidf_matrix = vectorizer.fit_transform(raw_texts)
        feature_names = vectorizer.get_feature_names_out()

        print("\n" + "=" * 60)
        print(" TOP keywords")
        print("=" * 60)
        
        for i in range(len(names)):
            row_data = tfidf_matrix[i].T.todense()
            df_tfidf = pd.DataFrame(row_data, index=feature_names, columns=['tfidf'])
            
            top_keywords = df_tfidf.sort_values(by='tfidf', ascending=False).head(30)
            
            keywords_list = [word for word, val in top_keywords.itertuples() if val > 0 and not word.isnumeric() and len(word) > 3]
            keywords_list = keywords_list[:15]
            
            print(f" {names[i]}")
            print(f" URL: {urls_used[i]}")
            print(f" Keywords: {', '.join(keywords_list)}")
            print("-" * 60)



        print("\n" + "#" * 60)
        print(" SUMMARY:")
        print("#" * 60)

        sum_tfidf = np.squeeze(np.asarray(tfidf_matrix.sum(axis=0)))
        
        df_global = pd.DataFrame({'slovo': feature_names, 'skore': sum_tfidf})
        
        df_global = df_global[
            (~df_global['slovo'].str.isnumeric()) & 
            (df_global['slovo'].str.len() > 3)
        ]
        
        top_global_keywords = df_global.sort_values(by='skore', ascending=False).head(50)

        for rank, row in enumerate(top_global_keywords.itertuples(), 1):
            print(f" {rank:2d}. {row.slovo:<20} (skóre: {row.skore:.2f})")
            
        print("#" * 60 + "\n")

    except Exception as e:
        print(f"Unexpected error: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    run_raw_web_tfidf()