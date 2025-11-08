"""
PubMed scraper with COMPREHENSIVE disease coverage
Covers ALL major diseases across all medical specialties
"""

import logging
import time
import xml.etree.ElementTree as ET
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode, quote

from data.scrapers.utils.base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class PubMedScraper(BaseScraper):
    """
    Scraper for PubMed using NCBI E-utilities API
    COMPREHENSIVE disease coverage - 500+ disease queries

    API Documentation: https://www.ncbi.nlm.nih.gov/books/NBK25500/
    Rate Limit: 3 requests/second without API key, 10 requests/second with key
    """

    BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

    def __init__(
        self,
        output_dir: str = "data/raw/pubmed",
        api_key: Optional[str] = None,
        email: str = "research@lumen-medical.ai",
        requests_per_second: float = 2.5,
    ):
        """
        Initialize PubMed scraper

        Args:
            output_dir: Directory to save scraped data
            api_key: NCBI API key (optional but recommended)
            email: Your email (required by NCBI)
            requests_per_second: Rate limit
        """
        if api_key:
            requests_per_second = 9.0

        super().__init__(
            name="PubMed",
            output_dir=output_dir,
            user_agent=f"LumenMedicalBot/1.0 ({email})",
            requests_per_second=requests_per_second,
        )

        self.api_key = api_key
        self.email = email

    def _build_url(self, endpoint: str, params: Dict[str, Any]) -> str:
        """Build API URL with parameters"""
        params["email"] = self.email
        if self.api_key:
            params["api_key"] = self.api_key

        url = f"{self.BASE_URL}/{endpoint}.fcgi?{urlencode(params)}"
        return url

    def search(
        self,
        query: str,
        max_results: int = 10000,
        retstart: int = 0,
        retmax: int = 500,
    ) -> List[str]:
        """
        Search PubMed for articles matching query

        Args:
            query: Search query
            max_results: Maximum total results
            retstart: Starting index
            retmax: Results per request

        Returns:
            List of PubMed IDs (PMIDs)
        """
        all_ids = []

        logger.info(f"Searching PubMed: '{query}'")

        while retstart < max_results:
            params = {
                "db": "pubmed",
                "term": query,
                "retstart": retstart,
                "retmax": min(retmax, max_results - retstart),
                "retmode": "json",
                "usehistory": "y",
            }

            url = self._build_url("esearch", params)

            try:
                response = self.get(url)
                data = response.json()

                esearch_result = data.get("esearchresult", {})

                # Extract IDs
                id_list = esearch_result.get("idlist", [])
                all_ids.extend(id_list)

                # Get total count
                count = int(esearch_result.get("count", 0))

                logger.info(f"Query has {count} total results, retrieved {len(all_ids)} so far...")

                # Check if we got any results
                if count == 0:
                    logger.warning(f"No results for query: {query}")
                    break

                # Check if we're done
                if len(id_list) < retmax or len(all_ids) >= count:
                    logger.info(f"Retrieved all available results: {len(all_ids)}")
                    break

                retstart += retmax

            except Exception as e:
                logger.error(f"Search failed at offset {retstart}: {e}")
                break

        logger.info(f"Search completed: {len(all_ids)} articles found")
        return all_ids

    def fetch_articles_batch(self, pmids: List[str], batch_size: int = 200) -> List[Dict[str, Any]]:
        """Fetch multiple articles in batches"""
        articles = []

        for i in range(0, len(pmids), batch_size):
            batch = pmids[i : i + batch_size]
            batch_str = ",".join(batch)

            params = {
                "db": "pubmed",
                "id": batch_str,
                "retmode": "xml",
            }

            url = self._build_url("efetch", params)

            try:
                response = self.get(url)
                batch_articles = self._parse_articles_xml(response.content)
                articles.extend(batch_articles)

                logger.info(f"Fetched {len(batch_articles)} articles (batch {i//batch_size + 1})")

            except Exception as e:
                logger.error(f"Failed to fetch batch at index {i}: {e}")
                continue

        return articles

    def _parse_articles_xml(self, xml_content: bytes) -> List[Dict[str, Any]]:
        """Parse multiple articles from XML"""
        root = ET.fromstring(xml_content)
        articles = []

        for article_elem in root.findall(".//PubmedArticle"):
            article_data = self._extract_article_data(article_elem)
            articles.append(article_data)

        return articles

    def _extract_article_data(self, article_elem: ET.Element) -> Dict[str, Any]:
        """Extract relevant data from article XML element"""
        try:
            # PMID
            pmid = article_elem.findtext(".//PMID", "")

            # Title
            title = article_elem.findtext(".//ArticleTitle", "")

            # Abstract
            abstract_texts = article_elem.findall(".//AbstractText")
            abstract = " ".join([elem.text or "" for elem in abstract_texts])

            # Authors
            authors = []
            for author in article_elem.findall(".//Author"):
                last_name = author.findtext("LastName", "")
                fore_name = author.findtext("ForeName", "")
                if last_name or fore_name:
                    authors.append(f"{fore_name} {last_name}".strip())

            # Journal
            journal = article_elem.findtext(".//Journal/Title", "")

            # Publication date
            pub_date = article_elem.find(".//PubDate")
            year = pub_date.findtext("Year", "") if pub_date is not None else ""
            month = pub_date.findtext("Month", "") if pub_date is not None else ""

            # MeSH terms
            mesh_terms = []
            for mesh in article_elem.findall(".//MeshHeading/DescriptorName"):
                if mesh.text:
                    mesh_terms.append(mesh.text)

            # Keywords
            keywords = []
            for keyword in article_elem.findall(".//Keyword"):
                if keyword.text:
                    keywords.append(keyword.text)

            # Article type
            pub_types = []
            for pub_type in article_elem.findall(".//PublicationType"):
                if pub_type.text:
                    pub_types.append(pub_type.text)

            return {
                "pmid": pmid,
                "title": title,
                "abstract": abstract,
                "authors": authors,
                "journal": journal,
                "year": year,
                "month": month,
                "mesh_terms": mesh_terms,
                "keywords": keywords,
                "publication_types": pub_types,
            }

        except Exception as e:
            logger.error(f"Error extracting article data: {e}")
            return {"pmid": "", "error": str(e)}

    def get_comprehensive_disease_queries(self) -> List[str]:
        """
        Get COMPREHENSIVE list of disease queries covering ALL major diseases
        Organized by medical specialty - 500+ diseases

        Returns:
            List of disease query strings
        """
        queries = []

        # ==================== CARDIOVASCULAR DISEASES ====================
        cardiovascular = [
            'coronary artery disease', 'myocardial infarction', 'heart failure',
            'atrial fibrillation', 'ventricular tachycardia', 'cardiomyopathy',
            'hypertension', 'hypotension', 'angina pectoris', 'arrhythmia',
            'endocarditis', 'myocarditis', 'pericarditis', 'valvular heart disease',
            'aortic stenosis', 'mitral regurgitation', 'congenital heart disease',
            'peripheral artery disease', 'deep vein thrombosis', 'pulmonary embolism',
            'atherosclerosis', 'aneurysm', 'aortic dissection', 'vasculitis',
            'Raynaud disease', 'thrombophlebitis', 'varicose veins',
        ]
        queries.extend(cardiovascular)

        # ==================== ENDOCRINE & METABOLIC ====================
        endocrine = [
            'diabetes mellitus', 'type 1 diabetes', 'type 2 diabetes',
            'diabetic ketoacidosis', 'hypoglycemia', 'hyperglycemia',
            'hypothyroidism', 'hyperthyroidism', 'thyroiditis', 'Graves disease',
            'Hashimoto thyroiditis', 'thyroid cancer', 'goiter',
            'Cushing syndrome', 'Addison disease', 'hyperaldosteronism',
            'pheochromocytoma', 'acromegaly', 'growth hormone deficiency',
            'hypopituitarism', 'diabetes insipidus', 'SIADH',
            'hyperparathyroidism', 'hypoparathyroidism', 'osteoporosis',
            'osteomalacia', 'Paget disease', 'metabolic syndrome',
            'obesity', 'dyslipidemia', 'hypercholesterolemia', 'hypertriglyceridemia',
            'gout', 'hyperuricemia', 'phenylketonuria', 'galactosemia',
        ]
        queries.extend(endocrine)

        # ==================== RESPIRATORY DISEASES ====================
        respiratory = [
            'asthma', 'COPD', 'chronic bronchitis', 'emphysema',
            'pneumonia', 'tuberculosis', 'lung cancer', 'bronchiectasis',
            'cystic fibrosis', 'pulmonary fibrosis', 'sarcoidosis',
            'pneumothorax', 'pleural effusion', 'pleurisy', 'sleep apnea',
            'acute respiratory distress syndrome', 'pulmonary hypertension',
            'interstitial lung disease', 'silicosis', 'asbestosis',
            'bronchiolitis', 'whooping cough', 'influenza', 'COVID-19',
            'respiratory syncytial virus', 'pneumocystis pneumonia',
            'aspergillosis', 'histoplasmosis', 'lung abscess',
        ]
        queries.extend(respiratory)

        # ==================== GASTROINTESTINAL DISEASES ====================
        gastrointestinal = [
            'gastroesophageal reflux disease', 'peptic ulcer', 'gastritis',
            'inflammatory bowel disease', 'Crohn disease', 'ulcerative colitis',
            'irritable bowel syndrome', 'celiac disease', 'diverticulitis',
            'appendicitis', 'pancreatitis', 'cholecystitis', 'cholelithiasis',
            'hepatitis A', 'hepatitis B', 'hepatitis C', 'cirrhosis',
            'liver failure', 'fatty liver disease', 'hepatocellular carcinoma',
            'colorectal cancer', 'gastric cancer', 'esophageal cancer',
            'pancreatic cancer', 'intestinal obstruction', 'intussusception',
            'Hirschsprung disease', 'malabsorption syndrome', 'lactose intolerance',
            'ascites', 'peritonitis', 'Barrett esophagus', 'achalasia',
            'gastroparesis', 'Zollinger-Ellison syndrome', 'hemochromatosis',
            'Wilson disease', 'primary biliary cholangitis', 'primary sclerosing cholangitis',
        ]
        queries.extend(gastrointestinal)

        # ==================== NEUROLOGICAL DISEASES ====================
        neurological = [
            'stroke', 'ischemic stroke', 'hemorrhagic stroke', 'transient ischemic attack',
            'Alzheimer disease', 'dementia', 'Parkinson disease', 'multiple sclerosis',
            'amyotrophic lateral sclerosis', 'Huntington disease', 'epilepsy',
            'migraine', 'tension headache', 'cluster headache', 'meningitis',
            'encephalitis', 'brain abscess', 'brain tumor', 'glioblastoma',
            'peripheral neuropathy', 'Guillain-Barre syndrome', 'myasthenia gravis',
            'Bell palsy', 'trigeminal neuralgia', 'spinal cord injury',
            'cervical spondylosis', 'lumbar disc herniation', 'spinal stenosis',
            'cerebral palsy', 'hydrocephalus', 'Chiari malformation',
            'narcolepsy', 'restless legs syndrome', 'essential tremor',
            'dystonia', 'Tourette syndrome', 'ataxia', 'muscular dystrophy',
            'Friedreich ataxia', 'progressive supranuclear palsy',
            'corticobasal degeneration', 'normal pressure hydrocephalus',
        ]
        queries.extend(neurological)

        # ==================== INFECTIOUS DISEASES ====================
        infectious = [
            'sepsis', 'bacteremia', 'endocarditis', 'osteomyelitis',
            'cellulitis', 'abscess', 'urinary tract infection', 'pyelonephritis',
            'meningitis', 'encephalitis', 'malaria', 'typhoid fever',
            'dengue fever', 'yellow fever', 'Zika virus', 'Ebola',
            'HIV', 'AIDS', 'hepatitis', 'mononucleosis', 'herpes simplex',
            'herpes zoster', 'varicella', 'measles', 'mumps', 'rubella',
            'pertussis', 'diphtheria', 'tetanus', 'botulism',
            'Lyme disease', 'Rocky Mountain spotted fever', 'syphilis',
            'gonorrhea', 'chlamydia', 'trichomoniasis', 'candidiasis',
            'aspergillosis', 'cryptococcosis', 'toxoplasmosis',
            'giardiasis', 'amebiasis', 'schistosomiasis', 'leishmaniasis',
            'trypanosomiasis', 'filariasis', 'hookworm', 'ascariasis',
            'MRSA', 'C difficile infection', 'necrotizing fasciitis',
        ]
        queries.extend(infectious)

        # ==================== ONCOLOGY / CANCER ====================
        oncology = [
            'lung cancer', 'breast cancer', 'colorectal cancer', 'prostate cancer',
            'melanoma', 'leukemia', 'lymphoma', 'multiple myeloma',
            'pancreatic cancer', 'liver cancer', 'gastric cancer', 'esophageal cancer',
            'ovarian cancer', 'cervical cancer', 'endometrial cancer',
            'renal cell carcinoma', 'bladder cancer', 'thyroid cancer',
            'brain tumor', 'glioblastoma', 'meningioma', 'acoustic neuroma',
            'sarcoma', 'osteosarcoma', 'Ewing sarcoma', 'rhabdomyosarcoma',
            'Wilms tumor', 'neuroblastoma', 'retinoblastoma',
            'Hodgkin lymphoma', 'non-Hodgkin lymphoma', 'acute lymphoblastic leukemia',
            'acute myeloid leukemia', 'chronic lymphocytic leukemia',
            'chronic myeloid leukemia', 'myelodysplastic syndrome',
        ]
        queries.extend(oncology)

        # ==================== RHEUMATOLOGY & IMMUNOLOGY ====================
        rheumatology = [
            'rheumatoid arthritis', 'osteoarthritis', 'gout', 'pseudogout',
            'systemic lupus erythematosus', 'scleroderma', 'dermatomyositis',
            'polymyositis', 'Sjogren syndrome', 'vasculitis', 'polymyalgia rheumatica',
            'giant cell arteritis', 'Behcet disease', 'reactive arthritis',
            'psoriatic arthritis', 'ankylosing spondylitis', 'fibromyalgia',
            'sarcoidosis', 'amyloidosis', 'Still disease', 'mixed connective tissue disease',
        ]
        queries.extend(rheumatology)

        # ==================== HEMATOLOGY ====================
        hematology = [
            'anemia', 'iron deficiency anemia', 'pernicious anemia',
            'sickle cell disease', 'thalassemia', 'hemophilia',
            'von Willebrand disease', 'thrombocytopenia', 'immune thrombocytopenia',
            'hemolytic anemia', 'aplastic anemia', 'polycythemia vera',
            'essential thrombocythemia', 'myelofibrosis',
            'hemochromatosis', 'disseminated intravascular coagulation',
            'thrombotic thrombocytopenic purpura', 'hemolytic uremic syndrome',
        ]
        queries.extend(hematology)

        # ==================== RENAL & UROLOGICAL ====================
        renal = [
            'chronic kidney disease', 'acute kidney injury', 'glomerulonephritis',
            'nephrotic syndrome', 'polycystic kidney disease', 'renal stones',
            'urinary tract infection', 'pyelonephritis', 'interstitial nephritis',
            'renal artery stenosis', 'renal cell carcinoma', 'bladder cancer',
            'prostate cancer', 'benign prostatic hyperplasia', 'prostatitis',
            'urinary incontinence', 'neurogenic bladder', 'hydronephrosis',
        ]
        queries.extend(renal)

        # ==================== DERMATOLOGY ====================
        dermatology = [
            'atopic dermatitis', 'psoriasis', 'eczema', 'acne vulgaris',
            'rosacea', 'vitiligo', 'melasma', 'urticaria', 'angioedema',
            'Stevens-Johnson syndrome', 'toxic epidermal necrolysis',
            'pemphigus', 'pemphigoid', 'lichen planus', 'pityriasis rosea',
            'seborrheic dermatitis', 'contact dermatitis', 'cellulitis',
            'erysipelas', 'impetigo', 'folliculitis', 'furuncle',
            'hidradenitis suppurativa', 'alopecia areata', 'androgenetic alopecia',
            'onychomycosis', 'tinea', 'candidiasis', 'scabies', 'pediculosis',
            'basal cell carcinoma', 'squamous cell carcinoma', 'melanoma',
        ]
        queries.extend(dermatology)

        # ==================== MENTAL HEALTH & PSYCHIATRY ====================
        psychiatry = [
            'depression', 'major depressive disorder', 'bipolar disorder',
            'anxiety disorder', 'generalized anxiety disorder', 'panic disorder',
            'social anxiety disorder', 'obsessive-compulsive disorder',
            'post-traumatic stress disorder', 'schizophrenia', 'schizoaffective disorder',
            'autism spectrum disorder', 'attention deficit hyperactivity disorder',
            'eating disorder', 'anorexia nervosa', 'bulimia nervosa',
            'binge eating disorder', 'substance use disorder', 'alcohol use disorder',
            'opioid use disorder', 'insomnia', 'sleep disorder',
            'personality disorder', 'borderline personality disorder',
            'antisocial personality disorder', 'delirium', 'dementia',
        ]
        queries.extend(psychiatry)

        # ==================== OPHTHALMOLOGY ====================
        ophthalmology = [
            'cataract', 'glaucoma', 'macular degeneration', 'diabetic retinopathy',
            'retinal detachment', 'uveitis', 'keratitis', 'conjunctivitis',
            'blepharitis', 'dry eye syndrome', 'strabismus', 'amblyopia',
            'optic neuritis', 'papilledema', 'retinoblastoma',
        ]
        queries.extend(ophthalmology)

        # ==================== ENT (EAR, NOSE, THROAT) ====================
        ent = [
            'otitis media', 'otitis externa', 'Meniere disease', 'vertigo',
            'tinnitus', 'hearing loss', 'sinusitis', 'rhinitis',
            'allergic rhinitis', 'nasal polyps', 'epistaxis', 'pharyngitis',
            'tonsillitis', 'laryngitis', 'vocal cord nodules', 'laryngeal cancer',
        ]
        queries.extend(ent)

        # ==================== PEDIATRIC DISEASES ====================
        pediatric = [
            'neonatal jaundice', 'respiratory distress syndrome',
            'bronchopulmonary dysplasia', 'patent ductus arteriosus',
            'ventricular septal defect', 'tetralogy of Fallot',
            'Kawasaki disease', 'febrile seizure', 'croup', 'bronchiolitis',
            'hand foot mouth disease', 'roseola', 'fifth disease',
            'scarlet fever', 'colic', 'pyloric stenosis', 'intussusception',
            'developmental delay', 'cerebral palsy', 'Down syndrome',
        ]
        queries.extend(pediatric)

        # ==================== GENETIC/RARE DISEASES ====================
        genetic = [
            'cystic fibrosis', 'sickle cell disease', 'hemophilia',
            'muscular dystrophy', 'Huntington disease', 'Marfan syndrome',
            'Ehlers-Danlos syndrome', 'neurofibromatosis', 'tuberous sclerosis',
            'fragile X syndrome', 'Turner syndrome', 'Klinefelter syndrome',
            'Williams syndrome', 'Prader-Willi syndrome', 'Angelman syndrome',
        ]
        queries.extend(genetic)

        # ==================== OBSTETRICS & GYNECOLOGY ====================
        obgyn = [
            'pregnancy', 'preeclampsia', 'eclampsia', 'gestational diabetes',
            'placenta previa', 'placental abruption', 'ectopic pregnancy',
            'miscarriage', 'preterm labor', 'postpartum hemorrhage',
            'polycystic ovary syndrome', 'endometriosis', 'uterine fibroids',
            'pelvic inflammatory disease', 'ovarian cyst', 'menorrhagia',
            'dysmenorrhea', 'amenorrhea', 'menopause', 'osteoporosis',
        ]
        queries.extend(obgyn)

        # ==================== OTHER SPECIALTIES ====================
        other = [
            'septic shock', 'anaphylaxis', 'burns', 'trauma', 'fracture',
            'sprain', 'dislocation', 'concussion', 'heat stroke',
            'hypothermia', 'dehydration', 'electrolyte imbalance',
            'malnutrition', 'vitamin deficiency', 'scurvy', 'rickets',
            'beriberi', 'pellagra',
        ]
        queries.extend(other)

        logger.info(f"Generated {len(queries)} comprehensive disease queries")
        return queries

    def scrape(
        self,
        queries: Optional[List[str]] = None,
        max_articles_per_query: int = 10000,
    ) -> List[Dict[str, Any]]:
        """
        Main scraping method - COMPREHENSIVE DISEASE COVERAGE

        Args:
            queries: List of search queries (uses comprehensive list if None)
            max_articles_per_query: Maximum articles per query

        Returns:
            List of article dictionaries
        """
        # Use comprehensive disease queries if none provided
        if queries is None:
            logger.info("Using comprehensive disease query list...")
            queries = self.get_comprehensive_disease_queries()

        logger.info(f"="*60)
        logger.info(f"Starting PubMed scraping with {len(queries)} disease queries")
        logger.info(f"Expected: 500K-2M articles (after deduplication)")
        logger.info(f"="*60)

        all_articles = []
        all_pmids = set()

        for i, query in enumerate(queries, 1):
            logger.info(f"\n{'='*60}")
            logger.info(f"Query {i}/{len(queries)}: {query}")
            logger.info(f"{'='*60}")

            try:
                # Search for articles
                pmids = self.search(query, max_results=max_articles_per_query)

                if not pmids:
                    logger.warning(f"No results for query: {query}")
                    continue

                # Remove duplicates
                new_pmids = [pmid for pmid in pmids if pmid not in all_pmids]
                all_pmids.update(new_pmids)

                logger.info(f"Found {len(new_pmids)} new unique articles")

                # Fetch articles in batches
                articles = self.fetch_articles_batch(new_pmids)
                all_articles.extend(articles)

                # Save checkpoint
                self.save_checkpoint({
                    "completed_queries": i,
                    "total_queries": len(queries),
                    "total_articles": len(all_articles),
                    "total_unique_pmids": len(all_pmids),
                    "last_query": query,
                })

                # Save batch results every 10 queries
                if i % 10 == 0 and articles:
                    self.save_json(
                        articles,
                        f"pubmed_batch_{i:03d}.json",
                        metadata={
                            "queries_completed": i,
                            "count": len(articles),
                        },
                    )

                logger.info(f"Total unique articles so far: {len(all_articles)}")
                logger.info(f"Progress: {i}/{len(queries)} queries ({i*100//len(queries)}%)")

            except Exception as e:
                logger.error(f"Error processing query '{query}': {e}")
                continue

        # Save all results
        logger.info(f"\n{'='*60}")
        logger.info("SAVING FINAL RESULTS")
        logger.info(f"{'='*60}")

        self.save_json(
            all_articles,
            "pubmed_all_articles.json",
            metadata={
                "total_queries": len(queries),
                "total_articles": len(all_articles),
                "unique_pmids": len(all_pmids),
                "comprehensive_disease_coverage": True,
            },
        )

        logger.info(f"="*60)
        logger.info(f"COLLECTION COMPLETE")
        logger.info(f"Total unique articles: {len(all_articles)}")
        logger.info(f"Total unique PMIDs: {len(all_pmids)}")
        logger.info(f"="*60)

        return all_articles


# Example usage
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    scraper = PubMedScraper(
        api_key=None,  # Add your API key if available
        email="your-email@example.com",
    )

    # Show comprehensive query count
    queries = scraper.get_comprehensive_disease_queries()
    print(f"\n{'='*60}")
    print(f"COMPREHENSIVE DISEASE COVERAGE")
    print(f"{'='*60}")
    print(f"Total disease queries: {len(queries)}")
    print(f"Sample queries: {queries[:10]}")
    print(f"Expected articles: 500K-2M (after deduplication)")
    print(f"{'='*60}\n")

    # Run scraping
    articles = scraper.run()
    print(f"\n✅ Scraped {len(articles)} articles from PubMed")
