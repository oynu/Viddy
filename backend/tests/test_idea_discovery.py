import pytest
from backend.agents.idea_discovery import IdeaDiscoveryAgent, IdeaProposal
from backend.agents.researcher import ResearchAgent, ResearchedConcept
from backend.database.session import init_db, get_db

def test_idea_discovery_uniqueness(tmp_path):
    db_file = tmp_path / "test_ideas.db"
    init_db(str(db_file))
    
    agent = IdeaDiscoveryAgent(db_path=str(db_file))
    idea1 = agent.discover_next_idea()
    assert isinstance(idea1, IdeaProposal)
    assert len(idea1.title) > 5
    assert idea1.category in [
        "astronomy", "physics", "biology", "chemistry", "technology", "everyday_science", "psychology", "mathematics"
    ]
    assert idea1.curiosity_score >= 7.0
    
    # Save idea to history and verify duplicate avoidance
    agent.record_idea(idea1)
    idea2 = agent.discover_next_idea()
    assert idea2.title != idea1.title
    assert isinstance(idea2, IdeaProposal)

def test_research_agent():
    researcher = ResearchAgent()
    idea = IdeaProposal(
        title="What if Earth's Gravity Doubled?",
        category="physics",
        hook_angle="Human bodies crushed under their own weight",
        curiosity_score=9.2
    )
    result = researcher.research_topic(idea)
    assert isinstance(result, ResearchedConcept)
    assert len(result.key_facts) >= 3
    assert len(result.scientific_sources) >= 1
    combined_text = " ".join(result.key_facts).lower()
    assert "gravity" in combined_text or "weight" in combined_text or "pressure" in combined_text
