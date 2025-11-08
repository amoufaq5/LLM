"""
ClinicalTrials.gov scraper for clinical trial data
Comprehensive collection of trial information for drugs and treatments

API Documentation: https://clinicaltrials.gov/api/gui
Rate Limit: No official limit (be respectful, 2 req/sec)
"""

import logging
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode

from data.scrapers.utils.base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class ClinicalTrialsScraper(BaseScraper):
    """
    Scraper for ClinicalTrials.gov database
    """

    BASE_URL = "https://clinicaltrials.gov/api/v2"

    def __init__(self, output_dir: str = "data/raw/clinicaltrials"):
        """
        Initialize ClinicalTrials scraper

        Args:
            output_dir: Directory to save data
        """
        super().__init__(
            name="ClinicalTrials",
            output_dir=output_dir,
            user_agent="LumenMedicalBot/1.0",
            requests_per_second=2.0,
        )

    def search_studies(
        self,
        query: str = "",
        page_token: Optional[str] = None,
        page_size: int = 100,
    ) -> Dict[str, Any]:
        """
        Search for clinical trials

        Args:
            query: Search query
            page_token: Pagination token
            page_size: Results per page (max 1000)

        Returns:
            Search results with trials
        """
        params = {
            "query.term": query if query else "",
            "pageSize": min(page_size, 1000),
            "format": "json",
        }

        if page_token:
            params["pageToken"] = page_token

        query_string = urlencode({k: v for k, v in params.items() if v})
        url = f"{self.BASE_URL}/studies?{query_string}"

        try:
            response = self.get(url)
            return response.json()

        except Exception as e:
            logger.error(f"Error searching trials: {e}")
            return {}

    def get_all_studies(
        self,
        query: str = "",
        max_results: int = 50000,  # Collect comprehensive set
    ) -> List[Dict[str, Any]]:
        """
        Get all clinical trials matching query

        Args:
            query: Search query (empty = all)
            max_results: Maximum results to retrieve

        Returns:
            List of clinical trial records
        """
        all_studies = []
        page_token = None

        logger.info(f"Searching clinical trials: '{query or 'ALL'}'")

        while len(all_studies) < max_results:
            try:
                response = self.search_studies(
                    query=query,
                    page_token=page_token,
                    page_size=1000,
                )

                studies = response.get("studies", [])

                if not studies:
                    logger.info("No more results")
                    break

                # Extract relevant data from each study
                for study in studies:
                    protocol = study.get("protocolSection", {})

                    # Identification
                    ident = protocol.get("identificationModule", {})
                    nct_id = ident.get("nctId", "")
                    title = ident.get("officialTitle") or ident.get("briefTitle", "")
                    org_study_id = ident.get("orgStudyIdInfo", {}).get("id", "")

                    # Status
                    status_module = protocol.get("statusModule", {})
                    overall_status = status_module.get("overallStatus", "")
                    start_date = status_module.get("startDateStruct", {}).get("date", "")
                    completion_date = status_module.get("completionDateStruct", {}).get("date", "")

                    # Sponsor/Collaborators
                    sponsor_module = protocol.get("sponsorCollaboratorsModule", {})
                    lead_sponsor = sponsor_module.get("leadSponsor", {}).get("name", "")

                    # Description
                    desc_module = protocol.get("descriptionModule", {})
                    brief_summary = desc_module.get("briefSummary", "")
                    detailed_desc = desc_module.get("detailedDescription", "")

                    # Conditions
                    conditions_module = protocol.get("conditionsModule", {})
                    conditions = conditions_module.get("conditions", [])

                    # Interventions
                    interventions_module = protocol.get("armsInterventionsModule", {})
                    interventions = []
                    for intervention in interventions_module.get("interventions", []):
                        interventions.append({
                            "type": intervention.get("type", ""),
                            "name": intervention.get("name", ""),
                            "description": intervention.get("description", ""),
                        })

                    # Outcomes
                    outcomes_module = protocol.get("outcomesModule", {})
                    primary_outcomes = outcomes_module.get("primaryOutcomes", [])
                    secondary_outcomes = outcomes_module.get("secondaryOutcomes", [])

                    # Design
                    design_module = protocol.get("designModule", {})
                    study_type = design_module.get("studyType", "")
                    phases = design_module.get("phases", [])
                    design_info = design_module.get("designInfo", {})

                    # Eligibility
                    eligibility_module = protocol.get("eligibilityModule", {})
                    eligibility_criteria = eligibility_module.get("eligibilityCriteria", "")
                    sex = eligibility_module.get("sex", "")
                    min_age = eligibility_module.get("minimumAge", "")
                    max_age = eligibility_module.get("maximumAge", "")

                    study_data = {
                        "nct_id": nct_id,
                        "title": title,
                        "org_study_id": org_study_id,
                        "overall_status": overall_status,
                        "start_date": start_date,
                        "completion_date": completion_date,
                        "lead_sponsor": lead_sponsor,
                        "brief_summary": brief_summary,
                        "detailed_description": detailed_desc,
                        "conditions": conditions,
                        "interventions": interventions,
                        "primary_outcomes": primary_outcomes,
                        "secondary_outcomes": secondary_outcomes,
                        "study_type": study_type,
                        "phases": phases,
                        "design_info": design_info,
                        "eligibility_criteria": eligibility_criteria,
                        "sex": sex,
                        "min_age": min_age,
                        "max_age": max_age,
                    }

                    all_studies.append(study_data)

                logger.info(f"Retrieved {len(all_studies)} studies so far...")

                # Save checkpoint every 1000 studies
                if len(all_studies) % 1000 == 0:
                    self.save_checkpoint({
                        "studies_collected": len(all_studies),
                        "page_token": page_token,
                    })

                # Get next page token
                page_token = response.get("nextPageToken")

                if not page_token:
                    logger.info("Reached end of results")
                    break

            except Exception as e:
                logger.error(f"Error fetching studies: {e}")
                break

        logger.info(f"Total studies retrieved: {len(all_studies)}")
        return all_studies

    def scrape(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Main scraping method - collect comprehensive clinical trial data

        Returns:
            Dictionary of clinical trials by category
        """
        all_data = {}

        # Define key therapeutic areas
        therapeutic_areas = [
            ("Drug", "Interventional AND Drug"),
            ("Cancer", "Cancer OR Neoplasm"),
            ("Cardiovascular", "Cardiovascular OR Heart Disease"),
            ("Diabetes", "Diabetes"),
            ("Infectious Disease", "Infectious Disease OR Infection"),
            ("Neurological", "Neurological OR Neurology"),
            ("Immunology", "Immunology OR Autoimmune"),
            ("Mental Health", "Mental Health OR Psychiatric"),
            ("Respiratory", "Respiratory OR Lung Disease"),
        ]

        for area_name, query in therapeutic_areas:
            logger.info("=" * 60)
            logger.info(f"Collecting trials for: {area_name}")
            logger.info("=" * 60)

            studies = self.get_all_studies(query=query, max_results=5000)

            all_data[area_name] = studies

            # Save per category
            safe_name = area_name.lower().replace(" ", "_")
            self.save_json(
                studies,
                f"clinicaltrials_{safe_name}.json",
                metadata={
                    "category": area_name,
                    "query": query,
                    "count": len(studies),
                },
            )

        # Save all data
        total_studies = sum(len(studies) for studies in all_data.values())

        self.save_json(
            all_data,
            "clinicaltrials_all.json",
            metadata={
                "total_studies": total_studies,
                "categories": list(all_data.keys()),
            },
        )

        logger.info(f"Total clinical trials collected: {total_studies}")

        return all_data


# Example usage
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    scraper = ClinicalTrialsScraper()
    trials = scraper.run()

    total = sum(len(studies) for studies in trials.values())
    print(f"\n✅ Scraped {total} clinical trials")
